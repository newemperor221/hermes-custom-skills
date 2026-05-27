# IPv6-Only 节点管理 — SSH 跳板模式

部分 VPS/LXC 容器只有 IPv6 地址（无 IPv4），而管理机可能没有 IPv6 直连能力。需通过一台**双栈（IPv4+IPv6）的兄弟节点**作为 SSH 跳板。

## 场景

```
管理机 (仅有 IPv4) ──SSH──→ 跳板机 (双栈, LXC共有IPv6) ──SSH──→ 目标机 (仅有 IPv6)
```

## 操作步骤

### 前置条件

- 跳板机有 IPv6 可达目标机（`ping6 <target-ipv6>` 通）
- 跳板机安装了 `sshpass`（否则先安装：`apk add sshpass`）

### 1. 密钥分发（首次连接用密码）

```bash
# 生成统一管理密钥（如果还没有）
ssh-keygen -t ed25519 -f ~/.ssh/hermes_admin -N ""

# 上传公钥到跳板机
cat ~/.ssh/hermes_admin.pub | ssh -p <跳板机端口> root@<跳板机IP> \
  'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys'

# 复制私钥到跳板机（用于再跳到目标机）
ssh -p <跳板机端口> root@<跳板机IP> \
  'cat > ~/.ssh/hermes_jump && chmod 600 ~/.ssh/hermes_jump' \
  < ~/.ssh/hermes_admin

# 测试密钥登录跳板机
ssh -i ~/.ssh/hermes_admin -p <跳板机端口> root@<跳板机IP> "echo OK"
```

### 2. 首次连接目标机（密码登录）

```bash
# 经跳板机 SSH 到目标机（IPv6）
ssh -i ~/.ssh/hermes_admin -p <跳板机端口> root@<跳板机IP> \
  "sshpass -p '<目标机密码>' ssh -o StrictHostKeyChecking=no -6 root@<目标机IPv6> 'hostname; uptime'"
```

⚠️ **密码特殊字符处理**：`$` `%` `!` `#` 等字符可能在 shell 中被解释。用单引号包裹，或用 `sspass -f` 从文件读取。

### 3. 安装密钥到目标机

```bash
cat ~/.ssh/hermes_admin.pub | ssh -i ~/.ssh/hermes_admin -p <跳板机端口> root@<跳板机IP> \
  "sshpass -p '<目标机密码>' ssh -o StrictHostKeyChecking=no -6 root@<目标机IPv6> \
    'mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys && echo KEY_INSTALLED'"
```

### 4. 测试密钥登录

```bash
ssh -i ~/.ssh/hermes_admin -p <跳板机端口> root@<跳板机IP> \
  "ssh -i ~/.ssh/hermes_jump -o StrictHostKeyChecking=no -6 root@<目标机IPv6> 'echo KEY_OK; hostname; uptime'"
```

### 4b. 启用 SSH 远程端口转发（如需代理 agent 流量）

如果目标机是 IPv6-only 而管理服务器是 IPv4-only，需要用 SSH 远程端口转发打通 agent 连接。**目标机的 sshd 默认可能禁止端口转发：**

```bash
# 检查是否被禁用
grep AllowTcpForwarding /etc/ssh/sshd_config

# 如果输出 "AllowTcpForwarding no"，改成 yes
sed -i 's/^AllowTcpForwarding no/AllowTcpForwarding yes/' /etc/ssh/sshd_config
rc-service sshd restart

# 建立远程端口转发（从跳板机发起连接）
# 目标机上的端口 X → 通过跳板机 → 管理服务器 IP:端口
ssh -i ~/.ssh/hermes_jump -o StrictHostKeyChecking=no -6 -N -R <TARGET_PORT>:<MGMT_IP>:<MGMT_PORT> root@<目标机IPv6>

# 在目标机上验证端口已建立
ss -tlnp | grep <TARGET_PORT> || netstat -tlnp 2>/dev/null | grep <TARGET_PORT>
```

⚠️ 原理：`-R` 让 SSH 服务器（目标机）监听端口，转发到 SSH 客户端（跳板机）指定的地址。适用于目标机能发起 SSH 连接且跳板机/管理服务器可达的场景。

限制：
- `AllowTcpForwarding` 必须在目标机 sshd_config 中设为 `yes`（默认 `no`）
- ULA IPv6 地址（以 `fd` 开头）在不同 LXC 主机间可能不可达
- 管理服务器只有 ULA IPv6 而目标机只有公网 IPv6 时，端口转发可能不通

### 5. 加固目标机 SSH

```bash
ssh -i ~/.ssh/hermes_admin -p <跳板机端口> root@<跳板机IP> \
  "ssh -i ~/.ssh/hermes_jump -o StrictHostKeyChecking=no -6 root@<目标机IPv6> '
cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak 2>/dev/null
sed -i \"s/^#*PasswordAuthentication.*/PasswordAuthentication no/\" /etc/ssh/sshd_config
sed -i \"s/^#*PermitRootLogin.*/PermitRootLogin prohibit-password/\" /etc/ssh/sshd_config
sed -i \"s/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/\" /etc/ssh/sshd_config
rc-service sshd restart 2>&1 | tail -2
echo SSH_DONE
'"
```

### 6. 验证加固

```bash
ssh -i ~/.ssh/hermes_admin -p <跳板机端口> root@<跳板机IP> \
  "ssh -i ~/.ssh/hermes_jump -o StrictHostKeyChecking=no -6 root@<目标机IPv6> '
grep -E \"PasswordAuthentication|PermitRootLogin\" /etc/ssh/sshd_config
'"
```

## 真实案例

| 跳板机 | 目标机 | 说明 |
|--------|--------|------|
| 56idc 洛杉矶 (<洛杉矶2_IP>:42185) | 将军鸡 (2001:470:e2db:100:0:5459:389:6b27:22) | 同为无聊云/欢乐云 LXC，共享 IPv6 内网，跳板可达 |

## 注意事项

- 跳板机自身也要先加固（密钥+关密码），否则跳板被攻破则目标机全暴露
- 目标机加固后，跳板机上的 `hermes_jump` 私钥仍然可用——保持跳板机安全即可
- 如果目标机重装（系统重置），需要重新走一遍全部流程
