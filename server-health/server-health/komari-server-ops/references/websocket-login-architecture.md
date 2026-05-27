# Komari WebSocket 登录架构

## 问题

admin 登录后跳回登录页，session 不持久。

## 根因

galaxy-proxy.py 使用 Python `http.server.BaseHTTPRequestHandler`，它是 **HTTP only**——不支持 WebSocket 升级握手。而 Komari admin 面板的登录流程完全基于 WebSocket：

1. 用户打开 `/admin/` → komari server 返回 admin SPA HTML
2. SPA 建立 WebSocket 连接到 `/api/rpc2`
3. 用户输入密码 → WebSocket message → komari 验证 → 返回 session_token cookie
4. 后续请求通过 `Cookie: session_token=xxx` 鉴权

如果 galaxy-proxy 拦截了 WebSocket 请求（因为它匹配了 catch-all 路由），HttpOnly 代理无法处理 Upgrade 头，连接失败。

## 修复

用 **tcp-proxy.py**（raw TCP forwarding）取代 galaxy-proxy 做入口代理。TCP 转发完全不关心协议——它只是把字节流从 A 传到 B，WebSocket 握手头透明通过。

## 架构对比

```
❌ HTTP proxy (galaxy-proxy.py) 在入口:
  cloudflared → galaxy-proxy:25774 (HTTP) → komari:25776
  WebSocket 连接到这里被 HTTP handler 拦截，握手失败

✅ TCP proxy (tcp-proxy.py) 在入口:
  cloudflared → tcp-proxy:25774 (raw TCP) → galaxy-proxy:25775 (HTTP, 静态文件)
                                          → komari:25776 (API + WebSocket)
  WebSocket 字节流透传到 komari，握手正常完成
```

## 验证

```bash
# 登录 API（HTTP）正常工作
curl -s -X POST http://localhost:25774/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"xxx"}'
# → {"status":"success","data":{"set-cookie":{"session_token":"..."}}}

# 注意: /api/session 不存在纯 JSON 端点
# GET /api/session 返回 admin SPA HTML（因为 komari 把它当 SPA 路由处理）
# session 验证通过 WebSocket 在客户端完成
```
