# tg_master.sh 多实例洪水：刷屏排查指南

## 现象

- 点一次按钮 → bot 回好几条（甚至十几条）相同的消息
- `/start` 后收到多个相同的面板
- "深海声呐探测失败" 疯狂刷屏
- 战报/告警消息大量重复
- "**数据库中未找到该节点的通讯地址**" — 多个实例同时抢同一个 callback_query 回调。先处理完的调用了 `answerCallbackQuery` 确认该回调（TG 标记为"已处理"），后续实例再尝试查 DB 时可能因 callback 上下文已被清除（`CHAT_ID`/`TARGET_NODE` 变量在竞争条件中被覆盖或为空），导致查不到节点。虽然 DB 数据完好，但根因仍是多实例竞争。

## 根因

**多个 `tg_master.sh` 进程同时轮询同一个 bot token。** 每个进程独立接收同一批 TG 消息并分别处理——每个进程都认为自己是唯一实例。

```
TG 消息 ──→ tg_master.sh #1  →  处理 → 回复 "探测失败"
TG 消息 ──→ tg_master.sh #2  →  处理 → 回复 "探测失败"
TG 消息 ──→ tg_master.sh #3  →  处理 → 回复 "探测失败"
...
TG 消息 ──→ tg_master.sh #16 →  处理 → 回复 "探测失败"
                              ↓
                    用户收到 16 条 "探测失败"
```

这种模式与 409 Conflict（连接被拒）是 **两个不同阶段** 的问题：
1. **初期（≤5 个实例）** → 每个实例都正常轮询，但重复处理消息 → 洪水刷屏
2. **后期（≥10 个实例）** → offset 竞争导致混乱，部分实例收到 409 Conflict → 部分停摆，部分继续刷

### 多服务器同 token 冲突（跨服务器实例）

**现象：** 两台不同物理服务器上各跑一个 tg_master.sh，共享同一个 TG Bot Token。用户发一条消息，两台服务器各自处理并回复，用户收到重复响应（包括 `/start` 面板、按钮操作结果）。

**典型场景：** 迁移 Master 到新服务器后，旧服务器的 tg_master.sh 仍在运行（或 OpenRC 服务仍在 runlevel 中，下次重启后自动启动）。

**诊断方法：**

```bash
# 在所有可能运行 tg_master.sh 的服务器上检查
for host in server1 server2; do
  ssh "$host" "hostname; pgrep -af tg_master.sh | grep -v supervise; echo '---'"
done
```

从 **token 角度**验证——TG Bot 对所有使用同一 token 的长轮询连接一视同仁：
- 两个独立服务器 = 两个独立的 getUpdates 长连接
- TG 将更新随机分配给其中一个连接
- 两个连接独立维护各自的 offset，导致部分更新被处理两次，部分被跳过
- `getUpdates` 的 offset 在不同服务器之间不同步

**修复：**

```bash
# 1. 在旧服务器上，停服并移除自启
rc-service ip-sentinel-master stop 2>/dev/null || rc-service tg-master stop 2>/dev/null
rc-update del ip-sentinel-master default 2>/dev/null
rc-update del tg-master default 2>/dev/null

# 2. 杀残余进程
pkill -f tg_master.sh 2>/dev/null

# 3. 可选：删除配置（防止下次误启动）
rm -rf /opt/ip_sentinel_master

# 4. 在新服务器上重启 Master（清 offset 重新开始）
rc-service tg-master restart
```

**避免：** 迁移后务必检查旧服务器的服务状态和自启配置。不留旧进程在 runlevel 中。

## 常见导致多实例的原因

| 原因 | 触发生成速度 | 典型规模 |
|------|-------------|---------|
| **cron 看门狗错误**（`pgrep -x` 永不匹配） | 每分钟 1 个 | 10-30 个 |
| **SSH 断联后残留** | 每次手动启动 | 2-5 个 |
| **同时用 cron + OpenRC + 手动** | 混合 | 3-8 个 |
| **OpenRC 未配 `supervise-daemon`** | 崩溃重启 | 2-3 个 |

### cron 看门狗是如何造出 16 个实例的

```sh
# ❌ 错误的看门狗
#!/bin/sh
PID_FILE=/var/run/ip-sentinel-master.pid
if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    exit 0
fi
nohup bash /opt/ip_sentinel_master/tg_master.sh >/dev/null 2>&1 &
```

如果 `PID_FILE` 指向 webhook.py 的 PID，而 **tg_master.sh 已经在跑**，这个看门狗检查的是 webhook.py 而不是 tg_master.sh，所以：
- webhook.py 活着 → 看门狗 exit 0 → **不产生新实例**（这个 case 是安全的）

但如果看门狗检查的是 **tg_master.sh 自身**（比如有人改成了检查 `.tg_pid` 文件），且用了 `pgrep -x tg_master.sh`：

```sh
# ❌ 错误的 tg_master.sh 健康检查
if pgrep -x tg_master.sh > /dev/null; then
    exit 0
fi
nohup bash /opt/ip_sentinel_master/tg_master.sh &
```

`pgrep -x tg_master.sh` **永远返回空**，因为：
- 进程名（`COMMAND` 列）是 **`bash`**，不是 `tg_master.sh`
- `-x` 只匹配进程名，不匹配完整命令行
- 进程名为 `bash`，命令行为 `bash /opt/.../tg_master.sh`，`pgrep -x` 只看前者

→ 每分钟看门狗都认为 tg_master.sh 挂了，启动一个新实例 → 1 小时后 60 个实例。

## 排查流程

### 1. 数一下有多少个 tg_master.sh

```bash
# 准确的计数（排除 supervise-daemon 和管理进程）
ps aux | grep tg_master | grep -v grep | grep -v supervise | awk '{print $2, $11, $12}'
# 或
pgrep -f "tg_master.sh" | grep -v -E "supervise|grep" | wc -l
```

如果输出多于 1 行（不包括 supervise-daemon），就是多实例问题。

### 2. 检查看门狗是否在捣乱

```bash
crontab -l
grep tg_master /var/spool/cron/crontabs/root /etc/crontab 2>/dev/null
ls /etc/cron.d/*tg_master* /etc/periodic/*/ip-sentinel* 2>/dev/null
```

### 3. 检查 OpenRC 是否重复

```bash
rc-service tg-master status
rc-service ip-sentinel-master status
```

## 修复

### 一次性清理所有多余实例

```bash
# 1. 停止 OpenRC 服务
rc-service tg-master stop

# 2. 手动杀光所有 tg_master.sh（排除 supervise-daemon）
for pid in $(pgrep -f "tg_master.sh" | grep -v "supervise-daemon"); do
    kill -9 "$pid" 2>/dev/null
done

# 3. 确认杀光
ps aux | grep tg_master | grep -v grep

# 4. 重置 offset（可选）
echo "0" > /opt/ip_sentinel_master/.tg_offset

# 5. 等待 TG API 释放旧长连接
sleep 3

# 6. 重启单实例
rc-service tg-master start

# 7. 验证只有 1 个实例
pgrep -af tg_master.sh | grep -v grep
# 应有：
#   PID1 supervise-daemon tg-master ...
#   PID2 /bin/bash /opt/ip_sentinel_master/tg_master.sh
```

### 删除错误的看门狗

```bash
# 删除 cron 看门狗文件
rm -f /etc/periodic/ip-sentinel/cron_watchdog

# 或删除 cron 条目
crontab -e  # 注释/删除包含 tg_master 的行
```

### 替换为正确的 OpenRC 服务

用 `supervise-daemon` 代替 cron 看门狗：

```bash
cat > /etc/init.d/tg-master << 'SERVICE'
#!/sbin/openrc-run

name="tg-master"
description="IP-Sentinel TG Bot Polling Master (getUpdates mode)"

supervisor=supervise-daemon
command="/bin/bash"
command_args="/opt/ip_sentinel_master/tg_master.sh"
command_background=true
pidfile="/run/tg-master.pid"
command_user="root:root"

depend() {
    need net
    after ip-sentinel-master
}

start_pre() {
    checkpath -f -m 0644 /var/log/tg-master.log
    echo "0" > /opt/ip_sentinel_master/.tg_offset
}
SERVICE
chmod +x /etc/init.d/tg-master
rc-service tg-master start
rc-update add tg-master default
```

## 对 Agent 的连锁影响

多实例洪水不仅刷用户的 TG，还会对 Agent 造成实际伤害：

| 实例数 | 点一次"投放声呐" → Agent 被锤次数 |
|:------:|:--------------------------------:|
| 1 | 1 次（正常） |
| 5 | 5 次（轻微冗余） |
| 16 | 16 次！每个都独立执行 `mod_quality.sh` |

如果 agent 的 `ip_probe.sh` 需要 5 分钟超时（`timeout 300`），16 个同时请求可能导致：
- CPU 和内存飙升
- 端口连接数暴增
- 多个 `mod_quality.sh` 同时发 TG 消息 → 又一轮重复

### 清理陷阱：orphan webhook.py（旧端口残留）

迁移 Master 到新端口（如 50000 → 42186）后，旧 webhook.py 进程可能仍在旧端口监听。两个 webhook.py 同时运行（不同端口）会导致日志分散、端口混淆、配置管理混乱。

```bash
# 检查是否有多个 webhook.py（不同端口）
ps aux | grep webhook | grep -v grep
# 输出示例：
# root 17457 python3 webhook.py 50000   ← 旧端口残留
# root 18198 python3 webhook.py 42186   ← 新服务

# 杀掉旧的
kill -9 <OLD_PID>
```

**最佳实践**：迁移/重配端口后立即检查 `ps aux | grep webhook`，杀掉旧端口上的进程。

## "深海声呐探测失败" 的特殊性

这个失败消息不是 master 发的，而是 **Agent 端的 `mod_quality.sh`** 直接通过 TG API 发送的（不经过 tg_master.sh）：

```
[TG 用户] → 点"投放声呐"按钮
    → tg_master.sh 收到回调
    → 向 Agent 发 /trigger_quality 请求
    → Agent 的 webhook.py 收到，执行 mod_quality.sh
    → mod_quality.sh 运行 ip_probe.sh（查询 IP 质量）
    → 如果超时或无有效回波
    → mod_quality.sh 直接用 TG_TOKEN 发出 "❌ 深海声呐探测失败"
    → TG 用户收到消息（跳过 master）
```

所以 **16 个 tg_master.sh = Agent 被触发 16 次 = 16 条"探测失败"**。

## "数据库中未找到该节点的通讯地址" 排查

这个错误可能由两种不同根因导致，**区分方法很简单：**

| 根因 | 特征 | 修复 |
|------|------|------|
| **多实例洪水**（16 个 tg_master.sh 抢同一个回调） | 清理多实例后错误消失，DB 数据完好 | 杀多余实例，用 OpenRC supervise-daemon 管理单实例 |
| **单实例仍报错**（Debug 日志分析） | 清理后只剩 1 个进程时错误仍持续 | 加 debug 日志排查回调变量值 |

### 加 Debug 日志

在 tg_master.sh 中找到 `google:*|trust:*|run:*|report:*|log:*|quality:*)` 回调段，在 `CHAT_ID=$(echo "$CHAT_ID" | tr -cd '0-9-')` 后插入：

```bash
echo "[Q-DEBUG] callback: CHAT_ID=$CHAT_ID TARGET_NODE=$TARGET_NODE TEXT=$TEXT" >> /tmp/tg_debug.log
```

⚠️ 有多处相同的 `CHAT_ID=...tr -cd` 行（svq 处理器、manage 处理器各有一处），必须定位到 quality 段。用 Python 基于 section 特征字符串定位：

```python
target = '# 【核心升级 v4.0.0】增加拦截规则，支持 quality 前缀'
idx = content.find(target)
```

触发按钮后检查 `/tmp/tg_debug.log` 看 CHAT_ID、TARGET_NODE、TEXT 的真实值。

## 预防 checklist

- [ ] 只用一种实例管理方式（OpenRC `supervise-daemon`）
- [ ] 不要用 cron 看门狗管理 tg_master.sh
- [ ] 不要在 SSH 命令中用 `pkill -f tg_master.sh`（自杀风险）
- [ ] 迁移后检查旧进程是否残留
- [ ] 启动前先 `kill -9` 所有旧 tg_master 进程
- [ ] 确保 `pgrep -x tg_master.sh` 没有出现在任何脚本中

## Offset 被重置的灾难：重播所有历史消息

**现象：** 重启 tg_master 后，offset 变成了 0 或 1，bot 开始重新处理所有历史消息。用户收到几十条重复的 /start 面板、按钮回复等。

**根因：** 以下任一情况都会导致 offset 重置：
1. **OpenRC 服务的 `start_pre()` 中写死了 `echo "0" > .tg_offset`** — 每次 restart 都会重置
2. **.tg_offset 文件被杀进程波及被误写** — 多个 `kill -9` 循环中，offset 文件可能被截断或写空
3. **用 `getUpdates` 返回空结果时 Python 解析返回 "1"** — 新 token 没有历史消息时，`jq -r ".result[-1].update_id"` 返回空，+1 后为 1
4. **手动 `echo "0" > .tg_offset` 作为"修复"步骤** — 重置 offset 不是修复，反而会引发二次灾难

**恢复步骤（已有受害者）：**
```bash
# 1. 先停 master
kill $(pgrep -f tg_master.sh | grep -v supervise)

# 2. 确认当前最新 update_id
LATEST_OFFSET=$(curl -s "https://api.telegram.org/bot${TG_TOKEN}/getUpdates" |
  jq -r '.result[-1].update_id // empty')
if [ -z "$LATEST_OFFSET" ]; then
  # 没有历史消息时，从当前 offset 继续
  cat /opt/ip_sentinel_master/.tg_offset
else
  # 有历史消息时，设为最新 + 1 跳过所有旧消息
  echo $((LATEST_OFFSET + 1)) > /opt/ip_sentinel_master/.tg_offset
fi

# 3. 重启 master
bash /opt/ip_sentinel_master/tg_master.sh &>/dev/null &

# 4. 验证 offset 不再回退
cat /opt/ip_sentinel_master/.tg_offset

# 5. 发一条新 /start 验证只回复一次
```

**预防：** OpenRC 服务的 `start_pre()` 不要碰 offset 文件。首次安装时手动 `echo "0" > .tg_offset`，之后永远不动。
