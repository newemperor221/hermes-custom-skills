---
name: iptables-firewall
description: iptables 防火墙全栈 — 规则部署、fail2ban 联动、DNAT 端口转发、UFW 工作流。触发："iptables"、"fail2ban"、"防火墙"、"端口转发"、"DNAT"、"UFW"。
triggers:
  - iptables 配置
  - fail2ban 部署
  - 防火墙规则
  - 端口转发 DNAT
  - UFW 规则管理
---

# iptables 防火墙全栈

iptables + fail2ban 部署、DNAT 端口转发、UFW 工作流一站式指南。

---

## 一、iptables + fail2ban 部署

### 适用场景
- 服务器无 UFW，或想用更原生的方式管理防火墙
- 需要在多台 VPS 上统一部署安全规则
- 需要 fail2ban 动态防护 SSH 暴力破解

### 标准规则模板

```bash
# 刷新规则
iptables -F
iptables -X

# 默认策略
iptables -P INPUT ACCEPT
iptables -P FORWARD DROP
iptables -P OUTPUT ACCEPT

# SSH 防爆破（每30秒最多6个新连接，nf_tables 兼容写法）
iptables -A INPUT -p tcp --dport SSH_PORT -m conntrack --ctstate NEW -m recent --set --name SSH
iptables -A INPUT -p tcp --dport SSH_PORT -m conntrack --ctstate NEW -m recent --update --seconds 30 --hitcount 6 --name SSH -j DROP
iptables -A INPUT -p tcp --dport SSH_PORT -m conntrack --ctstate NEW -m recent --rcheck --name SSH -j ACCEPT

# 已建连放行
iptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT

# 本地回环
iptables -A INPUT -i lo -j ACCEPT

# Ping（可开关）
# iptables -A INPUT -p icmp --icmp-type echo-request -j ACCEPT
# iptables -A INPUT -p icmp --icmp-type echo-request -j DROP

# 保存
mkdir -p /etc/iptables
iptables-save > /etc/iptables/rules.v4
```

IPv6 同理（`--name SSH6`，`ipv6-icmp`）。

### ⚠ recent 模块语法关键坑

Debian 12 用 `nf_tables` 内核模块而非 `iptable_filter`，`--recent` 必须跟操作类型：
- `--set` — 首次新建记录
- `--rcheck` — 检查记录存在
- `--update` — 检查并更新时间戳/计数

**错误**：直接 `--name SSH -j ACCEPT`（缺少 `--rcheck` 或 `--update`）
**正确**：`--rcheck --name SSH -j ACCEPT`

三条规则缺一不可：
1. `--set --name SSH` — 记录来访 IP
2. `--update --seconds 30 --hitcount 6 --name SSH -j DROP` — 30秒超过6次则封
3. `--rcheck --name SSH -j ACCEPT` — 在白名单则放行

### fail2ban 关键坑

**Debian 12 没有 `/var/log/auth.log`**：SSH 日志走 systemd journal，必须指定 `backend = systemd`。

```ini
# /etc/fail2ban/jail.local
[DEFAULT]
bantime  = 3600
findtime = 600
maxretry = 5
banaction = iptables-multiport
chain = INPUT

[sshd]
enabled  = true
port     = SSH_PORT
filter   = sshd
backend  = systemd
maxretry = 5
bantime  = 3600
```

**sudo 延迟**：`sudo: unable to resolve host` → `/etc/hosts` 加 `127.0.1.1  $(hostname)`。

### 验证

```bash
iptables -L INPUT -v -n          # 规则顺序
fail2ban-client status sshd      # jail 运行中
ss -tlnp                         # 监听端口
# 从另一台机器测试 SSH 连接
```

---

## 二、DNAT 端口转发

### ⚠ 核心认知：DNAT 只改地址，不建端口

加了 `iptables -t nat -A PREROUTING ... -j DNAT` 不会创建监听端口。没有服务绑定该端口 → TCP RST。**真正端口转发用 socat**。

### 流量路径

| 流量类型 | 走哪个链 |
|---------|---------|
| 外部访问公网 IP | `nat/PREROUTING` |
| 本机访问 127.0.0.1 | `nat/OUTPUT` |
| 实际转发报文 | `filter/FORWARD` |

**踩坑**：Docker 在 `nat/OUTPUT` 的 DOCKER 链排除了 `127.0.0.0/8`，本机 `curl 127.0.0.1:port` 不触发 DNAT。

### 方案 A：纯 iptables DNAT

```bash
# 1. 备份
sudo iptables-save > /tmp/iptables-backup-$(date +%Y%m%d_%H%M%S).v4

# 2. DNAT
sudo iptables -t nat -I PREROUTING -p tcp --dport 22080 -j DNAT --to-destination 172.18.0.2:80

# 3. FORWARD（Docker 环境写 DOCKER-USER 链！）
sudo iptables -I DOCKER-USER -p tcp -d 172.18.0.2 --dport 80 -j ACCEPT

# 4. 验证（从外部机器）
curl http://公网IP:22080/

# 5. 清理
sudo iptables -t nat -D PREROUTING -p tcp --dport 22080 -j DNAT --to-destination 172.18.0.2:80
sudo iptables -D DOCKER-USER -p tcp -d 172.18.0.2 --dport 80 -j ACCEPT
```

### 方案 B：socat（更简单）

```bash
sudo socat TCP-LISTEN:22081,fork,reuseaddr TCP:172.18.0.2:80 &
curl http://127.0.0.1:22081/
sudo pkill socat
```

### Docker 环境 FORWARD 链顺序

```
FORWARD (policy DROP)
  → DOCKER-USER       ← 手动规则写这里
  → DOCKER-FORWARD    ← Docker 自动规则
  → ufw-before-forward
```

手动 FORWARD 规则加在 `ufw-user-forward` 对容器流量**不生效**。

---

## 三、UFW 工作流

### 基本操作

```bash
sudo ufw allow SSH_PORT/tcp
sudo ufw insert 1 deny from any to any port 22
sudo ufw status verbose
sudo ufw status numbered
sudo bash -c 'echo y | ufw delete 2; echo y | ufw delete 3'
```

### 改 SSH 端口正确步骤（防锁）

1. 先开新端口 UFW 规则
2. `sudo systemctl edit sshd` 改 Port
3. `sudo systemctl restart sshd`
4. **新开终端**测试新端口
5. 删除旧端口规则
6. 确认后 disable 旧端口

### fail2ban + UFW 联动

```bash
sudo fail2ban-client status sshd
sudo iptables -L -n | grep -i f2b   # 有规则即正常
```

## 四、UFW → 纯 iptables 迁移

### 迁移流程

**0. 查清现有 UFW 规则**
```bash
# 看实际生效的 ufw 链内容（不是 user.rules）
iptables -L -n -v --line-numbers
cat /etc/ufw/user.rules   # 用户自定义规则
cat /etc/ufw/user6.rules
```

**1. 在远程服务器上逐条写 iptables 规则（不要 SSH 执行太长管道）**

分开执行短的命令集，不要一条 SSH 命令塞太多。

**2. 确认 SSH 能连后再卸载 UFW**

SSH 新连接会触发 `recent --set`，在白名单后能正常放行。但若规则写错（缺 `--rcheck` 或 policy 过严），SSH 会断开。

**3. UFW 卸载后 iptables 残留链清理**
```bash
# 卸载 ufw 后，原有 ufw-* 链还在内存里
ip6tables -F
ip6tables -X
# 或重启 systemd-journald 让 netfilter 重载
```

**4. 保存规则**
```bash
mkdir -p /etc/iptables
iptables-save > /etc/iptables/rules.v4
ip6tables-save > /etc/iptables/rules.v6
```

### ⚠ 迁移炸机恢复

若 SSH 断了（通常是因为 `recent` 模块语法错误或 policy 过严）：

1. 通过 **服务商控制台 VNC** 登录
2. `iptables -F` 清空所有规则，`iptables -P INPUT ACCEPT` 恢复默认
3. 重新写入正确规则

---

## Alpine Linux 防火墙

### 安装与启用

```bash
# 安装 iptables + ip6tables（IPv4/IPv6 都要）
apk add iptables iptables-openrc iproute2

# 规则保存（Alpine 重启后规则丢失，需每次开机加载）
rc-update add iptables default

# 常用命令
rc-service iptables start    # 启动
rc-service iptables save     # 保存当前规则到 /var/lib/iptables/rules-save
rc-update add iptables boot  # 开机自启

# 查看规则
iptables -L -n
ip6tables -L -n
```

### ⚠️ LXC 容器上绝对不能用 iptables（包括 iptables -F）

NAT VPS（无聊云、isvoro 等）的公网端口由宿主机网关映射到容器内网端口（如公网 48256 → 内网 47632）。容器内 `iptables -F` + `-P INPUT DROP` 会清掉提供商预设的过滤规则，导致**所有入站连接断掉**（SSH、面板访问全挂），而出站和 agent 上报仍正常。唯一恢复手段：到提供商面板**重装容器**。

如果容器里 iptables 不可用（需要 CAP_NET_ADMIN），不要安装：只做 SSH 加固即可。

安全做法：不 `-F`，直接追加：
```bash
iptables -A INPUT -p tcp --dport <SSH_PORT> -j ACCEPT
iptables -P INPUT DROP
```

**检查 iptables 可用性后再操作：**
```bash
which iptables && iptables -L 2>&1 | head -3 || echo "iptables不可用，跳过防火墙配置"
```

### Alpine 修改 SSH 端口后连接失败排障：
1. `cat /proc/net/tcp` 查监听端口（十六进制）
2. `grep "^Port" /etc/ssh/sshd_config` 确认配置生效
3. Alpine 没装 `ss`/`netstat`：`apk add iproute2 net-tools`

**IPv6-only 服务器**：用 `ip6tables`，IPv6 没有 NAT。访问 IPv4 资源走 NAT64 或 HE 隧道反向转发。

## 四、各服务器参考配置

| 服务器 | IP | SSH端口 | 防火墙 | fail2ban |
|--------|-----|--------|--------|---------|
| LA (198.46.147.71) | 198.46.147.71 | 43827 | UFW | sshd jail 启用 |
| LA-1c2.5g (155.94.180.55) | 155.94.180.55 | 28394 | iptables | sshd jail 启用 |
| 纽约 (172.245.159.219) | 172.245.159.219 | 22 | 重装后待配 | 待装 |
| 亚特兰大 (23.95.218.144) | 23.95.218.144 | 15927 | 重装后待配 | 待装 |
| KS (45.39.12.227) | 45.39.12.227 | 65239 | 待配 | 待装 |
| TK (156.231.141.232) | 156.231.141.232 | 45781 | 待配 | 待装 |
