---
name: server-health
description: 一键巡检服务器健康状态 — CPU、内存、磁盘、SSH安全配置、fail2ban、UFW防火墙状态。触发场景：\"巡检服务器\"、\"服务器健康检查\"、\"所有服务器状态\"。
---

# Server Health Check

跨服务器健康状态巡检，使用 paramiko SSH 库，每台服务器只建一条 SSH 连接，所有命令打包执行。

## 使用方式

```
server-health                      # 扫描所有服务器（完整检查）
server-health --quick             # 基础检查（CPU/内存/磁盘）
server-health --servers "洛杉矶1,纽约"  # 只扫指定机器
server-health --json              # 输出 JSON 格式
```

## 健康检查项目

### 基础项（默认）
| 检查项 | 命令 | 告警阈值 |
|--------|------|---------|
| CPU使用率 | `top -bn1` | > 80% |
| 系统负载 | `uptime` | load > 2.0 |
| 内存使用 | `free -m` | > 85% |
| 磁盘使用 | `df -h` | > 85% |
| 系统运行时间 | `uptime -s` | - |

### 安全项（默认开启）
| 检查项 | 命令 | 告警阈值 |
|--------|------|---------|
| SSH允许密码登录 | `awk` 读取 sshd_config | yes（应为 no）|
| SSH允许root登录 | `awk` 读取 sshd_config | yes（应为 no）|
| SSH端口 | `awk` 读取 sshd_config | 22（应为非标准）|
| fail2ban状态 | `systemctl is-active fail2ban` | 非 active |
| SSH服务状态 | `systemctl is-active ssh` | 非 active |
| UFW防火墙 | `ufw status` | inactive |

## 运维角色

对当前环境，作为运维工程师（Ops Engineer）工作：
- **主动巡检**：定期检查所有服务器的 CPU/内存/磁盘/服务状态，发现隐患提前报
- **能修的立刻修**：告警/异常 → 先查日志定位 → 确认修复方案 → 直接修 → 汇报结果
- **服务清单有数**：服务器、域名、端口、服务角色、依赖关系要记准确，搞混了立刻纠正
- **效率优先**：不废话，直接给结论和操作。巡检发现有异常直接修，修完汇报
- **记忆即运维台账**：VPS IP/端口/角色/服务列表的第一手信息存记忆，修过的坑存 skill

## 服务器配置

## ⚠️ 小磁盘服务器（≤1.5G）监控工具选择原则

**绝对禁止在这类机器上跑任何本地数据库服务。** SQLite WAL、MySQL、PostgreSQL、MongoDB 等在 1.2G 磁盘上都会爆。

**56idc-la（<洛杉矶2_IP>）当前状态（2026-05-12）：**
- SSH 端口: 42185
- OS: Alpine Linux v3.22
- 磁盘: 991M 总量，16M 已用（2%），~975M 剩余
- 运行中服务：**仅 komari-agent**（已降级为纯探针节点）
- 已迁移至荷兰机：komari server、ip_sentinel webhook、ip_sentinel_master、cloudflared
- SSH 密钥登录被拒，必须 `sshpass -p 'Y@BU1%wmP#xFs8bK'`

## Alpine / OpenRC 支持

`health.py` 目前假设 systemd（Debian/Ubuntu）。在 Alpine 上运行会失败，因为：

| 命令 | systemd 版 | OpenRC 版 |
|------|-----------|-----------|
| 服务状态检查 | `systemctl is-active ssh` | `rc-service sshd status` (exit code) |
| fail2ban | `systemctl is-active fail2ban` | `rc-service fail2ban status` |
| SSH 配置 | `/etc/ssh/sshd_config` | 相同路径 |
| 防火墙 | `ufw status` | 相同命令（需已安装） |

**Alpine 上手动检查的替代命令：**

```bash
# 服务状态
rc-service sshd status        # → "* status: started"
rc-service fail2ban status    # → "* status: started"

# 端口监听（Alpine 无 ss，用 netstat 或 /proc）
netstat -tlnp                 # 或
cat /proc/net/tcp | awk '{print $2}'  # 只列监听地址

# 进程状态（无 /proc/uptime 的完整度）
cat /proc/loadavg
# 输出：3.85 4.76 4.84 3/3464 3489287
#         1m   5m  15m  running/total  latest_pid

# 系统运行时间
uptime -s                     # Alpine 也支持

# 进程 CPU 累计时间（诊断长期 CPU 消耗）
ps -o cputime,etimes,pid,comm -p <PID>
# cputime=累计CPU时间 (MM:SS or HH:MM:SS)
# etimes=进程已运行秒数
# 有效占用率 ≈ cputime / etimes × 100%
```

### CPU 负载虚高诊断（HDD I/O Wait — 磁盘瓶颈型）

**现象：** 1 核 LXC 容器，load average 3~5，`%id` 接近 0%，但 `%us` 也接近 0%，没有明显吃 CPU 的进程。

**根本原因：** 廉价 LXC 母鸡的 **机械硬盘（HDD, ROTA=1）** 被大量容器共享，I/O 请求排队，CPU 等磁盘响应。内核上报为 `%wa`（iowait），但 top 里没有任何进程在"跑"。

**诊断步骤：**

```bash
# 1. 立即确认：top 看 wa 占比
top -bn1 | head -3
# %Cpu(s): 0.0 us, 50.0 sy, 0.0 ni, 0.0 id, 50.0 wa, 0.0 hi, 0.0 si, 0.0 st
#         ↑%us=0  ↑%sy=50     ↑%id=0    ↑%wa=50         ↑%st=0
# 关键特征: us≈0, id≈0, wa>30, st≈0

# 2. 验证：磁盘是否为 HDD
lsblk -d -o NAME,ROTA,SIZE,MODEL
# NAME  ROTA   SIZE
# vda     1    50G   ← ROTA=1 = 机械盘（HDD）
# vda     0    50G   ← ROTA=0 = SSD（问题不在此）

# 3. 负载解读
cat /proc/loadavg
# 3.06 2.67 2.60 1/1595 3763566
# 1 核机子负载 3+，但没有 CPU-bound 进程 → 全是 I/O 阻塞

# 4. iostat 确认磁盘瓶颈（需安装 sysstat）
iostat -x 1 3
# avg-cpu:  %user  %nice %system %iowait  %steal   %idle
#            0.0    0.0   50.0    50.0      0.0      0.0
# Device     r/s     w/s    rkB/s    wkB/s  await  svctm  %util
# vda      120.0  150.0   960.0   1200.0  450.0   3.0   80.0+
```

**与中断风暴的区别诊断：**

| 特征 | HDD I/O Wait | 中断风暴 |
|------|-------------|---------|
| 空闲(%id) | **≈0%** | >30% |
| iowait(%wa) | **>30%** | <2% |
| 系统CPU(%sy) | 30-50%（I/O 相关） | >20%（中断相关） |
| 用户CPU(%us) | ≈0% | 10-30% |
| 中断/s | 正常 <5K | >50K |
| 根因 | `ROTA=1` 机械盘 | cloudflared + virtio |
| 处理方式 | **无解**，母鸡硬件限制 | 可忽略或缓解 |
| 适用场景 | 超廉价玩具 LXC（¥10/年） | 所有 LXC 跑 cloudflared |

**结论：** 如果 `%id≈0` + `%wa>30` + `ROTA=1`，这是母鸡 HDD 性能天花板造成的"假高 CPU"，**软件层面无法解决**。唯一方案是换 SSD 母鸡的 VPS 或升级套餐。

### CPU 负载虚高诊断（LXC 中断风暴 — 面板/agent 密集型）

**现象：** 1 核 LXC 容器，load average 高达 3~13，`%sy`（系统CPU）> 20%，但空闲仍有 20%+。

**根本原因：** 不是 CPU 算不过来，而是 **网络中断密集**。LXC 共享内核 + virtio 网络设备，当容器内有多个服务产生频繁的网络 I/O（HTTP 请求/响应、TLS 加密、脚本触发），内核中断处理占满 CPU 时间片。

**⚠️ cloudflared 的常见误解：** cloudflared 本身 **CPU 消耗几乎为零**（实测长期稳定 0.0% CPU，内存 ~24MB）。高 `%sy` + `%si` 的真正来源通常是 **面板服务**（komari server 处理 HTTP 请求、ip_sentinel 执行脚本循环、Telegram bot 长轮询），而不是 cloudflared 隧道。不要习惯性把高 sy/si 归因于 cloudflared。

**诊断步骤：**

```bash
# 1. 看区分度：CPU 空闲（%id）vs 系统 CPU（%sy）
#    空闲 > 20% + 系统 CPU > 20% = 网络中断密集型负载
top -bn1 | head -5
# %Cpu(s): 13.3 us, 53.3 sy, 0.0 ni, 20.0 id, 0.0 wa, 13.3 si, 0.0 st
#         ↑用户    ↑系统      ↑空闲     ↑IOwait ↑软中断

# 2. 确认不是 I/O wait（与 HDD 瓶颈区分）
# 特征：id>20% + wa<2% ≈ 网络/服务型负载（不是磁盘问题）
# 特征：id≈0% + wa>30% ≈ HDD I/O 瓶颈（见上一节）

# 3. 看中断频率（vmstat 的 in 列）
vmstat 1 3
# in 列 > 50K/秒 = 中断密集
# 正常值 < 5K/秒

# 4. 锁定高 CPU 进程
ps aux --sort=-%cpu | head -8
# 重点关注 komari server / agent / ip_sentinel / cloudflared

# 5. 验证 cloudflared 实际消耗（别猜，看数据）
ps -o cputime,%cpu,rss,pid,comm -p $(pgrep -f cloudflared | head -1)
# cputime=32:00 (累计CPU时间), %cpu=0.0 (实时), RSS=23980 (24MB)

# 6. 看 iostat 确认不是磁盘瓶颈
iostat -x 1 2
# %iowait < 2% 说明磁盘没问题
```

**常见贡献者（按场景分类）：**

| 场景 | 主要贡献者 | 特征 |
|------|-----------|------|
| **挖矿木马**（新） | **XMRig** 伪装为 systemd/kworker | %us>70, %id≈0, %wa≈0, %si≈0, 高 RES 内存 |
| 主控面板机（komari server + web + agent） | **komari server** HTTP 处理、**ip_sentinel** 脚本循环、**TG bot** 长轮询 | sy>40%, si>10%, id<30% |
| 纯 agent 节点（只跑一个 agent） | **komari agent** 定期上报 | sy<20%, id>60% |
| 纯 cloudflared 隧道 | cloudflared 约 0% CPU, ~24MB 内存 | 几乎不影响 CPU |
| ip_sentinel 主控 | 循环执行 shell 脚本 + curl webhook | sy 波动大，us 低 |

> ⚠️ **挖矿木马症状与中断风暴/IOwait 区分**：挖矿是唯一种 %us>70 且 %id≈0 的情况。IOwait 是 %wa>30, %us≈0。中断风暴是 %sy>30, %id>20。详见 system-hardening skill 的「挖矿木马检测与清除」。

| 场景 | 主要贡献者 | 特征 |
|------|-----------|------|
| 主控面板机（komari server + web + agent） | **komari server** HTTP 处理、**ip_sentinel** 脚本循环、**TG bot** 长轮询 | sy>40%, si>10%, id<30% |
| 纯 agent 节点（只跑一个 agent） | **komari agent** 定期上报 | sy<20%, id>60% |
| 纯 cloudflared 隧道 | cloudflared 约 0% CPU, ~24MB 内存 | 几乎不影响 CPU |
| ip_sentinel 主控 | 循环执行 shell 脚本 + curl webhook | sy 波动大，us 低 |

**缓解方法：**
- 如果是**面板机**（56idc-la 类型）：这是正常现象，面板 + ip_sentinel + bot 三个服务在 1 核 LXC 上必然高 sy/si，20%+ 空闲说明还能撑
- 如果是**纯探针节点** sy 还高：检查是否有额外的 cron/脚本在跑
- 如果宿主机 E5 v2 太老（Ivy Bridge 2013），换新硬件是唯一根本解

### SSH 连接策略
- **用 paramiko.SSHClient**，不用 sshpass，避免所有 shell 管道符转义问题
- **每台服务器只建一条 SSH 连接**，所有命令打包执行，用 `echo '<<TAG>>'` 标记分割输出
- **不要**在 Python 的 subprocess 里跑 `python3 -c "..."` 来测试 paramiko（平台会拦截超时），测试时用 `terminal()` 调用独立脚本文件

### CPU 解析关键
从 `top -bn1` 输出中找 CPU 行，解析 `X.X id` 字段：
```python
m = re.search(r'([\d.]+)\s+id[, ]', cpu_line)
idle = float(m.group(1))
cpu_pct = round(100 - idle, 1)
```
注意：top 取样是瞬时值，idle=0 并不意味着持续 100% 负载，要看 `load average` 判断。

### 管道符处理
- **绝对不要**在 SSH 命令里用管道符 `|`，shell 解析行为不可预测
- 替代方案：
  - 用 `awk '/pattern/ {print}' file` 替代 `grep pattern file`
  - 用 `echo '<<TAG>>'; cmd1; echo '<<TAG2>>'; cmd2` 打包多个命令，用字符串标记分割输出
  - 任何需要管道的操作都在远程命令内完成（远程 shell 处理）

### fail2ban 日志路径问题
如果 fail2ban 启动失败且报错 `Have not found any log file for sshd jail`，说明：
- SSH 日志走 systemd journal（`journalctl`），没有物理文件 `/var/log/auth.log`
- 修复：在 `/etc/fail2ban/jail.local` 的 `[sshd]` 段加 `backend = systemd`
- 配置示例：
```
[sshd]
enabled = true
port = 你的ssh端口
backend = systemd
```
然后 `systemctl restart fail2ban`

## 维护操作

### UFW 安装/启用
**坑**：`apt install ufw` 可能报"已安装"但状态是 inactive。先检查：
```bash
which ufw           # 是否存在
ufw status verbose  # 是否 active
```
非 root 用户（如亚特兰大 woioeow）需 `sudo`，密码见 servers.yaml 或 `echo '密码' | sudo -S ufw enable`。

启用后必须放行 SSH 端口，否则锁死自己：
```bash
ufw allow <SSH端口>/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw enable
```

### Docker 清理
```bash
docker image prune -a --filter "until=168h" -f  # 清理7天未使用的镜像
docker system df  # 查看回收效果
```

## 端口扫描安全须知

**NEVER run nmap or port scanning tool against servers in this infrastructure** unless user explicitly asks. Port scanning triggers fail2ban and gets the current server's IP banned (~10 min).

### If you need to discover a port
- Ask the user directly
- If must scan: `-T5 --top-ports 5` with 5s timeout, not aggressive full scans

### Known SSH Ports (don't scan, just use)
- Buffalo (<纽约_IP>):27391
- Los Angeles-1 (<旧Master_IP>):58193
- Los Angeles-2 (<洛杉矶1_IP>):47283
- Santa Clara (<KS_IP>):63841
- Atlanta (<亚特兰大_IP>):23

---

## 已知问题

- 堪萨斯/纽约等 CPU 瞬时 100% 是真实值（idle=0），看负载（load average）判断是否持续高负载
- 纽约 fail2ban 需要配置 `backend = systemd` 才能正常工作
- health.py 的 `ufw status` 在未安装 UFW 的机器上会返回 "command not found"，需手动安装后重跑

## 56idc（<洛杉矶2_IP>）磁盘精简记录

**初始状态**：1.2G LXC，731M 已用（64%）
**目标**：保留 SSH + cloudflared + Komari agent，删除所有无用包

### 已清理项

| 操作 | 释放空间 | 日期 |
|------|----------|------|
| apt-get clean + rm /var/cache/apt/archives/*.deb | ~180M | 2026-05-04 |
| 删 gcc-12 g++-12 build-essential | ~96M | 2026-05-04 |
| 删 manpages manpages-dev | ~5M | 2026-05-04 |
| 删 vim + vim-common + vim-runtime | ~11M | 2026-05-04 |
| 删 python3-pip + autoremove 连带 dev 库 | ~112M | 2026-05-04 |
| 清 /usr/share/locale（只留 en/zh） | ~40M | 2026-05-04 |
| 清 /usr/share/doc 小文件 | ~3M | 2026-05-04 |
| 清 /tmp 临时文件 | ~15M | 2026-05-04 |
| 清 locale（仅保留 en_US zh_CN zh_TW） | ~40M | 2026-05-04 |
| 清 apt pkgcache/srcpkgcache | ~46M | 2026-05-04 |
| **累计释放** | **~490M** | |

**最终（2026-05-04）**：362M 已用（33%），741M 可用

### 小磁盘深度精简顺序（按大小排序）

```
1. /var/cache/apt/archives/*.deb        ~180M  apt-get clean
2. /usr/share/locale/                   ~40M   只留 en_US zh_CN zh_TW
3. /var/cache/apt/pkgcache.bin          ~23M   rm -f 后 apt update 重建
4. /var/cache/apt/srcpkgcache.bin       ~23M   rm -f 后 apt update 重建
5. /var/lib/apt/lists/                  ~32M   rm -rf 后 apt update 重建
6. gcc/g++/build-essential              ~96M   探针不需要编译器
7. python3-pip + autoremove            ~112M  探针不需要 pip
8. manpages/manpages-dev               ~5M
9. vim 相关                            ~11M
10. /usr/share/doc changelog             ~3M   改版记录用处不大
```

### perl 不可删——硬依赖链

`perl` 本包可删，但以下三个删了系统废：
- `perl-base` — 内核级依赖，连 libc6-dev 都靠它
- `libdpkg-perl` — dpkg 自身依赖，dpkg 跑 pre/postinst 脚本必须用 perl
- `libperl5.36` — 共享库

验证方法：
```bash
dpkg -l | grep perl       # 看装了哪些
apt-cache rdepends perl    # 看谁依赖 perl（列出的包都不在本地可接受删）
```

### /usr/share/man 仍残留 9.8M

之前清理过但仍有残余，可再清：
```bash
rm -rf /usr/share/man/zh* /usr/share/man/man[0-9]  # 只留部分常用
```

### locale 清理安全命令

```bash
mkdir -p /tmp/locale_keep
cp -r /usr/share/locale/en_US /tmp/locale_keep/
cp -r /usr/share/locale/zh_CN /tmp/locale_keep/
cp -r /usr/share/locale/zh_TW /tmp/locale_keep/ 2>/dev/null || true
rm -rf /usr/share/locale/*
cp -r /tmp/locale_keep/* /usr/share/locale/
rm -rf /tmp/locale_keep
```

### apt lists 重建后大小

`rm -rf /var/lib/apt/lists/*` 后 `apt update` 会重新拉取索引，压缩后 32M → 32M（没有净减少），但首次 `apt update` 期间磁盘会短暂翻倍膨胀，**操作前确保有足够可用空间**。

### 精简原则
- **编译行为本地化**：需要编译的程序在本地编译后传二进制，**绝不**在 1.2G LXC 上装 gcc/build-essential
- **pip 禁止**：探针不需要 pip，删
- **manpages 删**：没人用 man 查命令
- **locale 精简**：只保留 en 和 zh，其余删
- **perl 保留**：dpkg/系统脚本依赖 Perl

### 当前包清单（精简后）
以下包确认可安全删除（探针不需要）：
- `gcc g++ g++-12 build-essential`（已删）
- `python3-pip python3-dev python3.11-dev`（已删）
- `manpages manpages-dev`（已删）
- `vim vim-tiny vim-common vim-runtime`（已删，用 nano 替代）

### 仍需保留（系统依赖）
- `perl perl-base perl-modules-5.36`（dpkg 脚本依赖）
- `curl wget jq`（运维工具）
- `nano`（文本编辑）

## 参考文档

- `references/cpu-interrupt-storm.md` — CPU 中断风暴诊断（适用于 cloudflared + LXC 环境的高负载现象）
- `references/lxc-vs-kvm-probes.md` — LXC vs KVM 探针选型对比（邻居干扰显示方式、磁盘类型判断、选型建议）

## Komari Server 维护（在 DediRock 母机 <旧Master_IP>）

### auto_discovery_key 告警修复
日志持续报 `unmarshal config failed key=auto_discovery_key error=invalid character 'E' looking for beginning of value`。
原因：DB 里 `auto_discovery_key` 的值是裸字符串 `EFcLfyQ6qByKLprRXMOkaTWz`，Go 代码按 JSON 解析时 `E` 开头不合法。
修复：
```bash
sqlite3 /opt/komari/data/komari.db "UPDATE configs SET value = '\"EFcLfyQ6qByKLprRXMOkaTWz\"' WHERE key = 'auto_discovery_key';"
systemctl restart komari
```
加双引号包裹后 Go 的 JSON unmarshal 就能解析了。

### Komari Agent 状态检查
```bash
sqlite3 /opt/komari/data/komari.db 'SELECT name, ipv4, updated_at FROM clients;'
```
所有 agent 的 `updated_at` 应在最近 5 分钟内，否则 agent 断连。
