---
name: vps-init
description: 新 VPS 全生命周期初始化——从购买到上线。输入IP+SSH端口+root密码，自动走完：安全加固→系统配置→sing-box代理→探针部署→komari注册→财务登记。加载此skill时会检查是否也加载了sing-box-ops/lxc-probe-deploy等依赖skill。支持 Debian 和 Alpine。
---

# VPS 初始化流水线

## 前置依赖
加载此 skill 前，也加载以下依赖 skill：
- `sing-box-ops` — sing-box 部署（VLESS+Reality）
- （可选）`lxc-probe-deploy` — LXC 容器探针部署

## 输入
- `$IP`：VPS IPv4 地址
- `$SSH_PORT`：SSH 端口（默认 22，初始化后改高位）
- `$ROOT_PASSWORD`：root 密码
- `$NAME`：节点简称（如 "东京1"）
- `$PROXY_PORT`：代理端口
- `$BILLING`：价格信息（¥/月, 周期, 到期日）

## OS 检测
第一步必须先确认目标系统：

```bash
ssh root@$IP "cat /etc/os-release | head -3"
# Debian → NAME="Debian GNU/Linux"
# Alpine → NAME="Alpine Linux"
# Ubuntu → NAME="Ubuntu"
```

所有后续步骤根据 OS 分支走不同命令。

---

## 阶段一：初始接入

```bash
sshpass -p '$ROOT_PASSWORD' ssh -o StrictHostKeyChecking=no -p $SSH_PORT root@$IP
```

---

## 阶段二：安全加固

### Debian / Ubuntu
```bash
apt update && apt upgrade -y
apt install -y curl wget ufw fail2ban
```

### Alpine
```bash
apk update && apk upgrade
apk add curl wget ufw fail2ban
# Alpine 可能没有 ufw（用 iptables 代替），安装：
apk add iptables ip6tables iptables-openrc
```

### SSH 端口变更（通用）
```bash
sed -i "s/#Port 22/Port $NEW_PORT/" /etc/ssh/sshd_config
sed -i "s/PermitRootLogin yes/PermitRootLogin prohibit-password/" /etc/ssh/sshd_config
```

### 防火墙
```bash
# Debian
ufw allow $NEW_PORT/tcp
ufw enable

# Alpine（iptables）— ⚠️ 仅限 KVM/非LXC！LXC绝对不能配iptables！
iptables -A INPUT -p tcp --dport $NEW_PORT -j ACCEPT
iptables -A INPUT -j DROP  # 默认拒绝入站
ip6tables -A INPUT -p tcp --dport $NEW_PORT -j ACCEPT
rc-service iptables save
```

### ⚠️ LXC 容器：永远不要碰 iptables！
LXC 容器共享宿主机网络命名空间，`iptables -F` 会清掉提供商预设的 NAT 端口转发规则，导致 SSH 锁死。
**LXC 容器只需 SSH 加固**（禁用密码 + 密钥登录），不做任何 iptables 操作。
详见 `sysadmin/system-hardening` 技能的「NAT VPS LXC 陷阱」章节。

### 重启 SSH（⚠️ 注意 OS 差异）
```bash
# Debian / Ubuntu
systemctl restart sshd

# Alpine
rc-service sshd restart
```

---

## 阶段三：系统配置

### 时区
```bash
# Debian
timedatectl set-timezone Asia/Tokyo
# 如果 timedatectl 不存在，用：
ln -sf /usr/share/zoneinfo/Asia/Tokyo /etc/localtime

# Alpine
cp /usr/share/zoneinfo/Asia/Tokyo /etc/localtime
```

### DNS 配置（sing-box REALITY 握手需要）
```bash
# Debian — systemd-resolved
resolvectl dns eth0 1.1.1.1 8.8.8.8
mkdir -p /etc/systemd/resolved.conf.d
cat > /etc/systemd/resolved.conf.d/dns-servers.conf << 'EOF'
[Resolve]
DNS=1.1.1.1 8.8.8.8
EOF

# Alpine — 没有 systemd-resolved，直接用 /etc/resolv.conf
cat > /etc/resolv.conf << 'EOF'
nameserver 1.1.1.1
nameserver 8.8.8.8
EOF
```

---

## 阶段四：部署服务

### 1. sing-box 代理 → 加载 `sing-box-ops` skill

### 2. Komari 探针
```bash
# Debian — 从 56idc-la 获取 agent
sshpass -p '...' ssh root@107.172.231.70 "cat /opt/komari/agent" > /opt/komari/agent
chmod +x /opt/komari/agent

# Alpine — 同样适用（komari agent 是静态编译二进制）
# 注意：Alpine 用 musl libc，确保 agent 是 musl 编译版
```

### 3. Cloudflare Tunnel（按需）

---

## 阶段五：注册登记

1. **Komari 面板**：通过 56idc-la komari API 添加节点
2. **servers.yaml**：更新 `~/.hermes/inventory/servers.yaml`

---

## 阶段六：验证

```bash
# 代理测试
curl -s --socks5 127.0.0.1:1080 https://www.google.com -o /dev/null -w "%{http_code}"

# DNS 验证
# Debian
resolvectl status eth0

# Alpine
nslookup google.com   # 或直接 cat /etc/resolv.conf

# 面板确认 — 查看 komari 是否显示新节点数据
```

---

## ⚠️ OS 差异速查表

| 操作 | Debian | Alpine |
|------|--------|--------|
| 包管理 | `apt install` | `apk add` |
| 服务管理 | `systemctl` | `rc-service` |
| 自启动 | `systemctl enable` | `rc-update add` |
| 防火墙 | `ufw` | `iptables` + `iptables-openrc` |
| 端口监听 | `ss -tlnp` | `netstat -tlnp`（无 `ss`） |
| 默认 shell | `bash` | `ash`（POSIX 子集，无 bashism） |
| 网络配置 | `systemd-resolved` / `resolvectl` | `/etc/resolv.conf` 直接写 |
| 时区 | `timedatectl` | `cp zoneinfo` |
| init 目录 | `/etc/systemd/system/` | `/etc/init.d/` |
| SSH 服务 | `sshd` | `sshd`（Alpine 默认安装 dropbear？检查 `ps aux \| grep ssh`） |
| Python | `python3`（预装或 `apt install`） | `python3`（需 `apk add python3`） |
| 命令来源 | GNU coreutils | BusyBox（精简实现，参数可能不同） |

> **BusyBox 陷阱**：Alpine 的 `ps`、`grep`、`sed`、`awk`、`netstat` 都是 BusyBox 版本，参数和 GNU 版有差异。复杂操作需要 `apk add coreutils` 或先用 `ash` 测试。

---

## 🔧 Alpine 常见坑

### 1. heredoc 中的引号
Alpine 的 `ash` 解析 heredoc 时，变量展开规则与 bash 有差异。复杂内容用 `<< 'EOF'`（单引号包裹定界符）禁用变量展开。

### 2. 无 bash 兼容性
OpenRC init 脚本用 `#!/sbin/openrc-run`，不是 `#!/bin/bash`。不要在 Alpine init 脚本里写 bash 语法（`source` 不用，用 `.`）。

### 3. `ss` 命令不存在
用 `netstat -tlnp` 代替。如需要 `ss`，`apk add iproute2`。

### 4. 内存敏感
Alpine 常用于 256MB-512MB 的 LXC 容器，注意 `swap` 配置，大内存操作用 `timeout` 包裹防止 OOM。
