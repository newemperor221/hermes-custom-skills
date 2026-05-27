# 挖矿木马真实案例 — 荷兰机 2026-05-18

## 时间线

| 时间 (UTC) | 事件 |
|------------|------|
| 5月16日 16:00 | **首次入侵** — 攻击者 165.154.155.174 (UCloud HK) 首次密码登录成功 (messages.0 日志确认，之前版本误记为 5月17日) |
| 5月17日 ~12-13 (文件时间) | 矿机配置文件 `.config.json` / `config.json` 被上传 |
| 5月16日 16:00 ~ 5月18日 14:13 | **持续 46 小时** — 攻击者登录 **87 次** (33次在 messages.0 + 54次在 messages)，平均每 ~30 分钟一次。每次登录 2-3 个并发 SSH 会话、连接仅持续数秒（登录→检查→断开） |
| 5月18日 13:01 | 上传 `free_proc.sh`（反竞争脚本）和最新版 `systemd` 矿机二进制 |
| 5月18日 13:02 | 矿机启动，`systemd` 进程 PID 1006637 |
| 5月18日 13:27 | **第一次清除** — kill 进程 + 删除 /root/.sys-cache/ |
| 5月18日 13:29 | SSH 加固（改配置但 sshd 重启失败—路径用错） |
| 5月18日 14:13 | **矿机复活！** 攻击者再次用密码登录（sshd 没重启成功），重新上传矿机 |
| 5月18日 15:22 | **第二次清除** — kill 新进程 PID 1029496，保留证据文件，iptables 封禁攻击者 IP |
| 5月18日 15:22 | SSH 加固真正生效（`/usr/sbin/sshd -t` 验证后重启） |

## 关联节点检查

发现荷兰鸡中招后，检查并加固了同网络中其他 5 台 Alpine LXC：

| 节点 | IP | 端口 | 状态 |
|------|-----|------|------|
| 56idc 洛杉矶 | 107.172.231.70 | 42185 | 干净 ✅ |
| GCP 台湾 | 35.189.164.32 | 43590 | 干净 ✅（刚重装） |
| isvoro 首尔 | 146.56.191.86 | 10260 | 干净 ✅ |
| isvoro 新加坡 | 140.245.97.144 | 10425 | 干净 ✅ |
| 将军鸡 | 2001:470:e2db:100:0:5459:389:6b27 | 22 | 已重装 ✅ |

5 台均未发现矿机，但全部统一做了 SSH 密钥加固 + 禁用密码。

### 将军鸡特殊处理

将军鸡（欢乐云 | 平壤）最初已断联 5 天（LXC 容器内 sshd 崩溃，ping 通但端口拒绝）。用户从管理面板重装后才恢复。它只有 IPv6，管理机无 IPv6 直连能力，需经 56idc 洛杉矶（同为无聊云 LXC，共享 IPv6 内网）做 SSH 跳板：

```bash
# 跳板流程
管理机 → SSH → 56idc(双栈) → SSH(IPv6) → 将军鸡
```

详见 `references/ipv6-jumpbox.md`。

## 感染服务器详情

- **机器**：无聊云 | 阿姆斯特丹（波兰主控），31.58.51.127:46748
- **OS**：Alpine Linux v3.22.2 LXC
- **资源**：1核 488MB RAM，LXC 容器
- **入口**：SSH root 密码认证（PermitRootLogin yes + PasswordAuthentication yes）
- **密码**：OX8w$nE9A%tfqb6v（来自 SSH 凭证泄露/撞库）

## 矿机详情（第一次，May 17）

- **二进制路径**：`/root/.sys-cache/systemd`（3.1MB）
- **运行名**：`systemd` — 伪装成系统守护进程
- **配置**：`/root/.sys-cache/config.json` + `.config.json`
- **矿池**：`xmr.kryptex.network:8029`（Kryptex 算力平台，TLS 加密）
- **钱包地址**：`47S6DU9Qm3K848Krv6fAfZGgRn75653nbEPMxx3CYrWXBeTYnttJaWCDxDErGhH53u2cmbwahUymzPx71qDPneMsGjQ5pj4`
- **CPU 参数**：`--cpu-max-threads-hint=100`（吃满单核）
- **线程数**：`-t 1`（单线程）
- **资源消耗**：81.8% CPU + 273MB RAM（54.6%）

## 矿机详情（第二次，May 18 14:13 — 复活版）

- **二进制路径**：同上 `/root/.sys-cache/systemd`
- **大小**：3,149,464 bytes
- **SHA256**：`baca0922a6ce82f250d15c7b71a209f0ba60274ff7e9654338900020a36de6c4`
- **UPX 加壳**：ELF 64-bit LSB executable, **UPX packed**（`$Info: This file is packed with the UPX executable packer http://upx.sf.net $`）
- **无配置文件**：第二次入侵没带 config.json，所有参数走命令行
- **XMRig 版本**：6.25.0（从 pool dashboard 的 Worker 详情确认）
- **手法变化**：UPX 加壳避免杀软特征码检测 + 无配置文件减少痕迹

### UPX 加壳分析

攻击者用 UPX（Ultimate Packer for eXecutables）加壳的目的：
1. 文件缩小 60%+（上传更快，带宽费用更低）
2. 绕过基于静态签名的检测（不同版本的 UPX packer 产生不同 hash）
3. 字符串混淆（矿池 URL、钱包地址等敏感字符串被压缩，`strings` 输出几乎全是乱码）
4. 反 forensic — 只有 `IG_VERSION` 和 `UPX!` 等少数字符串暴露

检测方法：`strings` 输出中搜索 `UPX` 和 `$Info: This file is packed with` 即可确认。

### 二进制深度分析（UPX 解包后）

解包工具：UPX 4.2.4
解包前后体积：3,149,464 bytes → 8,350,988 bytes（37.67% 压缩率）

#### 编译环境

| 属性 | 值 |
|------|-----|
| 编译时间 | `built on Mar 28 2026 with GCC`（约1.5个月前） |
| 编译器 | `GCC: (Alpine 13.2.1_git20231014) 13.2.1 20231014` |
| 编译系统 | **Alpine Linux**（musl libc，非 glibc） |
| 编译用户 | `buildbot`（自动化流水线） |
| 构建路径 | `/home/buildbot/xmrig/scripts/build/hwloc-2.12.1/` |
| 链接方式 | **静态链接**（`There is no dynamic section in this file`）— 无外部依赖，任何 Linux x86_64 上都能跑 |
| 符号表 | stripped |
| ELF 特征 | ELF 64-bit LSB executable, x86-64, statically linked, stripped |
| Build ID | `c746d5445679e29ea09a8ae5bdc7fbbbf3720c44` |
| CPU 指令集 | x86-64-v4 (AVX-512), XMM, YMM, ZMM, XSAVE |

编译环境推断：攻击者使用 Alpine Linux 的 buildbot 自动编译最新 XMRig，静态链接 musl libc，输出体积比 glibc 静态链接更小。

#### 版本识别

**矿池页面显示** → `XMRig/6.25.0`（可能只读了二进制中某个版本字符串）
**strings 分析确认** → `XMRig 6.26.0` ✅（实际编译版本）

版本差异可能是因为编译时改了版本号，或者矿池读取了不同的版本字段。

#### 硬件功能支持（字符串分析）

解包后 `strings` 确认支持：
- RandomX（门罗币专属算法）
- KawPow（RVN 算法）
- Argon2 / Argon2d / Argon2i / Chukwa / Chukwav2
- 1GB 大页 / 2MB 大页
- MSR 寄存器调优（`/dev/cpu/{}/msr`）
- AES-NI 硬件加速
- TLS 1.3（内嵌 CA 证书链）
- hwloc 2.12.1（CPU 拓扑检测）

#### 无魔改确认

标准 XMRig 代码，未发现后门、挖矿劫持之外的恶意载荷。所有矿池/钱包参数走命令行，二进制本身是干净的原版 XMRig。

#### 分析操作步骤

```bash
# 1. 从被黑机子拉回文件（不要在被黑机上做分析！）
scp -P 46748 root@<IP>:/root/.sys-cache/systemd /tmp/evidences/

# 2. 确认 UPX 加壳
strings /tmp/evidences/systemd | grep -i upx
# 输出: $Info: This file is packed with the UPX executable packer

# 3. 下载 UPX 解包
# 从 https://github.com/upx/upx/releases 下载对应架构的 UPX
wget https://github.com/upx/upx/releases/download/v4.2.4/upx-4.2.4-amd64_linux.tar.xz
tar xf upx-*.tar.xz
./upx-*/upx -d /tmp/evidences/systemd -o /tmp/evidences/systemd.unpacked

# 4. 解包后分析
file /tmp/evidences/systemd.unpacked
strings /tmp/evidences/systemd.unpacked | grep -iE 'XMRig|[0-9]+\.[0-9]+\.[0-9]+|built on|GCC|glibc|musl' | sort -u
sha256sum /tmp/evidences/systemd*
readelf -n /tmp/evidences/systemd.unpacked  # Build ID

# 5. VirusTotal 交叉查询
# UPX版SHA: baca0922...
# 解包版SHA: b20f39fc...
# Build ID: c746d544...
# 这三个标识符可全网搜索关联其他受害者
```

#### 关键发现用途

| 发现 | 价值 |
|------|------|
| Build ID | 唯一标识该二进制，可关联多台受害机 |
| 编译时间 (Mar 28) | 攻击者持续活动至少1.5个月 |
| Alpine musl 编译 | 攻击者使用 Alpine 作为构建环境（不常见，缩小体积） |
| SHA256 UPX/解包版 | 提交给安全社区/IoC 平台

### 反竞争机制

`/root/.sys-cache/free_proc.sh`：
```bash
while true; do
    ps -eo pid,pcpu,args | awk '$2 > 200 && !/systemd/ {print $1}' | xargs -r kill -9
    sleep 2
done
```
每 2 秒杀一次任何 CPU >200% 的非 systemd 进程，防止其他矿工抢占资源。
这也解释了为何攻击者要反复登录检查——free_proc.sh 也可能被对手 kill。

## 矿机复活原因（关键教训）

第一次 kill 后矿机又活了，因为：

1. **`sshd -t` 失败被忽略**：Alpine 上 `/sbin/sshd` 不存在，正确路径是 `/usr/sbin/sshd`
2. **`UsePAM no` 在 Alpine 上不兼容**：配置文件里有 Alpine OpenSSH 不支持的 UsePAM 选项
3. **`rc-service sshd restart` "成功"却没生效**：OpenRC 实际上没重启成功，但没报错
4. **密码认证仍然开着**：所以攻击者 14:13 又能用密码登录
5. **文件被删了**：第一次 cleanup 删除了 `/root/.sys-cache/`，新矿机带"干净"文件重新进来

**教训**：
- Alpine 上一定要用 `/usr/sbin/sshd -t` 验证配置，然后 `rc-service sshd restart`
- 改完配置后先开新终端测试连接通过再关旧会话
- 不要急着删证据文件——改名保留或用 tar 打包再删

## 日志取证

### 登录审计（Alpine /var/log/messages）

```bash
# 全部已接受连接 IP 统计
cat /var/log/messages | grep 'Accepted password' | sed 's/.*from //' | sed 's/ port.*//' | sort | uniq -c | sort -rn
# 609 198.46.147.71     ← 运维本机（CCS LA2）
#  84 165.154.155.174   ← 攻击者（UCloud HK）
# 0 次 Failed password → 说明不是暴力破解，是密码直接泄露
```

### 攻击者行为模式

- 每次登录 2-3 个 SSH 会话（脚本化）
- 每次连接持续仅数秒（登录→检查→断开）
- IP geolocation：香港 UCloud（AS135377）
- 无暴力破解痕迹（日志中 0 次 Failed password）
- **87 次成功密码登录，密码被正确使用而非暴力破解**

### SSH 密钥泄露评估

**结论：本机无 SSH 私钥可供偷窃。**

审计结果：
- `/root/.ssh/` 目录仅有 `authorized_keys`（公钥，无法反推私钥）和 `known_hosts`
- 无 `id_rsa`、`id_ed25519` 或任何 `*.pem` 私钥文件
- 跳板机（ccs-la2）的私钥**不在**这台服务器上
- 因此攻击者无法通过这台机器扩散 SSH 到其他服务器

**已暴露的其他凭据（需更换）：**
- ip_sentinel Telegram Bot Token（`master.conf` 明文）
- cloudflared tunnel token（ps aux 可见）
- Komari 管理密码
- `/root/data/secret.key`（44字节，疑似 WireGuard 密钥）

## 修复操作

### 第一次（13:27 — 不完整）

1. Kill 矿机进程：`kill -9 1006637`
2. 删除木马目录：`rm -rf /root/.sys-cache/`  ← **错误！用户想要保留证据**
3. SSH 加固配置改了但未生效（sshd 没重启成功）

### 第二次（15:22 — 完整）

1. Kill 矿机进程：`kill -9 1029496`
2. **保留证据文件**：`/root/.sys-cache/` 完整保留（systemd + free_proc.sh）
3. SSH 加固：
   - `PasswordAuthentication no`
   - `PermitRootLogin prohibit-password`
   - 删除 `UsePAM no`（Alpine 不支持）
   - `/usr/sbin/sshd -t` 验证 → `rc-service sshd restart`
4. iptables 封禁攻击者 IP：`iptables -A INPUT -s 165.154.155.174 -j DROP`
5. fail2ban 启动验证
6. 矿池验证：Kryptex pool 搜钱包地址，确认 "systemp" worker 算力下降

### 恢复后验证

```bash
# 验证 SSH 加固
ssh -o PasswordAuthentication=yes root@localhost "echo test"  # → Permission denied (publickey)
ssh -o PreferredAuthentications=publickey root@localhost "echo OK"  # → OK

# 验证 iptables 封禁
iptables -L INPUT -n --line-numbers | grep DROP  # → 应有 DROP all -- 165.154.155.174

# 验证 fail2ban
fail2ban-client status sshd  # → Currently banned/Banned IP list

# 验证 CPU/内存恢复
top -bn1 | head -3  # idle > 90%
free -m             # used < 100MB

# 验证 Kryptex pool
# 搜索钱包地址 → worker "systemp" 的 30min hashrate 持续降至 0
```

## 攻击者钱包（Kryptex Pool 取证）

### 钱包数据（查询时间 2026-05-18 15:20 UTC）

| 项目 | 数值 |
|------|------|
| 未支付余额 | 0.094969 XMR ≈ **$36.43** |
| 累计已提现 | 0.801242 XMR ≈ **$307.32** |
| 7天收益 | 0.048991 XMR ≈ $18.79 |
| 30天收益 | 0.241896 XMR ≈ $92.78 |
| 在线矿机 | 3台 |

### Worker 列表（清除前）

| 矿机名 | 30min 算力 | 24h 算力 | 版本 | 推测 |
|--------|-----------|---------|------|------|
| worker | 132.61 KH/s | 108.94 KH/s | XMRig/6.26.0 | 主力服务器（25-50核） |
| systemp | 1.00 KH/s ↓ | 1.13 KH/s | XMRig/6.25.0 | 荷兰鸡（已 kill，算力在降） |
| u7reyy-4C | 317.70 H/s | 378.29 H/s | XMRig/6.24.0 | 超售 ARM 或超低配 VPS |

### 版本分析

不同 worker 用不同 XMRig 版本说明不是批量部署的，而是不同时间感染的不同机器：
- 6.24.0（最老）→ u7reyy，约2-3个月前
- 6.25.0 → systemp，最近
- 6.26.0（最新）→ worker，可能自购机器一直开着自动更新

---

## 攻击者机器侦察（165.154.155.174 端口扫描结果）

**扫描时间**：2026-05-18 13:47 UTC
**工具**：nmap 7.93 TCP Connect 扫描 Top 1000 端口

| 端口 | 状态 | 服务 | 版本/详情 |
|------|------|------|-----------|
| 22/tcp | ✅ 开放 | OpenSSH | 9.6p1 Ubuntu 3ubuntu13.16 |
| 80/tcp | ✅ 开放 | HTTP | Caddy httpd（返回全路径 200 空响应） |
| 443/tcp | ❌ 关闭 | - | - |
| 其余 997 端口 | 🚫 过滤 | - | iptables DROP |

### SSH 指纹

```text
ECDSA:   ee09 2a2f 2f55 41a8 fbc0 132b 1399 b21a
ED25519: 375d 1891 08cf 4060 e451 2db9 6127 cd8f
```

### Web 行为

所有路径（`/` `/admin` `/login` `/panel` `/dashboard` `/manager` `/api` `/miner` `/stats`）均返回 **HTTP 200 空响应**（Content-Length: 0），Server 头为 `Caddy`。符合 Caddy 空响应反向代理配置特征——可能是 C2 面板，仅对授权客户端返回实际内容。

### 结论

一台 UCloud 香港的专用攻击跳板机：Ubuntu + OpenSSH 9.6p1 + Caddy 反代。同 IP 段 `165.154.206.139` 在 AbuseIPDB 有 13,463 次举报。
