# TG Bot /start 重复响应排查

## 现象

用户向 IP-Sentinel bot 发送 `/start`，收到 **两条相同的回复**（面板消息）。

## 根因速查

| 原因 | 概率 | 判断方式 |
|------|------|----------|
| **多服务器同 token**（最常见） | 70% | 迁移后旧服务器上的 tg_master.sh 未清理 |
| **offset 被重置为 0** | 20% | 查看 `.tg_offset`，值远小于最新 update_id |
| **多个 tg_master.sh 实例** | 8% | `pgrep -af tg_master.sh` 显示多个进程 |
| **两个不同的 bot 使用相同配置** | 2% | 用户创建过多个 bot token，新老 bot 被混淆，需要查 `getMe` 区分 |

## 排查步骤（按顺序执行）

### 1. 确认进程数量

```bash
# 应该只有 1 个 bash tg_master.sh 进程
pgrep -af tg_master.sh | grep -v supervise | grep -v grep
```

如果多个 → 杀到剩一个。

### 2. 检查 offset

```bash
cat /opt/ip_sentinel_master/.tg_offset
# 发一条 /start 后 5 秒再查，offset 应增长
```

如果 offset 值很小（如 < 1000，而用户已经发了很多消息），说明曾被重置为 0，会重播所有旧消息。

### 3. 检查本机（Hermes Agent 运行的主机）

**在被远程服务器绕晕之前，先查本机。** IP-Sentinel 可能直接安装在本机系统上，通过 systemd 服务或 cron 运行。

```bash
# 本机快速检查
ps aux | grep -iE 'sentinel|tg_master|webhook'
systemctl list-units --type=service --state=running | grep -i sentinel
crontab -l | grep -i sentinel
find /opt /tmp -name '*sentinel*' -o -name '*tg_master*' 2>/dev/null
ss -tlnp | grep -E '4008[0-9]'
```

**常见场景：** 之前某个会话在本机安装了 IP-Sentinel，后来又在远程 VPS 上安装了另一个 Master。两个同时轮询同一 bot token → 两条回复。本机有则先清理再查远程。

### 4. 跨服务器搜索相同 token

**这是最容易被忽略的步骤之一：** 同 bot token 的 tg_master.sh 可能在多台服务器上同时运行。

```bash
# 在已知的 Master 服务器上查 token
grep TG_TOKEN /opt/ip_sentinel_master/master.conf

# SSH 到所有可能运行过 IP-Sentinel 的服务器，查是否有残留
for host in "<荷兰_IP>:46748" "<新加坡_IP>:10425" "其他可能的IP"; do
  ip=$(echo $host | cut -d: -f1)
  port=$(echo $host | cut -d: -f2)
  echo "=== $ip ==="
  ssh -o StrictHostKeyChecking=no -p $port -i ~/.ssh/user_key root@$ip \
    "pgrep -af tg_master 2>/dev/null || echo '无进程'; \
     ls /opt/ip_sentinel_master/ 2>/dev/null || echo '无目录'; \
     ls /opt/IP-Sentinel/ 2>/dev/null || echo '无旧目录'; \
     ls /opt/ip_sentinel/ 2>/dev/null || echo '无 agent 目录'"
done
```

**常见场景：** Master 从旧服务器迁移到新服务器后，旧服务器上的 tg_master.sh 没有停服，两个 tg_master.sh 同时轮询同一个 bot token。每条消息被两个 Master 各自处理一次 → 两条回复。

### 4. 跨服务器 token 冲突排查

如果多台服务器的 `tg_master.sh` 用同一个 TG bot token 同时轮询，TG API 会不断交替回应，每条消息被每台服务器独立处理。这是"两个窗口"最常见的原因。

**修复流程：**

```bash
# 1. 在每一台可能有残留的服务器上杀进程 + 删目录
ssh other-server "pkill -f tg_master.sh; rm -rf /opt/ip_sentinel_master; rm -f /etc/local.d/ip-sentinel*; rc-update del tg-master default 2>/dev/null"

# 2. 在主 Master 服务器上重启
rc-service tg-master restart

# 3. 发送 /start 验证（应只有一条回复）
```

### 6. 未知服务器发现（端口扫描法）

如果查遍所有已知服务器都找不到 tg_master.sh 残留，但 bot 仍然响应，可能有一个**你不知道的服务器**在跑 Master。

```bash
# 对于已知运行过 IP-Sentinel 但连不上的服务器，扫描常见端口
# 看是否有隐藏的 SSH 端口
for port in 22 2222 50000 50001 42186 42187 9922 22022 30000; do
  result=$(nc -zv -w 3 <IP> $port 2>&1)
  if echo "$result" | grep -q "open"; then
    # 检查是否是 SSH
    echo "open" | timeout 3 nc <IP> $port 2>&1 | head -1
  fi
done
```

**如果端口返回 `SSH-2.0-OpenSSH` banner：** 说明找到了 SSH 端口，尝试用用户密钥登录。

**实战案例：** <洛杉矶2_IP> 的 SSH 端口是 50000 而不是默认的 22。端口扫描揭示了这台沉睡的 Master 服务器。

如果步骤 3 没查到，但问题仍在，可能存在第三台你忘记了的服务器。检查方式：

```bash
# 用 TG API 查看 bot 的 getUpdates offset
TG_TOKEN=$(grep TG_TOKEN /opt/ip_sentinel_master/master.conf | cut -d'=' -f2)
curl -s "https://api.telegram.org/bot${TG_TOKEN}/getUpdates?offset=-1&limit=1"
# 看 update_id 是否与你本地的 offset 一致
# 如果不一致，说明有其他 getUpdates 长连接在消费消息
```

## Real-World Case Study: Four-Server Broom Sweep (2026-05-26)

**Symptom:** User sends /start to @ip_sentinel_tg_bot, gets **TWO identical reply panels** every time.

**Initial mistake:** Iterated server-by-server. Deleted Master from Singapore → bot still responded. Deleted from Dutch VPS → still responded. Deleted from local machine systemd → still responded. Finally found the real culprit on the fourth server.

**Root cause:** Four locations had IP-Sentinel Master components polling the same bot token:

| Location | SSH | What was found | How discovered |
|----------|-----|----------------|----------------|
| **本机** (Hermes host) | local | systemd `ip-sentinel-agent-daemon` (ACTIVE+ENABLED) + 3 systemd timers + cron watchdog | `systemctl list-units` + `crontab -l` |
| **新加坡** (<新加坡_IP>:10425) | 10425 | `/opt/ip_sentinel_master/` dir + cron | SSH check |
| **荷兰** (<荷兰_IP>:46748) | 46748 | OpenRC residual dirs + stale cron | SSH check |
| **无聊云洛杉矶** (<洛杉矶2_IP>) | **42185** | **Two concurrent tg_master.sh processes!** + cron + both agent and master dirs | Port scan found port 50000 OpenSSH banner; actual SSH on 42185 |

**Key takeaways:**
1. **Do NOT iterate server-by-server.** Broom sweep ALL known servers first.
2. **The local machine IS a server** — it can run systemd services + cron independently of any remote Master.
3. **SSH ports are not always 22.** Use nc sweep: `for port in 22 2222 50000 42185 48256 46748; do nc -zv IP $port; done`. If banner says `SSH-2.0-OpenSSH`, you found SSH.
4. **systemd timers survive file deletion.** Stamp files in `/var/lib/systemd/timers/stamp-ip-sentinel-*.timer` keep the timer alive. Must manually remove stamps + `daemon-reload`.
5. **Two tg_master.sh on one server = double response.** Cron watchdog respawned faster than processes died.
6. **The cron watchdog pattern `pgrep -f tg_master.sh || nohup bash ...` is dangerous.** `pgrep -x` doesn't match `bash` as process name, so watchdog always thinks process is dead and spawns another.

## Offsets 混乱排查

当 tg_master.sh 的 offset 值被误操作（如 `echo 0 > .tg_offset`）导致重置时：

- Master 会从 update_id=0 开始重播所有历史消息
- 包括所有旧 `/start` 命令 → 用户收到两条回复（一条是历史重播，一条是当前）
- 如果有多台服务器，offset 混乱加剧

**修复：**

```bash
# 1. 获取最新 update_id（发一个新消息给 bot，然后）
curl -s "https://api.telegram.org/bot${TG_TOKEN}/getUpdates?offset=-1&limit=1" | python3 -c "
import sys,json
data = json.load(sys.stdin)
if data.get('result'):
    last_id = data['result'][-1]['update_id']
    print(last_id + 1)
"

# 2. 设置为 last_update_id + 1（跳过所有旧消息）
echo "<last_update_id+1>" > /opt/ip_sentinel_master/.tg_offset

# 3. 重启
rc-service tg-master restart
```

## 最终手段：从头全部清除

如果排查后仍然有重复回复，最彻底的方案是：

1. **停掉本机 + 所有远程机器上的 Master**
2. **删光所有 IP-Sentinel 目录、自启、定时器、临时文件**
3. **让用户手动重装**

```bash
# === 本机（Hermes 主机）清理 ===
systemctl stop ip-sentinel-agent-daemon ip-sentinel-runner ip-sentinel-report ip-sentinel-updater 2>/dev/null
systemctl disable ip-sentinel-agent-daemon ip-sentinel-runner.timer ip-sentinel-report.timer ip-sentinel-updater.timer 2>/dev/null
rm -f /etc/systemd/system/ip-sentinel-*.service /etc/systemd/system/ip-sentinel-*.timer
rm -f /etc/systemd/system/*.wants/ip-sentinel-*
rm -f /var/lib/systemd/timers/stamp-ip-sentinel-*.timer
(crontab -l | grep -v sentinel) | crontab -
rm -rf /opt/ip_sentinel /opt/ip_sentinel_master /opt/IP-Sentinel
rm -f /tmp/ip-sentinel-* /tmp/install_sentinel.sh
rm -f /var/log/ip-sentinel-*.log

# === 每台可能的远程服务器上执行 ===
ssh remote "pkill -f tg_master.sh 2>/dev/null; pkill -f master.py 2>/dev/null;
  rm -rf /opt/ip_sentinel_master /opt/IP-Sentinel /opt/ip_sentinel;
  rm -f /etc/local.d/ip-sentinel*;
  for svc in tg-master ip-sentinel-master ip-sentinel; do
    rc-service \"\$svc\" stop 2>/dev/null;
    rc-update del \"\$svc\" default 2>/dev/null;
    rm -f \"/etc/init.d/\$svc\";
  done;
  echo '💀 Clean'"
```
