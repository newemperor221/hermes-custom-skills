# cloudflared 隧道架构参考（2026-05-10 修订）

## <监控面板域名> 当前架构

```
Internet (HTTPS 443)
  → Cloudflare Edge (SNI: <监控面板域名>)
    → cloudflared tunnel (进程在 56idc-la，token 模式)
      → localhost:25774 (komari server)
```

**不是 CDN 缓存模式**，是 cloudflared tunnel 直连。

## 两个 cloudflared Token（冲突根源）

| Token | 值 | 来源 | 用途 |
|-------|-----|------|------|
| Init script token | `eyJhIj...` | `/etc/init.d/cloudflared` | 旧 cloudflared 进程（OpenRC 管理） |
| DB token | `hmcSeFny...` | `komari.db → configs.cloudflare_tunnel_token` | v1.2.0 内置 tunnel 管理 |

**两 token 不能共存**，同时跑会导致 tunnel 路由混乱，<监控面板域名> 返回 404。

## 当前状态（2026-05-10）

56idc-la 跑的是 komari **1.1.9** + 手动 cloudflared（init script 方式）。

## cloudflared 文件位置（Alpine）

```bash
/usr/local/bin/cloudflared    # 二进制（38MB）
/etc/init.d/cloudflared       # init 脚本
/var/log/cloudflared.err      # 日志（看这个）
/var/log/cloudflared.log      # stdout（通常空）
```

**⚠️ init 脚本路径 bug**：新装 cloudflared 后 init 脚本可能指向 `/tmp/cloudflared`（不存在）。修复：
```bash
sed -i 's|/tmp/cloudflared|/usr/local/bin/cloudflared|g' /etc/init.d/cloudflared
```

## cloudflared 启停（Alpine OpenRC）

```bash
# 查进程
ps aux | grep cloudflared | grep -v grep

# 查日志
tail -20 /var/log/cloudflared.err

# 重启（stop 可能失败，必须 killall + start）
killall cloudflared; sleep 2
/etc/init.d/cloudflared start

# 验证（4个 connIndex 注册成功）
tail /var/log/cloudflared.err | grep "Registered tunnel connection"
```

## <监控面板域名> 404 排查

1. `curl -s -I https://<监控面板域名>/` → TLS 握手成功 + HTTP 404 = tunnel 路由损坏
2. `dig <监控面板域名> +short` → 确认 DNS 指向 Cloudflare IP
3. 本地验证：`curl -s -H "Host: <监控面板域名>" http://127.0.0.1:25774/` 返回 HTML = komari 正常，tunnel 问题
4. Cloudflare Dashboard → Zero Trust → Networks → Tunnels → 检查 <监控面板域名> tunnel 是否 Active

## v1.2.0 内置 tunnel 管理

v1.2.0 的 `cloudflare_tunnel_token` 存数据库 `configs` 表，komari server 自己管理 cloudflared 进程。但：
- v1.2.0 在 Alpine 上 **SIGSEGV**（glibc vs musl），56idc-la 不适用
- 切换到 v1.2.0 前需确认 Cloudflare Dashboard 端 tunnel 配置正确关联 DB 里的 token
