# Cloudflare CDN + VLESS+WS 部署与排障

## 部署流程

```
用户 ──TLS──→ Cloudflare CDN ──TLS/明文──→ 源站 sing-box
```

## 排障步骤

### Step 1: 确认 DNS 解析

```bash
dig +short app.<用户域名>
```

期望结果：返回 `172.67.x.x` 或 `104.21.x.x`（Cloudflare Anycast IP）。  
如果是源站真实 IP → DNS 是灰色云（DNS Only），不走 CDN 缓存。

### Step 2: 确认 Cloudflare 端口转发

Cloudflare CDN 只支持以下端口：

```
80  443  2052  2053  2082  2083  2086  2087  2095  2096  8080  8443  8880
```

用 `curl` 测试端口可达性：

```bash
curl -svo /dev/null --connect-timeout 15 https://app.<用户域名>:443/
```

### Step 3: 理解 525 错误

HTTP 525 = Cloudflare → origin SSL 握手失败。

**原因**：Cloudflare 默认 SSL/TLS 模式是"完全"或"完全（严格）"，会尝试用 TLS 连接 origin。如果 origin 没开 TLS，握手失败。

**解法**：
- 方案 A（推荐）：源站配自签 TLS 证书，CF 面板设为"完全"（不勾严格）
- 方案 B：CF 面板 SSL/TLS 加密改为"灵活"

### Step 4: 生成源站自签证书

```bash
mkdir -p /etc/sing-box
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/sing-box/key.pem \
  -out /etc/sing-box/cert.pem \
  -subj '/CN=app.<用户域名>' \
  -addext 'subjectAltName=DNS:app.<用户域名>'
```

注意：`-addext` 中的 CN 和 SAN 要与域名匹配，否则"完全（严格）"模式会报 526。

### Step 5: 验证 CF→origin 连通性

```bash
# 连上不求返回正常内容，不报 5xx 就行
curl -svo /dev/null --connect-timeout 15 https://app.<用户域名>/ 2>&1 | grep -E 'SSL|TLS|HTTP|error'
```

- `HTTP/2 200` → 正常（sing-box 返回的也不是 HTTP，但连接建立了）
- `HTTP 525` → origin TLS 问题（走方案 A 或 B）
- `timeout` → 端口不支持或 origin 防火墙没放行

### Step 6: WebSocket 测试

```bash
curl -sv --connect-timeout 15 \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  https://app.<用户域名>/ 2>&1 | tail -10
```

期望：`HTTP 101 Switching Protocols` 或 sing-box 的 VLESS 响应（可能是 4xx 但不会 timeout）。  
CF WebSocket 默认开启，无需手动配置。

## 常见错误速查

| 现象 | 可能原因 | 解决 |
|------|---------|------|
| DNS 返回源站 IP | DNS 灰色云（未 proxied） | Cloudflare 面板开启橙色云 |
| 连接 timeout | 端口不是 CF 支持列表里的 | 改 443/80/8443/2096 |
| HTTP 525 | origin 无 TLS 或 CF 设为严格 | 改"完全"模式或配 origin TLS |
| WebSocket 升级失败 | curl 用了 HTTP/2（CF 默认） | 等待客户端测试，curl 仅验证端口通 |
| 能连但速度慢 | 非 WebSocket 问题 | 排查中美/中日线路质量 |

## 完整部署命令速查（洛杉矶 ColoCrossing 实战记录）

```bash
# 1. 安装 sing-box（确保 with_reality_server 或 ws 支持）
# 2. 生成自签证书
mkdir -p /etc/sing-box
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/sing-box/key.pem -out /etc/sing-box/cert.pem \
  -subj '/CN=app.<用户域名>' \
  -addext 'subjectAltName=DNS:app.<用户域名>'

# 3. 写 config.json（见 SKILL.md 方案 B）
# 4. 开 UFW
ufw allow 443/tcp

# 5. sing-box check 校验
# 6. systemctl restart sing-box
# 7. 验证监听
ss -tlnp | grep 443
```
