# tcp-proxy 路由 bug + cloudflared IPv6 修复实录 (2026-05-27)

## 问题：所有节点离线，records 表为空

**现象：** 面板显示 12 个节点，全部离线。`/api/recent/{uuid}` 返回 `{"status":"success","message":""}`（无 data）。`clients.updated_at` 在持续更新（几分钟前），但 `records` 表为 **0 行**。

## 排查过程

### 第1步：确认代理层

```bash
netstat -tlnp | grep -E '2577[456]'
```
三层代理都在运行：tcp-proxy:25774, galaxy-proxy:25775, komari:25776

### 第2步：检查 cloudflared 日志

```bash
tail -20 /tmp/cf6.log
```
大量报错：`"stream canceled by remote with error code 0"` — agent 的 WebSocket/HTTP 请求被后端关闭。

### 第3步：本地路由测试

```bash
# 测试 API 直连 komari
timeout 3 bash -c 'exec 3<>/dev/tcp/127.0.0.1/25776; echo -e "GET /api/public HTTP/1.1\r\n\r\n" >&3; head -1 <&3'
# → HTTP/1.1 200 OK  ✅ komari 正常

# 测试通过 tcp-proxy 转发
timeout 3 bash -c 'exec 3<>/dev/tcp/127.0.0.1/25774; echo -e "GET /api/public HTTP/1.1\r\n\r\n" >&3; head -1 <&3'
# → 超时 ❌  tcp-proxy 没转发到 komari

# 测试 WebSocket 通过 tcp-proxy
timeout 3 bash -c 'exec 3<>/dev/tcp/127.0.0.1/25774; echo -e "GET /api/clients/report?token=x HTTP/1.1\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n\r\n" >&3; head -1 <&3'
# → 超时 ❌  galaxy-proxy 无法处理 WS 升级
```

### 第4步：定位根因 — tcp-proxy 路由 bug

```python
# /opt/komari/scripts/tcp-proxy.py
ROUTES = {
    "/themes/": 25775,
    "/": 25775,           # ← 这个匹配 ALL 路径！
    "/instance/": 25775,
}

def get_target_port(data):
    ...
    for prefix, port in ROUTES.items():
        if path == prefix.rstrip("/") or path.startswith(prefix):
            return port
    return 25776  # 默认 komari — 永远走不到这里！
```

`"/"` 作为 prefix，`path.startswith("/")` 匹配**所有路径**（任何 URL 都以 `/` 开头）。所有 API 调用和 WebSocket 连接被错发到 galaxy-proxy（端口 25775），galaxy-proxy 是 Python http.server 不支持 WebSocket，导致连接挂起超时。

### 修复

```python
# 修正：对根路径只做精确匹配
if path == prefix.rstrip("/") or (prefix != "/" and path.startswith(prefix)):
```

验证结果：
- `GET /` → galaxy-proxy:25775 ✅（200）
- `GET /api/public` → komari:25776 ✅（200）
- `WS /api/clients/report?token=x` → komari:25776 ✅（401）

## 第2个问题：cloudflared IPv6 localhost

重启 tcp-proxy 后 cloudflared 日志出现新错误：
```
"Unable to reach the origin service: dial tcp [::1]:25774: connect: connection refused"
```

**根因：** Alpine Linux 的 `/etc/hosts` 中 `localhost` 解析为 IPv6 `::1`。tcp-proxy.py 绑定 `0.0.0.0:25774`（IPv4 only），cloudflared 尝试 IPv6 连接被拒。

**修复：** 显式用 `127.0.0.1` 代替 `localhost`：
```bash
# ❌ Alpine 上 localhost → ::1
cloudflared tunnel run --token TOKEN --url http://localhost:25774

# ✅ 显式 IPv4
cloudflared tunnel run --token TOKEN --url http://127.0.0.1:25774
```

## 第3个问题：cloudflared 隧道 token 丢失

kill cloudflared 进程后 token 从 `/proc/PID/cmdline` 消失，无法恢复。需用户从 Cloudflare Dashboard 重新生成或提供 token。

## 架构简化（三层→两层）

修复后直接简化为 komari 原生主题模式：
1. `sqlite3 /opt/komari/data/komari.db "UPDATE configs SET value='\"Glass\"' WHERE key='theme';"`
2. 杀掉 tcp-proxy + galaxy-proxy + 旧 komari
3. 在 25774 启动 komari（`./komari server -l 0.0.0.0:25774`）
4. 重启 cloudflared 指向 `http://127.0.0.1:25774`

结果：省 2 进程、~24MB RSS、少 3 个故障点。
