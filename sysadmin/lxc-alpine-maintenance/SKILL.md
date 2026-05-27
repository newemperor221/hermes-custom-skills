---
name: lxc-alpine-maintenance
description: Alpine LXC 容器（低配 488M/1G）定期维护—WAL checkpoint、清理/tmp和旧日志、logrotate 配置。适用于 无聊云 等极小规格 LXC。
tags: [alpine, lxc, maintenance, komari, cleanup]
---

# Alpine LXC 容器维护

## 适用场景
- Alpine Linux LXC 容器，磁盘 ~1GB，内存 ~500MB
- 运行 komari 面板 + SQLite
- 限制日志大小防止磁盘写满

## 维护操作

### 1. SQLite WAL 压缩

SQLite 的 WAL（Write-Ahead Log）文件会持续增长，与数据库文件几乎等大。安全在线压缩：

```bash
# 在线 checkpoint（不影响运行中的 komari）
sqlite3 /opt/komari/data/komari.db "PRAGMA wal_checkpoint(TRUNCATE);"
```

`0|0|0` = 完全 checkpoint 成功，WAL 文件清空。

### 2. 清理迁移残留

搬家后 `/tmp/` 常留旧二进制和压缩包：

```bash
# 旧 komari/agent 二进制（~40MB）
rm -f /tmp/agent
# 迁移备份包（~17MB）
rm -f /tmp/komari-migrate.tar.gz /tmp/ip-sentinel-migrate.tar.gz
```

### 3. 系统日志清理

Alpine 默认日志很小，但 cloudflared 写 `/var/log/cloudflared*.log`：

```bash
# logrotate 配置 /etc/logrotate.d/cloudflared
/var/log/cloudflared*.log {
    weekly
    rotate 4
    compress
    missingok
    notifempty
}
```

### 4. 每周维护脚本

路径：`/etc/periodic/weekly/komari-maintenance`
Alpine crond 自动每周执行（周期：`0 3 * * 6`）：

```bash
#!/bin/sh
# WAL checkpoint
sqlite3 /opt/komari/data/komari.db "PRAGMA wal_checkpoint(TRUNCATE);" 2>/dev/null
# 清理 7 天前的临时文件
find /tmp -type f -atime +7 -delete 2>/dev/null
# 清理 30 天前的旧日志
find /var/log -name "*.log.*" -mtime +30 -delete 2>/dev/null
```

## Komari Agent on Alpine LXC

所有 4 台 Alpine LXC（新加坡/荷兰/无聊云洛杉矶/首尔）运行 **Rust komari agent**（1.2MB），**不是 Go agent**（11MB）。

### 安装命令（按架构选）

```bash
# ARM64 (Alpine aarch64-musl) — 新加坡、首尔
wget -O /opt/komari/agent https://github.com/GenshinMinecraft/komari-monitor-rs/releases/download/latest/komari-monitor-rs-linux-aarch64-musl

# x86_64 (Alpine amd64-musl) — 荷兰、无聊云洛杉矶
wget -O /opt/komari/agent https://github.com/GenshinMinecraft/komari-monitor-rs/releases/download/latest/komari-monitor-rs-linux-x86_64-musl

chmod +x /opt/komari/agent
```

### 启动命令

```bash
# Rust agent 用 --http-server + --tls，不是旧 Go agent 的 -e/--endpoint
nohup /opt/komari/agent \
  --http-server https://<监控面板域名> \
  --tls \
  -t <TOKEN> \
  --disable-network-statistics \
  > /tmp/komari-agent.log 2>&1 &

# 验证：日志出现 "Successfully pushed Basic Info" = 上报成功
```

### 开机自启（OpenRC local.d）

Alpine LXC 没有 systemd，用 `/etc/local.d/` 实现开机自启：

```bash
cat > /etc/local.d/komari-agent.start << 'EOF'
#!/bin/sh
/opt/komari/agent \
  --http-server https://<监控面板域名> \
  --tls \
  -t <TOKEN> \
  --disable-network-statistics \
  > /tmp/komari-agent.log 2>&1 &
EOF
chmod +x /etc/local.d/komari-agent.start
rc-update add local default
```

### 从 Go agent 切换到 Rust agent

```bash
# 1. 停旧 agent
rc-service komari-agent stop 2>/dev/null
kill $(pgrep -f "/opt/komari/agent -e") 2>/dev/null
sleep 2

# 2. 备份旧 Go agent，放 Rust agent 到相同路径
mv /opt/komari/agent /opt/komari/agent-go.bak
# 然后下载 Rust agent 到 /opt/komari/agent（见上方安装命令）

# 3. 启动新 agent
nohup /opt/komari/agent --http-server https://<监控面板域名> --tls -t <TOKEN> --disable-network-statistics > /tmp/komari-agent.log 2>&1 &

# 4. 验证
tail -f /tmp/komari-agent.log
# → "Successfully pushed Basic Info" = OK
```

### ⚠️ 不能在 LXC 里配 iptables

LXC 容器共享宿主机网络命名空间。`iptables -F` 会清掉提供商预设的 NAT 端口转发规则，导致**所有入站连接断掉**（SSH、面板访问全挂），出站和 agent 上报仍正常。唯一恢复手段：到 VPS 提供商面板**重装容器**。

正确的 LXC 安全方案：只做 SSH 加固，不做防火墙：
```bash
sed -i "s/^#\?PermitRootLogin .*/PermitRootLogin prohibit-password/" /etc/ssh/sshd_config
sed -i "s/^#\?PasswordAuthentication .*/PasswordAuthentication no/" /etc/ssh/sshd_config
rc-service sshd restart
```

### 架构对应关系

| 节点 | IP | SSH端口 | 架构 | Agent 版本 |
|:-----|:--:|:-------:|:----:|:----------:|
| 新加坡 isvoro | <新加坡_IP> | 10425 | aarch64-musl | Rust ✅ |
| 荷兰 无聊云 | <荷兰_IP> | 46748 | x86_64-musl | Rust ✅ |
| 无聊云洛杉矶 | <洛杉矶2_IP> | 42185 | x86_64-musl | Rust ✅ |
| 首尔 isvoro | <首尔_IP> | 10260 | aarch64-musl | Rust ✅ |

## 磁盘布局参考

```
~1GB 总空间
├── /opt/komari/komari     (41M — server binary)
├── /opt/komari/agent      (11M — agent binary)
├── /opt/komari/data/       (~12M — DB + WAL + theme)
│   ├── komari.db           (~6M)
│   ├── komari.db-wal       (~6M — 可压缩)
│   └── komari.db-shm
├── /var/log/               (微小)
└── /tmp/                   (日常 ~0，迁移后需清理)
```
