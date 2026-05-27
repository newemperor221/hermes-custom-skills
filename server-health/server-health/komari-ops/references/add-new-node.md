# 添加新节点到 Komari（新节点不在 DB 中时）
# 添加新节点到 Komari（2026-05-08 更新）

## 两种场景

| 场景 | 方法 |
|------|------|
| 节点已在 DB 中 | 拿 token → 直接装 agent |
| 节点不在 DB 中 | **先插 DB 生成 token → 再装 agent** |

## 完整流程

### 1. 登新节点检查环境

```bash
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no -p PORT USER@IP
ps aux | grep komari   # 检查是否已装
```

### 2. 生成 token

```python
python3 -c "import secrets; print(secrets.token_hex(16))"
```

### 3. 查 Komari server 的 clients 表结构

```bash
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> \
  "sqlite3 /opt/komari/data/komari.db '.schema clients'"
```

### 4. 插入节点到 DB

```bash
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> \
  "sqlite3 /opt/komari/data/komari.db \"
  INSERT INTO clients (uuid, name, token, os, created_at, updated_at) VALUES
  ('<uuid>', '<节点名>', '<token>', 'Linux', datetime('now'), datetime('now'));
  \""
```

### 5. 装 agent

**Debian**：
```bash
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no -p PORT USER@IP \
  "wget -qO- https://raw.githubusercontent.com/komari-monitor/komari-agent/refs/heads/main/install.sh | sh -s -- -e https://stat.357561.xyz -t <TOKEN>"
```

**Alpine**（sh 而非 bash）：
```bash
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no -p PORT USER@IP \
  "curl -fsSL https://raw.githubusercontent.com/komari-monitor/komari-agent/refs/heads/main/install.sh | sh -s -- -e https://stat.357561.xyz -t <TOKEN>"
```

**⚠️ Debian systemd 安装后检查 ExecStart**：
```bash
grep ExecStart /etc/systemd/system/komari-agent.service
# 应该有：ExecStart=/opt/komari/agent -e https://stat.357561.xyz -t <TOKEN>
# 修复：
sed -i 's|ExecStart=/opt/komari/agent $|ExecStart=/opt/komari/agent -e https://stat.357561.xyz -t <TOKEN>|' \
  /etc/systemd/system/komari-agent.service
systemctl daemon-reload && systemctl restart komari-agent
```

### 6. 验证

```bash
# 服务器日志
tail -20 /var/log/komari.log | grep <token>
# 期望：200 POST /api/clients/uploadBasicInfo

# DB 确认
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> \
  "sqlite3 /opt/komari/data/komari.db \"select name, ipv4, ipv6, region from clients;\""
```

## 坑

- **clients.uuid 不能重复** — 用简写如 `acc-k-hk-45`
- **字段名因版本而异** — 必须先 `.schema clients` 确认
- **install.sh 用 bash vs sh** — Debian 用 bash，Alpine 用 sh
- **ExecStart 缺少参数** — Debian systemd 安装后必须检查
- **⚠️ agent 连 stat.357561.xyz 而非 IP** — Cloudflare CDN 不认原始 IP，必须用域名
- **token 用 `secrets.token_hex(16)`** — 保证 32 字符 hex，Komari server 验证 token 长度
