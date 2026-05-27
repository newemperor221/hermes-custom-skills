# 批量添加 11 台服务器到 Komari（2026-05-07）

## 本次部署结果

**成功率：10/11**

| 节点 | IP | 系统 | Agent 状态 |
|------|-----|------|------------|
| racknerd-atlanta | 23.95.218.144:53621 | Debian? | ✅ ON |
| ccs-la2 | 198.46.147.71:43827 | Debian? | ✅ ON |
| dedirock-la | 155.94.180.55:58193 | Debian? | ✅ ON |
| acck-tokyo | 156.231.141.232:47283 | Debian? | ✅ ON |
| acck-hk | 45.192.192.210:47632 | Debian? | ✅ ON |
| akile-tokyo | 154.83.94.183:62174 | Debian? | ✅ ON |
| racknerd-ny | 172.245.159.219:27391 | Debian? | ✅ ON |
| ccs-la1 | 23.95.201.153:47283 | Debian? | ✅ ON |
| hostvds-ks | 45.39.12.227:63841 | Debian? | ✅ ON |
| yecaoyun-hk | 38.55.198.243:62839 | Debian? | ✅ ON |
| 56idc-la | 107.172.231.70:52137 | Alpine 3.22 | ❌ PANIC |

## 关键流程

### 1. 一次性生成全部 token + SQL

```python
python3 << 'PYEOF'
import secrets
servers = [
    ('racknerd-atlanta', '23.95.218.144', 53621, 'woioeow', '4561834'),
    ('ccs-la2', '198.46.147.71', 43827, 'woioeow', '4561834'),
    # ... 全部 11 台
]
for name, ip, port, user, pwd in servers:
    token = secrets.token_hex(16)
    print(f"INSERT INTO clients (uuid, name, token, ipv4, created_at, updated_at) "
          f"VALUES ('{name}', '{name}', '{token}', '{ip}', datetime('now'), datetime('now'));")
PYEOF
```

### 2. 批量插入数据库

```bash
# 清理旧数据（如果需要）
ssh -p 52137 -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no root@107.172.231.70 \
  "sqlite3 /opt/komari/data/komari.db 'DELETE FROM clients;'"
# 然后执行所有 INSERT
```

### 3. 并行安装 agent（max 3 台/批）

```bash
# delegate_task 每次最多 3 个任务
# 非 root 用户用 sshpass，root 用户用 SSH key
```

## install.sh 的 bug

**症状**：安装完成后 `journalctl -u komari-agent` 看到：
```
Failed to connect to WebSocket: malformed ws or wss URL
Error uploading basic info: Post "/api/clients/uploadBasicInfo?token=": unsupported protocol scheme ""
```

**原因**：`/etc/systemd/system/komari-agent.service` 的 `ExecStart` 行是：
```ini
ExecStart=/opt/komari/agent
```
缺少 `-e http://...` 和 `-t TOKEN` 参数。

**修复**：
```bash
sed -i 's|ExecStart=/opt/komari/agent |ExecStart=/opt/komari/agent -e http://107.172.231.70:25774 -t TOKEN|' \
  /etc/systemd/system/komari-agent.service
systemctl daemon-reload && systemctl restart komari-agent
```

## 56idc-la 最终修复

**根因**：agent 配置文件里 `-e http://107.172.231.70:47926` 指向了旧端口（47926 无 komari），导致反复重连触发 komari server panic。

**修复**：
```bash
# 修改 agent endpoint
sed -i 's|http://107.172.231.70:47926|http://127.0.0.1:25774|' /etc/init.d/komari-agent
rc-service komari-agent restart
```

**结果**：BasicInfo 上传 200 OK，56idc-la 在线，CPU/内存/磁盘数据正常。

## 在线时间不正确的坑

56idc-la 今天重装 Alpine，但面板显示在线 43 天。**原因**：komari.db 从旧系统迁移带入旧 boot_time。**修复**：删除旧记录让 agent 重新注册（见 alpine-komari-deploy.md）。

## 最终 token 映射（Alpine komari:25774）

| 节点 | IP | SSH 端口 | Token | 状态 |
|------|-----|---------|-------|------|
| racknerd-atlanta | 23.95.218.144 | 53621 | 2b394ac2d09e90fd65fdbf0a5dd9f8a8 | ON |
| ccs-la2 | 198.46.147.71 | 43827 | e686925a5fa1e68cb006e9e99e0c1368 | ON |
| dedirock-la | 155.94.180.55 | 58193 | aa7bc0fa301777b60c30caba611e7e09 | ON |
| acck-tokyo | 156.231.141.232 | 47283 | a1150a6df7df87c7f1f7452a79756d41 | ON |
| acck-hk | 45.192.192.210 | 47632 | 59de8480178809d986b6a29f0dcfcca8 | ON |
| akile-tokyo | 154.83.94.183 | 62174 | 32d87cec990bd8dac8f3c3e7d3f6ad31 | ON |
| racknerd-ny | 172.245.159.219 | 27391 | 5917ccd325721122fdc035345e9c3b50 | ON |
| ccs-la1 | 23.95.201.153 | 47283 | 03c911f33e3c335a36e9a0954151152b | ON |
| hostvds-ks | 45.39.12.227 | 63841 | a5f9700b6317b6fada7a9454dfdcd259 | ON |
| yecaoyun-hk | 38.55.198.243 | 62839 | ecc25edf63b43da62d9525b56020afff | ON |
| 56idc-la | 107.172.231.70 | 52137 | c0b500332a549571a0e4983f6b20b8b0 | ✅ ON（Alpine，重装后 agent 连 127.0.0.1:25774） |
