---
name: wireguard-vps-mesh
description: WireGuard VPS 组网 — 多台 VPS 间搭建站点到站点 VPN 隧道，实现内网互访、免公网端口暴露、简化跨机通信。覆盖安装配置、密钥管理、路由规则、systemd 自启、调试排障。触发："WireGuard"、"组网"、"VPN"、"隧道"、"wg"、"内网互通"。
---

# WireGuard VPS 组网

## 适用场景

- 多台 VPS（香港/东京/LA）之间建立内网隧道
- 跨服务器直接访问数据库/API 而不暴露公网端口
- 构建安全的服务 mesh（komari 面板互通等）
- 低于 cloudflared 的延迟，纯 UDP 无中间节点

## 架构设计

```
                   ┌──────────┐
                   │  LA(VPS) │
                   │ 10.0.0.1 │ ← 中心节点（如果选星型）
                   └────┬─────┘
                        │
              ┌─────────┼─────────┐
              │         │         │
         ┌────▼──┐ ┌───▼───┐ ┌──▼────┐
         │ 香港   │ │ 东京  │ │ 其他  │
         │10.0.0.2│ │10.0.0.3│ │...    │
         └────────┘ └───────┘ └───────┘
```

推荐**全互联（full mesh）**模式，每台机器直接连接所有其他机器，不依赖中心节点。

## 安装

```bash
# Debian/Ubuntu
sudo apt install wireguard

# Alpine
sudo apk add wireguard-tools

# 检查内核模块
sudo modprobe wireguard
lsmod | grep wireguard
```

## 配置步骤

### 1. 每台 VPS 生成密钥对

```bash
# 在每台 VPS 上执行
wg genkey | tee /etc/wireguard/private.key | wg pubkey | tee /etc/wireguard/public.key
chmod 600 /etc/wireguard/private.key
```

### 2. 收集所有机器的公钥

创建表格（手工填）：

```
VPS      | 公网 IP:端口       | 私网 IP    | 公钥
LA       | <洛杉矶1_IP>:51820 | 10.0.0.1   | <la-pubkey>
香港     | <香港_IP>:51820 | 10.0.0.2   | <hk-pubkey>
东京     | <东京_IP>:51820|10.0.0.3   | <tokyo-pubkey>
```

### 3. 配置每台 VPS 的 wg0.conf

以 **LA (10.0.0.1)** 为例，配置为全互联模式：

`/etc/wireguard/wg0.conf`：

```ini
[Interface]
Address = 10.0.0.1/24
ListenPort = 51820
PrivateKey = <LA的私钥>
MTU = 1420

# 开启 IP 转发（如果这台还要做路由）
PostUp = sysctl -w net.ipv4.ip_forward=1
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT

# 香港 VPS
[Peer]
PublicKey = <hk-pubkey>
Endpoint = <香港_IP>:51820
AllowedIPs = 10.0.0.2/32
PersistentKeepalive = 25

# 东京 VPS
[Peer]
PublicKey = <tokyo-pubkey>
Endpoint = <东京_IP>:51820
AllowedIPs = 10.0.0.3/32
PersistentKeepalive = 25
```

以 **香港 (10.0.0.2)** 为例：

```ini
[Interface]
Address = 10.0.0.2/24
ListenPort = 51820
PrivateKey = <香港的私钥>
MTU = 1420

# LA VPS
[Peer]
PublicKey = <la-pubkey>
Endpoint = <洛杉矶1_IP>:51820
AllowedIPs = 10.0.0.1/32
PersistentKeepalive = 25

# 东京 VPS
[Peer]
PublicKey = <tokyo-pubkey>
Endpoint = <东京_IP>:51820
AllowedIPs = 10.0.0.3/32
PersistentKeepalive = 25
```

### 4. 配置防火墙（UFW）

```bash
# 放行 WireGuard UDP 端口
ufw allow 51820/udp
ufw reload

# 如果使用 iptables：
iptables -A INPUT -p udp --dport 51820 -j ACCEPT
```

### 5. 启动 WireGuard

```bash
# 启动
sudo wg-quick up wg0

# 设置开机自启
sudo systemctl enable wg-quick@wg0

# 查看状态
sudo wg show
```

### 6. 测试连通性

```bash
# 从 LA ping 香港
ping 10.0.0.2

# 从 LA ping 东京
ping 10.0.0.3

# 查看握手状态
sudo wg show
# 应该看到 latest handshake: 几秒前
```

## 高级用法

### 将 WireGuard 作为 sing-box 的出站（outbound）

可以让代理流量走 WG 隧道出站，实现落地分流：

```json
{
  "outbounds": [
    {
      "type": "direct",
      "tag": "wg-out"
    },
    {
      "type": "wireguard",
      "tag": "wg-tun",
      "server": "10.0.0.2",
      "server_port": 51820,
      "local_address": ["10.0.0.1/32"],
      "private_key": "...",
      "peer_public_key": "...",
      "mtu": 1420
    }
  ]
}
```

### 节点间暴露服务（如 Komari API）

香港的 Komari 跑在 `localhost:25774`，但你想从 LA 直接访问：

在 LA 上：`curl http://10.0.0.2:25774` 即可。

不需要开 UFW 端口，不需要 cloudflared，延迟更低。

### 全互联自动配置

如果要管理的节点多，可以用 `wg-gen-web` 或 `wg-config` 工具生成配置。

## 排障

```bash
# 查看 WG 状态
sudo wg show

# 查看内核日志
sudo dmesg | grep wireguard

# 检查端口是否通（从外部）
nc -zvu <ip> 51820

# 抓包验证
sudo tcpdump -i wg0 -n icmp

# 重启
sudo wg-quick down wg0 && sudo wg-quick up wg0

# 检查路由
ip route show dev wg0
```

## 踩坑记录

1. **防火墙必须放 UDP 51820** — WireGuard 是 UDP，UFW 默认 DROP 的情况下不放行就连不上。初始化完成后装 WG 前先配 UFW
2. **PersistentKeepalive 必须有** — NAT 后或防火墙有连接跟踪时，没有心跳包会导致隧道断连。建议 25 秒
3. **MTU 问题** — 某些 VPS 的 UDP 分片有问题，设 MTU=1420 比较安全。如果 SSH 连上但 WG 卡住，先试 `ping -M do -s 1372 10.0.0.x`
4. **公钥配错** — Peer 配的是对方的公钥，Interface 是自己的私钥。最容易混淆的错误
5. **EndPoint 是公网 IP** — Peer 的 Endpoint 是对方的**公网 IP:端口**，不是虚拟 IP
6. **重启后 WG 未自启** — 确认 `systemctl enable wg-quick@wg0` 启用

## 验证步骤

```bash
# 1. 所有节点启动 wg
sudo wg-quick up wg0

# 2. 互相 ping 通
ping -c 3 10.0.0.2    # 从其他节点
ping -c 3 10.0.0.3    # 从其他节点

# 3. 检查握手时间
sudo wg show | grep handshake

# 4. 性能测试（可选）
iperf3 -c 10.0.0.2
```
