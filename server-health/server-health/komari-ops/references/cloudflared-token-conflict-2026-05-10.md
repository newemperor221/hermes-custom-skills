# Cloudflared Token 冲突 + stat.357561.xyz 404 排查

**日期**：2026-05-10
**服务器**：56idc-la（Alpine，<洛杉矶2_IP>:42185）

---

## 现象

`stat.357561.xyz` 公网返回 HTTP 404，但：
- `curl localhost:25774/` 返回正常 HTML ✅
- cloudflared 进程在跑，4 个 LAX 连接都注册成功 ✅
- TLS 握手正常，证书匹配 ✅
- DNS 解析正常 ✅

## 根因：两套 cloudflared token 冲突

| 来源 | Token | 用途 |
|------|-------|------|
| `/etc/init.d/cloudflared`（init script） | `eyJhIj...MSJ9` | 旧版 cloudflared（手动管理） |
| `komari.db → configs.cloudflare_tunnel_token` | `hmcSeF...` | v1.2.0 内置 tunnel 管理 |

v1.2.0 在数据库里存了自己的 tunnel token，但旧 cloudflared 进程用另一个 token 同时连着 Cloudflare，导致路由混乱。

## 排查步骤

```bash
# 1. 确认 cloudflared 进程和日志
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> 'ps aux | grep cloudflared | grep -v grep'
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> 'tail -20 /var/log/cloudflared.err'
# 应有 "Registered tunnel connection" × 4（connIndex 0-3）

# 2. 对比两个 token
# init script token:
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> "grep -o 'token [^'\'']*' /etc/init.d/cloudflared"
# DB token:
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> "sqlite3 /opt/komari/data/komari.db 'SELECT value FROM configs WHERE key=\"cloudflare_tunnel_token\";'"

# 3. 本地 Host header 测试
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> "curl -s -H 'Host: stat.357561.xyz' http://127.0.0.1:25774/ | grep -o 'video.src = [^;]*'"
# 返回带 siteInfo.videoUrl 的行 = 本地 tunnel 通

# 4. 公网测试
curl -s -I https://stat.357561.xyz/
# 404 = tunnel 路由层问题（不是 CDN 缓存）

# 5. DNS 确认
dig stat.357561.xyz +short
# 应返回 104.21.x.x 或 172.67.x.x

# 6. TLS 握手确认
curl -sv https://stat.357561.xyz/ 2>&1 | grep -E 'TLS|subject|ALPN'
```

## 解法

**如果是 token 冲突**（旧 cloudflared 和 v1.2.0 用不同 token）：

1. 停旧 cloudflared：
```bash
killall cloudflared
```

2. 如果想用 v1.2.0 内置 tunnel 管理：升级到 1.2.0（⚠️ Alpine 会 SIGSEGV）
3. 如果继续用 1.1.9：确保只有一套 cloudflared，用 init script 的 token 跑

**如果是 Cloudflare Dashboard 端 tunnel 损坏**：
- 登录 Cloudflare Dashboard → Zero Trust → Networks → Tunnels
- 检查 stat.357561.xyz tunnel 是否存在、状态是否 Active
- tunnel 若损坏：删除重建 → 更新 DNS CNAME

## 教训

- **stat.357561.xyz 是 cloudflared tunnel 模式，没有 CDN 缓存层**。返回 404 一定是 tunnel 路由层的问题。
- v1.2.0 内置 cloudflared tunnel 管理（token 存数据库），不需要手动装 cloudflared binary。
- 但 v1.2.0 在 Alpine 上 SIGSEGV（glibc 二进制在 musl 环境崩溃），所以 56idc-la 实际跑的是 1.1.9 + 手动 cloudflared。
- 两个 token 不能共存，否则 Cloudflare 不知道该路由到哪个 tunnel。
