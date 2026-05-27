# WebSocket 连通性排查

## 典型症状
StatusShow 卡在"连接后端中…"，后端报错 `nodeget-server_list_all_agent_uuid 超时`。

## 排查路径

### 1. 确认前端部署平台
```bash
# 查 DNS 解析，看是 Vercel 还是 CF Pages
dig +short A <监控面板域名>
# Vercel → 有 vercel-dns.com 后缀
# CF Pages → 解析到 CF IP
```

### 2. 确认服务端 WS 端口可达（从外网测试）
```bash
# TCP 443 连通性
timeout 5 bash -c 'echo >/dev/tcp/statapi.<用户域名>/443' && echo "TCP OK" || echo "TCP FAIL"

# WebSocket 握手测试（Python）
python3 << 'EOF'
import socket, ssl, json, base64, struct, time

def ws_handshake(host, port):
    sock = socket.socket()
    ctx = ssl.create_default_context()
    ssock = ctx.wrap_socket(sock, server_hostname=host)
    ssock.settimeout(10)
    ssock.connect((host, port))
    key = base64.b64encode(b'hermes_test_key_123').decode()
    req = f"GET / HTTP/1.1\r\nHost: {host}:{port}\r\n"
    req += "Upgrade: websocket\r\nConnection: Upgrade\r\n"
    req += f"Sec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n"
    ssock.sendall(req.encode())
    resp = b""
    while b"\r\n\r\n" not in resp:
        resp += ssock.recv(4096)
    return resp.decode()

resp = ws_handshake('statapi.<用户域名>', 443)
print("101" in resp.split('\r\n')[0] and "WS OK" or "WS FAIL")
EOF
```

### 3. 从服务器本地测 WS（绕过网络层）
```bash
# 在 statapi 所在服务器上测
python3 << 'EOF'
# 同上，直接连 127.0.0.1:42211 或 unix socket
EOF
```

### 4. 检查 CF Bot Fight Mode
去 Cloudflare Dashboard → statapi 域名 → Security Settings：
- Bot Fight Mode 是否开启（会拦截 Vercel 等数据中心 IP 的 WS 请求）
- Security Level 是否过高

### 5. 浏览器 Console 直接测 WS
在 <监控面板域名> 页面 F12 → Console：
```js
const ws = new WebSocket('wss://statapi.<用户域名>');
ws.onopen = () => console.log('WS OK');
ws.onerror = (e) => console.log('WS FAIL', e);
```

## 结论快速判定
| 平台组合 | 结果 |
|---|---|
| Vercel → CF statapi | 可能被 Bot Fight Mode 拦 |
| CF Pages → statapi | 必败，CF Pages 不支持 WS |
| 直连（本地/同网络）→ statapi | 成功 → 排除服务端问题 |
