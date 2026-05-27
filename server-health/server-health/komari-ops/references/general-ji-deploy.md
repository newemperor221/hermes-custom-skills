# 将军鸡 IPv6-only 小鸡接入 Komari

**日期**: 2026-05-07  
**节点**: 将军鸡（欢乐云 NAT 小鸡）  
**系统**: Alpine 3.22 LXC, 1C128M, HE IPv6 隧道  
**结果**: 成功接入，12/12

## 背景

- 将军鸡是 NAT 小鸡，只有 HE 隧道 IPv6（`2001:470:e2db:100::/64`），无原生 IPv4/IPv6
- 56idc-la 有 komari server（`stat.357561.xyz`），将军鸡无法直接用 IPv4 连接
- 两台机器都有 HE IPv6，但 HE endpoint 地址（`2001:470:e2db::2`）不能直接用于 agent 连接

## 连接方案演变

### 方案 A（失败）：HE IPv6 endpoint 直连
```bash
# 在将军鸡上测试
nc -6 -zv 2001:470:e2db::2 25774
# 结果：Failed to connect - HE endpoint 不是可路由地址
```
**原因**：HE 隧道 endpoint 地址不是机器的可路由 IPv6，komari server 监听的 `:::25774` 含 HE 网卡，但 agent 直接连 endpoint 会失败。

### 方案 B（成功）：公网 HTTPS 域名连接
将军鸡 agent 连接 `https://stat.357561.xyz`（cloudflared 隧道暴露的 komari 服务），不依赖直接 IPv4/IPv6 互通。

## 操作步骤

### 1. 在将军鸡上下载并安装 agent
```bash
mkdir -p /opt/komari
wget https://github.com/komari-monitor/komari/releases/download/1.1.9/komari-linux-amd64 -O /opt/komari/agent
chmod +x /opt/komari/agent
```

### 2. 在 56idc-la（komari server）上生成 token 并写入数据库
```bash
ssh -p 52137 -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no root@107.172.231.70 \
  "sqlite3 /opt/komari/data/komari.db \"INSERT INTO clients (uuid, token, name, os, created_at, updated_at) VALUES (lower(hex(randomblob(16))), '207c22bb50597a5b27e72e57c66f3cd9', '将军鸡', 'Alpine Linux', datetime('now'), datetime('now'));\""
```

### 3. 在将军鸡上创建 OpenRC init 脚本
```bash
cat > /etc/init.d/komari-agent << 'EOF'
#!/sbin/openrc-run
name=komari-agent
description="Komari Agent"
command="/opt/komari/agent"
command_args="-e https://stat.357561.xyz -t 207c22bb50597a5b27e72e57c66f3cd9"
command_background=true
pidfile="/run/${RC_SVCNAME}.pid"
output_log="/var/log/komari-agent.log"
error_log="/var/log/komari-agent.err"
supervisor=supervise-daemon
respawn_delay=2
respawn_max=5
respawn_period=180
EOF
chmod +x /etc/init.d/komari-agent
rc-service komari-agent start
rc-update add komari-agent default
```

### 4. 验证
等待 10 秒，刷新 stat.357561.xyz，检查将军鸡是否出现且数据非零。

## 教训

1. **HE endpoint IPv6 不能直接用于连接**：komari server 监听 `:::25774`，但 agent 连 `http://[2001:470:e2db::2]:25774` 失败。正确做法是用公网域名。
2. **每台机器的 init 脚本名必须唯一或确保目标 IP 正确**：本次将军鸡和 56idc-la 都用了 `/etc/init.d/komari-agent`，操作时容易搞混覆盖。
3. **IPv6 连通性测试用 `nc -6 -zv`**：不用 `-6` 会把 IPv6 地址当域名解析。

## 将军鸡 SSH 信息（欢乐云）

- 欢乐云官网: xuei.de
- 节点: 将军鸡（朝鲜）
- IPv6: `2001:470:e2db:100::/64`（HE 隧道）
- SSH: 需要从欢乐云后台查看端口映射
