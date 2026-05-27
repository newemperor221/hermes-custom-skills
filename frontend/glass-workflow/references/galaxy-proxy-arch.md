# galaxy-proxy.py 架构与运维参考

## 架构概览

**当前生产架构（2026-05-26 更新）**：

```
stat.357561.xyz
    ↓ Cloudflare (orange cloud)
    ↓ cloudflared tunnel (Alpine, 端口无暴露)
    ↓
tcp-proxy.py (:25774)  ← TCP 字节级代理（透传 HTTP + WebSocket）
    ├── /themes/* + / + /instance/* → galaxy-proxy.py (:25775)
    └── 其他所有路径（含 /api/rpc2 WebSocket） → Komari (:25776)
    ↓
galaxy-proxy.py (:25775)  ← 反向代理，Python SimpleHTTP
    ├── 静态文件服务：/opt/komari/data/theme/ 目录
    ├── /fonts/* 字体文件服务
    ├── /api/proxy/exchange-rate 汇率缓存
    └── /api/proxy/online-count tab 心跳追踪
    ↓
Komari (:25776)  ← 实际的探针面板后端
```

**⚠️ WebSocket 兼容性（关键架构陷阱）**：

Python `http.server.HTTPServer` 不支持 WebSocket upgrade 请求。Komari 的 admin 登录页使用 WebSocket（`/api/rpc2`）进行 JSON-RPC 2.0 通信，登录请求经过 galaxy-proxy 时会被 `urllib.request.urlopen()` 以普通 HTTP 方式处理，导致 WebSocket 握手失败。

**现象**：admin 页面加载正常（HTTP GET 返回 HTML），但填入密码点登录后无响应或 `"Unexpected token '<', "<!DOCTYPE ..." is not valid JSON"` —— admin 页面的 JS 请求 WebSocket endpoint 拿到了 HTML 而非 JSON-RPC 响应。

**修复**：在 galaxy-proxy 前面加一层 tcp-proxy.py（纯字节级 TCP 转发），WebSocket 请求被透传到 komari，不再经过 Python http.server 的 HTTP 处理管道。

## tcp-proxy 路由

tcp-proxy 在 25774 端口监听，读取第一个 HTTP 请求行的路径来决定目标后端：

```python
ROUTES = {
    "/themes/": 25775,    # galaxy-proxy — 主题静态文件
    "/": 25775,           # galaxy-proxy — index.html 首页
    "/instance/": 25775,  # galaxy-proxy — 实例页面
}
# 默认目标：komari :25776（所有 API + WebSocket + admin 页面）
```

**字节级转发**：tcp-proxy 不解析 HTTP 内容，不处理 WebSocket upgrade，仅做 TCP 层面双向字节流透传。

## 关键文件

- TCP 代理：`/opt/komari/scripts/tcp-proxy.py`（2026-05-26 新增）
- galaxy-proxy：`/opt/komari/scripts/galaxy-proxy.py`（统一使用 scripts/ 版本）
- 主题目录：`/opt/komari/data/theme/`

## 启动与验证

```bash
# 先 komari，再 galaxy-proxy，最后 tcp-proxy
kill $(pgrep -f "komari server") 2>/dev/null
cd /opt/komari && nohup ./komari server -l 0.0.0.0:25776 > /tmp/komari.log 2>&1 &

kill $(lsof -ti :25775) 2>/dev/null
cd /opt/komari/scripts && nohup python3 galaxy-proxy.py > /tmp/gp.log 2>&1 &

kill $(lsof -ti :25774) 2>/dev/null
cd /opt/komari/scripts && nohup python3 tcp-proxy.py > /tmp/tcp.log 2>&1 &

# 验证三端口
curl -s -o /dev/null -w "%{http_code}" http://localhost:25775/admin
curl -s -o /dev/null -w "%{http_code}" http://localhost:25776/admin
curl -s -o /dev/null -w "%{http_code}" http://localhost:25774/admin
```

**注意**：cloudflared 必须指向 tcp-proxy 的端口（:25774），否则 WebSocket 无法透传。komari 启动必须指定 `-l 0.0.0.0:25776`（默认 25774 已被 tcp-proxy 占用）。

## 常见故障

- **Admin 登录无响应**：tcp-proxy 未运行，WebSocket 无法透传
- **Komari 启动端口冲突**：忘了 `-l 0.0.0.0:25776`，与 tcp-proxy 抢 25774
- **Cloudflare 缓存**：加 `?v=N` 参数绕开
