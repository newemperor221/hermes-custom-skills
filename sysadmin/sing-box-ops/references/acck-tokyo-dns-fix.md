# Acck 东京 — sing-box DNS 故障修复记录

## 症状

代理连不上，客户端超时。Sing-box 日志：
```
REALITY: failed to dial dest: lookup www.cloudflare.com
→ exchange6: link has no DNS servers configured
→ exchange4: link has no DNS servers configured
```

## 根因

`systemd-resolved` 的 **eth0 接口没有关联 DNS 服务器**，导致链路级 DNS 解析失败：

```bash
# 全局 level ✅ 有 DNS
resolvectl dns          → 1.1.1.1 8.8.8.8

# 链路级 (eth0) ❌ 空的
resolvectl dns eth0     → (空)

# 验证问题
resolvectl query www.cloudflare.com  # 失败
```

Sing-box 的 REALITY 握手需要解析 `www.cloudflare.com`，但 `exchange6` 和 `exchange4` 走到链路级发现没有 DNS → 直接报错 → 握手失败。

## 修复

### 1. 临时修复（立即生效）
```bash
resolvectl dns eth0 1.1.1.1 8.8.8.8
```

### 2. 验证
```bash
resolvectl query www.cloudflare.com  # 应返回 IP
systemctl restart sing-box           # 重启后日志干净
```

### 3. 持久化（重启不丢）
```bash
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/dns-servers.conf << 'EOF'
[Resolve]
DNS=1.1.1.1 8.8.8.8
Domains=~.
EOF
```

## 服务器信息

| 项目 | 值 |
|------|-----|
| 主机 | Acck 东京 |
| IP | <东京_IP> |
| SSH | root@<东京_IP>:47283 |
| OS | Debian 12 (bookworm) |
| 代理 | sing-box VLESS+Reality |
| 用途 | 核心翻墙节点 |

## 类似问题排查

如果 sing-box REALITY 握手失败，按以下顺序排查：

1. **DNS 解析**：`resolvectl dns` 检查全局 DNS，`resolvectl dns eth0` 检查链路级
2. **直连测试**：`curl -v https://www.cloudflare.com`（跳过代理）
3. **端口连通**：`timeout 3 bash -c 'echo >/dev/tcp/1.1.1.1/53'`
4. **路由检查**：`ip route | grep default`
