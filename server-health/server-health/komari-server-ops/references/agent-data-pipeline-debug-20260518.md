# Agent 数据管道深度排查（2026-05-18）

## 症状

- 页面显示 13 台机器全部"在线"（绿色圆点）
- 所有机器的 CPU/MEM/DSK/NET 均为 0.0%
- `records` 表 0 行（空），`records_long_term` 停在 `2026-05-17 09:30:00`
- Server 日志显示 `uploadBasicInfo` 持续 POST（3-5s 间隔），但**没有**任何 `uploadNodeData`、`reportSystemState` 或其他指标上报端点
- `/api/recent/{uuid}` 返回 `{"status":"success","message":""}`（空 data）

## 根因：Galaxy-Proxy WebSocket 隧道缺陷

**Galaxy-Proxy 的 `_ws()` 方法做的是原始 TCP 隧道，不是完整的 WebSocket 代理。**

```python
def _ws(self):
    try:
        be = socket.create_connection((BHOST, BPORT), timeout=10)
        self.send_response(101)
        self.send_header("Upgrade", "websocket")
        self.send_header("Connection", "Upgrade")
        # 直接把客户端的 WS 头透传回去，不真正握手
        for k in ("Sec-WebSocket-Accept","Sec-WebSocket-Protocol","Sec-WebSocket-Version","Sec-WebSocket-Extensions"):
            v = self.headers.get(k)
            if v: self.send_header(k, v)
        self.end_headers()
        tunnel(self.request, be)  # 原始 TCP 双向 tunnel
    except Exception as e:
        self.send_response(502); self.end_headers(); self.wfile.write(str(e).encode())
```

**问题：** 这个实现创建了原始 TCP 连接到后端（komari server），然后把客户端 WebSocket 帧原样转发过去。但后端 komari server **没有参与 WebSocket 握手**（两个端点各自独立完成握手，proxy 只是盲转发）。这意味着：

1. Agent → Proxy: WebSocket upgrade 请求（带 Sec-WebSocket-Key）
2. Proxy → Agent: 101 响应（带 Agent 的 header，而非后端计算的 Sec-WebSocket-Accept）
3. Agent 以为自己完成了握手，开始发送 WebSocket 帧（已用 Agent 自己的 key 加密）
4. Proxy 把帧原样转发到后端原始 TCP 连接
5. 后端 komari server 收到无法解析的 WebSocket 帧 → 丢弃或 Reset

**结果：** Agent 只通过 HTTP POST `uploadBasicInfo` 发送心跳，全量指标数据在断掉的 WebSocket 通道里永远传不出去。

## 数据管道架构

```
┌──────────────┐     HTTP POST uploadBasicInfo (心跳)     ┌──────────────────┐
│ Agent (VPS)  │ ──────────────────────────────────────►  │ Galaxy-Proxy     │
│              │     WebSocket RPC2 (指标数据)             │ :25774            │
│              │ ────[WS 帧 ── raw TCP tunnel ──]────►   │ ↓ raw TCP tunnel  │
└──────────────┘                                        │ ↓                 │
                                                         │ ┌─────────────┐   │
                                                         │ │ komari      │   │
                                                         │ │ server      │   │
                                                         │ │ :25776      │   │
                                                         │ └─────────────┘   │
                                                         └──────────────────┘
                                                                  │
                                                         ┌────────┴────────┐
                                                         │ komari.db       │
                                                         │ records: 0 行   │ ← 空！
                                                         └─────────────────┘
```

**Agent 实际连接路径（cloudflared）：**
```
Agent → Cloudflare CDN (162.159.153.2:443) → cloudflared tunnel → localhost:45774 → socat → :25774 (galaxy-proxy)
```

## 排查方法

### 第一步：确认问题范围

```bash
# 1. 检查 records 表
sqlite3 /opt/komari/data/komari.db 'SELECT COUNT(*) FROM records;'
# → 0 = 全量指标从未入库

# 2. 检查 records_long_term 最后写入时间
sqlite3 /opt/komari/data/komari.db 'SELECT client, time FROM records_long_term ORDER BY time DESC LIMIT 5;'
# → 停在昨天 = 数据库迁移后没再写入

# 3. 确认 agents 的心跳在发（clients 表在更新）
sqlite3 /opt/komari/data/komari.db 'SELECT uuid, name, updated_at FROM clients ORDER BY updated_at DESC LIMIT 5;'
# → updated_at 接近当前时间 = 心跳正常

# 4. 检查 server 日志中有没有指标上报端点
grep -c 'uploadNodeData\|reportSystemState\|uploadMetrics\|POST /api/clients/upload' /tmp/komari-start.log
# → 0 = 只有 uploadBasicInfo，没有指标上报
```

### 第二步：检查 Agent 实际连接

```bash
# 登录客户端 VPS
sshpass -p '密码' ssh -p PORT root@VPS_IP "ss -tnp | grep agent | head -5"
# → ESTAB 0 0 VPS_IP:PORT 162.159.153.2:443 → 走 Cloudflare CDN
# → 不是直接连 <荷兰_IP>:45774！

# 检查 agent 进程
sshpass -p '密码' ssh -p PORT root@VPS_IP "pgrep -af agent"
# → /opt/komari/agent -e http://<荷兰_IP>:45774 -t TOKEN --disable-web-ssh
```

### 第三步：检查 Galaxy-Proxy WebSocket 处理

```bash
# 检查 proxy 的 fd（是否有 active WS 连接）
sshpass -p 'OX8w$nE9A%tfqb6v' ssh -p 46748 root@<荷兰_IP> \
  "ls -la /proc/$(pgrep -f galaxy-proxy)/fd/ | grep socket"
# → 只有 LISTEN socket (fd 3)，无 ESTABLISHED 连接
```

### 第四步：验证数据链路

```bash
# 从 VPS 直接测试到面板
sshpass -p '密码' ssh -p PORT root@VPS_IP \
  "curl -s --connect-timeout 3 http://<荷兰_IP>:45774/api/public | head -5"
# → 成功返回 JSON（HTTP 通畅）

# 确认数据库可写
sshpass -p 'OX8w$nE9A%tfqb6v' ssh -p 46748 root@<荷兰_IP> \
  "sqlite3 /opt/komari/data/komari.db \"INSERT INTO records(client, time, cpu, ram, ram_total, disk, disk_total, net_in, net_out) VALUES('test-uuid', datetime('now'), 50.0, 1073741824, 2147483648, 10737418240, 21474836480, 1000, 500);\""
# → 手动 insert 成功 → 数据库未锁
```

### 第五步：排查端口架构

```bash
# 检查所有监听端口
sshpass -p 'OX8w$nE9A%tfqb6v' ssh -p 46748 root@<荷兰_IP> "ss -tlnp | grep -E '25774|25776|45774'"
# → LISTEN 0.0.0.0:25774  ← galaxy-proxy.py (Python3)
# → LISTEN *:25776         ← komari server
# → LISTEN 0.0.0.0:45774   ← socat (port-forward.sh)
```

## 修复方向

### 方案 A：修复 Galaxy-Proxy WebSocket 实现（推荐）

修改 `_ws()` 方法，使其在接收端**终结** WebSocket 连接（理解 WebSocket 帧），然后建立到后端的独立连接：

```python
import websocket  # 或 asyncio + websockets

def _ws(self):
    # 1. 接受客户端的 WebSocket 升级 (HTTP 101)
    # 2. 创建到 backend 的新 WebSocket 连接
    # 3. 双工桥接帧（非原始 TCP 隧道）
```

### 方案 B：Agent 绕过 WS，用 HTTP 上报全量指标

Komari agent 默认走 WebSocket RPC2。如果让 agent 降级为纯 HTTP（可能不支持全量指标），或给 komari server 添加 HTTP metrics 端点。

### 方案 C：Agent 直连 komari server（绕过 galaxy-proxy）

修改 agent endpoint 为 `http://<荷兰_IP>:25776`（komari server 直连端口），避开 galaxy-proxy 的 WebSocket 隧道问题。但需要注意端口 25776 的防火墙规则和 cloudflared 隧道路径。

## 关键教训

| 发现 | 分类 |
|------|------|
| Galaxy-Proxy `_ws()` 是原始 TCP 隧道，非完整 WS 代理 | **根本原因** |
| 所有 `::1` log entries = proxy 透传，不是 agent 直接连到 server | 排查方法 |
| 13 个不同的 token IDs 在 uploadBasicInfo log 里 = 13 个 agent 进程 | 系统认知 |
| Agent 实际连到 162.159.153.2:443 (Cloudflare)，不是直接连到面板 IP | 架构认知 |
| records 为空但 clients 在更新 = WebSocket 断了但 HTTP 心跳还在走 | 诊断模式 |
| Restart komari server 不解决问题 → galaxy-proxy 架构问题是根本 | 架构缺陷 |
| **不要假设 Python SimpleHTTPRequestHandler 的 WebSocket 实现能工作** — 它只处理 HTTP，WS 需要单独的库 | 一般原则 |
