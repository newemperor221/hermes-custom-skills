# TG Bot 409 Conflict 排查与修复

## 现象

`getUpdates` 返回 409：
```json
{"ok":false,"error_code":409,"description":"Conflict: terminated by other getUpdates request; make sure that only one bot instance is running"}
```

## 诊断流程

```bash
# 1. 用 token 直接测试 getUpdates（需要 source 环境变量）
source /opt/ip_sentinel_master/master.conf
timeout 10 curl -s "https://api.telegram.org/bot${TG_TOKEN}/getUpdates?offset=0&timeout=5"
# → 返回 409 表示有活跃连接

# 2. 检查进程数
ps aux | grep tg_master | grep -v grep
# → 如果有多个 bash tg_master.sh，就是多实例冲突

# 3. 确认 bot 没有 webhook 冲突
curl -s "https://api.telegram.org/bot${TG_TOKEN}/getWebhookInfo"
# → {"url": ""} 才是正确状态（轮询模式，无 webhook）
```

## 根因

**唯一原因：** 同一个 bot token 同时有 **2 个以上** 活跃的 `getUpdates` 长连接。

TG API 的单 bot 限制：
- 无论多少进程/线程/机器，一个 token 同时只能有 1 个 getUpdates 请求
- 第二个请求立即被 409 拒绝
- 旧的连接即使进程已死，TG 侧可能还保持连接数分钟（优雅关闭未做）

## 常见场景

| 场景 | 原因 |
|------|------|
| cron 看门狗错误 | `pgrep -x tg_master.sh` 永不匹配 → 每分钟都 spawn 新实例 |
| SSH 连接残留 | `pkill -f` 自杀后，旧连接被断，但 SSH 断开前已 spawn 的进程存活 |
| 误操作启动多个 | 同时运行了多个手动 `setsid` / `nohup` 实例 |
| 容器重启未清进程 | Docker/LXC 重启后旧进程未被清理，新服务又启动 |

## 修复步骤

### 1. 彻底清理所有 tg_master 进程

```bash
# 安全方式（避免自杀）
for pid in $(pgrep -f "tg_master.sh" | grep -v "supervise-daemon"); do
    kill -9 "$pid" 2>/dev/null
done
# 确认杀光
ps aux | grep tg_master | grep -v grep
```

### 2. 重置 offset（可选）

```bash
echo "0" > /opt/ip_sentinel_master/.tg_offset
```

offset=0 表示"从最早的未读消息开始"。如果 bot 从未用于节点注册，建议重置以便重新捕获所有注册消息。

### 3. 等待 TG API 释放旧连接

```bash
sleep 5
```

TG 侧的长连接在进程死后可能保持 30-60 秒。耐心等待。

### 4. 重新启动单实例

```bash
# 如果使用 OpenRC（推荐）
rc-service tg-master start

# 如果直接启动
bash /opt/ip_sentinel_master/tg_master.sh &
```

### 5. 验证

```bash
# 等 10 秒让第一次轮询完成
sleep 10
source /opt/ip_sentinel_master/master.conf

# 换一个新连接测（此时不应再有 409）
timeout 10 curl -s "https://api.telegram.org/bot${TG_TOKEN}/getUpdates?offset=0&timeout=5" 2>&1 | head -c 200
# → 应返回正常的 updates JSON（{"ok":true,"result":[...]}）

# 检查 offset 更新
cat /opt/ip_sentinel_master/.tg_offset
# → 应 > 0（如果有待处理消息）或保持 0（无消息，正常空闲）
```

## 预防

**永远只用一个单实例管理器：**
- ✅ Alpine：OpenRC `supervise-daemon`（见 SKILL.md「服务 2：tg-master」）
- ❌ 不要 cron 看门狗（`supervise-daemon` 自带重启策略）
- ❌ 不要同时用 cron + OpenRC + 手动后台

**验证单实例：**
```bash
# 应有且只有 1 个 bash tg_master.sh（外加 1 个 supervise-daemon 管理进程）
pgrep -af tg_master.sh | grep -v grep
```

## 长轮询时序参考

第一次启动 tg_master.sh 的时序：
1. t=0s: 初始化（source config, DB migrations ~0.5s）
2. t=0.5s: 首次 getUpdates?offset=0&timeout=30
   - 如果有待处理消息 → TG 立即返回（~1s），offset 更新
   - 如果没有消息 → 等 30 秒超时返回空，offset 保持 0
3. t=30.5s: sleep 1
4. t=31.5s: 第二次 getUpdates?offset=0&timeout=30（开始监听新消息）

所以首次启动后约 35 秒进入真正的消息监听状态。之后用户发消息会被秒回（长连接即时响应）。
