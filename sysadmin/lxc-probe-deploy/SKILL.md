---
name: lxc-probe-deploy
description: "LXC 容器探针部署 — IPv6-only VPS、cloudflared 隧道、轻量探针安装、极低资源环境适配。触发：\"LXC\"、\"探针部署\"、\"cloudflared 隧道\"、\"IPv6-only\"、\"小内存VPS\"、\"tz子域名\"。"
tags: [lxc, probe, cloudflared, ipv6, komari, lightweight, monitoring]
---

# LXC 容器探针部署

## 适用场景
- 低配 LXC VPS（512M 以下内存、1-2G 磁盘）
- IPv6-only 或 IPv4 NAT（非标准端口）环境
- 需要通过 cloudflared 隧道暴露服务

## Step 0: 环境检查
```bash
uname -m                    # 架构：x86_64/aarch64
free -h                     # 实际可用内存（LXC 通常比标称少 10-15%）
df -h                       # 磁盘空间（ZFS 后端会显示 zfs 路径）
cat /etc/os-release         # 系统版本
ip addr show                # 网络（IPv6 地址）
ss -tlnp                    # 已监听端口
```

## Step 1: SSH 密钥登录
```bash
# 上传公钥
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@<IP>

# 禁用密码登录（注意 Alpine 用 rc-service，Debian 用 systemctl）
sed -i 's/^#\?PermitRootLogin .*/PermitRootLogin prohibit-password/' /etc/ssh/sshd_config
sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
# Alpine: rc-service sshd restart
# Debian: systemctl restart sshd
```

**注意**: 不要在 VPS 上 ssh-keygen（私钥在别人机器上不安全）

## Step 2: 基础加固

### 🚫 LXC 容器不配置防火墙

LXC 容器共享宿主机网络命名空间，容器内 iptables/ufw 会破坏提供商预设的 NAT 端口转发规则。**LXC 上只做 SSH 加固，不要装 ufw 或改 iptables。**

如果确定是 KVM 独服（非 LXC），可以用 ufw：
```bash
apt update && apt install -y ufw fail2ban
ufw default deny incoming
ufw allow 22/tcp
ufw allow <探针端口>/tcp    # 如果需要入站
ufw enable
```

## Step 3: 安装探针

### Komari Agent（~20MB）
```bash
curl -fsSL https://raw.githubusercontent.com/KomariLab/komari/main/install.sh | bash
# 按提示输入 Komari Server 地址和 token
```

### Node Exporter（~10MB，给 Prometheus 用）
```bash
wget https://github.com/prometheus/node_exporter/releases/latest/download/node_exporter-*-linux-amd64.tar.gz
tar xzf node_exporter-*.tar.gz
mv node_exporter-*/node_exporter /usr/local/bin/
useradd --no-create-home --shell /bin/false node_exporter

cat > /etc/systemd/system/node_exporter.service << 'EOF'
[Unit]
Description=Node Exporter
After=network.target
[Service]
User=node_exporter
ExecStart=/usr/local/bin/node_exporter
Restart=always
[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now node_exporter
```

## Step 4: Cloudflared 隧道（IPv6-only/NAT 环境必备）

### 安装
```bash
# Debian bookworm
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | gpg --dearmor -o /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/debian bookworm main" > /etc/apt/sources.list.d/cloudflared.list
apt update && apt install -y cloudflared
```

### 创建隧道
```bash
# 登录（需要浏览器，可在本地完成）
cloudflared tunnel login

# 创建隧道
cloudflared tunnel create <tunnel-name>

# 添加 DNS 路由
cloudflared tunnel route dns <tunnel-name> <子域名>.<域名>
```

### 配置 (`~/.cloudflared/config.yml`)
```yaml
tunnel: <tunnel-name>
credentials-file: /root/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: tz.example.com
    service: http://localhost:<探针端口>
  - service: http_status:404
```

### 启动
```bash
cloudflared service install
systemctl enable --now cloudflared
systemctl status cloudflared
```

### 如果已安装过 cloudflared
```bash
cloudflared tunnel list          # 查看已有隧道
cloudflared service uninstall    # 重装（慎用）
```

## Step 5: 验证
```bash
# 探针进程
systemctl status komari-agent   # 或 node_exporter

# cloudflared 隧道
systemctl status cloudflared
cloudflared tunnel info <tunnel-name>

# 外部访问
curl -I https://tz.example.com
```

## 极低资源环境优化
444M 内存 + 1G 磁盘的 LXC：
- ❌ 不装 Docker（吃 200M+）
- ❌ 不装 Uptime Kuma（Node.js 吃 200M+）
- ❌ 不装 nginx（cloudflared 直接代理即可）
- ✅ 探针 agent（20M）
- ✅ cloudflared（30-50M）
- ✅ node_exporter（10M）
- 剩余约 350M 内存，够用

## 命名约定
- `tz.域名` = 探针节点（tz = 探针拼音首字母）
- `stat.域名` = 状态页
- `mon.域名` = 监控面板（Komari Server）

## 常见坑
1. **apt 报 "changed its Version value"** → `apt update --allow-releaseinfo-change`
2. **cloudflared 已安装** → `cloudflared tunnel list` 查看已有隧道
3. **IPv6 ping 不通** → 本地可能没 IPv6，用 cloudflared 或 WARP 解决
4. **NAT 端口随机** → 无法绑定 80/443，必须用 cloudflared 隧道
5. **内存不够** → 关闭不必要服务，用 `systemctl disable` 清理
6. **🚨 LXC 里配 iptables/ufw → 直接断连，只能重装！** 容器共享宿主网络命名空间，iptables 操作会破坏 NAT 转发。区分方法：`cat /proc/1/cgroup | grep -c lxc` 返回 > 0 就是 LXC，跳过防火墙配置。
