# Komari Server 重启 + Cloudflared 隧道恢复

> 2026-05-10 实测教训

## 背景

**关键依赖关系（2026-05-10 才发现）**：`pkill komari`（或 `killall komari`）会**连带杀掉 cloudflared**。因为 cloudflared 也是 nohup 启动，与 komari server 共享进程树。重启 komari server 后，所有 agent 连不上 `stat.357561.xyz`，返回 **HTTP 530 / error 1033**。

## 完整重启步骤

### 第1步：停 komari server
```bash
pkill -9 komari
sleep 2
```

### 第2步：确认 cloudflared 也死了
```bash
ps aux | grep cloudflared | grep -v grep
# 输出为空 = 被连带杀掉了
```

### 第3步：启动 komari server
```bash
nohup /opt/komari/komari server -l :25774 -d /opt/komari/data/komari.db > /var/log/komari.log 2>&1 &
```

### 第4步：检查 cloudflared init 脚本是否存在
```bash
ls /etc/init.d/cloudflared 2>/dev/null || echo 'MISSING'
```

**⚠️ 已知问题**：重启 komari server 时，`/etc/init.d/cloudflared` 可能被自动删除（v1.2.0 内置 cloudflared 管理冲突？）。需要重建。

### 第5步：重建 cloudflared init 脚本（如果缺失）
```bash
cat > /etc/init.d/cloudflared << 'CFEOF'
#!/sbin/openrc-run
name=cloudflared
command="/usr/local/bin/cloudflared"
command_args="tunnel run --token <TOKEN>"
command_background=true
pidfile="/run/cloudflared.pid"
output_log="/var/log/cloudflared.log"
error_log="/var/log/cloudflared.err"
depend() { need net; }
CFEOF
chmod +x /etc/init.d/cloudflared
```

**Token 来源**：`sqlite3 /opt/komari/data/komari.db "SELECT value FROM configs WHERE key='cloudflare_tunnel_token';"` 或旧文档备份。

### 第6步：启动 cloudflared
```bash
rc-service cloudflared start
```

### 第7步：验证隧道
```bash
tail -5 /var/log/cloudflared.err
# 应看到 4 条 "Registered tunnel connection"（connIndex 0-3）
```

### 第8步：等待 agent 回连
```bash
sleep 15
grep 'reconnect success' /var/log/komari.log | tail -5
# 应看到所有节点的 reconnect 记录
```

## 诊断

| 症状 | 原因 | 处理 |
|------|------|------|
| agent 日志: "530 / error 1033" | cloudflared 隧道挂了 | 重启 cloudflared |
| agent 日志: "401" | token 不匹配 | 检查 DB token vs agent service 参数 |
| agent 日志: "reconnect success" 但无数据 | 刚重连，等 15-30 秒 | 等 |
| `curl localhost:25774` 通但 `stat.357561.xyz` 不通 | tunnel 问题 | 检查 cloudflared 进程和日志 |
