---
name: sing-box-ops
description: sing-box 全生命周期运维 — VLESS+Reality 部署、DNS 故障排查、客户端配置、Let's Encrypt SSL。触发："sing-box"、"VLESS"、"Reality"、"connection reset"、"代理部署"。
triggers:
  - sing-box 部署
  - VLESS Reality 配置
  - sing-box DNS 失败
  - connection reset by peer
  - sing-box 连不上
  - 代理节点搭建
---

# sing-box 全生命周期运维

sing-box VLESS+Reality 落地节点的部署、调试、客户端配置一站式指南。

---

## 一、部署（sing-box 1.9.x）

### 安装

```bash
cd /tmp
wget https://github.com/SagerNet/sing-box/releases/download/v1.9.4/sing-box-1.9.4-linux-amd64.tar.gz
tar xzf sing-box-1.9.4-linux-amd64.tar.gz
sudo mv sing-box-1.9.4-linux-amd64/sing-box /usr/local/bin/
sing-box version   # 确认有 with_reality_server tag
```

### 生成密钥（关键：公钥私钥必须配对）

```bash
sing-box generate reality-keypair
# PrivateKey → 服务端 config.json
# PublicKey → 客户端 VLESS URI

sing-box generate rand 8 --hex   # short_id（8位hex）

# UUID（服务器 python3 可能超时，用本地生成）
cat /proc/sys/kernel/random/uuid
```

**⚠️ 关键坑：公钥私钥必须配对**

- `sing-box generate reality-keypair` 输出的 PrivateKey 和 PublicKey 是一对，必须**同时使用**
- 如果手动更换了 private_key（比如补抄旧配置），**public_key 也必须同步更新**
- 不匹配时客户端报错：`reality verification failed`
- 每次重新生成 keypair 后，**所有客户端都必须更新 VLESS URI 中的 pbk=**

### ⚠ 字段名坑（1.9.x 重大变化）

| 旧版字段 | 1.9.x 正确字段 |
|---------|--------------|
| `inbounds[].port` | `inbounds[].listen_port` |
| `tls.server` | `tls.server_name` |
| `outbounds` (对象) | `outbounds` (数组) |
| `type: api` inbound | 不存在，删除 |

### Reality TLS 结构

```json
"tls": {
  "enabled": true,
  "server_name": "www.cloudflare.com",
  "reality": {
    "enabled": true,
    "private_key": "<PrivateKey>",
    "handshake": { "server": "www.cloudflare.com", "server_port": 443 },
    "short_id": ["04814792"]
  }
}
```

### 最小可运行配置

```json
{
  "log": {"level": "info", "timestamp": true},
  "inbounds": [
    {
      "tag": "reality", "type": "vless",
      "listen": "0.0.0.0", "listen_port": 44308,
      "users": [{"uuid": "<UUID>", "flow": "xtls-rprx-vision"}],
      "tls": {
        "enabled": true, "server_name": "www.cloudflare.com",
        "reality": {
          "enabled": true, "private_key": "<PrivateKey>",
          "handshake": {"server": "www.cloudflare.com", "server_port": 443},
          "short_id": ["<short_id>"]
        }
      }
    },
    {"tag": "socks", "type": "socks", "listen": "127.0.0.1", "listen_port": 1080},
    {"tag": "http", "type": "http", "listen": "127.0.0.1", "listen_port": 1081}
  ],
  "outbounds": [{"tag": "direct", "type": "direct"}]
}
```

### JSON 传输到远程

```bash
# 推荐：echo + ssh（避免 heredoc EOF 问题）
echo '{"log":{"level":"info",...}}' | ssh user@host 'cat > ~/sing-box/config.json'
```

### 启动验证

```bash
sudo mkdir -p /var/lib/sing-box && sudo chown $USER:$USER /var/lib/sing-box

# 前台测试
/usr/local/bin/sing-box run -C ~/sing-box -D /var/lib/sing-box

# systemd 管理
sudo systemctl daemon-reload
sudo systemctl enable --now sing-box

# 验证
ss -tlnp | grep <listen_port>
```

### UFW 放行

```bash
sudo ufw allow <proxy_port>/tcp comment 'sing-box vless-reality'
```

> ⚠ 如果放行后外部仍连不上，检查 UFW 规则是否真正生效：`ufw status numbered`，以及服务器提供商是否有额外防火墙（Host-level firewall / iptables policy DROP）。

### BBR 开启（强烈推荐）

BBR 能显著提升 TCP 吞吐量，尤其是在高延迟的中美线路上：

```bash
echo "net.core.default_qdisc=fq" >> /etc/sysctl.conf
echo "net.ipv4.tcp_congestion_control=bbr" >> /etc/sysctl.conf
sysctl -p
# 验证
sysctl net.ipv4.tcp_congestion_control
# 应输出: net.ipv4.tcp_congestion_control = bbr
```

> 在启用 VLESS+Reality 的节点上任何时候都能补开，不影响现有连接。

### systemd 服务文件

```ini
[Unit]
Description=sing-box VLESS+Reality
After=network.target

[Service]
ExecStart=/usr/local/bin/sing-box run -C /home/woioeow/sing-box -D /var/lib/sing-box
Restart=on-failure
User=woioeow

[Install]
WantedBy=multi-user.target
```

### 客户端 VLESS URI

```
vless://<UUID>@<IP>:<PORT>?type=tcp&encryption=none&security=reality&flow=xtls-rprx-vision&sni=<server_name>&fp=chrome&pbk=<PublicKey>&sid=<short_id>#<节点名>
```

---

## 二、DNS 故障排查

### 触发场景

sing-box 流量不通，日志报：
- `"The name org.freedesktop.resolve1 was not provided by any .service files"`
- `"link has no DNS servers configured"`
- `"connection reset by peer"`（握手阶段）

### 根因

sing-box DoH DNS 底层调用 glibc `getaddrinfo`，需要 systemd-resolved stub resolver（127.0.0.53:53）。容器类/最小化 VPS 默认没有 systemd-resolved 或网卡没绑定 DNS。

### 错误演变路径

1. **没装 systemd-resolved** → `org.freedesktop.resolve1 was not provided`
2. **装了但没绑定 DNS 到 eth0** → `link has no DNS servers configured`
3. **正确绑定后** → 无 ERROR，连接正常

### 方案 A：改用 UDP DNS（快速修复）

编辑 `/etc/sing-box/config.json`：

```json
"dns": {
  "servers": [{"type": "udp", "tag": "cf", "server": "1.1.1.1", "server_port": 53}],
  "final": "cf"
},
"route": {
  "default_domain_resolver": {"server": "cf", "strategy": "prefer_ipv4"}
}
```

> ⚠ `default_domain_resolver` 控制 REALITY 握手时解析目标域名，必须设对。

### 方案 B：修复 systemd-resolved（推荐，DoH 更隐蔽）

#### 错误：`link has no DNS servers configured`（Debian 12 特有）

**典型场景**：`resolvectl status` 显示 Global DNS servers 有 `1.1.1.1 8.8.8.8`，但 **Link 2 (eth0)** 没有 `DNS Servers` 行：

```
Global
  DNS Servers: 1.1.1.1 8.8.8.8           ← 配了全局
Link 2 (eth0)
  Current Scopes: LLMNR/IPv4 LLMNR/IPv6  ← 没有 DNS scope！
  Protocols: -DefaultRoute +LLMNR        ← 没有 DefaultRoute
```

**根因**：Debian 12 默认安装的 `systemd-resolved` 在 `/etc/systemd/resolved.conf` 中写入 `DNS=1.1.1.1 8.8.8.8` 只配了全局 DNS，**没有绑定到网络接口**（Link level）。sing-box 通过 `systemd-resolved` stub（127.0.0.53:53）做 REALITY 握手 DNS 解析时，链路级找不到上游 DNS → 报 `link has no DNS servers configured` → TLS 握手失败。

**修复**：必须将 DNS 绑定到 eth0 接口：

```bash
resolvectl dns eth0 1.1.1.1 8.8.8.8
```

验证：`resolvectl status eth0` 应显示 `Current Scopes: DNS LLMNR/IPv4 LLMNR/IPv6` + `DNS Servers: 1.1.1.1 8.8.8.8` + `+DefaultRoute`。

**持久化配置（重启不丢）**：

```bash
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/dns-servers.conf << 'EOF'
[Resolve]
DNS=1.1.1.1 8.8.8.8
EOF
systemctl restart systemd-resolved
```

```bash
# 1. 安装
apt-get update && apt-get install -y systemd-resolved
systemctl enable --now systemd-resolved

# 2. 写入 DNS 配置（默认为空！）
echo "[Resolve]
DNS=1.1.1.1 8.8.8.8" > /etc/systemd/resolved.conf
systemctl restart systemd-resolved

# 3. 绑定到网卡
resolvectl dns eth0 1.1.1.1 8.8.8.8

# 4. 确认
resolvectl status eth0   # 应看到 +DefaultRoute
cat /etc/resolv.conf     # 应看到 nameserver 127.0.0.53

# 5. 重启 sing-box
systemctl restart sing-box
journalctl -u sing-box --no-pager -n 5
```

### 一键修复命令

```bash
apt-get install -y systemd-resolved && \
echo "[Resolve]
DNS=1.1.1.1 8.8.8.8" > /etc/systemd/resolved.conf && \
systemctl enable --now systemd-resolved && \
timeout 20 resolvectl dns eth0 1.1.1.1 8.8.8.8 && \
systemctl restart sing-box
```

### 坑

| 坑 | 原因 | 解法 |
|----|------|------|
| resolvectl 超时 | 容器 D-Bus 不稳定 | 先写 resolved.conf，再用 `timeout 20 resolvectl` |
| python3/nslookup 能解析但 sing-box 失败 | eth0 没有 +DefaultRoute | 必须做 `resolvectl dns eth0` 绑定 |
| resolved.conf 默认为空 | Debian 精简镜像 | 必须手动写入 `[Resolve]` DNS 字段 |
| 装了 resolved 还是失败 | eth0 没 DNS scope | resolved.conf + resolvectl 双重配置 |

---

## 三、客户端配置（sing-box 1.13.x）

```json
{
  "inbounds": [
    {"tag": "socks", "type": "socks", "listen": "127.0.0.1", "listen_port": 1080},
    {"tag": "http", "type": "http", "listen": "127.0.0.1", "listen_port": 1081}
  ],
  "outbounds": [{
    "tag": "atlanta", "type": "vless",
    "server": "<IP>", "server_port": <PORT>,
    "uuid": "<UUID>", "flow": "xtls-rprx-vision",
    "tls": {
      "enabled": true, "server_name": "www.cloudflare.com",
      "utls": {"enabled": true, "fingerprint": "chrome"},
      "reality": {"enabled": true, "public_key": "<PublicKey>", "short_id": "<short_id>"}
    }
  }]
}
```

> ⚠ `utls.fingerprint` 必须指定，1.13.x 单配 `reality.public_key` 报 `uTLS is required by reality client`

```bash
# 测试
curl -s --socks5 127.0.0.1:1080 https://www.google.com -o /dev/null -w "%{http_code}"
```

---

## 四、Docker 环境 nginx + Let's Encrypt SSL

当 Docker nginx 占 80 端口时，certbot 用 `--webroot` 模式：

```bash
# 1. 关 Cloudflare 代理（DNS Only）
# 2. docker-compose 挂载 /var/lib/letsencrypt 和 /etc/letsencrypt
# 3. nginx.conf 配置 acme-challenge 路径
# 4. certbot certonly --webroot -w /var/lib/letsencrypt -d <domain>
# 5. 自动续期：certbot renew --deploy-hook "docker exec <container> nginx -s reload"
```

---

## 五、Atlanta 重置风险

Atlanta (23.95.218.144) RackNerd VPS 会周期性重置。**会被清空**：UFW、fail2ban、sudoers、sing-box。**不受影响**：Docker、nginx 配置、Let's Encrypt、用户主目录。

重建顺序：apt install ufw fail2ban → ufw allow → 重建 sing-box → 恢复 sudo NOPASSWD。

---

## 七、安全事件响应

当 VPS 被入侵（如 Acck 东京之前被黑），应急响应流程：

### 7.1 应急操作

1. **断网隔离**：`ufw deny from any to any` 或停止 sing-box
2. **检查入侵痕迹**：`last` / `journalctl -xe` / `cat /var/log/auth.log | grep -i "failed\|accepted"`
3. **修改 root 密码**：`passwd`
4. **撤销所有 SSH 密钥**
5. **重新生成 sing-box 密钥对**
6. **更新 config.json**：替换 private_key、生成新 UUID
7. **重启 sing-box**
8. **通知用户更新客户端 VLESS URI**

### 7.2 密钥轮换

```bash
PRIVATE_KEY=$(sing-box generate reality-keypair | grep PrivateKey | cut -d' ' -f2)
PUBLIC_KEY=$(sing-box generate reality-keypair | grep PublicKey | cut -d' ' -f2)
UUID=$(cat /proc/sys/kernel/random/uuid)
SHORT_ID=$(sing-box generate rand 8 --hex)
```

### 7.3 更新 servers.yaml

更新 `uuid`、`pbk`、`sid` 字段，改 `status` 为"已修复"。

### 7.4 事后加固

检查未知用户、cron job、systemd 服务，确认 SSH 端口 + fail2ban + UFW 均已配置。

## 八、性能验证

### 8.1 临时客户端测试

部署节点后，在本机（如有 sing-box 二进制）启动临时客户端验证：

**客户端配置文件** (`/tmp/sb-test-client.json`)：

```json
{
  "log": {"level": "warn"},
  "inbounds": [
    {"type": "socks", "tag": "socks-in", "listen": "127.0.0.1", "listen_port": 10808},
    {"type": "http", "tag": "http-in", "listen": "127.0.0.1", "listen_port": 10809}
  ],
  "outbounds": [{
    "type": "vless", "tag": "test",
    "server": "<IP>", "server_port": <PORT>,
    "uuid": "<UUID>", "flow": "xtls-rprx-vision",
    "tls": {
      "enabled": true, "server_name": "www.microsoft.com",
      "utls": {"enabled": true, "fingerprint": "chrome"},
      "reality": {"enabled": true, "public_key": "<PublicKey>", "short_id": "<short_id>"}
    }
  }],
  "route": {"final": "test"}
}
```

```bash
# 启动后台客户端
sing-box run -c /tmp/sb-test-client.json &

# 验证
curl -sx socks5h://127.0.0.1:10808 https://httpbin.org/ip  # 应返回节点IP
curl -sx socks5h://127.0.0.1:10808 -o /dev/null -w "Google: %{http_code} | %{time_total}s\n" https://www.google.com
curl -sx socks5h://127.0.0.1:10808 -o /dev/null -w "CF 10MB: %{http_code} | %{time_total}s | %{speed_download}B/s\n" "https://speed.cloudflare.com/__down?bytes=10485760"

# 清理
pkill -f "sing-box.*test"
```

### 8.2 代理测试（已有客户端环境）

```bash
curl -s --socks5 127.0.0.1:1080 https://www.google.com -o /dev/null -w "HTTP %{http_code}, %{time_total}s\n"
curl -s --socks5 127.0.0.1:1080 -o /dev/null -w "速度: %{speed_download}B/s\n" https://speed.cloudflare.com/__down?bytes=1048576
```

### 8.3 状态检查

```bash
journalctl -u sing-box --since "5 minutes ago" --no-pager
systemctl status sing-box
ss -tlnp | grep sing-box
ss -tn | grep <proxy_port> | wc -l
```

### 8.3 DNS 验证

```bash
resolvectl status eth0     # 必须看到 DNS Servers
resolvectl query www.cloudflare.com
nslookup google.com 127.0.0.53
```

---

## 九、Vision 流控 mux EOF 诊断

### 错误现象

```
ERROR inbound/vless[in-vless-reality]: process connection from <IP>:<PORT>: mux connection closed: read frame header: EOF
```

### 真实原因

**这是正常的，不是真正的错误。**

Vision（`xtls-rprx-vision`）内部使用 mux 多路复用。当客户端正常关闭一个连接后，服务端 Vision handler 会尝试再读一个 mux 帧头——但连接已关闭，所以返回 EOF。

### 何时出现

- 客户端关闭了一个网页 / 断开了一个会话
- 客户端 mux 会话超时（如 NAT 重置、网络切换）
- 中美线路丢包导致 mux 分片超时断开

### 区分用户连接 vs 扫描攻击

**不要一看到 ERROR 就封IP！** 用户自己的连接也会记录同样的 mux EOF 错误。

| 特征 | 用户正常连接 | 端口扫描/攻击 |
|------|------------|-------------|
| 错误位置 | `inbound/vless[in-vless-reality]: mux connection closed: read frame header: EOF` | 握手阶段失败（TLS/Reality 拒绝） |
| 连接状态 | 成功到达 Vision handler | 根本进不了 handler |
| 来源 IP | 已知用户 IP 段（如中国电信/联通/移动） | 随机国外 IP，未见过 |
| 频率 | 与用户活跃度相关 | 有规律、全端口扫描 |
| 确认方法 | 客户端验证 —— 问用户是否在连接；查看 `ss -tn \| grep <port> \| wc -l` 活跃连接是否匹配 | 无对应客户端 |

**黄金法则：先查 IP 归属，再决定拦截。** 用户来自中国电信/联通，IP `1xx.xx.xxx.xxx` 是中国家庭宽带段 —— 不要封。

### 影响

- ❌ 不影响连接建立（TLS/Reality 握手正常）
- ❌ 不影响已建立的流量（视频、网页正常）
- ✅ 只是 sing-box 将连接清理事件记录为 ERROR 级别

### 如何确认连接正常

```bash
ss -tn | grep <proxy_port> | wc -l           # 查看活跃连接数
curl -s --connect-timeout 5 -o /dev/null -w "%{http_code} %{time_total}s\n" https://www.google.com
```

### 减少日志噪音

```bash
# 将 log.level 改为 "error" 及以上
# 或在 sing-box config 中:
"log": {"level": "error", "timestamp": true}
```

> 注：sing-box 没有针对 Vision mux 日志的独立开关，改 log level 是唯一方式。

---

## 十、中美线路性能诊断

### 触发场景

用户反馈：
- "延迟 200ms+"
- "视频流只有两三千 kbps"
- "能连上但速度慢"

### 诊断流程

#### 1. 排除服务器自身瓶颈

```bash
# CPU/内存/负载
uptime
free -h

# 服务器带宽测试
curl -s -o /dev/null -w 'CacheFly: %{speed_download} B/s\n' --max-time 15 http://cachefly.cachefly.net/10mb.test
curl -s -o /dev/null -w 'Tokyo: %{speed_download} B/s\n' --max-time 15 http://speedtest.tokyo2.linode.com/100MB-tokyo2.bin

# 网络队列
tc qdisc show dev eth0
```

服务器带宽 >100 Mbps → 瓶颈不在服务器。

#### 2. 判断客户端一侧延迟

```bash
# 从服务器 ping 客户端 IP
ping -c 5 -W 3 <client_ip>
```

> ⚠ **ICMP 屏蔽**：中国电信/联通/移动普遍**屏蔽 ICMP ping**（从境外发往中国），100% 丢包不代表线路不通。改用 TCP 探测：
> ```bash
# 确认 80/443 端口可达
curl -s -o /dev/null -w "TCP connect: %{time_connect}s\n" --connect-timeout 10 http://www.baidu.com

# 或从第三方日本/港台节点 curl 测
```

#### 3. 典型路由表现

| 服务器位置 | 中国用户预期延迟 | 视频流速度（非 CN2） |
|-----------|-----------------|--------------------|
| 洛杉矶 (ColoCrossing/RackNerd) | 180-250ms | 2-10 Mbps，高峰期可能 <5 Mbps |
| 东京 (AkileCloud) | 60-100ms | 10-50 Mbps |
| 香港 | 30-60ms | 50-200 Mbps（但存量少，易被墙） |

#### 4. 定位瓶颈

- **服务器到美国/日本 CDN 快**（>100 Mbps）→ 服务器带宽不是瓶颈
- **客户端到服务器丢包 >5%** → 中国电信非 CN2 线路，高峰期必然受限
- **客户端同区域其他节点也慢** → 确认是中国侧限速

#### 5. 识别拥堵路径（traceroute 常见模式）

客户端 traceroute 到代理服务器，重点关注第 2-4 跳（国内出口段）：

```
9    51ms      202.97.12.17              ← 电信骨干（国内段延迟正常）
10  219ms      202.97.22.122             ← 电信国际出口（延迟突增 = 拥塞）
11  490ms      ...                        ← 丢包/高延迟 = 国际段拥堵
12  223ms      be6009.ccr81.sjc13...      ← CogentCo 圣何塞接入
13  223ms      be3097.ccr41.lax01...      ← CogentCo 洛杉矶
```

**关键判断规则：**
- `202.97.x.x` = 电信 163 普通骨干。国内段（＜30ms 内跳）快，国际出口段突增 200ms+ 表示 163 出口拥塞
- CogentCo（`154.54.x.x`, `be*.ccr*.cogentco.com`）与电信的 peer 是知名的拥堵点
- GTT（`62.115.x.x`）、CogentCo 均为 Tier 1 批发商，中国方向无 QoS 保障
- 对比：走 CN2 GIA 的 traceroute 电信段会显示 `59.43.x.x`，延迟平稳 150-170ms

**给客户的简洁解释：** "你的流量从成都电信 163 普通出口出去，走 CogentCo 批发商到洛杉矶，高峰期这条线路就是被 QoS 压到 2-3 Mbps，物理限制。不是服务器问题。"

#### 6. 解决方案（按推荐排序）

| 方案 | 效果 | 代价 |
|------|------|------|
| **换东京/香港节点** | 延迟降 50-70%，速度翻倍以上 | 需重新分发客户端配置 |
| **换 CN2 GIA 线路 VPS** | 延迟稳 150ms，速度 20+ Mbps | 价格 2-3x，国内购买困难 |
| **换中转（如隧道转发到香港）** | 中等改善 | 多一跳，运维复杂度增加 |
| **保持现状** | 2-3 Mbps 对非视频场景可用 | 视频体验差 |

#### 7. 中日 vs 中美节点对比（实测参考）

| 指标 | 洛杉矶 (ColoCrossing) | 东京 (AkileCloud) |
|------|---------------------|-------------------|
| ping (成都→节点) | 214-230ms | 87-99ms |
| 百度 CDN 下载 | 2-3 Mbps（高峰期） | 65 Mbps |
| 骨干路径 | 电信163 → CogentCo | 电信 → NTT/KDDI |
| 高峰期限速 | 严重（<5 Mbps） | 较轻（>20 Mbps） |

**底线：** 国内用户追求视频体验，优先推荐**日本节点**。洛杉矶只能当"能用"水平。

> **要点**：国内用户到美国非 CN2 线路，高峰期 2-3 Mbps 是**正常现象**，不是故障。服务器带宽再大，中国电信国际出口的物理限制无法绕过。

---

## 参考文件

- [`references/china-us-routing-patterns.md`](references/china-us-routing-patterns.md) — 实测 traceroute 模式、电信 163 vs CN2 识别、各线路性能速查

## 十一、VLESS+WS 套 Cloudflare CDN

### 适用场景

Reality 模式在某些网络下可能不稳定（如中国移动/部分留学生宿舍），或需要 CDN 加速/隐藏源站 IP 时。

### 原理

```
用户 ──TLS──→ Cloudflare CDN ──WebSocket──→ 源站
    ↑ CF 边缘终止 TLS             ↑ 源站不需要 TLS
```

Cloudflare 支持 WebSocket 代理（所有套餐默认开启），TLS 在 CF 边缘终止，源站只需运行 VLESS+WS（无 TLS）。

### ⚠ 前置条件

1. **域名在 Cloudflare 托管**（如 `357561.xyz`）
2. **加一条 DNS A 记录**指向源站 IP，开启橙色云（Proxied）
3. **Cloudflare Tunnel 无关**：此方案不需要 cloudflared，直接走 Cloudflare CDN 的 WebSocket 代理
4. **端口必须使用 Cloudflare 支持的端口**（见下方）

### ⚡ Cloudflare 端口限制（重要）

Cloudflare CDN（橙色云）**只代理以下端口**（其他端口连接会超时）：

```
80  443  2052  2053  2082  2083  2086  2087  2095  2096  8080  8443  8880
```

**不要用 37182 或其他随机端口** → Cloudflare 不会转发这些端口的流量，连接会一直 timeout。

推荐用 **443**（伪装 HTTPS）或 **8443**（或 2096）。

### 🔐 Cloudflare SSL/TLS 模式与源站 TLS 的关系

当 DNS 记录开启橙色云，Cloudflare 到源站的连接受 SSL/TLS 加密模式控制：

| CF SSL/TLS 模式 | 源站是否需要 TLS | 适用场景 |
|----------------|----------------|---------|
| **关闭** | ❌ 不需要 | 不安全，不推荐 |
| **灵活** | ❌ 不需要 | 源站无 TLS 时用（CF→origin 明文） |
| **完全** | ✅ 需要（任意证书） | 自签证书可用 ✅ |
| **完全（严格）** | ✅ 需要（有效 CA 证书） | Let's Encrypt 等 CA 签发证书 |

**坑：默认模式是"完全"或"完全（严格）"**。如果源站没开 TLS，Cloudflare 连接 origin 时返回 **525（SSL 握手失败）**。

**推荐做法**：源站开 TLS + 自签证书，CF 面板设为**完全**（不勾选严格）。

### 服务端配置（sing-box）

**方案 A：源站无 TLS（CF 灵活模式）**

```json
{
  "inbounds": [{
    "type": "vless", "tag": "in-vless-ws",
    "listen": "0.0.0.0", "listen_port": 443,
    "tcp_fast_open": true,
    "users": [{ "name": "client", "uuid": "<UUID>" }],
    "tls": { "enabled": false },
    "transport": { "type": "ws", "path": "/" }
  }]
}
```
→ 需 CF 面板设为 **SSL/TLS 加密：灵活**

**方案 B：源站有 TLS（CF 完全模式，推荐）**

先生成自签证书：
```bash
mkdir -p /etc/sing-box
openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
  -keyout /etc/sing-box/key.pem \
  -out /etc/sing-box/cert.pem \
  -subj '/CN=<域名或IP>' \
  -addext 'subjectAltName=DNS:<域名>,IP:<IP>'
```

```json
{
  "inbounds": [{
    "type": "vless", "tag": "in-vless-ws",
    "listen": "0.0.0.0", "listen_port": 443,
    "tcp_fast_open": true,
    "users": [{ "name": "client", "uuid": "<UUID>" }],
    "tls": {
      "enabled": true,
      "certificate_path": "/etc/sing-box/cert.pem",
      "key_path": "/etc/sing-box/key.pem"
    },
    "transport": { "type": "ws", "path": "/" }
  }]
}
```
→ 需 CF 面板设为 **SSL/TLS 加密：完全**（不勾选严格）

**关键点：**
- 端口必须用 CF 支持列表中的（推荐 443 或 8443）
- `transport.type: ws` — WebSocket 传输
- `path` 可自定义（如 `/vless`、`/ws`），对 CF 无影响
- WebSocket 在 Cloudflare **默认开启**，无需手动配置

### UFW 放行

```bash
ufw allow 443/tcp comment 'VLESS+WS via CF'
```

**保护源站（可选但推荐）**：限制只允许 Cloudflare IP 段访问：

```bash
for ip in $(curl -s https://www.cloudflare.com/ips-v4); do
  ufw allow from $ip to any port 443 proto tcp
done
ufw deny 443/tcp
```

### 客户端配置

| 参数 | 值 |
|------|-----|
| 地址 | 你的域名 | 
| 端口 | 443（或 8443/2096） |
| UUID | 同服务端 |
| 传输 | WebSocket |
| 路径 | / |
| TLS | ✅ 开启 |
| 流控 | 无 |

#### VLESS URI

```
vless://<UUID>@<域名>:443?type=ws&encryption=none&security=tls&path=%2F&host=<域名>#<节点名>
```

#### sing-box 客户端 outbound

```json
{
  "tag": "cf-ws", "type": "vless",
  "server": "<域名>", "server_port": 443,
  "uuid": "<UUID>",
  "tls": { "enabled": true, "server_name": "<域名>" },
  "transport": { "type": "ws", "path": "/" }
}
```

#### 验证方法

```bash
# 检查 TLS 握手是否通过 Cloudflare
curl -svo /dev/null --connect-timeout 15 https://<域名>/ 2>&1 | grep -E 'SSL|TLS|HTTP'

# 不应看到 525/530 错误
```

### 已知限制

| 问题 | 原因 | 解法 |
|------|------|------|
| WebSocket 闲置超时断开 | Cloudflare 默认 60-120s | 客户端 mux 保活 / heartbeat |
| 大文件可能被限速 | CF 免费套餐 heavy 下载限制 | 分片下载或用 Reality 直连 |
| CF ToS 风险 | 代理/VPN 通过 CDN 违反 ToS | 小流量通常无问题，大量使用建议 Reality |
| 525 错误 | CF→origin TLS 握手失败 | 在源站配置 TLS 或 CF 改为"灵活"模式 |

## 十二、常见错误速查

| 错误 | 原因 | 解决 |
|------|------|------|
| `unknown field "port"` | 旧版字段名 | 改 `listen_port` |
| `unknown field "server"` | TLS 里应为 `server_name` | 重命名 |
| `unknown inbound type: api` | 不存在 | 删除 |
| `cannot unmarshal object into []Outbound` | outbounds 应为数组 | 改 `[{...}]` |
| `decode config: EOF` | JSON 传输失败 | 用 `echo \| ssh` |
| `chdir /var/lib/sing-box: no such file` | 数据目录不存在 | `mkdir -p && chown` |
| `uTLS is required by reality client` | 1.13.x 必须指定 uTLS | outbound.tls 加 utls |
| `sing-box: command not found` | PATH 不同 | 用绝对路径 |
