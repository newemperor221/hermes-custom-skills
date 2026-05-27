---
name: system-hardening
description: "服务器安全加固 — SSH 加固、内核参数调优、审计日志、最小权限部署。触发：\"加固\"、\"安全\"、\"hardening\"、\"SSH 安全\"、\"内核参数\"、\"audit\"。"
tags: [security, hardening, ssh, kernel, audit, cis-benchmark]
---

# 服务器安全加固

## SSH 加固 (`/etc/ssh/sshd_config`)
```bash
# 禁用密码登录（只允许密钥）
PasswordAuthentication no
PubkeyAuthentication yes

# ⚠️ Alpine 必须额外禁用 keyboard-interactive！
# Alpine 的 OpenSSH 默认启用 keyboard-interactive 认证，
# 攻击者可通过此接口提交密码绕过 PasswordAuthentication no。
# 配合 KbdInteractiveAuthentication no 才能彻底封死密码。
KbdInteractiveAuthentication no

# 禁用 root 密码登录
PermitRootLogin prohibit-password  # 允许 root 用密钥
# 或完全禁止 root SSH
# PermitRootLogin no

# 限制用户
AllowUsers deploy admin
# 或用组
AllowGroups ssh-users

# 修改默认端口
Port 62839

# 禁用空密码
PermitEmptyPasswords no

# 限制认证尝试
MaxAuthTries 3
LoginGraceTime 30

# 禁用 X11 转发
X11Forwarding no

# 禁用 agent 转发
AllowAgentForwarding no

# 超时断开
ClientAliveInterval 300
ClientAliveCountMax 2

# 限制加密算法（只用强算法）
KexAlgorithms curve25519-sha256@libssh.org,diffie-hellman-group16-sha512
Ciphers chacha20-poly1305@openssh.com,aes256-gcm@openssh.com
MACs hmac-sha2-512-etm@openssh.com,hmac-sha2-256-etm@openssh.com
```

```bash
# 应用配置
sshd -t                    # 测试配置语法（⚠️ Alpine 上路径是 /usr/sbin/sshd，不是 /sbin/sshd）
systemctl restart sshd      # systemd 系统
rc-service sshd restart     # Alpine OpenRC 系统
# ⚠️ 保持当前 SSH 会话！新开终端测试连接后再关闭旧会话
```

## 内核参数加固 (`/etc/sysctl.d/99-hardening.conf`)
```bash
# 禁用 IP 转发（除非需要路由器功能）
net.ipv4.ip_forward = 0

# 防 SYN flood
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2

# 禁用 ICMP 重定向
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.default.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

# 禁用源路由
net.ipv4.conf.all.accept_source_route = 0

# 启用反向路径过滤
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# 忽略 ICMP 广播
net.ipv4.icmp_echo_ignore_broadcasts = 1

# 记录可疑数据包
net.ipv4.conf.all.log_martians = 1

# 禁用 IPv6（如不需要）
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

# 应用
sysctl -p /etc/sysctl.d/99-hardening.conf
```

## 文件系统加固
```bash
# 关键目录权限
chmod 700 /root
chmod 600 /etc/shadow
chmod 644 /etc/passwd

# /tmp 独立分区 + noexec
# /etc/fstab:
# tmpfs /tmp tmpfs defaults,noexec,nosuid,nodev 0 0

# 限制 cron 使用
echo "root" > /etc/cron.allow
chmod 600 /etc/cron.allow

# SUID/SGID 审计
find / -perm -4000 -type f 2>/dev/null   # SUID
find / -perm -2000 -type f 2>/dev/null   # SGID
# 移除不必要的 SUID
chmod u-s /usr/bin/unnecessary_binary
```

## 审计日志（auditd）
```bash
apt install auditd

# /etc/audit/rules.d/hardening.rules
-w /etc/passwd -p wa -k identity
-w /etc/shadow -p wa -k identity
-w /etc/sudoers -p wa -k sudoers
-w /etc/ssh/sshd_config -p wa -k sshd
-a always,exit -F arch=b64 -S execve -k exec
-a always,exit -F arch=b64 -S connect -k network

# 应用
augenrules --load
systemctl restart auditd

# 查看审计日志
ausearch -k identity -ts recent
aureport --auth --summary
```

## fail2ban 的替代品：iptables recent 模块做 SSH 速率限制

当攻击者已有正确密码（密码泄露）时，fail2ban 完全不生效——所有登录都是 `Accepted password`，没有 `Failed password` 可匹配。这种情况下直接用 **iptables `recent` 模块**替代 fail2ban：

```bash
# 添加到 SSH 接受规则之后：
# 对每 60 秒内超过 5 次新 SSH 连接的源 IP 自动 DROP
iptables -A INPUT -p tcp --dport 22 -m state --state NEW \
  -m recent --set --name SSH-LIMIT

iptables -A INPUT -p tcp --dport 22 -m state --state NEW \
  -m recent --update --seconds 60 --hitcount 5 --name SSH-LIMIT \
  -j DROP
```

**工作原理：** `recent --set` 记录每个新连接的源 IP 和时间戳，`recent --update` 检查该 IP 在 60 秒内是否超过 5 次。超过则 DROP，不超则放过。

```bash
# 查看 recent 列表
cat /proc/net/xt_recent/SSH-LIMIT

# 手动清除某个 IP 的限制
echo "<攻击者IP>" > /proc/net/xt_recent/SSH-LIMIT

# 持久化（Alpine OpenRC）
rc-service iptables save     # 保存到 /etc/iptables/rules-save
rc-update add iptables boot  # 开机自启
```

**适用场景对比：**

| 场景 | 方案 | 理由 |
|------|------|------|
| 暴力破解（未知密码） | fail2ban | 匹配 Failed password 正则 |
| 已知密码复用/泄露 | **iptables rate limit** | fail2ban 抓不到 Accepted 日志 |
| 无 iptables 内核模块 | fail2ban | 容器不支持 netfilter |

## fail2ban 进阶

### Debian/Ubuntu
```bash
# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 86400
findtime = 600
maxretry = 3
banaction = iptables-multiport

[sshd]
enabled = true
port = 62839  # 改了端口要对应
filter = sshd
logpath = /var/log/auth.log

[nginx-botsearch]
enabled = true
port = http,https
filter = nginx-botsearch
logpath = /var/log/nginx/access.log
maxretry = 2
```

### Alpine Linux (OpenRC)
```bash
# 安装
apk add fail2ban

# /etc/fail2ban/jail.local
[DEFAULT]
bantime = 86400
findtime = 600
maxretry = 3

[sshd]
enabled = true
port = ssh
logpath = /var/log/messages   # Alpine SSH 日志在这里，不是 /var/log/auth.log
maxretry = 3
bantime = 604800

# 启用开机自启 + 启动
rc-update add fail2ban default
rc-service fail2ban start
```

### 🚫 NAT VPS LXC 陷阱：永远不要在 LXC 内配置 iptables

**NAT VPS 端口映射原理：**
NAT VPS 提供商（无聊云、isvoro 等）在宿主机网关做映射：公网 `IP:48256` → 容器内 `IP:47632`。SSHD 监听的是**内网端口**（47632），公网端口仅由提供商网关处理。

**核心原则：LXC 容器共享宿主机网络命名空间，容器内任何 iptables 操作（包括 `-F`、追加规则、改策略）都可能破坏提供商预设的 NAT 端口转发规则。最佳做法是完全不碰 iptables。**

**✅ LXC 节点的安全方案：只做 SSH 加固，不做防火墙**
```bash
# 禁用密码登录 + 改 root 为仅密钥
sed -i "s/^#\?PermitRootLogin .*/PermitRootLogin prohibit-password/" /etc/ssh/sshd_config
sed -i "s/^#\?PasswordAuthentication .*/PasswordAuthentication no/" /etc/ssh/sshd_config
sed -i "s/^#\?KbdInteractiveAuthentication .*/KbdInteractiveAuthentication no/" /etc/ssh/sshd_config
rc-service sshd restart   # Alpine
# systemctl restart sshd  # Debian
```

**❌ 绝对不要在 LXC 上做的事：**
```bash
# ❌ 致命错误：iptables -F — 清掉提供商预设的过滤规则 → 断连
iptables -F

# ❌ 同样危险：改 iptables 默认策略
iptables -P INPUT DROP

# ❌ 即使只追加规则也不安全：LXC netfilter 可能干扰宿主 conntrack
iptables -A INPUT -p tcp --dport <SSH_PORT> -j ACCEPT
```

**现象（锁死后的典型表现）：**
- Panel 显示在线（出站正常，agent 上报正常）
- 但所有人 SSH 均超时（含从用户的成都网络）
- 出站通信正常，仅入站端口转发中断

**唯一恢复手段：从 VPS 提供商控制面板重装/重置 LXC 容器。**

**例外场景：** 某些 Cloud VM（KVM 而非 LXC）的 iptables 操作安全。区分方法：
- LXC：共享宿主机内核，`cat /proc/1/cgroup | grep -c lxc` 返回 > 0
- KVM：每台独立内核，`ls /dev/ | grep kvm` 存在

### Alpine LXC 无 iptables

某些 Alpine LXC（低版本 / arm64）完全无法用 iptables：

```bash
$ which iptables && iptables -L 2>&1 | head -3
# → Permission denied (need CAP_NET_ADMIN) 或 not found
```

不装 iptables（装了也用不了），只做 SSH 加固：

```bash
sed -i "s/^#\?PermitRootLogin .*/PermitRootLogin prohibit-password/" /etc/ssh/sshd_config
sed -i "s/^#\?PasswordAuthentication .*/PasswordAuthentication no/" /etc/ssh/sshd_config
rc-service sshd restart
```

### ⚠️ Alpine SSH 加固陷阱

| 陷阱 | 现象 | 修复 |
|------|------|------|
| `sshd` 路径 | `/sbin/sshd: not found` | 用 `/usr/sbin/sshd -t` |
| `UsePAM` 选项 | `Unsupported option UsePAM` | Alpine 的 OpenSSH 不支持 PAM，配置里删掉这一行 |
| 服务重启 | `systemctl` 不存在 | 用 `rc-service sshd restart` |
| 日志路径 | `/var/log/auth.log` 不存在 | 日志在 `/var/log/messages` |
| `ps` 参数 | `--sort=-%cpu` 不生效 | Alpine busybox 的 ps 不支持 GNU 参数，用 `ps aux` 手动看 |
| **Alpine LXC 无 iptables** | `iptables: not found` | `apk add iptables iptables-openrc` 安装，然后 `rc-service iptables save; rc-update add iptables boot` 持久化 | | SSH 远程端口转发(-R)静默失败，`ss -tlnp` 看不到转发的端口 | 检查 `/etc/ssh/sshd_config`，把 `AllowTcpForwarding no` 改成 `yes`，重启 sshd。转发成功后 `ss -tlnp \\| grep <port>` 应显示 sshd 进程。 |
| **`PasswordAuthentication no` 不阻止 keyboard-interactive** | 配置了 `PasswordAuthentication no`，攻击者仍然成功用**密码**登录（87次），`/var/log/messages` 显示 `Accepted password ... ssh2` | `PasswordAuthentication no` 仅拦截明文密码协议。Alpine 的 OpenSSH 默认启用 keyboard-interactive 认证，攻击者可以用键盘交互方式提交密码绕过此设置。**必须同时加 `KbdInteractiveAuthentication no`** |
| **fail2ban 对"正确密码登录"无效** | fail2ban 只匹配日志中的 `Failed password` 正则。攻击者已有正确密码时，每次登录都是 `Accepted password`，fail2ban 显示 0 total failed、0 total banned，即使发生了 87 次 SSH 登录 | fail2ban 无法防御凭据复用/密码泄露场景。**根本方案是禁密码 + 禁 keyboard-interactive**，只留 SSH 密钥。

### 配置验证与回退

**修改 sshd_config 后，必须先验证语法再重启，否则可能锁住自己：**

```bash
# 1. 验证配置语法（⚠️ Alpine 上路径是 /usr/sbin/sshd，不是 /sbin/sshd）
/usr/sbin/sshd -t
# 无输出 = 语法正确
# 有报错 = 修正配置（常见：UsePAM 在 Alpine 上不支持，直接删掉这行）

# 2. 重启 sshd
# Debian/Ubuntu: systemctl restart sshd
# Alpine: rc-service sshd restart

# 3. ⚠️ 保持当前 SSH 会话！开新终端测试连接后再关旧会话
# 测试密钥：ssh -i ~/.ssh/key -o PasswordAuthentication=no user@host
# 测试密码应被禁：ssh -o PasswordAuthentication=yes user@host  # → Permission denied (publickey)
```

**回滚（被锁住时）：**
1. 如果还有另一个 SSH 会话（如通过跳板机、管理面板的 VNC/console），回去改回来
2. 如果完全锁死：通过 VPS 管理面板的 rescue mode / VNC 进入，改回 `PasswordAuthentication yes`

### 验证密码已彻底封死（包含 keyboard-interactive）

```bash
# 测试 1：明文密码协议被禁 → 应被拒绝
ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@localhost
# → Permission denied (publickey)

# 测试 2：keyboard-interactive 也被禁 → 应被拒绝
ssh -o PreferredAuthentications=keyboard-interactive -o PubkeyAuthentication=no root@localhost
# → Permission denied (publickey)

# 测试 3：密钥认证正常 → 应能连
ssh -o PreferredAuthentications=publickey root@localhost "echo OK"
# → OK

# 如果测试 2 返回 password prompt 而不是 Permission denied，
# 说明 KbdInteractiveAuthentication no 没生效，攻击者仍能用密码登录
```

## 自动化加固检查脚本
```bash
#!/bin/bash
echo "=== 加固检查 ==="

# SSH 配置
echo "[SSH]"
grep -E "^(PasswordAuthentication|PermitRootLogin|Port)" /etc/ssh/sshd_config

# 防火墙
echo "[Firewall]"
iptables -L INPUT -n --line-numbers | head -20

# fail2ban
echo "[fail2ban]"
fail2ban-client status 2>/dev/null || echo "not installed"

# 开放端口
echo "[Open Ports]"
ss -tlnp | grep LISTEN

# SUID 文件
echo "[SUID binaries]"
find /usr -perm -4000 -type f 2>/dev/null | wc -l

# 自动更新
echo "[Auto Updates]"
cat /etc/apt/apt.conf.d/20auto-upgrades 2>/dev/null || echo "not configured"

# 内核加固
echo "[Sysctl hardening]"
sysctl net.ipv4.tcp_syncookies net.ipv4.conf.all.accept_redirects 2>/dev/null
```

### 挖矿木马检测与清除

#### komari agent OpenRC 服务模板

Alpine 上没有 systemd，用 OpenRC 管理 komari agent 持久化运行：

```bash
# 模板在 templates/komari-agent-init
# 部署示例：
cat > /etc/init.d/komari-agent << 'EOF'
#!/sbin/openrc-run
command=/opt/komari/agent
command_args="-e http://<荷兰_IP>:45774 -t <NODE_TOKEN> --disable-web-ssh"
command_background=true
pidfile=/run/komari-agent.pid
EOF
chmod +x /etc/init.d/komari-agent
rc-update add komari-agent default
rc-service komari-agent start
```

`command_background=true` 是关键——告诉 OpenRC 这个进程需要 fork 到后台运行。另外注意 Alpine OpenRC 不支持 `command_background=true` 的旧版本可能需用 `start-stop-daemon --background`。Alpine 3.22+ 正常支持此选项。

### 典型特征

| 特征 | 说明 |
|------|------|
| CPU 100% 持续燃烧 | `top` 里 `%id` ≈ 0，`%us` > 80% |
| 伪装进程名 | 常用 `systemd`、`kworker`、`[kblockd]`、`cron` 等迷惑名 |
| 隐藏目录 | `/root/.sys-cache/`、`/dev/shm/`、`/tmp/.xxx/` |
| 连接矿池 | `xmr.kryptex.network`、`pool.minexmr.com`、`pool.supportxmr.com` |
| 反竞争脚本 | 附带 `free_proc.sh` 杀其他挖矿进程 |

### 检测步骤

```bash
# 1. 看 CPU
top -bn1 | head -5
# %Cpu(s): 84.6 us, 15.4 sy, 0.0 id → CPU 吃满

# 2. 找可疑进程
ps aux --sort=-%cpu | head -10
# 注意 0.0% CPU 但高 RES 的进程（矿机可能在休眠周期）
# 看 COMMAND 路径：/root/.sys-cache/systemd 这种路径必有问题

# 3. 查连接
ss -tpn | grep -E '443|8029|3333|5555|7777|14444'
# 矿池常见端口：8029(Kryptex)、3333/5555/7777(XMRig 默认)

# 4. 查隐藏目录
find /root /tmp /dev/shm /var/tmp -name '.*' -type d 2>/dev/null | xargs ls -la
# .sys-cache 是常见伪装名

# 5. Alpine 特别提示
# OpenRC 没有 systemctl，用 rc-service 替代
# 没有 /var/log/auth.log — 日志在 /var/log/messages
# busybox ps 参数不同：用 `ps aux` 而不是 `ps aux --sort=-%cpu`
```

### 清除步骤

```bash
# 1. 定位并 kill 矿机进程
ps aux | grep -E 'systemd|kworker|xmrig|minerd' | grep -v grep
kill -9 <PID>

# 2. ⚠️ 保留证据文件，不要先删除！
# 用户可能要用文件做 hash/取证/举报。先 kill 进程保留文件，确认不需要后再删。
# 典型路径：ls -la /root/.sys-cache/
# 安全做法：
#   mv /root/.sys-cache /root/.sys-cache.evidence   # 改名保留
#   或 tar czf /tmp/miner-evidence.tar.gz /root/.sys-cache/  # 打包保存

# 3. 清理反竞争脚本（可能在 cron 或后台跑）
pkill -9 -f free_proc.sh
grep -r 'sys-cache' /etc/ /var/spool/cron/ /root/ 2>/dev/null

# 4. 验证恢复
top -bn1 | head -3
# %Cpu(s): X.X us, X.X sy, XX.X id → idle 回到正常值
free -m
# 内存应释放大量（矿机通常占 RAM 的 30-70%）
ps aux | grep -E 'systemd|xmrig' | grep -v grep
# 无输出 = 清理干净

# 5. 矿池验证（确认矿机离线）
# 去 Kryptex pool 首页搜索钱包地址
# 对应 worker 的 30min 算力应持续下降至 0
# 比单纯 ps 更可靠——确认矿池端已断连
```

### 矿池钱包取证

Kryptex 矿池首页输入钱包地址可查算力、Worker 列表、余额和提现记录。详见 `references/miner-wallet-investigation.md`。

### 矿机行为模式

来自真实案例（荷兰鸡被入侵实录）：

- **入口**：SSH 密码认证（`PermitRootLogin yes` + `PasswordAuthentication yes`），密码泄露/撞库
- **行为**：攻击者从可访问的 IP（如香港 UCloud）频繁登录检查矿机，平均每 15 分钟一次
- **掩体**：`free_proc.sh` — 每 2 秒杀一遍 >200% CPU 的非 systemd 进程，防止其他矿工竞争
- **文件名**：伪装成 `systemd`，放在 `/root/.sys-cache/`
- **矿池**：`xmr.kryptex.network:8029` — Kryptex 算力平台，支持 TLS 连接
- **攻击者 IP**：`<攻击者IP>`（UCloud HK），84 次登录，持续 20 小时
- **日志**：Alpine 上已登录 SSH 记录在 `/var/log/messages`，格式 `Accepted password for root from <IP> port <PORT> ssh2`

### UPX 加壳分析

见 `references/upx-malware-analysis.md` — 完整工作流：检测 UPX → 解包 → 版本/编译器/构建路径指纹提取 → 钱包地址提取。

### 矿机进程命名诡计

攻击者用 `systemp`（不是 `systemd`）作 worker 名，在 `ps aux` 输出中混在系统进程行里：

```
root       290  0.0  0.0   1640   572  ?  S  May12  0:01 /sbin/syslogd
root      1029  0.0 54.6 312116 273124 ?  Sl 14:13 57:53 systemd          ← 矿机
root       318  0.0  0.1   1628   572  ?  Ss May12  0:02 /usr/sbin/crond
```

不仔细看 `systemd` 那行的 RES 273MB 根本看不出问题。`systemp` 是 `system` + `p` 的拼接，人类扫读时自动忽略。

### 矿机版本差异

| 来源 | 版本 | 说明 |
|------|------|------|
| 矿池 Worker 详情 | XMRig/6.25.0 | 矿池读取的 User-Agent |
| strings 解包二进制 | XMRig 6.26.0 | 二进制内嵌的版本字符串 |
| 编译时间 | `built on Mar 28 2026 with GCC` | 约 1.5 个月前 |

版本差异可能是因为矿池读到的是编译时的 `XMRig/6.25.0` 标识，而二进制内嵌的是 `6.26.0` 的完整版本号——说明攻击者可能在官方 6.26.0 代码上手动改版本标识后编译。

### 构建流水线推断

- 编译路径：`/home/buildbot/xmrig/scripts/build/hwloc-2.12.1/`
- 编译环境：Alpine Linux（musl libc），GCC 13.2.1
- 用户名 `buildbot` 表明存在**自动化编译流水线**
- 静态链接 + UPX 加壳 → 单一可分发文件，任何 Linux x86_64 上都能跑
- Build ID：`c746d5445679e29ea09a8ae5bdc7fbbbf3720c44`（唯一标识）

三个指纹可全网搜索关联其他受害者：UPX版 SHA256、解包版 SHA256、Build ID。

## 入侵事件响应

### 确认入侵

```bash
# 1. 检查所有 SSH 登录记录
cat /var/log/messages | grep 'Accepted password' | sed 's/.*from //' | sed 's/ port.*//' | sort | uniq -c | sort -rn
# 注意非自己 IP 的记录（有 `Accepted password` 但没有 `Failed password` 的攻击说明是密码泄露而非暴力破解）
# ⚠️ fail2ban 统计的是 Failed password，如果日志只有 Accepted password 那 fail2ban 的 0 total banned 是正常现象，不要误以为「没人进来过」
# 真实案例：87次 Accepted password + 0次 Failed password → fail2ban 显示 0 total banned

# 2. 检查 authorized_keys
cat /root/.ssh/authorized_keys
ls -la /root/.ssh/

# 3. 检查已有服务是否被篡改
find /usr/bin /usr/sbin /opt /root -mmin -1440 -type f 2>/dev/null | grep -v -E 'cache|npm|node_modules|\\.git'
# 最近 24h 改动的文件

# 4. 检查 crontab
crontab -l
cat /etc/crontabs/* 2>/dev/null
ls /etc/periodic/*/
```

### 入侵溯源取证（攻击者机器侦察）

确认入侵后，对攻击者 IP 做侦察，收集举报证据：

```bash
# 1. 端口扫描（从本机 nmap，不要从被黑机子扫，避免反打）
nmap -sT -sV -p 22,80,443,8080 <攻击者IP>

# 2. 版本扫描关键信息
#   - SSH 版本 + 指纹（举报关键证据）
#   - Web 服务类型（Caddy/Nginx/Apache）
#   - OS 类型

# 3. Web 服务探活（确认是否为 C2 面板）
curl -v http://<攻击者IP>/
# 注意 Server 头、返回内容、各路径是否都有 200 空响应（Caddy 特征）

# 4. 攻击者 IP 信息收集
#   - whois 归属（APNIC/ARIN RDAP）
#   - ASN + 运营商
#   - geolocation
#   - AbuseIPDB 历史记录
#   - 联系邮箱（abuse contact）

# 5. 整理时间线
#   - 首次登录时间
#   - 总登录次数
#   - 攻击行为模式（间隔、并发会话数）
```

⚠️ **关键安全原则**：永远不要从被黑机子扫攻击者。攻击者可能在你机子上留了反制/log 脚本。用第三方堡垒机/本机扫。本 session 是从 CCS LA2（<运维本机_IP>）经由 sshpass 上主控扫的。

### 举报证据整理

**原则：不要只说"你举报吧"——直接把证据打包好给用户。**

举报邮件应包含：

```
1. 受害服务器信息：IP、OS、入口漏洞
2. 攻击者 IP + ASN + 地域
3. 时间线：首次入侵 → 最后活动
4. 恶意软件详情：路径、矿池地址、钱包地址、反竞争脚本
5. SSH 指纹（锁定攻击者机器的 DNA）
6. 端口扫描结果（攻击者机器开放的服务）
7. 日志片段（登录记录、进程列表）
```

举报联系方式查询：
```bash
# APNIC RDAP 查 abuse contact
curl -s 'https://rdap.apnic.net/ip/<IP>' | python3 -c 'import json,sys;d=json.load(sys.stdin);[print(json.dumps(e,indent=2)) for e in d.get("entities",[]) if "abuse" in e.get("roles",[])]'

# 常见的 abuse 邮箱模式
# UCloud: pn-wan@ucloud.cn / hegui@ucloud.cn
# 阿里云: ipas@cn.alibaba.com
# 腾讯云: abuse@tencent.com
# 一般: abuse@<运营商域名>
```

### 应急处置

1. **立即**：kill 可疑进程 → 删除隐藏文件 → pkill 后门脚本
2. **封锁入口**：`PasswordAuthentication no` + `PermitRootLogin prohibit-password` → `rc-service sshd restart`（保留当前 SSH 会话！）
3. **改密码**：如果实在要留密码登录，换强密码
4. **配置 SSH 密钥**：生成密钥对，上传公钥，禁用密码
5. **检查持久化**：cron、local.d、init.d 是否有自动重启机制

### 恢复后验证

```bash
# CPU 空闲恢复
top -bn1 | head -3
# 对比：清理前 idle≈0%，清理后 idle>60%

# 内存释放
free -m
# 对比：清理前 used>300MB，清理后 used<80MB

# 确认无残留进程
ps aux | grep -E 'systemd|kworker|xmrig|minerd|sys-cache' | grep -v grep

# 确认关键服务仍运行
rc-service komari status 2>/dev/null || systemctl is-active komari
rc-service sshd status
```

### IPv6-Only 节点管理

对于仅有 IPv6 地址的节点（如某些 LXC 容器），管理机可能无法直连。需要一个双栈（IPv4+IPv6）的兄弟节点作为 SSH 跳板。详见 `references/ipv6-jumpbox.md`。

关键流程：跳板机装 sshpass → 跳板机生成/持有管理密钥 → 经跳板机 SSH 到目标机 → 同样流程加固。

## 批量加固多个服务器（矿机事件恢复后的标准流程）

当一台服务器被入侵后，**检查并加固所有同网络/同厂商的服务器**。攻击者扫到了一个密码，很可能扫到了更多。**哪怕其他机子没中招也要加固**，因为攻击者可能已经知道了它们的密码。

### 检测 → 修复 → 扫描 → 加固 → 文档

```text
Step 0: 确认入侵源（日志审计）
Step 1: 清理被黑机（kill 进程，保留证据）
Step 2: 封锁入口（SSH 加固 + IP 封禁）
Step 3: 列出所有同网络/同厂商的服务器清单
Step 4: 逐个测试 SSH 连通性（确认端口、用户名、密码）
Step 5: 检查是否已中招（ps / top / 可疑目录）
Step 6: 生成统一 SSH 密钥对（如 ~/.ssh/hermes_admin）
Step 7: 每台上传公钥
Step 8: 每台测试密钥登录
Step 9: 每台禁用密码登录 + 重启 sshd
Step 10: 每台验证密码已关 + 密钥仍通
Step 11: 文档化（服务器清单、端口、密钥指纹）
```

**流程：**

```
Step 1: 列出所有同网络/同厂商的服务器清单
Step 2: 逐个测试 SSH 连通性（确认端口、用户名、密码）
Step 3: 检查是否已中招（ps / top / 可疑目录）
Step 4: 生成统一 SSH 密钥对（如 ~/.ssh/hermes_admin）
Step 5: 每台上传公钥
Step 6: 每台测试密钥登录
Step 7: 每台禁用密码登录 + 重启 sshd
Step 8: 每台验证密码已关 + 密钥仍通
```

**真实案例数据（5 台 Alpine LXC 同时加固）：**

| 服务器 | IP | 端口 | SSH 加固 | 防火墙 |
|--------|-----|------|---------|--------|
| 主控 荷兰 | <荷兰_IP> | 46748 | ✅ | ✅ iptables + recent限速 |
| 56idc 洛杉矶 | <洛杉矶2_IP> | 42185 | ✅ | ✅ iptables（需`apk add iptables iptables-openrc`安装） |
| GCP 台湾 | <台湾_IP> | 43590 | ✅ | - |
| isvoro 首尔 | <首尔_IP> | 10260 | ✅ | - |
| isvoro 新加坡 | <新加坡_IP> | 10425 | ✅ | - |

**性能影响：** 修正后 CPU 从 91.7% us 降至 0-10%，内存从 45MB 空闲恢复至 312MB 空闲。

**坑：**
- 每台机器的 SSH 端口可能不同（NAT 转发、非标端口）
- 密码中的特殊字符（`$`、`%`、`!`）在 shell 中需引号保护
- Alpine 上 sshd 重启用 `rc-service sshd restart`，不是 `systemctl`
- 改配置后用 `/usr/sbin/sshd -t` 先验证语法（不是 `/sbin/sshd`）
- 删除 `UsePAM no`（Alpine OpenSSH 不支持这个选项）
- 保持当前 SSH 会话！开新终端测试连接后再关旧会话

## 加固优先级（按高风险→低风险）

1. 🔴 **SSH 密钥认证 + 禁用密码** — 防止密码泄露/撞库
2. 🔴 **防火墙默认 DROP + 只开必要端口**
3. 🟡 **fail2ban** 防暴力破解
4. 🟡 内核参数调优
5. 🟢 审计日志
6. 🟢 文件系统权限审查
7. 🟢 自动安全更新
