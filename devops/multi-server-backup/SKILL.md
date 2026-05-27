---
name: multi-server-backup
description: 多 VPS 自动化备份方案 — rsync 异地同步、Borg 增量加密备份、cron 定时任务、恢复验证流程。覆盖配置/数据/数据库备份。触发："备份"、"backup"、"数据备份"、"rsync 备份"、"Borg 备份"、"异地备份"。
---

# 多 VPS 自动化备份方案

## 适用场景

- 多台 VPS（香港/东京/LA）的配置和关键数据备份
- sing-box、nginx、komari 数据库等配置文件跨机备份
- 每日自动增量加密备份
- 备份空间/cron/压缩比检查
- 灾难恢复流程

## 方案选择

| 方案 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **rsync** | 简单文件同步 | 速度快、全量/增量 | 无加密、无版本历史 |
| **Borg** | 长期增量加密备份 | 去重、压缩、加密、版本化 | 学习曲线略高 |
| **Restic** | 云存储备份 | 支持 S3/R2/本地 | 配置稍多 |

推荐组合：**rsync 做日常配置同步 + Borg 做定期全量加密备份**

## 方案一：rsync 跨机同步（配置备份）

### 前提

各 VPS 之间配好 SSH 密钥认证：

```bash
# 在备份机（如 LA）生成密钥
ssh-keygen -t ed25519 -f ~/.ssh/backup_key -N ""

# 将公钥追加到被备份机的 authorized_keys
ssh-copy-id -i ~/.ssh/backup_key root@<target-ip> -p <ssh-port>
```

### 备份脚本

保存为 `~/scripts/rsync-backup.sh`：

```bash
#!/bin/sh
DATE=$(date +%Y%m%d)
BACKUP_DIR="/backup"
SSH_KEY="$HOME/.ssh/backup_key"
SSH_PORT=48256

# VPS 列表: "标签 IP:端口 远程路径"
VPS_LIST="
hk    38.55.198.243   /etc/sing-box /etc/nginx /root/.hermes
tokyo 156.231.141.232 /etc/sing-box /etc/nginx /root/.hermes
la    23.95.201.153   /etc/sing-box /etc/nginx /root/.hermes
"

echo "=== rsync 备份 $(date) ==="

echo "$VPS_LIST" | grep -v '^$' | while read label ip paths; do
  for remote_path in $paths; do
    dest="$BACKUP_DIR/$label/$remote_path"
    mkdir -p "$dest"
    rsync -avz --delete -e "ssh -p $SSH_PORT -i $SSH_KEY -o StrictHostKeyChecking=no" \
      "root@$ip:$remote_path/" "$dest/" 2>/dev/null
    echo "  ✓ $label:$remote_path → $dest"
  done
done

echo "=== 完成 ==="
```

### 设置 cron

```bash
# 每天凌晨 3 点执行
crontab -e
# 添加：
0 3 * * * /root/scripts/rsync-backup.sh >> /var/log/backup.log 2>&1
```

## 方案二：Borg 增量加密备份

### 安装

```bash
# Debian/Ubuntu
sudo apt install borgbackup

# Alpine
sudo apk add borgbackup

# Python 安装
pip install borgbackup
```

### 初始化存储库

```bash
# 创建备份存储库（放在有空间的机器或挂载点）
mkdir -p /backup/borg
borg init --encryption=repokey /backup/borg
# 输入两次密码（务必记住！）

# 或使用无加密（不推荐，除非在信任网络）
borg init --encryption=none /backup/borg
```

### 备份脚本

保存为 `~/scripts/borg-backup.sh`：

```bash
#!/bin/sh
export BORG_REPO="/backup/borg"
export BORG_PASSPHRASE="your-strong-password-here"  # 或从文件读取
export BORG_RSH="ssh -p 48256 -i $HOME/.ssh/backup_key"

DATE=$(date +%Y%m%d_%H%M)

echo "=== Borg 备份 $DATE ==="

# 创建新备份（去重 + 压缩）
borg create --verbose --stats --progress \
  --compression lz4 \
  ::"{hostname}-$DATE" \
  /etc/sing-box \
  /etc/nginx \
  /root/.hermes \
  --exclude '/root/.hermes/cache' \
  --exclude '*.log'

# 清理旧备份：保留最近 7 天每日、最近 4 周每周、最近 6 月每月
borg prune --verbose --list \
  --keep-daily 7 \
  --keep-weekly 4 \
  --keep-monthly 6

echo "=== 完成 ==="
```

### 查看备份

```bash
# 列出所有备份
borg list /backup/borg

# 查看某个备份内容
borg list /backup/borg::hostname-20240101_0300

# 查看存储库信息
borg info /backup/borg
```

### 恢复

```bash
# 列出可恢复的备份
borg list /backup/borg

# 恢复整个备份到目录
borg extract /backup/borg::hostname-20240101_0300

# 恢复特定文件
borg extract /backup/borg::hostname-20240101_0300 etc/sing-box/config.json

# 挂载为 FUSE 文件系统浏览
borg mount /backup/borg::hostname-20240101_0300 /mnt/restore
# 浏览完卸载
borg umount /mnt/restore
```

## 方案三：重要配置清单（每台 VPS 要备份什么）

| 路径 | 说明 | 优先级 |
|------|------|--------|
| `/etc/sing-box/` | sing-box 配置 | 🔴 必需 |
| `/etc/nginx/` | nginx 站点配置 | 🔴 必需 |
| `/root/.hermes/` | Hermes Agent 配置 + skills | 🔴 必需 |
| `/etc/ssh/` | SSH 主机密钥 + 配置 | 🟡 重要 |
| `/etc/cloudflared/` | Cloudflare Tunnel 配置 | 🟡 重要 |
| `/etc/fail2ban/` | fail2ban 规则 | 🟢 可选 |
| `/root/.ssh/` | SSH 密钥 | 🟢 可选（密钥敏感） |

## 踩坑记录

1. **密码忘了 = 数据全丢** — Borg 的 repokey 加密模式下密码丢失无法恢复。把密码放到 KeePass/密码管理器
2. **磁盘空间满导致备份失败** — Borg prune 会自动清理旧备份，但 `--keep-*` 策略要合理。**先 df -h 确认空间**
3. **SSH 端口非 22** — rsync 必须加 `-e "ssh -p <端口>"`，Borg 设 `BORG_RSH`
4. **大文件 rsync 超时** — 加 `--timeout=600` 参数
5. **首次 Borg 备份慢** — 首次全量，后续增量只传变化部分，会快很多
6. **恢复测试** — 不要等到灾难才测试恢复。每月手动试一次 `borg extract` 到临时目录

## 验证步骤

```bash
# 检查备份存储库完整性
borg check /backup/borg

# 列出最近备份
borg list /backup/borg | tail -5

# 测试恢复（到临时目录）
mkdir -p /tmp/restore-test
cd /tmp/restore-test
borg extract /backup/borg::<latest-archive> etc/sing-box/ --dry-run
echo "恢复验证通过"

# 检查备份大小
borg info /backup/borg
```
