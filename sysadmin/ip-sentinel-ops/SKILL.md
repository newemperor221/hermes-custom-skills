---
name: ip-sentinel-ops
description: IP-Sentinel（hotyue/IP-Sentinel）分布式 VPS 资产养护系统——安装、迁移、端口配置、Alpine/Debian 部署、故障排查。触发："IP-Sentinel"、"ip-sentinel"、"哨兵"、"资产养护"、"webhook"、"IP 定位纠偏"。
---

# IP-Sentinel 运维

> 开源项目：https://github.com/hotyue/IP-Sentinel
> AGENT_VERSION=4.0.9 / MASTER_VERSION=4.0.8（最新）
> 用户当前运行：v4.0.6（Python webhook 架构）

## ⚠️ 用户声明

**本用户（newemperor221 / 8101587606）自己管理 IP-Sentinel，不要擅自操作。** 除非用户主动要求，否则不碰 IP-Sentinel 的任何组件。

## 🚨 快速诊断：「/start 仍有弹窗，但已删了一台服务器」

当用户反馈「bot 还响应 /start」时，**不要逐台排查**。先做一次全面的 broom sweep：

### Step 1：列出所有已知服务器
- 本机（Hermes 运行的主机）— 最常见遗漏
- 所有已接入 Komari 面板的 VPS（查 `clients` 表）
- 历史部署过的任何 VPS（查 session 记录和已知的 ip-sentinel-ops 部署清单）

### Step 2：本地全面扫描（本机）
```bash
ps aux | grep -iE 'sentinel|tg_master|webhook|tg_bot'
crontab -l | grep -i sentinel
systemctl list-timers --all | grep sentinel
systemctl list-units --type=service --all | grep sentinel
find /etc/systemd/system -name '*sentinel*'
find /var/lib/systemd/timers -name '*sentinel*'
find /opt /tmp /var/log /etc/local.d -name '*sentinel*' -o -name '*tg_master*'
ss -tlnp | grep 4008[0-9]
```
⚠️ systemd timer 即使 service 文件和 timer 文件都删了，stamp 戳记仍在 `/var/lib/systemd/timers/`，必须手动清除 + `systemctl daemon-reload`。

### Step 3：远程全服务器扫描
对每一台已知服务器 SSH 进去跑：
```bash
ps aux | grep -iE 'sentinel|tg_master|webhook|tg_bot'
ls /opt/ip_sentinel* /opt/IP-Sentinel* 2>/dev/null
rc-update show | grep -i sentinel || systemctl list-units --type=service --all 2>/dev/null | grep sentinel
crontab -l | grep -i sentinel
```
⚠️ SSH 端口不一定是 22！用 `nc` 扫非标准端口：
```bash
for port in 22 2222 50000 42185 48256 46748; do
  result=$(echo "" | timeout 3 nc -v <IP> $port 2>&1)
  if echo "$result" | grep -q "SSH-2.0"; then echo "✅ SSH on port $port"; fi
done
```

### Step 4：确认 bot token 唯一
同一个 bot token 的 tg_master.sh 只能在一台服务器上运行。如果有两台以上服务器同时轮询同 token → 双弹窗 / N 弹窗。
- 检查每台服务器上 `/opt/ip_sentinel_master/master.conf` 或 `/opt/ip_sentinel/config.conf` 中的 `TG_TOKEN`
- 两个不同的 token = 两个完全不同的 bot，都需要排查

## 架构概览

**关键原则：优先使用项目自带的脚本，不写自定义代码。** 用户明确表示"不要写"自定义 TG bot 处理器。项目自带的 `tg_master.sh`（轮询模式）提供了完整的交互面板功能。如需扩展功能，通过修改现有文件而非从头编写新脚本。

项目 GitHub：https://github.com/hotyue/IP-Sentinel

```
hotyue/IP-Sentinel/
├── master/              # 司令部 — TG Bot 控制面板 + SQLite 调度
│   ├── tg_master.sh     # TG 轮询核心 (getUpdates, 非 webhook)
│   └── install_master.sh
├── core/                # 边缘哨兵 — 每台 VPS 各一个
│   ├── webhook.py       # HTTP 监听 + HMAC 签名校验
│   ├── runner.sh        # 主控调度引擎 (定时巡逻)
│   ├── mod_google.sh    # Google 区域纠偏
│   ├── mod_trust.sh     # IP 信用净化
│   └── tg_report.sh     # 每日战报推送
├── data/                # 全球 LBS 锚点 + 搜索词库 + UA 指纹
└── version.txt          # 版本信标
```

### 组件职责

| 组件 | 位置 | 功能 |
|------|------|------|
| **Master** (`tg_master.sh`) | `/opt/ip_sentinel_master/` | TG Bot 轮询器。处理 `/start`、`/panel`、按钮回调。维护 SQLite 节点数据库。向 Agent 发签名指令。 |
| **Agent** (`core/webhook.py`) | `/opt/ip_sentinel/` | 每台 VPS 各一个。接收 Master 指令执行养护任务。独立跑 Runner 巡逻 + Report 战报。 |

⚠️ **Master 和 Agent 使用同一个 TG Bot Token**，但用途不同：
- **Master** → 轮询 getUpdates（收指令、发面板、管理节点）
- **Agent** → 通过 `TG_API_URL` 发送战报/告警（只发不收）

### 关键区别：轮询 vs Webhook

tg_master.sh 使用 **长轮询**（`getUpdates?timeout=30`），不需要配置 bot webhook URL：
```json
// getWebhookInfo 应返回 "url": ""
{
  "url": "",
  "pending_update_count": 0
}
```
⚠️ 不要手动设置 webhook 地址——会与轮询冲突，导致 bot 不响应。

### Agent 注册流程

1. Agent 安装时通过 install.sh 自动向 Master 发送 `#REGISTER#` 消息
2. 格式：`#REGISTER#|REGION|NODE|IP|PORT|ALIAS|OTA`
3. Master 的 tg_master.sh 收到后写入 SQLite nodes 表
4. 也可手动注册：向 bot 发 `#REGISTER#|US|my-node|1.2.3.4|50000|MyNode`

### 手动注册（不经过 TG 消息）

当 Agent 已存在（如从旧集群迁移过来的 v4.0.6 Agent），无法发送 `#REGISTER#` 消息时，可直接写入 SQLite：

```bash
sqlite3 /opt/ip_sentinel_master/sentinel.db \
  "INSERT OR REPLACE INTO nodes \
   (chat_id, node_name, agent_ip, agent_port, region, node_alias, enable_ota, last_seen) \
   VALUES ('8101587606', '<node-id>', '<public-ip>', '<agent-port>', \
           '<region-code>', '<display-name>', 'false', CURRENT_TIMESTAMP);"
```

验证：
```bash
sqlite3 /opt/ip_sentinel_master/sentinel.db 'SELECT node_name, node_alias, agent_ip, agent_port, region FROM nodes;'
```

注意：Agent 端口是 webhook 监听端口（如 33020），**不是 SSH 端口**。Master 通过 `https://IP:PORT/trigger_*` 向 Agent 发指令。

## 安装

### Master (TG Bot 控制面板)

#### 自动安装（推荐）
```bash
curl -sL https://raw.githubusercontent.com/hotyue/IP-Sentinel/main/master/install_master.sh | bash
```
交互式：输入 TG_TOKEN + CHAT_ID，自动创建 systemd 服务（或 cron 看门狗）。

#### 手动安装（Alpine / 无 systemd 环境）

1. 安装依赖：
   ```bash
   apk add --no-cache curl jq sqlite cronie procps bash openssl
   ```

2. 创建配置 `/opt/ip_sentinel_master/master.conf`：
   ```ini
   MASTER_VERSION="4.0.9"
   TG_TOKEN="<BOT_TOKEN>"
   CHAT_ID="<CHAT_ID>"
   DB_FILE="/opt/ip_sentinel_master/sentinel.db"
   MASTER_DIR="/opt/ip_sentinel_master"
   IS_OFFICIAL_GATEWAY="false"
   ENABLE_MASTER_OTA="true"
   ```

3. 下载 tg_master.sh：
   ```bash
   curl -sL -o /opt/ip_sentinel_master/tg_master.sh \
     'https://raw.githubusercontent.com/hotyue/IP-Sentinel/main/master/tg_master.sh'
   chmod +x /opt/ip_sentinel_master/tg_master.sh
   ```

4. 初始化数据库：
   ```bash
   sqlite3 /opt/ip_sentinel_master/sentinel.db '
   CREATE TABLE IF NOT EXISTS nodes (
     chat_id TEXT, node_name TEXT, agent_ip TEXT, agent_port TEXT,
     region TEXT DEFAULT "UNKNOWN",
     last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
     node_alias TEXT,
     enable_google TEXT DEFAULT "true",
     enable_trust TEXT DEFAULT "true",
     enable_ota TEXT DEFAULT "false",
     UNIQUE(chat_id, node_name)
   );
   CREATE TABLE IF NOT EXISTS ip_trend_log (
     id INTEGER PRIMARY KEY AUTOINCREMENT,
     node_name TEXT,
     check_time DATETIME DEFAULT CURRENT_TIMESTAMP,
     scam_score INTEGER,
     nf_status TEXT,
     goog_status TEXT DEFAULT "Unknown",
     gpt_status TEXT DEFAULT "Unknown"
   );
   PRAGMA journal_mode=WAL;
   PRAGMA synchronous=NORMAL;'
   ```

5. 创建 offset 文件（记录已处理的最新更新 ID）：
   ```bash
   echo '0' > /opt/ip_sentinel_master/.tg_offset
   ```

6. 启动：
   ```bash
   setsid bash /opt/ip_sentinel_master/tg_master.sh
   ```

6. 创建 OpenRC 服务（替代 cron 看门狗，推荐方式）：\n   ```bash\n   cat > /etc/init.d/tg-master << 'SERVICE'\n#!/sbin/openrc-run\n\nname=\"tg-master\"\ndescription=\"IP-Sentinel TG Bot Polling Master\"\nsupervisor=supervise-daemon\ncommand=\"/bin/bash\"\ncommand_args=\"/opt/ip_sentinel_master/tg_master.sh\"\ncommand_background=true\npidfile=\"/run/tg-master.pid\"\ncommand_user=\"root:root\"\n\ndepend() {\n    need net\n}\n\nstart_pre() {\n    checkpath -f -m 0644 /var/log/tg-master.log\n    echo \"0\" > /opt/ip_sentinel_master/.tg_offset\n}\nSERVICE\n   chmod +x /etc/init.d/tg-master\n   rc-service tg-master start\n   rc-update add tg-master default\n   ```\n\n   ⚠️ **不要用 cron 看门狗**：`pgrep -x tg_master.sh` 永远不匹配（进程名是 `bash` 不是 `tg_master.sh`），会导致每分钟 spawn 新实例，产生 16+ 个进程。

#### 验证 Master 运行
```bash
# 1. 检查进程
pgrep -f tg_master.sh && echo "RUNNING"

# 2. 检查 offset（应不断增长，表示正在轮询新消息）
cat /opt/ip_sentinel_master/.tg_offset

# 3. 检查节点数
sqlite3 /opt/ip_sentinel_master/sentinel.db 'SELECT COUNT(*) FROM nodes;'

# 4. 配置验证
# getWebhookInfo 应返回 "url": ""（轮询模式，webhook 必须为空）
curl -s "https://api.telegram.org/bot${TG_TOKEN}/getWebhookInfo" | python3 -m json.tool

# 5. 功能测试：向 bot 发 /start，应收到控制面板
```

### Agent
```bash
apk add python3 curl  # ~64MB 空间
```

### 方式 A：从已有机器复制（推荐，保持版本一致）
```bash
# 在源机器上打包
tar czf /tmp/ip-sentinel.tar.gz -C / opt/ip_sentinel

# scp 到目标机器
scp -P <PORT> root@<SRC_IP>:/tmp/ip-sentinel.tar.gz /tmp/

# 在目标机器解压
tar xzf /tmp/ip-sentinel.tar.gz -C /
```

### 方式 B：从 GitHub 安装（交互式）
```bash
curl -sL https://raw.githubusercontent.com/hotyue/IP-Sentinel/main/core/install.sh | bash
# 注意：该脚本是交互式的，会询问地区/TG Token/端口等
# 不支持完全无人值守安装
```

### 方式 C：手动安装（可控）
```bash
# 1. 创建目录
mkdir -p /opt/ip_sentinel/{core,data,logs}

# 2. 下载核心文件
curl -sL -o /opt/ip_sentinel/core/webhook.py \
  https://raw.githubusercontent.com/hotyue/IP-Sentinel/main/core/webhook.py
  
# 注意：v4.0.9 版本已改用 shell 脚本（agent_daemon.sh），
# 但用户的 v4.0.6 使用 webhook.py（Python）。保持一致的话建议从现有机器复制。

# 3. 创建 config.conf（见下方模板）
```

## 配置

### config.conf 模板
```ini
# IP-Sentinel config
AGENT_VERSION="4.0.6"
REGION_CODE="US"              # 地区代码（US/JP/HK/...）
REGION_NAME="United States - Los Angeles"  # 地区全称
BASE_LAT="34.0522"            # 纬度（用于本地化搜索）
BASE_LON="-118.2437"          # 经度
LANG_PARAMS="hl=en&gl=US"     # Google 搜索参数（对应地区）
VALID_URL_SUFFIX="com"         # 网站后缀

# 模块开关
ENABLE_GOOGLE="true"          # Google 搜索流量
ENABLE_TRUST="true"           # 信任净化

# Telegram 配置
TG_TOKEN="8787213834:xxx"
TG_API_URL="https://api.telegram.org/bot${TG_TOKEN}/sendMessage"
CHAT_ID="8101587606"           # 接收告警的 Telegram Chat ID

# 网络配置
AGENT_PORT="50000"             # Webhook 监听端口
INSTALL_DIR="/opt/ip_sentinel"
LOG_FILE="/opt/ip_sentinel/logs/sentinel.log"
IP_PREF="4"                    # IPv4 优先
PUBLIC_IP="107.172.231.70"    # 公网 IP（Agent 对外通信用）
BIND_IP="0.0.0.0"             # 监听地址

# 节点标识
NODE_NAME="wuliaocloud-la"
NODE_ALIAS="wuliaocloud-la"
```

## TG Bot Master 的两组件架构

Master 由**两个独立服务**组成，需要分别管理：

| 组件 | 脚本 | 功能 | 端口 | 服务名 |
|------|------|------|:----:|:------:|
| **Webhook API** | `core/webhook.py` | Agent 指令接收 + HMAC 鉴权 | 42186 | `ip-sentinel-master` |
| **TG 轮询器** | `master/tg_master.sh` | TG Bot getUpdates 交互面板 | 无 | `tg-master` |

⚠️ **tg_master.sh 绝不能设 webhook URL**：它使用长轮询（getUpdates），如果设置了 bot webhook URL，两者互相冲突导致 bot 不响应。getWebhookInfo 应返回 `"url": ""`。

### TG Bot 409 Conflict 故障

**现象：** tg_master.sh 进程存在，但无法处理消息。`getUpdates` 返回 409 Conflict。

**原因：** TG API 不允许同一个 bot token 有多个活跃的 getUpdates 长连接。旧进程被杀后，其长连接可能仍被 TG 持有数分钟（未能优雅关闭）。新进程发 getUpdates 时被 TG 拒绝。

**修复流程：**
```bash
# 1. 先清掉所有 tg_master.sh 进程（注意不要用 pkill -f 自杀）
for pid in $(pgrep -f "tg_master.sh" | grep -v "supervise-daemon"); do
    kill -9 "$pid" 2>/dev/null
done

# 2. 重启 OpenRC 服务（supervise-daemon 确保单实例）
rc-service tg-master stop
sleep 2
rc-service tg-master start

# 3. 验证 offset 在 35 秒内更新（第一轮长轮询返回空后 offset 可能不增，
#    说明旧消息已清空。发一个新消息后 offset 应立刻变化）
cat /opt/ip_sentinel_master/.tg_offset
```

**预防：** 永远不要手动运行多个 tg_master.sh 实例。使用 OpenRC `supervise-daemon` 确保单实例。

### Alpine（OpenRC）特有问题排查

Alpine 是一个精简系统，缺少部分标准 Linux 调试工具，以下是常见缺失及替代方案：

| 缺失工具 | 替代方案 |
|----------|---------|
| `patch` | 用 `sed` 行插入，或用 Python 脚本 `content.replace()` |
| `screen`/`tmux` | 用 OpenRC `supervisor=supervise-daemon` 后台运行 |
| `ss` | 用 `netstat -tlnp` 或 `cat /proc/net/tcp` 查看端口 |
| `last` | 无替代（utmp 未启用） |

**Alpine 上调试 bash 脚本的推荐流程：**

1. **找目标行**：先用 `grep -n "特征字符串" script.sh` 定位行号，用 `sed -n "N,Mp"` 确认上下文
2. **插入 debug 日志**：用 `sed` 精确行号插入（而不是全局 `replace`，因为可能有多处相同的行）：
   ```bash
   sed -i "768a\\                    echo \"[DEBUG] var=\$var\" >> /tmp/debug.log" script.sh
   ```
   ⚠️ `tr -cd` 行可能在脚本中出现多次（svq 处理器、manage 处理器各有一处）。必须确认定位到**正确的代码段**，方法：
   - 用 `sed -n "N,Mp"` 确认上下文包含期望的特征字符串（如 `# 【核心升级 v4.0.0】增加拦截规则`）
   - 或用 Python 基于 section 特征字符串定位，避免误替换
3. **复杂替换**：`sed` 在含特殊字符时容易出错。先本地 `write_file` 写 Python 脚本，再 `scp` 到 Alpine 执行：
   ```bash
   # 本地写 Python 脚本
   write_file content="/tmp/patch.py" → Python 读取、替换、写入
   # scp 到服务器
   sshpass -p 'PASS' scp -P PORT /tmp/patch.py root@HOST:/tmp/
   # 执行
   sshpass -p 'PASS' ssh -p PORT root@HOST 'python3 /tmp/patch.py'
   ```
4. **不要在 SSH 命令中用 `pkill -f`**：`pkill -f tg_master.sh` 或 `kill $(pgrep -f tg_master.sh)` 会匹配到 SSH 连接自身（命令字符串包含 `tg_master.sh`），导致 exit code -15 连接中断。安全做法：
   ```bash
   # 先查 PID，逐个 kill（不要用 pkill -f）
   ps aux | grep tg_master | grep -v grep
   kill <PID1> <PID2>
   # 或排除当前 SSH
   for pid in $(pgrep -f "tg_master.sh" | grep -v "supervise-daemon"); do
       kill -9 "$pid" 2>/dev/null
   done
   ```
5. **SSH heredoc 会吃掉引号**：直接在 SSH 命令中用 `cat > file << 'EOF'` 写入包含引号的内容时，引号可能被 shell 剥离。正确做法：本地写文件 → `scp` → `chmod +x`

IP-Sentinel Master 由两个 OpenRC 服务管理，**分别处理不同组件**：

#### ⚠️ 服务名对照表

在服务器上看到的服务名不是 `tg-master`，而是：

| 脚本/组件 | 实际 OpenRC 服务名 | 说明 |
|-----------|-------------------|------|
| `tg_master.sh` | **`ip-sentinel-master`** | TG Bot 轮询面板 |
| `webhook.py` (Agent API) | **`ip-sentinel`** | Webhook 指令接收 |
| `webhook.py` (Master API) | **`ip-sentinel-master`**（未监督） | Master 自身 webhook |

**关键陷阱：** 不要用 `rc-service tg-master` — 这个服务不存在。正确命令是 `rc-service ip-sentinel-master`。

## 服务 1：ip-sentinel-master（Webhook API 层）

处理 Agent 指令接收，监听在指定 HTTPS 端口：

```bash
cat > /etc/init.d/ip-sentinel-master << 'SERVICE'
#!/sbin/openrc-run

name="ip-sentinel-master"
description="IP-Sentinel Webhook Master Service (Agent API)"
command="/usr/bin/python3"
command_args="/opt/ip_sentinel/core/webhook.py <PORT>"
command_background=true
pidfile="/run/ip-sentinel-master.pid"
command_user="root:root"
error_log="/var/log/ip-sentinel-master.err"
output_log="/var/log/ip-sentinel-master.log"

depend() {
    need net
    after firewall
}

start_pre() {
    checkpath -f -m 0644 /var/log/ip-sentinel-master.log
    checkpath -f -m 0644 /var/log/ip-sentinel-master.err
}
SERVICE
chmod +x /etc/init.d/ip-sentinel-master
rc-service ip-sentinel-master start
rc-update add ip-sentinel-master default
```

#### 服务 2：tg-master（TG Bot 轮询面板，✅ 推荐方式）

使用 `supervisor=supervise-daemon` 而不是 cron 看门狗。`supervise-daemon` 是 Alpine OpenRC 的内置守护进程管理器，自动重启崩溃的进程，且保证单实例：

```bash
cat > /etc/init.d/tg-master << 'SERVICE'
#!/sbin/openrc-run

name="tg-master"
description="IP-Sentinel TG Bot Polling Master (getUpdates mode)"

supervisor=supervise-daemon
command="/bin/bash"
command_args="/opt/ip_sentinel_master/tg_master.sh"
command_background=true
pidfile="/run/tg-master.pid"
command_user="root:root"

depend() {
    need net
    after ip-sentinel-master
}

start_pre() {
    checkpath -f -m 0644 /var/log/tg-master.log
    # ⚠️ 不要重置 offset！仅在首次安装时手动设为 0。
    # 重启时保留现有 offset，否则会重播所有历史消息造成刷屏。
}
SERVICE
chmod +x /etc/init.d/tg-master
rc-service tg-master start
rc-update add tg-master default
```

验证 tg-master 运行：
```bash
# 进程检查（应有 supervise-daemon + bash 两个进程）
pgrep -af tg_master.sh
# 输出示例：
# 59413 supervise-daemon tg-master --start --pidfile ...
# 59414 /bin/bash /opt/ip_sentinel_master/tg_master.sh

# 服务状态
rc-service tg-master status

# Offset 检查（发一条消息给 bot 后应更新）
cat /opt/ip_sentinel_master/.tg_offset
```

**优势：** `supervise-daemon` 比 cron 看门狗好得多：
- 自带 PID 文件管理，无竞争条件
- 内置重启策略（延迟 2 秒，5 次/30 分钟）
- 不依赖 crond 服务
- 不产生重复进程

#### ⚠️ 多实例洪水（Duplicate Process Flood）

当多个 tg_master.sh 同时轮询同一个 bot token，每条 TG 消息被每个实例独立处理，产生 N 倍重复回复。详见参考文档 `references/duplicate-process-flood.md`。

**典型规模：** 16 次操作 → 用户收到 16 条"探测失败"。点击一次"投放深海声呐"→ Agent 被锤 16 次。
**衍生症状：** "数据库中未找到该节点的通讯地址" 也可能是多实例抢回调导致——一个实例的 `answerCallbackQuery` 已确认该回调，后续实例的查询变量（CHAT_ID/TARGET_NODE）在竞争条件中被覆盖或污染。DB 数据完好，根因仍是多实例。

#### ⚠️ 关键陷阱：tg_master.sh 进程管理（不要用 cron 看门狗）

**不要用 cron 看门狗管理 tg_master.sh。** 使用 OpenRC `supervise-daemon`（见上方 `服务 2：tg-master`）。以下是两个容易踩的坑：

##### 坑 1：`pgrep -x tg_master.sh` 永远不匹配

`pgrep -x tg_master.sh` **不匹配** `bash /opt/ip_sentinel_master/tg_master.sh`：`-x`（exact match）只匹配进程名（basename），而实际进程名是 `bash`。

**后果：** 如果用 cron 看门狗做 `pgrep -x` 检测，每分钟都认为 tg_master.sh 未运行，启动一个新实例。数小时后变成 16+ 个进程同时轮询同一个 bot，造成 409 Conflict、消息重复、offset 混乱。

##### 坑 2：`pkill -f tg_master.sh` 自杀 SSH 连接

`pkill -f tg_master.sh` 或 `kill $(pgrep -f tg_master.sh)` 在 SSH 命令中执行时，会**杀掉 SSH 连接本身**，因为 SSH 命令字符串包含 "tg_master.sh"（exit code -15，连接中断）。这在 shell 的管道命令中尤其危险——`pkill` 在匹配到自己之前已经杀死了父 shell。

**安全清理多实例的方法：**
```bash
# ✅ 正确：先查 PID，逐个 kill（不要用 pkill -f）
ps aux | grep tg_master | grep -v grep
kill <PID1> <PID2>    # 逐个指定

# ✅ 或者排除 supervise-daemon（如果使用 OpenRC 服务）
for pid in $(pgrep -f "tg_master.sh" | grep -v "supervise-daemon"); do
    kill -9 "$pid" 2>/dev/null
done
```

##### 坑 3：重置 offset 修复 409 Conflict

当出现 409 Conflict（另一个 getUpdates 请求正在运行）时：
```bash
# 1. 停止服务（断开旧长连接）
rc-service tg-master stop

# 2. 手动关闭所有残留进程（可能会有僵尸进程）
for pid in $(pgrep -f "tg_master" | grep -v -E "supervise|grep"); do
    kill -9 "$pid" 2>/dev/null
done

# 3. 重置 offset（可选，从 0 开始重新获取所有未读消息）
echo "0" > /opt/ip_sentinel_master/.tg_offset

# 4. 等待 2 秒确保 TG API 释放旧连接
sleep 2

# 5. 重启服务（supervise-daemon 保证单实例）
rc-service tg-master start

# 6. 验证：offset 应在首次轮询后从 0 变为某个值
```

##### 坑 4：SSH heredoc 会吃掉引号

```bash
# ❌ 不要这么干（引号被 bash 吃掉）
ssh root@host "cat > /etc/init.d/ip-sentinel << 'EOF'
name="ip-sentinel-master"
description="Service with spaces here"
EOF"

# 写进文件后 name=ip-sentinel-master，引号没了！
```

**正确方法：先写本地文件，再 scp 过去**

```bash
# ✅ 正确
# 1. 本地用 write_file 创建 /tmp/ip-sentinel-init
# 2. scp 到服务器
scp -P <PORT> /tmp/ip-sentinel-init root@host:/etc/init.d/ip-sentinel-master
ssh root@host "chmod +x /etc/init.d/ip-sentinel-master"

# 或者用 Python 写（避免 shell 解析）
python3 -c "
content = '''#!/sbin/openrc-run
name=\"ip-sentinel-master\"
...
'''
with open('/tmp/init', 'w') as f: f.write(content)
"
```

#### 启用/管理
```bash
chmod +x /etc/init.d/ip-sentinel-master
rc-service ip-sentinel-master start
rc-update add ip-sentinel-master default
rc-service ip-sentinel-master status   # 检查状态
```

### Debian（systemd）
```bash
# 创建 /etc/systemd/system/ip-sentinel-agent-daemon.service
[Unit]
Description=IP-Sentinel Agent Daemon Service
After=network.target
[Service]
ExecStart=/usr/bin/python3 /opt/ip_sentinel/core/webhook.py <PORT>
Restart=on-failure
[Install]
WantedBy=multi-user.target

# 启用
systemctl daemon-reload
systemctl enable --now ip-sentinel-agent-daemon
```

### 迁移到新机器

### ⚠️ 迁移后必做：清理旧服务器的 Master 和服务

迁移 Master 到新机器后，**旧服务器上的 IP-Sentinel Master 必须停服并从 runlevel 移除**，否则两个 tg_master.sh 同时轮询同一个 bot token → 多服务器同 token 冲突（见 `references/duplicate-process-flood.md`）。

```bash
# 在旧服务器上执行
rc-service ip-sentinel-master stop 2>/dev/null
rc-update del ip-sentinel-master default 2>/dev/null
rc-update del ip-sentinel default 2>/dev/null

# 如果有 tg-master 服务名
rc-service tg-master stop 2>/dev/null
rc-update del tg-master default 2>/dev/null

# 杀残留进程
pkill -f tg_master.sh 2>/dev/null

# 验证无残留
rc-update show | grep sentinel
ps aux | grep -E 'tg_master|webhook|sentinel' | grep -v grep
```

⚠️ `ip-sentinel`（webhook API）和 `ip-sentinel-master`（TG 轮询器）是两个不同的 OpenRC 服务名，都需要处理。

### 完整流程（已验证：1c2.5g洛杉矶 → 无聊云 LXC Alpine）

1. **旧机器停服**：`systemctl stop+disable ip-sentinel-agent-daemon`
2. **复制文件**：打包 `/opt/ip_sentinel/`，scp 到新机器
3. **更新 config**：修改 `PUBLIC_IP`、`AGENT_PORT`、`NODE_NAME`、`REGION_*`
4. **创建自启动**：根据 OS 类型创建 init 脚本
5. **端口验证**：在新机器上启动，从外部测试 TCP 连通性
6. **验证日志**：检查 `/opt/ip_sentinel/logs/sentinel.log` 是否显示养护活动

### ⚠️ 关键注意

- **端口必须可公网访问**：如果新机器在 NAT 后面（如 LXC 容器），需要先确认目标端口已做端口转发。用 `timeout 5 bash -c 'echo >/dev/tcp/<PUBLIC_IP>/<PORT>'` 从外部测试。
- **Alpine 无 systemd**：使用 OpenRC（`rc-service`/`rc-update`）
- **Alpine 无 `ss` 命令**：用 `netstat -tlnp` 或 `cat /proc/net/tcp` 查看监听端口
- **文件权限**：`config.conf` 必须 `chmod 600`（包含 TG Token）
- **版本一致**：尽量从已有节点复制 v4.0.6（webhook.py 版），不升级到 v4.0.9（shell 脚本版），除非全集群统一升级
- **TLS 自动启用**：如果 `/opt/ip_sentinel/core/cert.pem` + `key.pem` 存在，webhook 自动包装 TLS。从外部验证必须用 `curl -sk https://...`，纯 HTTP 会收到 `Connection reset by peer`
- **双栈绑定行为**：webhook 先尝试 IPv6 `::`（设置 `IPV6_V6ONLY=0` 接收 IPv4 连接），失败后回退到 IPv4 `0.0.0.0`。这通常自动工作，无需手动干预
- **端口扫描**：新开 NAT 端口几分钟内就被互联网扫描器发现。webhook 的 HMAC 签名鉴权对此免疫

### 通过上游反向代理诊断（502 错误）

当 sentinel webhook 挂在一个反向代理（如 galaxy-proxy / cloudflared）后面时，502 错误意味着代理无法连接后端 webhook：

```bash
# 检查代理是否正常
curl -sI "https://stat.357561.xyz/" | grep -q "200" && echo "Proxy OK" || echo "Proxy DEAD"

# 检查 sentinel 路由（502 = webhook 未运行）
curl -s "https://stat.357561.xyz/sentinel/nodes" 2>&1
# error code: 502 → 后端 webhook 挂掉

# 对比不同 sentinel 路径（全 502 = 整个 webhook 挂掉）
for path in health status nodes; do
  echo -n "$path: "; curl -s "https://stat.357561.xyz/sentinel/$path" 2>&1
done
```

修复方法同下（SSH 进机器启动 webhook.py）。

### 部署验证清单（迁移/安装后必做）

1. **进程检查**：`ps aux | grep webhook | grep -v grep` → 确认 Python 进程存在
2. **端口监听**：`netstat -tlnp | grep <PORT>` → `LISTEN` 状态
3. **外网 TCP 握手**：`timeout 3 bash -c 'echo >/dev/tcp/<PUBLIC_IP>/<PORT>' && echo "OPEN"`
4. **HTTPS 响应**：`curl -sk https://<PUBLIC_IP>:<PORT>/` → 应返回 `"401 Unauthorized: Missing Signature"`（说明服务在运行且鉴权生效）
5. **TG 消息直达**：直接用 TG API 发测试消息验证 bot token
6. **日志有活动**：`tail -5 /opt/ip_sentinel/logs/sentinel.log` → 应有养护记录

```bash
# 快速一键验证
curl -sk https://127.0.0.1:<PORT>/ 2>&1 | grep -q "401" && echo "✅ Webhook alive" || echo "❌ Webhook dead"
```

## TG Token 管理与统一迁移

### 关键陷阱：TG_API_URL 必须随 TG_TOKEN 一起更新

TG_TOKEN 和 TG_API_URL 是 config.conf 中的两个独立字段。只改 TG_TOKEN 而不改 TG_API_URL 是一个极易踩入的陷阱：

- Agent 的 tg_report.sh 脚本使用 $TG_API_URL（从 config.conf 读取）发送消息
- $TG_TOKEN 仅被用于少数验证场景
- TG_API_URL 里硬编码了 token：https://api.telegram.org/bot<TG_TOKEN>/sendMessage

只改 TG_TOKEN 不改 TG_API_URL 的效果：
- 新 token 看起来"放进了 config"
- 但所有 TG 消息仍然通过旧 token 的 URL 发送
- 新 bot 收不到任何消息
- 服务日志仍显示"战报推送成功"，但这是对旧 bot API 的

正确做法 — 两条 sed 缺一不可：
```bash
sed -i 's|TG_TOKEN=".*"|TG_TOKEN="<NEW_TOKEN>"|' /opt/ip_sentinel/config.conf
sed -i 's|TG_API_URL=".*"|TG_API_URL="https://api.telegram.org/bot<NEW_TOKEN>/sendMessage"|' /opt/ip_sentinel/config.conf
```

### 更新单台服务器 Token + 验证

```bash
# 1. 改 token + url（必须两条）
sed -i 's|TG_TOKEN=".*"|TG_TOKEN="<NEW_TOKEN>"|' /opt/ip_sentinel/config.conf
sed -i 's|TG_API_URL=".*"|TG_API_URL="https://api.telegram.org/bot<NEW_TOKEN>/sendMessage"|' /opt/ip_sentinel/config.conf

# 2. 重启（OpenRC）
rc-service ip-sentinel-master restart
# 或（systemd）
systemctl restart ip-sentinel-agent-daemon

# 3. 手动触发战报（验证新 token 生效）
rm -f /opt/ip_sentinel/core/.report_lock
bash /opt/ip_sentinel/core/tg_report.sh
# 应输出：战报推送成功！
```

### 验证 Token 有效性（独立于 IP-Sentinel）
```bash
curl -s -m 10 -X POST "https://api.telegram.org/bot<TOKEN>/sendMessage" \
  -d "chat_id=<CHAT_ID>" \
  -d "text=Test message" \
  -d "parse_mode=Markdown"
# 返回 {"ok":true,...} 即为成功
```

### 多 Agent 统一换 Token 流程
当需要更换整个集群的 TG Bot 时（如 bot 被滥用、创建新 bot）：

1. **先在 master 上换** → 验证 master 能发 TG 消息
2. **逐个在 agent 上换** → 每个 agent 执行上述两条 sed 命令（token + url）+ 重启
3. **验证每个 agent** → bash /opt/ip_sentinel/core/tg_report.sh 手动触发战报
4. **检查 TG 是否收到消息**（来自每个 agent 的独立战报）

## Webhook 端点参考

webhook.py 只支持 `do_GET`（**不支持 `do_POST`**），所有端点需 HMAC 签名鉴权（PSK = CHAT_ID）：

| 路径 | 功能 |
|------|------|
| `/trigger_run` | 触发 runner.sh 主控调度 |
| `/trigger_google` | 触发 Google 区域纠偏 |
| `/trigger_trust` | 触发 IP 信用净化 |
| `/trigger_report` | 触发 TG 战报推送 |
| `/trigger_log` | 抓取并回传实时日志（带 inline keyboard） |
| `/trigger_quality` | 触发深海声呐 |

### 签名生成

```python
import hmac, hashlib, time
AUTH_TOKEN = '<CHAT_ID_value>'  # PSK = config 中的 CHAT_ID
req_path = '/trigger_report'
req_t = str(int(time.time()))
sign = hmac.new(AUTH_TOKEN.encode(), f'{req_path}:{req_t}'.encode(), hashlib.sha256).hexdigest()
url = f'https://<IP>:<PORT>{req_path}?t={req_t}&sign={sign}'
```

防重放：60 秒时间窗口 + nonce 缓存池。

### TG Bot 交互（tg_master.sh 版）

**tg_master.sh** 使用长轮询（getUpdates）处理 TG 命令和按钮回调，**不需要也绝不能设置 webhook**：

```json
// getWebhookInfo → "url": "" 是正确状态
```

#### 支持的命令

| 命令/回调 | 功能 |
|-----------|------|
| `/start` 或 `/menu` | 显示司令部面板（版本、节点数、OTA 信息） |
| `/panel` | 打开控制面板（与 /start 相同） |
| `list_nodes` | 按 region 显示战区列表（一级雷达） |
| `region:<code>` | 显示该战区下的节点（如 `region:JP`） |
| `manage:<node>` | 节点控制面板（三级菜单）：Google/Trust/Quality/日志/战报/OTA |
| `all_run` | 唤醒全局巡逻 |
| `all_reports` | 获取全局简报 |
| `toggle:google\|trust` | 模块启停 |
| `del:` | 删除节点 |
| `rename:` | 重命名节点 |

#### 按钮面板导航
```
司令部 → 🌍 全球雷达 → 🇯🇵 东京战区 → 节点控制台 → 执行操作
```

#### 注意事项
- tg_master.sh 只处理**授权用户**的消息（CHAT_ID 匹配）
- 新 Agent 必须通过 `#REGISTER#` 消息注册后才出现在雷达中
- 所有操作通过 HMAC 签名向 Agent webhook 发指令，60 秒过期
- 全节点操作（all_reports）有 2 秒间隔防 TG 限流

### TG Bot 限制（纯 core/webhook.py 版，无 Master）

仅当未安装 master/ 组件时：

- ✅ **能做的**：发送消息（战报/告警）、附带 inline keyboard 按钮（点击回调被丢弃）
- ❌ **不能做的**：处理用户命令（`/start`、`/panel`）、响应按钮回调、展示交互式面板

如需交互面板，需额外搭建 TG Bot 后端（python-telegram-bot / aiogram），在独立端口监听，配置 TG webhook 指向该端口。也可以把 bot 菜单链接到已有面板（如 stat.357561.xyz）。

### OTA 故障排查

## "数据库中未找到该节点的通讯地址" 排查

**现象：** 点击节点控制台的任何动作按钮（quality/trust/google/report/log/OTA），返回该错误。

### 根因速查

| 原因 | 判断方式 | 修复 |
|------|----------|------|
| **Callback 竞争**（最常见） | 同时点了多个按钮，或多实例 tg_master.sh 竞争回调 | 重启 `ip-sentinel-master` 服务 |
| **服务名不对** | 系统上服务名是 `ip-sentinel-master` 不是 `tg-master` | `rc-service ip-sentinel-master restart` |
| **数据库无节点** | `sqlite3 sentinel.db 'SELECT node_name, agent_ip, agent_port FROM nodes;'` 为空 | 重新注册节点 |
| **CHAT_ID 不匹配** | master.conf 的 `CHAT_ID` 与数据库 `chat_id` 字段不同 | 统一 chat_id |
| **节点名编码问题** | `node_name` 包含特殊字符，callback_data 的 `tr -cd` 过滤掉了 | 用纯 ASCII 字母数字连字符命名 |

### 代码中 4 个报错位置

错误信息出现在 tg_master.sh 的 4 处（均为节点名查询失败的回退消息）：

| 行号 | 触发方式 | 提取逻辑 |
|------|----------|---------|
| ~434 | 文本命令 `/quality node-name` | `awk '{print $2}'` 取第二个词 |
| ~715 | `do_rename` 回调 | `${TEXT#*:}` 取冒号后 |
| ~758 | `ota_execute` 回调 | `cut -d':' -f2` 取冒号后第二节 |
| ~811 | `google:/trust:/run:/report:/log:/quality:` 回调（按钮点击） | `cut -d':' -f2` |

### 快速验证

```bash
# 模拟 button callback 查询
CHAT_ID='8101587606'
TEXT='quality:acck-tokyo'
TARGET_NODE=$(echo "$TEXT" | cut -d':' -f2 | tr -cd 'a-zA-Z0-9_.-')
sqlite3 /opt/ip_sentinel_master/sentinel.db \
  "SELECT agent_ip, agent_port FROM nodes \
   WHERE chat_id='$CHAT_ID' AND node_name='$TARGET_NODE' LIMIT 1;"
# 应返回 IP|PORT，空则查不到
```

### 标准修复流程

```bash
# 1. 重启服务（清 stale 状态）
rc-service ip-sentinel-master restart

# 2. 确认单进程运行
pgrep -af tg_master.sh | grep -v ssh
# 应只有 1 个进程

# 3. 验证节点数据完整
sqlite3 /opt/ip_sentinel_master/sentinel.db \
  'SELECT node_name, agent_ip, agent_port FROM nodes;'

# 4. 验证 token 有效
TG_TOKEN=$(grep 'TG_TOKEN=' /opt/ip_sentinel_master/master.conf | cut -d'=' -f2)
curl -s -m 5 "https://api.telegram.org/bot${TG_TOKEN}/getMe"
# → {"ok":true,"result":{"id":...,"is_bot":true,...}}

# 5. 让用户重新点按钮测试
```

**现象：** 点击「全网节点 OTA 热重载」→ 确认风险 → 收到该错误，即使数据库已有节点且 `enable_ota='true'`。

**根因定位：** `tg_master.sh` 中 `all_ota_execute` 处理器执行以下查询（约 line 311）：

```bash
NODE_DATA=$(db_exec "SELECT node_name, agent_ip, agent_port
  FROM nodes WHERE chat_id='$CHAT_ID' AND enable_ota='true';")
if [ -z "$NODE_DATA" ]; then
    send_msg "$CHAT_ID" "⚠️ 您名下暂无开启 OTA 权限的在线节点。"
```

**排查步骤：**

```bash
# 1. 检查数据库数据是否真的正确
sqlite3 /opt/ip_sentinel_master/sentinel.db \
  "SELECT node_name, enable_ota, quote(enable_ota), length(enable_ota) FROM nodes;"
# ⚠️ 注意 quote() 和 length() — 确保 enable_ota 是 'true' 不是 'true ' 等

# 2. 执行与脚本完全相同的查询
sqlite3 /opt/ip_sentinel_master/sentinel.db \
  "SELECT node_name, agent_ip, agent_port FROM nodes
   WHERE chat_id='8101587606' AND enable_ota='true';"
# chat_id 必须与 master.conf 中的 CHAT_ID 一致

# 3. 确认 tg-master 进程正常运行且不卡死
ps aux | grep tg_master | grep -v grep | grep -v supervise
cat /opt/ip_sentinel_master/.tg_offset  # offset 应不断增长

# 4. 检查是否有残余进程导致消息竞争（多实例洪水）
for pid in $(pgrep -f "tg_master.sh" | grep -v "supervise-daemon"); do
    kill -9 "$pid" 2>/dev/null; done
rc-service tg-master restart
```

**常见原因：**

| 原因 | 表现 | 修复 |
|------|------|------|
| chat_id 不匹配 | 数据库 `chat_id` 与 `master.conf` 中 `CHAT_ID` 不同 | 统一 chat_id |
| enable_ota 有隐藏字符 | `quote()` 显示 `'true'` 但长度 > 4 | 重设：`UPDATE nodes SET enable_ota='true'` |
| Master 刚重启，offset 回退 | offset 值大幅回退，在处理旧消息序列中的错误回复 | 等待 offset 追上当前消息 |
| 节点注册时 OTA 字段缺失 | 旧版本注册消息 <7 字段，`RAW_OTA` 默认为 `"false"` | `UPDATE nodes SET enable_ota='true'` |
| 多实例洪水 | 多个 tg_master.sh 竞争处理回调，部分实例的上下文变量被污染 | 杀多余进程，restart tg-master |

**验证修复：** 直接向 bot 发送 `/start` 确认节点列表正常，再点 OTA 热重载。

## 清理/卸载

完全移除 IP-Sentinel，不留痕迹。**迁移后务必检查是否有旧进程残留：**

```bash
# 检查目标端口上是否有残留进程
fuser -l <OLD_PORT>/tcp 2>/dev/null
ps aux | grep webhook | grep -v grep
# 如果看到多个 webhook.py 在不同的端口上，说明旧进程未清理
kill <OLD_PID>  # 杀旧进程
```

**⚠️ orphan webhook.py：** 迁移 Master 到新端口（如 50000 → 42186）时，旧端口的 `webhook.py` 进程不会自动退出——它仍在后台运行。两步检查：
1. `ps aux | grep webhook | grep -v grep` 看看有几个
2. 如果有多个，比对端口号，杀掉旧的

```bash
# 示例：杀 PID 17457（旧 50000 端口的 webhook）
kill -9 17457
```

**⚠️ Master 有两个可能路径：**

IP-Sentinel Master 的 TG 轮询器可能在两个不同的目录下，取决于安装方式：

| 路径 | 内容 | 典型来源 |
|------|------|---------|
| `/opt/ip_sentinel/` | `core/webhook.py` + `config.conf`（Agent/API 层） | 从 GitHub install.sh 安装 |
| `/opt/ip_sentinel_master/` | `tg_master.sh` + `master.conf` + `sentinel.db`（TG 轮询层） | 从 GitHub install_master.sh 安装 |

**清理前必须确认的实际目录和自启脚本：**

```bash
# 先全面检查有哪些文件和服务
for dir in /opt/ip_sentinel /opt/ip_sentinel_master /opt/IP-Sentinel; do
  [ -d "$dir" ] && echo "📁 $dir 存在" || echo "❌ $dir 不存在"
done
echo "---"
echo "🔍 自启脚本："
ls -la /etc/local.d/ip-sentinel* 2>/dev/null || echo "  (无 /etc/local.d/ 自启)"
ls -la /etc/init.d/ip-sentinel* 2>/dev/null || echo "  (无 OpenRC 服务)"
ls -la /etc/systemd/system/ip-sentinel* 2>/dev/null || echo "  (无 systemd 服务)"
echo "---"
echo "🔍 相关进程："
ps aux | grep -E 'tg_master|webhook\.py|sentinel' | grep -v grep || echo "  (无进程)"
```

**Alpine（OpenRC）完整清理（覆盖两种安装路径）：**

```bash
# 1. 杀掉所有相关进程（逐个手动 kill，避免 pkill -f 自杀 SSH）
for pid in $(pgrep -f "tg_master" | grep -v -E "supervise|grep|ssh"); do
  kill -9 "$pid" 2>/dev/null
done
for pid in $(pgrep -f "webhook" | grep -v -E "grep|ssh"); do
  kill -9 "$pid" 2>/dev/null
done

# 2. 移除 OpenRC 服务（如果存在）
for svc in ip-sentinel-master ip-sentinel tg-master; do
  rc-service "$svc" stop 2>/dev/null
  rc-update del "$svc" default 2>/dev/null
  rm -f "/etc/init.d/$svc"
done

# 3. 移除 /etc/local.d/ 自启脚本（如果存在，通常是简单的手动自启方式）
rm -f /etc/local.d/ip-sentinel*

# 4. 删除目录（三个可能的路径都要删）
rm -rf /opt/ip_sentinel
rm -rf /opt/ip_sentinel_master
rm -rf /opt/IP-Sentinel

# 5. 验证无残留
ps aux | grep -E 'tg_master|webhook|sentinel' | grep -v grep || echo "✅ 无残留进程"
ls /opt/ip_sentinel* 2>/dev/null || echo "✅ 无残留目录"
ls /etc/local.d/ip-sentinel* /etc/init.d/ip-sentinel* /etc/init.d/tg-master 2>/dev/null || echo "✅ 无残留自启"
```

**Debian（Systemd）：**
```bash
# 停止所有服务和定时器
systemctl stop ip-sentinel-agent-daemon ip-sentinel-runner.timer ip-sentinel-runner.service ip-sentinel-updater.timer ip-sentinel-updater.service ip-sentinel-report.timer ip-sentinel-report.service 2>/dev/null

# 禁用自启动
systemctl disable ip-sentinel-agent-daemon ip-sentinel-runner.timer ip-sentinel-updater.timer ip-sentinel-report.timer 2>/dev/null

# 删除文件
rm -rf /opt/ip_sentinel
rm -f /etc/systemd/system/ip-sentinel-*.service /etc/systemd/system/ip-sentinel-*.timer

# 验证清理
systemctl list-units --type=service --all 2>/dev/null | grep ip-sentinel
systemctl list-timers --all 2>/dev/null | grep ip-sentinel
ps aux | grep -i ip-sentinel | grep -v grep
```

### ⚠️ 关键遗漏：本机（Hermes 运行的主机）也可能装有 IP-Sentinel

当排查 IP-Sentinel 问题时，**不要只检查远程 VPS**。本机（Hermes Agent 运行的主机）可能也装有 IP-Sentinel，且安装方式可能完全不同。

**本机常见的 IP-Sentinel 安装残留：**

| 类型 | 位置 | 说明 |
|------|------|------|
| systemd 服务 | `/etc/systemd/system/ip-sentinel-*.service` | agent-daemon, runner, report, updater |
| systemd 定时器 | `/etc/systemd/system/ip-sentinel-*.timer` | 自动触发养护/报告 |
| systemd 定时器戳记 | `/var/lib/systemd/timers/stamp-ip-sentinel-*.timer` | 即使删了 .timer 文件仍残留 |
| systemd 软链接 | `/etc/systemd/system/...wants/ip-sentinel-*` | 自启软链 |
| cron 看门狗 | `crontab` 中 `pgrep -f tg_master.sh` | 每分钟自启 tg_master |
| Agent 目录 | `/opt/ip_sentinel/` | webhook.py + config.conf |
| Master 目录 | `/opt/ip_sentinel_master/` | tg_master.sh + sentinel.db |
| 旧目录 | `/opt/IP-Sentinel/` | 大写版本目录 |
| 临时文件 | `/tmp/ip-sentinel-*` | bot.py, watchdog, init, tar.gz |
| 日志 | `/var/log/ip-sentinel-*.log` | master/webhook 日志 |
| OpenRC 残留 | `/run/openrc/options/ip-sentinel*` | 空目录残留 |

**排查本机：**
```bash
ps aux | grep -iE 'sentinel|tg_master|webhook|sentinel'
crontab -l | grep -i sentinel
find /etc/systemd/system -name '*sentinel*'
find /var/lib/systemd/timers -name '*sentinel*'
find /opt /tmp /var/log -name '*sentinel*' -o -name '*tg_master*' 2>/dev/null
ss -tlnp | grep 4008[0-9]
```

**清理本机（Debian/systemd）：**
```bash
systemctl stop ip-sentinel-agent-daemon ip-sentinel-runner ip-sentinel-report ip-sentinel-updater 2>/dev/null
systemctl disable ip-sentinel-agent-daemon ip-sentinel-runner.timer ip-sentinel-report.timer ip-sentinel-updater.timer 2>/dev/null
rm -f /etc/systemd/system/ip-sentinel-*.service /etc/systemd/system/ip-sentinel-*.timer
rm -f /etc/systemd/system/*.wants/ip-sentinel-*
rm -f /var/lib/systemd/timers/stamp-ip-sentinel-*.timer
rm -rf /run/openrc/options/ip-sentinel*
(crontab -l | grep -v sentinel) | crontab -
rm -rf /opt/ip_sentinel /opt/ip_sentinel_master /opt/IP-Sentinel
rm -f /tmp/ip-sentinel-* /tmp/install_sentinel.sh /tmp/sentinel_inputs.txt
rm -f /var/log/ip-sentinel-*.log
systemctl daemon-reload
```

⚠️ **systemd timer 坑：删了 .timer 文件 timer 还活着。** `systemctl list-timers` 可能显示已删除的 timer，因为 `/var/lib/systemd/timers/stamp-*.timer` 戳记文件没删。必须手动清理：\n```bash\nrm -f /var/lib/systemd/timers/stamp-ip-sentinel-*.timer\nsystemctl daemon-reload\nsystemctl reset-failed\n```\n\n⚠️ **顺序重要：** 先 `systemctl disable` 再删文件。定时器 stamp 必须手动清理。不删 stamp 不影响运行但 `systemctl list-timers` 仍会显示已删除的 timer。\n\n⚠️ **多 token 混淆：** 同一个用户可能在不同时期创建了多个不同的 TG bot token 用于 IP-Sentinel。清理时注意区分：\n- 旧 bot token 可能在本机 systemd 服务中使用（`/opt/ip_sentinel/config.conf` 中的 `TG_TOKEN`）\n- 新 bot token 可能在远程 Master 中使用（`/opt/ip_sentinel_master/master.conf` 中的 `TG_TOKEN`）\n- @ip_sentinel_tg_bot 使用的是哪个 token 需要确认：通过 `curl -s https://api.telegram.org/bot&lt;TOKEN&gt;/getMe` 返回的 `result.id` 判断\n- 两个不同的 bot token = 两个完全独立的 bot，都需要排查

### 报告定时器（systemd timer）

IP-Sentinel 的 TG 战报不是实时推送的，而是通过 systemd timer 按计划触发：

```bash
# 查看定时器
systemctl list-timers --all | grep ip-sentinel

# 典型的 timer 调度
ip-sentinel-runner.timer   →  每 20 分钟（养护任务）
ip-sentinel-report.timer   →  每天 12:00（TG 战报）
ip-sentinel-updater.timer  →  每天特定时间（OTA 更新）

# 手动触发战报（不等待 timer）
systemctl start ip-sentinel-report.service
# 或者
rm -f /opt/ip_sentinel/core/.report_lock
bash /opt/ip_sentinel/core/tg_report.sh
```

重要：runner.timer（养护任务）每 20 分钟运行但不发 TG 消息。只有 report.timer（每天 12:00）会触发战报推送。所以改完 token 后看不到消息是正常的 — 手动触发战报才能验证。

### 已知 Agent 部署清单（当前用户环境）

| Agent | IP | SSH 端口 | Webhook 端口 | OS | TG Token | 服务管理 | 状态 |
|-------|-----|----------|-------------|-----|----------|---------|------|
| **Master** (56idc-la) | 107.172.231.70 | **42185** (50000 also shows OpenSSH banner, likely NAT forward) | 42186 | Alpine 3.22 | 新（防送中） | OpenRC | ✅ 运行 |
| **Acck 东京** | 156.231.141.232 | 22 | 33020 | Debian 12 | 新（防送中） | systemd | ✅ 运行 |
| **野草云香港** | 38.55.198.243 | 22 | 42387 | (未确认) | 新（防送中） | systemd | ✅ 运行 |
| **CC 洛杉矶1** | 23.95.201.153 | 22 | 30910 | Debian 12 | 新（防送中） | systemd | ✅ 运行 |

⚠️ **SSH 端口不一定默认 22！** 某些 VPS 的 SSH 在奇怪端口上（如 50000）。用 `nc -zv IP PORT` 扫描常见端口，如果返回 `SSH-2.0-OpenSSH` banner 说明找到了 SSH 端口。

### 全服务器扫描（找不到 Bot 进程时的最后手段）

当 bot 仍然响应 /start，但排查了本机和所有已知远程服务器后都找不到 tg_master.sh 进程时：

1. **检查已知 Agent 部署清单**（看上方表格），尝试 SSH 到每台服务器
2. **如果 SSH 端口 22 连不上**，用 nc 扫描常见非标准 SSH 端口：
   ```bash
   for port in 22 2222 50000 50001 42186 42187 9922 22022 30000; do
     result=$(echo "" | timeout 3 nc -v <IP> $port 2>&1)
     if echo "$result" | grep -q "SSH-2.0"; then echo "✅ SSH on port $port"; fi
   done
   ```
3. **找到 SSH 端口后**，用用户密钥尝试登录查看

**实战案例：** 107.172.231.70 的 SSH 端口是 50000（nc 返回 OpenSSH banner），而非默认 22。端口扫描揭示了一个隐藏的 Master 服务器，tg_master.sh 一直在那里轮询。

所有 Agent 共享同一 TG Bot（@ip_sentinel_tg_bot / 防送中），各自独立发送战报。

## TLS/HTTPS 行为（重要）

webhook.py 启动时会检查 `/opt/ip_sentinel/core/cert.pem` 和 `key.pem`：

- **两个文件都存在** → 自动用 TLS 包装 socket，只接受 HTTPS
- **任一文件不存在** → 退化为纯 HTTP

**坑：** 如果 cert.pem 存在但用 `curl http://...` 测试，会收到 `Connection reset by peer`，不是因为服务挂了，而是 TLS 握手失败。**必须用 `curl -sk https://...`**。

验证端口是否存活的最可靠方法：

```bash
# 1. TCP 握手（最底层）
timeout 3 bash -c 'echo >/dev/tcp/<IP>/<PORT>' && echo "OPEN"

# 2. HTTPS 响应
curl -sk -m 5 https://<IP>:<PORT>/health

# 如果收到 "Connection reset by peer"，99% 是 TLS 问题，先用 -k 试试
```

### Alpine 执行 Python 一行的注意事项

在 Alpine SSH 会话中执行 Python 脚本时：
- `ssh` 命令行中的引号嵌套会导致 shell 解析混乱 → 用单行 `python3 -c "..."` 只适用简单语句
- 复杂脚本（多行、特殊字符）必须**先本地写 Python 文件，再 scp 到服务器执行**
- `busybox` 的 `sh` 不支持 `$'...'` 语法、`sed -i` 行为与 GNU 不同

### 手动触发 OTA（Python 签名生成）

当 Master 面板 OTA 按钮不可用，或需要绕过面板直接触发节点升级时：

```python
import hmac, hashlib, time, urllib.request, ssl

CHAT_ID = "<CHAT_ID>"  # 从 master.conf 获取
agents = [
    ("<node_name>", "<public_ip>", <agent_port>),
]

ctx = ssl._create_unverified_context()
for name, ip, port in agents:
    path = "/trigger_ota"
    ts = str(int(time.time()))
    sign = hmac.new(CHAT_ID.encode(), f"{path}:{ts}".encode(), hashlib.sha256).hexdigest()
    url = f"https://{ip}:{port}{path}?t={ts}&sign={sign}"
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url), context=ctx, timeout=10)
        print(f"✅ {name}: {resp.read().decode()[:80]}")
    except Exception as e:
        print(f"❌ {name}: {e}")
```

**执行环境：** 签名由 Master 端生成（需要 `CHAT_ID` 作为 PSK），在 Master 所在服务器执行（56idc-la 107.172.231.70:42185）。

```bash
# 1. 修改 config.conf
sed -i 's|AGENT_PORT="50000"|AGENT_PORT="42186"|' /opt/ip_sentinel/config.conf
sed -i 's|TG_TOKEN=".*"|TG_TOKEN="<NEW_TOKEN>"|' /opt/ip_sentinel/config.conf
sed -i 's|TG_API_URL=".*"|TG_API_URL="https://api.telegram.org/bot<NEW_TOKEN>/sendMessage"|' /opt/ip_sentinel/config.conf

# 2. 杀旧进程（如果有多个 listener 在旧端口）
fuser -k <OLD_PORT>/tcp 2>/dev/null
fuser -k <NEW_PORT>/tcp 2>/dev/null

# 3. 重新启动
rc-service ip-sentinel restart
# 或手动：python3 /opt/ip_sentinel/core/webhook.py <NEW_PORT>

# 4. 验证
sleep 2
netstat -tlnp | grep <NEW_PORT>
curl -sk https://127.0.0.1:<NEW_PORT>/   # → 401
```

### 端口被扫描

新开的 NAT 端口平均在几分钟内就会被互联网扫描器发现（如 HostPapa 邮件服务器、Censys、Shodan 等）。这是正常现象，不是安全事件。但如果端口上挂的是未认证的服务，则有风险。

webhook.py 自带 HMAC-SHA256 签名鉴权 + 时间戳防重放（60秒窗口），对端口扫描免疫。扫描器发来的无签名请求会返回 401，不执行任何操作。

## HMAC 签名测试

参考 `references/hmac-test.md` — Python 和 shell 两种方式生成签名、调用各 trigger 端点。
参考 `references/tg-bot-409-conflict.md` — TG Bot 409 Conflict 排查与修复流程。
参考 `references/duplicate-process-flood.md` — tg_master.sh 多实例洪水刷屏排查指南。
参考 `references/two-duplicate-response.md` — TG Bot /start 收到两条相同回复的排查步骤（跨服务器同 token + offset 混乱）。

### TG Token 安全
Token 明文存储在 `config.conf` 中，不要：
- 提交到 GitHub
- 在不安全的网络传输
- 泄露到日志中

### 日志解读
```
[2026-05-11 01:09:24 UTC] [v4.0.6] [SCORE] [Trust] [US] 自检结论: ✅ 信用净化完成
[2026-05-11 01:09:24 UTC] [v4.0.6] [END] [Trust] [US] ========== 会话结束 ==========
[2026-05-11 01:09:24 UTC] [v4.0.6] [INFO] [SYSTEM] [US] 本轮所有模块调度完毕
```
- `[SCORE]`：评分报告
- `[Trust]`：执行的模块（Trust/Google）
- `[US]`：地区
- 正常日志表示 Agent 在正常执行养护任务
