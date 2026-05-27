---
description: CDN 缓存 vs Cloudflared Tunnel 404 排查区分，<监控面板域名> 实际根因记录
---

# CDN 缓存 vs Cloudflared Tunnel 404 排查

## 两种暴露模式（关键区分）

**Cloudflare CDN 模式**（传统）：域名 → Cloudflare CDN → 源站，Cloudflare 会缓存 HTML/静态资源。
**Cloudflared Tunnel 模式**（<监控面板域名> 当前）：域名 → Cloudflare Edge → cloudflared tunnel → 源站，**没有 CDN 缓存层**，只有 tunnel 路由。

**判断方法**：
```bash
curl -s -I https://<监控面板域名>/
# cf-cache-status: DYNAMIC → tunnel 模式，不经过 CDN 缓存
# cf-cache-status: HIT/EXPIRED → CDN 缓存模式
```

## 核心问题（CDN 缓存模式）

"服务器文件已更新，但浏览器不生效" — 这几乎总是 CDN 缓存问题，而不是代码问题。

**典型症状**：
- 服务器文件 `grep` 有新内容 ✅
- `curl https://域名/` 没有新内容 ❌ → CDN 在缓存
- 浏览器 Ctrl+Shift+R (强制刷新) 仍不生效 → Cloudflare 等边缘缓存
- `flagEmoji.toString()` 在浏览器控制台返回旧代码 → 确认是前端资源被缓存

## 诊断流程

```
1. 服务器文件确认      ssh → grep "关键字" /path/to/index.html
                          ↓ 有内容 → 服务器文件 OK
                          ↓ 无内容 → 文件没更新到服务器

2. CDN 层确认          curl -s "https://域名/" | grep "关键字"
                          ↓ 有内容 → CDN 已更新，问题在浏览器缓存
                          ↓ 无内容 → CDN 在缓存旧版本

3. 浏览器层确认         浏览器控制台 → flagEmoji.toString()
                          ↓ 旧代码 → 浏览器缓存
                          ↓ 新代码 → CDN 缓存
```

## komari 架构（根路径 `/`）

```
浏览器 → Cloudflare Edge → cloudflared tunnel → komari server → embedded JS (binary embed.FS)
                        ↑ tunnel 模式无 CDN 缓存，但会缓存 HTML（cf-cache-status: DYNAMIC）
```

**<监控面板域名> 是 tunnel 模式**，返回 404 是 tunnel 路由问题，不是缓存问题。

## <监控面板域名> 404 实际根因（2026-05-10）

**不是 CDN 缓存，是 tunnel 路由问题**：
- cloudflared 进程活着，4 个 LAX 连接都注册成功 ✅
- TLS 握手正常，证书匹配 ✅
- 但公网返回 HTTP 404 ❌

**根因**：Cloudflare Dashboard 端的 tunnel 配置损坏/丢失，或两个不同的 cloudflared token 冲突。

**正确排查步骤**：
```bash
# 1. 确认 tunnel 进程
ps aux | grep cloudflared | grep -v grep

# 2. 确认 tunnel 日志有 4 个 Registered connection
tail -20 /var/log/cloudflared.err

# 3. 本地 Host header 测试
curl -s -H "Host: <监控面板域名>" http://127.0.0.1:25774/ | grep -o "video.src = [^;]*"

# 4. 公网测试
curl -s -I https://<监控面板域名>/
# 404 = tunnel 路由层问题

# 5. 对比两个 cloudflared token 是否冲突
grep "token" /etc/init.d/cloudflared
sqlite3 /opt/komari/data/komari.db "SELECT value FROM configs WHERE key='cloudflare_tunnel_token';"
```

## 相关坑

- **komari Korean flag（2026-05-08）**：服务器文件已更新朝鲜 emoji 分支，但 CDN 缓存导致浏览器跑旧 JS
- **Cloudflare JS 挑战**：komari agent 连接时 CF 返回 JS 挑战页，非浏览器无法通过
- **<监控面板域名> 404（2026-05-10）**：误以为是 CDN 缓存，实际是 tunnel token 冲突或 Dashboard 端 tunnel 损坏
