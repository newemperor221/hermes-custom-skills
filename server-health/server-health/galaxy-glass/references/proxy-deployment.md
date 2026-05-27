# GalaxyGlass Python 代理部署（2026-05-13 实施）

## 背景

官方 komari v1.2.0 将主题 HTML 编译进二进制（Go embed），不支持 `PurCarte-Plus/dist/index.html`
路径。为实现自定义 GalaxyGlass 主题，使用轻量 Python HTTP 代理服务：

- 监听 cloudflared tunnel 的目标端口（25774）
- 为 `/` 提供自定义 `index.html`
- 将 `/api/*`、`/admin` 等请求透传给后端 komari

## 当前线上端口映射

```
cloudflared tunnel → :25774 [Python 代理] → :25776 [Komari server]
```

## 代理脚本

位置：`/opt/komari/galaxy-proxy.py`

```python
#!/usr/bin/env python3
import http.server, urllib.request, urllib.error, os, signal, sys

BACKEND = 'http://localhost:25776'

class ProxyHandler(http.server.SimpleHTTPRequestHandler):
    def _forward(self, method):
        url = BACKEND + self.path
        body = None
        if method in ('POST', 'PUT', 'PATCH'):
            length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(length) if length > 0 else b''
        try:
            req = urllib.request.Request(url, data=body, method=method,
                headers={k: v for k, v in self.headers.items()
                         if k.lower() not in ('host','transfer-encoding','content-encoding')})
            resp = urllib.request.urlopen(req, timeout=10)
            self.send_response(resp.status)
            for k, v in resp.getheaders():
                if k.lower() not in ('transfer-encoding', 'content-encoding'):
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(resp.read())
        except urllib.error.HTTPError as e:
            self.send_response(e.code)
            for k, v in e.headers.items():
                if k.lower() not in ('transfer-encoding', 'content-encoding'):
                    self.send_header(k, v)
            self.end_headers()
            self.wfile.write(e.read())
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def do_GET(self):
        if self.path.startswith('/api/') or self.path.startswith('/admin') or \
           self.path in ('/manifest.json', '/favicon.ico'):
            self._forward('GET')
        else:
            if self.path == '/': self.path = '/index.html'
            super().do_GET()
    def do_POST(self): self._forward('POST')
    def do_PUT(self): self._forward('PUT')
    def do_PATCH(self): self._forward('PATCH')
    def do_DELETE(self): self._forward('DELETE')

os.chdir('/opt/komari/data/theme')
s = http.server.HTTPServer(('0.0.0.0', 25774), ProxyHandler)
signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
s.serve_forever()
```

### 关键细节

1. **`0.0.0.0:25774` 而非 `127.0.0.1`** — cloudflared tunnel 可能从非 localhost 连接
2. **后端 komari 在 `:25776`** — 与代理端口错开避免端口冲突
3. **过滤 `transfer-encoding` 和 `content-encoding`** — 避免 Python 代理的 HTTP 转发双重编码
4. **`os.chdir("/opt/komari/data/theme")`** — 使 `SimpleHTTPRequestHandler` 从主题目录提供静态文件

## 部署流程（完整步骤）

```bash
# === 初始化 ===
# 1. 创建主题目录
mkdir -p /opt/komari/data/theme

# 2. 传输修改后的 index.html
# 方法 A：通过 SSH 管道
cat galaxy-beautified.html | sshpass -p 'OX8w$nE9A%tfqb6v' ssh \
  -p 46748 root@31.58.51.127 "cat > /opt/komari/data/theme/index.html"

# 方法 B：先传到 DediRock 再 scp 到 Poland Master
# （不推荐，多一跳）

# 3. 传输代理脚本
cat galaxy-proxy.py | sshpass -p 'OX8w$nE9A%tfqb6v' ssh \
  -p 46748 root@31.58.51.127 "cat > /opt/komari/galaxy-proxy.py"

# 4. 确保代理脚本中后端地址正确
sed -i 's|http://localhost:25774|http://localhost:25776|g' \
  /opt/komari/galaxy-proxy.py
sed -i 's|127.0.0.1, 25775|0.0.0.0, 25774|' \
  /opt/komari/galaxy-proxy.py

# === 启动 ===
# 5. 启动 komari 后端（避让代理端口）
/opt/komari/komari server -l 0.0.0.0:25776 \
  -d /opt/komari/data/komari.db &

# 6. 验证 komari 就绪
curl -s http://127.0.0.1:25776/api/public | grep sitename

# 7. 停止旧代理进程
kill $(pgrep -f 'python3.*galaxy-proxy') 2>/dev/null; sleep 1

# 8. 启动代理
cd /opt/komari/data/theme && python3 /opt/komari/galaxy-proxy.py &

# 9. 验证代理
curl -s http://127.0.0.1:25774/ | grep 'html { font-size'
curl -s http://127.0.0.1:25774/api/nodes | grep -c '"uuid"'

# === 故障恢复 ===
# 如果 komari server 进程被杀或服务异常：
# 1. 检查进程：ps aux | grep komari
# 2. 检查端口：netstat -tlnp | grep 2577
# 3. 重新启动 komari + proxy（按上面步骤 5-9）
```

## 验证清单

| 检查项 | 命令 | 预期结果 |
|--------|------|----------|
| 代理监听 | `netstat -tlnp \| grep 25774` | `0.0.0.0:25774 LISTEN python3` |
| 代理服务 HTML | `curl -s http://127.0.0.1:25774/ \| head -1` | `<!DOCTYPE html>` |
| 代理转发 API | `curl -s http://127.0.0.1:25774/api/nodes \| python3 -c '...'` | `Nodes: 13` |
| 代理处理 POST | `curl -X POST http://127.0.0.1:25774/api/nodes -w '%{http_code}' -o /dev/null` | 200 or 404（非501） |
| 探针数据写入 | `curl -s http://127.0.0.1:25774/api/recent/ccs-la2 \| python3 -c '...'` | `pts > 0` |
| 线上域名 | `curl -sL https://stat.357561.xyz \| grep 'font-size'` | `font-size: 14px` |
| 静态文件目录 | `ls /opt/komari/data/theme/` | `index.html` |

## Cloudflare 缓存注意事项

- 即使 GalaxyGlass HTML 标记了 `no-cache, no-store, must-revalidate`，
  Cloudflare 在 Edge Cache TTL 配置下仍可能缓存
- `HEAD` 请求可能在 curl 中返回 404 而 `GET` 正常 — 这是 Cloudflare 行为
- 如需立即验证，使用 `?_=$(date +%s)` 参数绕过缓存
- 大规模部署后可通过 Cloudflare Dashboard → 缓存 → 清除所有文件 来刷新

## 踩坑记录

### 🚨 代理只处理 GET 导致探针数据全无（2026-05-13 灾难级踩坑）

**症状**：页面正常返回，API `/api/nodes` 返回 200 和 13 个节点，但所有节点显示 `0/13 在线`、`0.0%` 使用率，`/api/recent/{uuid}` 返回空数组。

**根因**：`SimpleHTTPRequestHandler` 默认只处理 GET/HEAD，其他方法返回 501。Komari 探针上报数据使用 POST `/api/clients/uploadBasicInfo`，请求被静默吞掉。探针跑了 20+ 小时数据一条也没入库。

**排查路径**：
```
curl -X POST http://localhost:25774/api/nodes -w '%{http_code}' -o /dev/null
→ 501  ← 证明代理不处理 POST

curl -X POST http://localhost:25776/api/nodes -w '%{http_code}' -o /dev/null  
→ 非 501  ← 证明 komari 后端正常，问题在代理层
```

**修复**：在处理器中实现 `do_POST` / `do_PUT` / `do_PATCH` / `do_DELETE`，均调用 `_forward(method)` 将请求原样转发到 komari 后端。详见 SKILL.md 中的完整代理脚本。

**防御**：
- 每次修改代理脚本后验证 `curl -X GET` 和 `curl -X POST` 两种方法
- 部署后观察 `/api/recent/{uuid}` 是否有数据写入

### 端口被占用
`OSError: [Errno 98] Address in use` — 代理端口被占用。解决方案：
```bash
# 1. 确认哪个进程占用了端口
netstat -tlnp | grep 25774
# 2. 杀旧进程
kill PID
# 3. 或换启动顺序：先停旧代理，等 1 秒，再启动新代理
```

### debug 提示代理脚本仍使用旧端口
修改 `proxy.py` 后，Python 脚本代码中同时存在监听地址和 print 消息两处需要更新。
```bash
sed -i 's/旧端口/新端口/g' /opt/komari/galaxy-proxy.py
grep -n '端口号' /opt/komari/galaxy-proxy.py  # 确认全部更新
```

### 🚨 代理必须用 ThreadingMixIn（2026-05-13）

**症状**：代理进程运行中（`ps aux` 可见）、端口已绑定（`fuser` 确认），但 curl 连接超时。即便最简单的 `GET /api/public` 也不响应。

**根因**：Python `http.server.HTTPServer` 是**单线程串行**处理请求。当代理启动时，13+ 探针同时连接，队列中第一个请求是 WebSocket 升级请求（长时间挂起），阻塞了所有后续 HTTP 请求。

**修复**：使用 `ThreadingMixIn` 创建线程池版 HTTPServer：
```python
from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    allow_reuse_address = True
    daemon_threads = True
```

### 🚨 WebSocket 升级请求被代理截断（2026-05-13）

**症状**：POST 修复后，`GET /api/clients/report?token=xxx` 仍返回 400，响应体为 `{"error":"Require WebSocket upgrade"}`。

**根因**：Komari 探针使用 **WebSocket** 上报实时数据。客户端发 HTTP GET + `Upgrade: websocket` + `Sec-WebSocket-*` 头，期望 101 升级。`urllib.request.urlopen()` 不理解 WebSocket，转发到后端时不带 WS 头，后端返回 400。

**修复**：在 `do_GET` 中检测 `Upgrade: websocket` 头，走原始 TCP 隧道：
```python
def do_GET(self):
    if self.path.startswith("/api/") and self.headers.get("Upgrade","").lower() == "websocket":
        return self._ws()  # 原始 TCP 隧道
```

代理脚本当前线上完整版见 SKILL.md 的「已知踩坑」→「线程+WebSocket」章节。

### 数据恢复确认流程（2026-05-13 实战总结）

代理修复后，数据不会立即恢复。探针重新建立 WebSocket 连接需要时间：

```
启动代理 → 等待探针重新 WS 握手（10-30秒）
→ curl /api/recent/某节点 → 检查 data[] 是否非空
→ 第一个节点恢复后，其他节点陆续跟上
→ 页面刷新即可看到数据
```

确认代理正常工作的完整指令链：
```bash
# 1. 基础 HTTP
curl -s --max-time 5 http://127.0.0.1:25774/api/nodes -w '%{http_code}' -o /dev/null
# → 200

# 2. 静态文件
curl -s --max-time 5 http://127.0.0.1:25774/ -w '%{http_code}' -o /dev/null
# → 200

# 3. POST 转发
curl -X POST http://127.0.0.1:25774/api/xxx -w '%{http_code}' -o /dev/null
# → 非 501

# 4. WebSocket 测试
timeout 5 bash -c 'exec 3<>/dev/tcp/127.0.0.1/25774; echo -e "GET /api/clients/report?token=test HTTP/1.1\r\nHost: localhost\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==\r\nSec-WebSocket-Version: 13\r\n\r\n" >&3; cat <&3' | head -5
# → 应返回 HTTP/1.1 101 Switching Protocols 或后端 WS 响应

# 5. 数据验证（等 30 秒后）
curl -s http://127.0.0.1:25774/api/recent/56idc-la | python3 -c "import sys,json; d=json.load(sys.stdin); print(len(d.get('data',[])), 'pts')"
# → > 0 pts
```
DediRock 上的旧 komari server 二进制被删除后替换为 v1.2.0。v1.2.0 与新数据库关联，
与 Poland Master 的主数据无关。DediRock 仅作为 tunnel connector 和 ds-free-api，
不必恢复其 komari 服务。
