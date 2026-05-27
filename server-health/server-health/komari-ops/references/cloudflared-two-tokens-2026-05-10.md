# cloudflared 双 Token 冲突问题（2026-05-10）

## 背景

56idc-la 上同时存在两个 cloudflared token：

| Token 来源 | 值 | 启动方式 |
|-----------|-----|---------|
| `/etc/init.d/cloudflared` 脚本 | `eyJhIj...` (旧) | OpenRC init |
| 数据库 `configs.cloudflare_tunnel_token` | `hmcSeFn...` (新) | v1.2.0 内置 |

两个 token 不能共存，同时跑会导致 <监控面板域名> 返回 HTTP 404。

## 现象

- cloudflared 进程活着（4个 LAX 连接）
- `tail /var/log/cloudflared.err` 显示 "Registered tunnel connection" × 4
- `curl https://<监控面板域名>/` 返回 HTTP 404
- TLS 握手正常，证书匹配

## 根因

Cloudflare Dashboard 端 tunnel 路由配置只关联了一个 token（init script 那个），v1.2.0 的新 token 没有在 Dashboard 端配置对应的 ingress rule。

## 解法

**方案A（当前采用）**：继续用 1.1.9 + init script 手动管理 cloudflared，不升级到 1.2.0

**方案B**：停掉 init script cloudflared，让 v1.2.0 用数据库里的 token 自动管理（需 Cloudflare Dashboard 端 tunnel 配置正确）

## 相关文件

- `/etc/init.d/cloudflared` — init 脚本，包含旧 token
- `/usr/local/bin/cloudflared` — 二进制（38MB）
- `/var/log/cloudflared.err` — cloudflared 日志
- `/opt/komari/data/komari.db` → `configs.cloudflare_tunnel_token` — v1.2.0 新 token

## 验证命令

```bash
# 看 init script 里的 token
grep -o 'token [^'\'']*' /etc/init.d/cloudflared

# 看数据库里的 token
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> \
  "sqlite3 /opt/komari/data/komari.db 'SELECT value FROM configs WHERE key=\"cloudflare_tunnel_token\";'"

# 验证 tunnel 本地连通
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> \
  "curl -s -H 'Host: <监控面板域名>' http://127.0.0.1:25774/" | head -c 200
```
