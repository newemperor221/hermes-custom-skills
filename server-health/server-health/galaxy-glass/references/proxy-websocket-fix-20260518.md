# Galaxy-Proxy WebSocket 修复（2026-05-18）

## 问题
Agent 实时指标数据不上报。面板显示 13 台机器"在线"但全部 CPU/MEM/DSK/NET = 0.0%。

## 诊断路径
1. 看 `komari.db` 的 `records` 表行数 → 0（无指标数据写入）
2. 看 `records_long_term` → 停在 2026-05-17 09:30（上次迁移后无新记录）
3. 看 agent 日志 `journalctl -u komari-agent` → `Failed to connect to WebSocket: 400 Bad Request: missing required Host header`
4. 看 agent 建立的 socket 连接 → 连到了 Cloudflare IP（162.159.153.2:443），不是直接到主控
5. 确认链路：Agent → Cloudflare CDN → cloudflared 隧道 → localhost:45774 → socat → localhost:25774 → galaxy-proxy → komari server:25776
6. 确认 HTTP 通但 WebSocket 不通：直接 curl WebSocket upgrade 到 31.58.51.127:45774 返回 400

## 根因
galaxy-proxy.py 的 `_ws()` 方法：
- 收到客户端的 WebSocket upgrade 请求后，**立即**回 101 Switching Protocols
- 然后创建 raw TCP 连接到后端 → `tunnel()`
- **没有把客户端的 upgrade 请求转发给后端**，后端没有参与 WebSocket 握手
- 同时 `do_GET` 路由检测 `Upgrade: websocket` 头正常跳转到 `_ws()`

## 修复

### 1. `_ws()` — 先转发 upgrade 请求到后端，等后端握手后再隧道
```python
def _ws(self):
    try:
        # Forward the client's full WebSocket upgrade request to the backend
        be = socket.create_connection((BHOST, BPORT), timeout=10)
        req_line = f"{self.command} {self.path} {self.request_version}\r\n"
        be.sendall(req_line.encode())
        for k, v in self.headers.items():
            if k.lower() not in ("transfer-encoding", "content-encoding", "content-length"):
                be.sendall(f"{k}: {v}\r\n".encode())
        be.sendall(b"\r\n")
        # Read the backend's response (including Sec-WebSocket-Accept)
        resp = b""
        while b"\r\n\r\n" not in resp:
            chunk = be.recv(4096)
            if not chunk:
                raise ConnectionError("backend closed during handshake")
            resp += chunk
        # Forward the backend response to the client
        self.request.sendall(resp)
        # Tunnel raw bytes between client and backend
        tunnel(self.request, be)
    except Exception as e:
        try:
            self.send_response(502); self.end_headers(); self.wfile.write(str(e).encode())
        except Exception:
            pass
```

**关键点：**
- 不要过滤 `Host` 头（之前踩坑：过滤了 Host 头，Cloudflare 返回 `400 Bad Request: missing required Host header`）
- 要等后端返回 101 响应（含 `Sec-WebSocket-Accept` 等正确头）后再开始 tunnel
- 后端处理握手失败时，把后端错误响应转发给客户端（不是 proxy 自己编造 101）

### 2. 根路径 404 — CWD 变更导致 index.html 找不到
重启 galaxy-proxy 后 CWD 变成 `/root`（非 theme 目录），根路径 `do_GET()` 的 fallback 找不到 index.html。在 `do_GET()` 中补充：
```python
rel = clean_path.lstrip("/")
if not rel:
    return self._serve_static("index.html")
if rel:
    fp_html = os.path.join(THEME_DIR, rel + ".html")
    ...
```

### 3. Agent 日志查看方法
```bash
sshpass -p 'PASS' ssh -p PORT root@VPS_IP "journalctl -u komari-agent -n 50 --no-pager"
```

### 4. WebSocket 连通性测试
```bash
# 从 VPS 上测试
curl -s -H 'Connection: Upgrade' -H 'Upgrade: websocket' -H 'Sec-WebSocket-Version: 13' \
  -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
  http://SERVER_IP:PORT/api/clients/report?token=test
# ✅ → 切换协议（101）或返回后端响应
# ❌ → 400 Bad Request（Host 头问题或 proxy 未正确转发）
```

### 5. 重启 galaxy-proxy 流程
```bash
pkill -f galaxy-proxy
sleep 2
cd /opt/komari/data/theme && python3 /opt/komari/data/theme/galaxy-proxy.py
# 验证：curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:25774/
```

## 验证
重启 galaxy-proxy + 重启任一 agent 后：
1. Agent 日志出现 `WebSocket connected`
2. `records` 表开始有数据写入
3. 面板显示 CPU/MEM/DSK/NET 真实数值
