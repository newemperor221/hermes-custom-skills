# IP-Sentinel 集群迁移记录 (2026-05-10/11)

## 背景

用户将 IP-Sentinel 集群从分散的"每台自管"模式迁移到统一的新 TG Bot（@ip_sentinel_tg_bot / 防送中）。

## 变更内容

### Master 迁移
- **旧 Master**: dedirock/1c2.5g 洛杉矶 (<旧Master_IP>:58193) → **完全清理**
- **新 Master**: 56idc-la (<洛杉矶2_IP>:42186, 需 NAT 转发)
  - 端口 42186（NAT 端口，需要在面板开通）
  - OS: Alpine Linux 3.22.2
  - 服务管理: OpenRC（`ip-sentinel-master`）
  - TLS 自动启用（cert.pem + key.pem 存在）
  - 从 1c2.5g 直接 rsync 复制 `/opt/ip_sentinel/`

### TG Bot 统一
- **旧 Bot**: 8787213834:AAH8rP0qN0dHLRVvur1CjehACF4JzHtcc7I
- **新 Bot**: 8617143423:AAEafHIwEK0F0yd2D3v6xwMntAUtz09Dg1Y
- **Chat ID**: 8101587606（不变）
- **Bot 名**: 防送中 (@ip_sentinel_tg_bot)

### 更新的 Agent
| Agent | 端口 | OS | 旧 Token 已替换 |
|-------|------|-----|:---------------:|
| 56idc-la (Master) | 42186 | Alpine 3.22 | ✅ |
| Acck 东京 | 33020 | Debian 12 | ✅ |
| 野草云 香港 | 42387 | — | ✅ |
| CC 洛杉矶1 | 30910 | Debian 12 | ✅ |

## 踩坑记录

### 1. TG_TOKEN 和 TG_API_URL 必须同时改
只改 TG_TOKEN 不改 TG_API_URL 会导致战报仍发到旧 bot。因为 tg_report.sh 读的是 TG_API_URL（里面嵌着 token）。

### 2. SSH heredoc 引号被吃掉
用 `ssh host "cat > file << 'EOF'\\nname=\\\"with spaces\\\"\\nEOF"` 时，引号被 bash 解析吃掉。正确做法：write_file 本地写 → scp → chmod。

### 3. TLS 自动启用
cert.pem + key.pem 存在则自动启用 TLS。从外网测试必须用 `curl -sk https://...`，HTTP 会 `Connection reset by peer`。

### 4. OpenRC 服务名冲突
旧有 `ip-sentinel` 服务和新 `ip-sentinel-master` 服务都在 default runlevel，需要 `rc-update del ip-sentinel` 清理。

### 5. webhook.py 只支持 do_GET
没有 do_POST 处理器，因此无法处理 TG Bot callback queries 和用户发来的命令。如需交互面板需额外搭建。

### 6. 端口扫描
NAT 端口新开后几分钟内就会被互联网扫描器发现。webhook 的 HMAC 签名鉴权对此免疫。

### 7. tg_master.sh 看门狗 16 进程爆炸
使用 `pgrep -x tg_master.sh` 作为看门狗检测条件，因为实际进程名是 `bash` 而非 `tg_master.sh`，每分钟都认为进程未运行，spawn 一个新实例。结果：16 个 tg_master.sh 同时轮询同一个 bot，所有 TG 消息重复 16 次。

修复：改用 PID 文件（`/var/run/ip-sentinel-master.pid`）配合 `kill -0` 检测。写入 PID 后后续 cron 周期检查该 PID 是否存活。避免重启后 PID 被回收的问题（`kill -0` 恰好也处理这个边缘情况）。

### 8. pkill -f tg_master.sh 会杀死 SSH 连接
SSH 命令本身包含字符串 "tg_master.sh"，`pkill -f` 匹配全部进程树，导致 SSH 会话中断（exit code 255）。正确做法：先用 `ps aux | grep tg_master | grep -v grep` 查 PID，再逐个 `kill`。

### 9. Agent 手动注册（无 #REGISTER#）
迁移过来的旧 Agent 无法自动发送 `#REGISTER#`。解决方案：直接写入 SQLite nodes 表。

注意：注册的端口是 Agent webhook 端口（如 33020），不是 SSH 端口。Master 通过 `https://IP:PORT/trigger_*` 向 Agent 发指令。

## 最终架构

```
┌─────────────────────────────────────────────────────┐
│  Master (56idc-la / <洛杉矶2_IP>:42186)           │
│  ├── webhook.py :42186       ← Agent 上报入口       │
│  ├── tg_master.sh (polling)  ← TG Bot 控制面板      │
│  └── SQLite sentinel.db      ← 节点数据库            │
├──────────────┬──────────────────────┬───────────────┤
│  Acck 东京   │  野草云香港          │  CC 洛杉矶1    │
│  :33020      │  :42387              │  :30910        │
│  Debian 12   │  —                   │  Debian 12     │
│  systemd     │  systemd             │  systemd       │
└──────────────┴──────────────────────┴───────────────┘
```

所有组件使用同一 TG Bot（@ip_sentinel_tg_bot / 防送中）。
