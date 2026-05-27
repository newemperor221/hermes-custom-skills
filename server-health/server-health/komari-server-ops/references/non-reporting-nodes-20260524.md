# 非上报节点排查记录（2026-05-24）

## 三节点离线排查

用户反馈三个节点在面板上显示为零资源（0% CPU/内存/硬盘/网络流量）。

### 1. 无聊云测试 | 台湾（TW）— ✅ 已修复

- **IP**: <台湾_IP>
- **内部 IP**: 10.171.50.145（GCP 内网地址）
- **SSH 端口**: 2222（直接拒绝）→ **43590**（接受 keyboard-interactive + publickey）
- **Ping**: ✅ 152ms (from NL主控)
- **系统**: Alpine Linux LXC（无 systemctl/journalctl/bash，使用 sh + OpenRC）
- **Agent 状态**: 二进制 `/opt/komari/agent` 存在但未运行
- **Root cause**: Agent 进程不存在（非安装问题，是进程挂了）

#### 修复过程

```bash
# 1. 关键发现：SSH 端口是 43590（不是 22 也不是 2222）
# 之前试 2222 端口返回 Connection refused
# 而 43590 端口接受 keyboard-interactive + publickey 认证

# 2. 密钥直接用 ssh -i 失败，但加入 ssh-agent 后成功
eval $(ssh-agent -s)
ssh-add ~/.ssh/hermes_admin
ssh -o StrictHostKeyChecking=no -p 43590 root@<台湾_IP> "hostname"
# → lxd1145111041938 ✅

# 3. 确认 agent 二进制存在，但不是 running 状态
ls -la /opt/komari/agent  # 11MB agent 二进制
ps aux | grep komari       # 无进程

# 4. 从面板获取正确的安装命令
# 面板 → Server → 搜索"台湾" → Install command →
# wget -qO- ... install.sh | sudo bash -s -- -e https://<监控面板域名> -t gcp-us-agent

# 5. Alpine 无 bash，直接启动现有二进制
nohup /opt/komari/agent -e https://<监控面板域名> -t gcp-us-agent > /opt/komari/agent.log 2>&1 &
# Agent 1.2.0 启动成功，获取 IPV4 <台湾_IP> 和 IPV6

# 6. 设置开机自启（Alpine OpenRC 方式）
echo '/opt/komari/agent -e https://<监控面板域名> -t gcp-us-agent > /opt/komari/agent.log 2>&1 &' > /etc/local.d/komari.start
chmod +x /etc/local.d/komari.start
rc-update add local default
```

#### SSH 密钥发现

- `hermes_admin` 密钥对台湾 43590 端口 `root` 用户有效
- 关键：直接 `ssh -i ~/.ssh/hermes_admin` 失败，必须 `ssh-add` 加入 agent 后才成功
- 这种现象可能是因为 OpenSSH 版本差异或代理认证策略导致

### 2. isvoro | 首尔（KR）— ⏳ 待修复

- **IP**: <首尔_IP>
- **SSH 端口**: 22（开放，所有密钥/用户名组合均 Permission denied）
- **Ping**: ✅ 133ms (from NL主控)
- **Komari Agent 端口 (35776)**: ❌ Connection refused
- **结论**: Agent 未运行。SSH 能连但密钥不匹配。

### 3. 欢乐云 | 平壤（KP / 将军鸡）— ⏳ 待修复

- **IPv6**: 2001:470:e2db:100:0:5459:389:6b27
- **状态**: 账单已过期（¥2/Monthly Expired）
- **连通性**: IPv6 主控不可达
- **跳板**: 需经 56idc-la（无聊云|洛杉矶）中转，SSH 端口 2222
- **结论**: 过期停服，续费 + 面板重启才能恢复

## 已知 SSH 密钥清单

| 密钥文件 | 生效节点 | 说明 |
|---------|---------|------|
| `id_ed25519` | 本机 | 本机的 authorized_keys |
| `hermes_admin` | 台湾 GCP (<台湾_IP>:43590 root) | 需先 `ssh-add` 加入 agent 才能用 |
| `hermes_admin` | 56idc-la / 将军鸡（已知，端口 2222） | 当前 56idc-la 端口 2222 不可用 |
| `id_rsa` | 未知 | 均无效 |

## 关键经验

1. **SSH 端口发现**：GCP VM 用 43590 端口，非标准。先用 `nc -zv <IP> 22 2222 43590` 扫
2. **ssh-agent 问题**：直接 `ssh -i` 可能失败但 `ssh-add` 后成功。标准做法：`eval $(ssh-agent -s); ssh-add ~/.ssh/hermes_admin; ssh user@host`
3. **Alpine LXC agent 恢复**：无 systemd，binary 在 `/opt/komari/agent`，用 nohup + `/etc/local.d/` 管理启动
4. **面板获取 endpoint/token**：Server 列表 → 搜节点名 → 点 Install command
