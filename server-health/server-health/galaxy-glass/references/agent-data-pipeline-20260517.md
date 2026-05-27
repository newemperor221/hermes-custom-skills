# Komari Agent 数据管道排查（2026-05-17）

## 症状

面板显示全部 13 台机器离线（`13 离线`），`records` 表 0 行，但 `clients.updated_at` 实时更新。

## 排查链路

### 1. 确认 Komari 服务运行中

```bash
# Komari server
ps aux | grep 'komari server'

# Galaxy proxy
ps aux | grep galaxy-proxy

# Agent (主控本地)
ps aux | grep '/opt/komari/agent'
```

### 2. 检查 API 是否正常返回数据

```bash
# 节点列表
curl -s http://127.0.0.1:25776/api/nodes | python3 -c '
import json,sys; d=json.load(sys.stdin)
nodes = d.get("data", d) if isinstance(d, dict) else d
print(f"Total: {len(nodes)} nodes")
for n in nodes:
  print(f"  {n.get(\"name\",\"?\")}: online={n.get(\"online\",\"?\")} cpu={n.get(\"cpu_usage\",\"?\")}")
'
```

### 3. 检查数据库

```bash
# 检查 records 表是否有数据
sqlite3 /opt/komari/data/komari.db 'SELECT COUNT(*) FROM records;'

# 查看最新的记录
sqlite3 /opt/komari/data/komari.db 'SELECT client, time, cpu FROM records_long_term ORDER BY time DESC LIMIT 10;'

# 查看各节点最后心跳时间
sqlite3 /opt/komari/data/komari.db 'SELECT uuid, name, updated_at FROM clients ORDER BY updated_at DESC;'
```

### 4. 检查 Galaxy Proxy 日志

```bash
cat /tmp/komari-start.log | grep -v uploadBasicInfo | tail -20
```

### 5. 检查 Cloudflare Tunnel 日志

```bash
cat /var/log/cloudflared.err | tail -20
# 常见错误：
# "Unable to reach the origin service" → proxy (:25774) 挂了
# "stream XXX canceled by remote" → 后端超时或崩溃
```

## 已知问题模式

### A. Records 表空但 clients.updated_at 在更新

**根因：** Galaxy Proxy 或 Komari Server 重启过，agents 的 WebSocket 断开。重连后只发心跳（`uploadBasicInfo`）不发指标数据。

**检查方式：**
```bash
# 检查 agent 日志中是否有 WebSocket 错误
# 登录到客户端 VPS
strings /opt/komari/agent | grep -i 'websocket\|handshake\|reconnect'
```

**修复：** 重启所有客户端 agent（需要逐一 SSH 到各 VPS 执行 `rc-service komari-agent restart` 或 `systemctl restart komari-agent`）。

### B. Galaxy Proxy 端口映射失效

**症状：** 客户端 agent 连接 `<荷兰_IP>:45774` 但 container 内 proxy 监听 `:25774`。

**根因：** LXD host 的端口映射（`45774 → container:25774`）丢失。之前靠 socat 或 iptables 做映射。

**修复：**
```bash
# 安装 socat（Alpine）
apk add socat

# 转发 45774 → 25774
socat TCP-LISTEN:45774,reuseaddr,fork TCP:127.0.0.1:25774 &
```

**持久化（OpenRC）：**
```bash
# 创建脚本
cat > /opt/komari/port-forward.sh << 'SCRIPT'
#!/bin/sh
while true; do
  socat TCP-LISTEN:45774,reuseaddr,fork TCP:127.0.0.1:25774
  sleep 1
done
SCRIPT
chmod +x /opt/komari/port-forward.sh

# 启动（后台）
nohup /opt/komari/port-forward.sh > /dev/null 2>&1 &
```

**更好的修复：** 修改 galaxy-proxy.py 同时监听两个端口：
```python
s = ThreadedHTTPServer(("0.0.0.0", 25774), PH)
s2 = ThreadedHTTPServer(("0.0.0.0", 45774), PH)
import threading
t = threading.Thread(target=s2.serve_forever, daemon=True)
t.start()
```

### C. 数据库迁移时被锁

**症状：** 日志中出现 `Error migrating old records: database is locked`

**根因：** 同时有大量 agent 连接发数据 + 定时迁移任务争锁。

**修复：** 重启 Komari server：
```bash
pkill -f 'komari server'
sleep 2
/opt/komari/komari server -l 0.0.0.0:25776 -d /opt/komari/data/komari.db &
```

**注意：** 重启后不要忘记同时重启 galaxy-proxy（如果 cwd 变了）。

### D. Agent 连接正常但 records 为空 — 需查看 agent 具体连接

```bash
# 在客户端 VPS 上检查 agent 网络连接
cat /proc/$(pgrep -f '/opt/komari/agent')/net/tcp | grep -v '00000000:0000' | head -10
# 解码：将 hex IP 转十进制：
# 7F333A1F = 127.51.58.31 → <荷兰_IP>
# B2CE = 45774
# 06 = TIME_WAIT, 01 = ESTABLISHED

# 检查 agent 的 WebSocket 连接
ss -tlnp 2>/dev/null || cat /proc/net/tcp6 | grep '01BB' | head -5  # 443 = Cloudflare WS
```

## 架构图

```
客户端 VPS (agent)
  ↓ HTTP POST /api/clients/uploadBasicInfo?token=xxx （心跳, ~3s间隔）
  ↓ WebSocket /api/... （实时数据通道）
  ↓ cloudflared tunnel（代理出口）
  ↓
<荷兰_IP>:45774 → socat → 127.0.0.1:25774 → galaxy-proxy.py
                                                       ↓
                                                 127.0.0.1:25776 → komari server
                                                                      ↓
                                                                komari.db
```

## 排查要点

1. **先看 records 表有没有数据** — 0 行 = agent 没上报指标，但 clients.updated_at 新 = 心跳正常
2. **查看 cloudflared.err** — 快速判断 proxy 是否曾宕机
3. **登录一台客户端 VPS 查 agent 连接** — `cat /proc/agent_pid/net/tcp` 比 curl 快得多
4. **不要假设端口映射一直有效** — LXD container 重启后 host 级的端口映射可能丢失
5. **重启前备份关键配置** — galaxy-proxy.py、port-forward.sh 等
