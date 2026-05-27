---
name: cloudflare-tunnel-ops
description: Cloudflare Zero Trust Tunnel（cloudflared）全栈运维——tunnel 部署、ingress 路由排障、缓存策略、开隧道的步骤。触发："tunnel断了"、"cloudflare 404"、"ingress"、"stat.357561.xyz 打不开"、"cloudflared"。
---

# Cloudflare Tunnel 运维

## 用户环境

- **cloudflared 版本**：荷兰主控(Alpine 3.22 LXC) 2026.5.0；1c2.5g洛杉矶(Debian) 2026.3.0
- **管理方式**：`--token` 模式（无本地 config.yml，ingress 规则在 Cloudflare Zero Trust Dashboard 配置）
- **服务类型**：
  - Alpine：OpenRC init.d 服务（`/etc/init.d/cloudflared`）
  - Debian：systemd 服务（`/etc/systemd/system/cloudflared.service`）
- **tunnel 类型**：Cloudflare Zero Trust Tunnel

### 服务分布

**荷兰主控** (31.58.51.127:46748, Alpine LXC, `~/.ssh/hermes_admin` 密钥)
| 子域名 | 后端服务 | 端口 |
|--------|---------|------|
| `stat.357561.xyz` | galaxy-proxy.py → Komari 面板 | `127.0.0.1:25774` → `127.0.0.1:25776` |
| `drive.357561.xyz` | WebDAV 网盘 | 配置在 Zero Trust Dashboard |
| `tz.357561.xyz` | 探针 | 配置在 Zero Trust Dashboard |

**1c2.5g洛杉矶** (155.94.180.55:58193, Debian)
| 子域名 | 后端服务 | 端口 |
|--------|---------|------|
| `ai.357561.xyz` | ds-free-api | `localhost:22217` |

### 命令

```bash
# 状态查看
rc-service cloudflared status

# 启动/停止/重启
rc-service cloudflared start|stop|restart

# 查看进程
ps aux | grep cloudflared

# 查看日志
cat /var/log/cloudflared*.log 2>/dev/null || ls /var/log/ | grep cloudflared
# 或直接看 stderr（cloudflared 后台输出到日志文件）
```

## 场景一：页面 404（ingress 路由问题）

### 根因
Cloudflare Tunnel 的 ingress 规则在 [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/) 配置，不在服务器本地。如果 dashboard 上某个子域名没有正确指向后端，就会返回 404。

### 排障步骤

1. **确认 cloudflared 在运行**：`ps aux | grep cloudflared | grep -v grep`
2. **确认后端服务在监听**：`ss -tlnp | grep <port>` 或 `curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:<port>/`
3. **检查 ingress 路由**：登录 Cloudflare Zero Trust Dashboard → Networks → Tunnels → 选择对应 tunnel → 检查 ingress rules
4. **公共路径和私有路径的差异**：`/instance/xxx` 可能在内网正常（curl localhost）但外网 404，说明 ingress rule 没配对该路径

### 修复
- 修改 Cloudflare Dashboard 上的 ingress 规则
- 子域名必须匹配 Host header
- 路径必须匹配 URL path

## 场景二：Cloudflare CDN 缓存导致旧内容（非 cloudflared）

### ⚠️ 重要区分
**cloudflared 本身没有缓存功能。** cloudflared 只是一个安全的隧道代理，将所有流量透传到后端服务，不做内容缓存。

如果页面显示了旧内容，原因是 Cloudflare 的 **CDN proxy（橙色云 DNS）** 缓存了响应，而不是 cloudflared。

### 问题
通过 `stat.357561.xyz`（启用了 Cloudflare proxy）修改 `index.html` 后，用户看到的是旧版本，因为 Cloudflare CDN 边缘节点缓存了页面。

cloudflared 直连（DNS only/灰色云模式）不会有此问题。

### 解法
1. **硬刷新**：通知用户 `Ctrl+Shift+R`（完全绕过浏览器缓存）
2. **清除 CDN 缓存**：Cloudflare Dashboard → Caching → Purge Everything（或按 URL 逐条清除）
3. **绕过 CDN 验证**：如果怀疑是 CDN 缓存，用 `curl` 直连源站（通过 cloudflared tunnel 直连，不走 CDN）：
   ```bash
   # 在服务器上测试本地响应
   curl -sI http://localhost:<port>/path
   # 或使用 DNS-Only 模式的备用域名
   ```
4. **注意**：即使服务器文件已更新，Cloudflare CDN 边缘节点可能仍服务旧缓存（最长取决于 Cache-Control max-age 或默认 TTL）
5. **偷跑开发**：MIME 类型问题（JS 返回 text/html 等）不是缓存造成的——如果代理没正确分发路由，即使无 CDN 也会出问题。排查时先确认本地 `curl -D-` 返回正确头，再排查 CDN 层。

## 场景三：tunnel 断开

### 检查
```bash
# 进程仍在运行？
ps aux | grep cloudflared | grep -v grep

# 如果进程不在，重启
rc-service cloudflared restart

# 如果进程在但隧道不通，检查日志
ls -la /var/log/ | grep cloudflared
cat /var/log/cloudflared.err 2>/dev/null | tail -20

# 检查连接数（正常应有 3-4 条 Registered tunnel connection）
grep -c "Registered tunnel connection" /var/log/cloudflared.err 2>/dev/null

# Alpine：journalctl 不可用，日志在 /var/log/cloudflared.{log,err}
# Debian：可用 journalctl -u cloudflared --since "1 hour ago"
```

### 恢复
```bash
rc-service cloudflared restart

# 如果是 Alpine 用系统中的 service 命令
/etc/init.d/cloudflared restart
```

### 触发断线的常见原因

- **DNS 超时（Alpine LXC 常见）**：cloudflared 需要解析 `region1.v2.argotunnel.com`（Cloudflare Edge），若 Alpine 容器的 DNS 配置不稳定或上游 DNS 超时，会报：
  ```
  ERR Failed to refresh DNS local resolver error="lookup region1.v2.argotunnel.com: i/o timeout"
  ```
  然后连接逐个断开，日志出现：
  ```
  ERR failed to accept incoming stream requests error="failed to accept QUIC stream: timeout: no recent network activity"
  WRN Serve tunnel error error="accept stream listener encountered a failure while serving"
  INF Retrying connection in up to 1s
  ```
  最终只剩 0 条活跃连接，Cloudflare 侧返回 530（Origin unreachable）。
  
  **修复**：重启 cloudflared 即可，无需改配置或换 token。
  ```bash
  # Alpine
  /etc/init.d/cloudflared restart
  # Debian
  systemctl restart cloudflared
  ```
  
  **验证恢复**：`tail -5 /var/log/cloudflared.err` 应看到 `Registered tunnel connection ... location=xxx protocol=quic`，至少 3-4 条连接。

- **后端服务重启/切换**：cloudflared 内部维持到本地后端的连接，如果后端服务短暂不可用（如 komari 切换到 25776 再启动 proxy），tunnel 引擎可能判定连接失效而主动退出。示例日志：
  ```
  ERR failed to serve tunnel connection error="accept stream listener failed"
  ERR no more connections active and exiting
  INF Tunnel server stopped
  ```
  修复：重启 cloudflared 即可（`rc-service cloudflared restart`），无需修改 token 或 Dashboard ingress 规则。

- **如果是 token 失效**（需要重注册）
  # 1. 在 Cloudflare Dashboard 复制新 token
  # 2. 编辑 /etc/init.d/cloudflared 中的 token
  # 3. 重启服务

## 场景四：Quick Tunnel（trycloudflare）快速暴露本地服务

无需 Cloudflare Dashboard 登录，一条命令即可让本地服务通过公网访问：

```bash
# 临时暴露（URL 会打印到控制台）
cloudflared tunnel --url http://localhost:22217

# 永久运行（systemd 服务）
cat > /etc/systemd/system/myservice-tunnel.service << 'SERVICE'
[Unit]
Description=Cloudflare Quick Tunnel
After=network.target

[Service]
Type=simple
User=youruser
ExecStart=/usr/bin/cloudflared tunnel --url http://localhost:22217
Restart=always
RestartSec=10
Nice=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl enable --now myservice-tunnel.service
```

### Quick Tunnel 的局限性

| 问题 | 说明 |
|------|------|
| URL 每次重启会变 | `https://<random>.trycloudflare.com`, 不能用于固定域名 |
| 无认证 | 任何人拿到 URL 就能访问你的服务 |
| 无 SLA | trycloudflare TOS 说明无承诺，不适合生产 |
| 适合场景 | 临时测试、个人尝鲜、演示 |

### 获取 URL

```bash
# 第一次启动时打印，或从日志查
journalctl -u myservice-tunnel.service --no-pager --output=cat | grep trycloudflare

# 如果没找到（已被日志冲刷），重启服务即可看到新 URL
```

## 场景五：新增服务走 Tunnel

### Token 隧道：Cloudflare Dashboard 操作

Token 模式（`--token` 启动）的配置入口在 Dashboard，不在服务器：

1. **服务端**：确保新服务已在 localhost 监听（如 `http://127.0.0.1:22217`）
2. **Dashboard**：登录 https://one.dash.cloudflare.com/ → Networks → Tunnels → 选对应 tunnel → Public Hostname 选项卡 → Add a public hostname
3. **配 ingress**：填子域名（如 `ai.357561.xyz`），服务指向 `http://localhost:22217`）
4. **保存**：立即生效，无需重启服务器上的 cloudflared
5. **验证**：`curl https://你的域名/health`

### 完整流程示例（新增 ds-free-api 到已有 tunnel）

```bash
# 服务端：部署并启动 ds-free-api
systemctl start ds-free-api
curl http://127.0.0.1:22217/health   # 确认本地可用

# Dashboard：进入 tunnel ingress 规则 → 添加一行
#   Hostname: ai.357561.xyz → Service: http://localhost:22217

# 验证外网访问
curl https://ai.357561.xyz/health
```

### ⚠️ Critical Pitfall: SSH Access May Depend on the Tunnel

**BEFORE deleting cloudflared, verify that SSH is NOT routing through the tunnel.**

There are two common configurations:

**Case A — Tunnel-independent SSH (safe to delete):**
- SSH listens directly on a public IP/port (e.g., port 22 on a non-NAT VPS)
- cloudflared only proxies web services (HTTP/HTTPS)
- Deleting cloudflared will NOT affect SSH access

**Case B — Tunnel-dependent SSH (deleting cloudflared = losing SSH):**
- SSH is behind NAT and only reachable via cloudflared's port forwarding (e.g., VPS provider maps external port 46748 → internal port 22 through a tunnel rule)
- The cloudflared tunnel IS the SSH transport
- Deleting cloudflared will IMMEDIATELY cut SSH access

#### How to check before deletion:
```bash
# 1. Check if SSH (port 22) is directly reachable from outside
nc -zv <PUBLIC_IP> 22 2>&1
# → "open" → Case A (safe)
# → "Connection refused" → SSH might be behind NAT or firewalled

# 2. Check if the tunnel is forwarding SSH
# Look at cloudflared's ingress rules in Cloudflare Dashboard
# If any rule forwards SSH traffic, deleting cloudflared kills SSH

# 3. Check if you're connecting through the tunnel's external port
# If your SSH command uses a non-standard port (e.g., `ssh -p 46748 root@IP`)
# and that port is only forwarded by cloudflared, DO NOT delete it
# without verifying an alternative SSH path
```

#### If you must delete cloudflared but SSH depends on it:
```bash
# Option 1: Set up alternative SSH access BEFORE deletion
#   - Ensure SSH port 22 is open in the firewall
#   - Ensure the VPS provider's NAT/firewall allows direct port 22 access
#   - Test alternative access BEFORE stopping cloudflared

# Option 2: Restore cloudflared if you already deleted it and lost SSH
#   - Use VPS provider's web console (VNC/Rescue mode) to reinstall cloudflared
#   - Or ask the provider to restore access

# Option 3: If the tunnel used DNAT/iptables to forward external ports to SSH
#   - Recreate the iptables rule after cloudflared is gone:
#     iptables -t nat -A PREROUTING -p tcp --dport <EXT_PORT> -j DNAT --to-destination :22
```

**Real-world example:** Dutch VPS (31.58.51.127) used cloudflared tunnel to expose SSH on port 46748 (NAT → port 22). Deleting cloudflared cut SSH access completely because port 22 was not directly reachable from the internet. The only recovery path was the VPS provider's web console.

### Tunnel Independence from SSH (when SSH is NOT tunnel-dependent)

In Case A above: **the tunnel keeps working even if SSH access is down**. This is because:

- The cloudflared process is managed independently from SSHd
- The tunnel maintains persistent QUIC connections to Cloudflare edge
- Ingress rules are managed via Dashboard (not local config)
- As long as the cloudflared process stays alive, the tunnel serves traffic

This means you can lose SSH access to a server but the services behind the tunnel (ds-free-api, komari, web servers) remain fully accessible via their Cloudflare domains.

### cloudflared service install（重新安装）

如果 cloudflared 服务需要重新注册（比如从旧配置切换到新 token）：

```bash
# 先停掉旧服务
systemctl stop cloudflared
systemctl disable cloudflared

# 用 token 重新安装服务（会自动创建 systemd 服务文件）
cloudflared service install eyJhIjoi...  # 你的完整 token

# 启动
systemctl start cloudflared
systemctl enable cloudflared
```

`cloudflared service install` 会自动：
- 创建 `/etc/systemd/system/cloudflared.service`
- 写入正确的 ExecStart（带 `--no-autoupdate tunnel run --token <token>`）
- 设置 Restart=on-failure

**注意**：这个命令会覆盖已有的 cloudflared.service 文件。如果之前是手动写的服务文件，会被替换。

## 场景六：迁移 Tunnel 到新服务器

当需要将某个 token 隧道的运行位置从旧服务器搬到新服务器时（例如 56idc-la → 荷兰新主控），步骤如下：

### 迁移流程

1. **旧服务器上停用（可选但推荐）**：
   ```bash
   systemctl stop cloudflared
   systemctl disable cloudflared
   # 或者 Alpine OpenRC:
   rc-service cloudflared stop
   rc-update del cloudflared
   ```

2. **新服务器上安装**：
   ```bash
   # 用相同的 token 安装
   cloudflared service install <同一token>
   systemctl start cloudflared
   systemctl enable cloudflared
   ```

3. **等待连接**：
   ```bash
   journalctl -u cloudflared -n 20 --no-pager  # 查看连接状态
   ```
   预期看到 `Registered tunnel connection ... location=xxx protocol=quic`，会有多条连接（如 lax01, atl13 等 4 条）。

4. **⚠️ 关键步骤：更新 Public Hostname**
   - Tunnel 连上后，Cloudflare Dashboard 上的 ingress 规则（Public Hostname）**仍指向旧服务器的 localhost**
   - 必须手动登录 [Cloudflare Zero Trust Dashboard](https://one.dash.cloudflare.com/) → Networks → Tunnels → 选对应 tunnel → Public Hostname 选项卡
   - 修改每条 ingress 规则中的 Service 地址（如 `http://localhost:25774`）
   - 保存后即时生效，无需重启 cloudflared

5. **验证**：
   ```bash
   curl https://你的域名/  # 确认返回新服务器上的内容
   ```

### 迁移注意事项

- **token 不需要换**：同一个 tunnel ID 的 token 在任意服务器上都可用
- **旧服务器上的 cloudflared 要停掉**：否则两个 cloudflared 用同一 token 同时跑，Dashboard 上会看到两倍连接数，可能导致路由混乱
- **新服务器必须跑在相同端口**：ingress 规则的 `localhost:25774` 指的是新服务器的 25774，新服务器上的服务必须监听同一端口
- **Cloudflare 边缘节点根据隧道距离选择**：新服务器位置不同，CF 边缘节点日志里的 location 会改变
- **返回 404 或 1033 错误**：都是 ingress 规则未正确配置的典型表现，检查 Dashboard

### Token-Based vs Config-Based Tunnels

Cloudflared 有两种不同的运行模式：

| 模式 | 认证方式 | Ingress 配置位置 | 适合场景 |
|------|---------|-----------------|---------|
| **Token** (`--token` 参数) | 远程 token（从 Dashboard 获取） | **Cloudflare Dashboard** | 快速部署、面板管理 |
| **Config** (`--config` 参数) | 本地 credentials JSON + cert.pem | **本地 config.yml** | 复杂 ingress、脱离面板管理 |
| **Quick** (`--url` 参数) | 无（trycloudflare.com） | 不支持（单服务直出） | 临时测试 |

### Token 模式架构

Token 模式下：
- token 是 base64 编码的 JWT，包含 `a`（account tag）、`t`（tunnel ID）、`s`（tunnel secret）
- 服务器上不存在 config.yml，ingress 规则 100% 在 Cloudflare Dashboard 管理
- 新增后端服务需要在 Dashboard 加 ingress 规则（不在服务器操作）
- Dashboard 修改后数秒生效（无需重启 cloudflared）

### Token 解码

```python
import json, base64
token = "eyJhIjoi..."
payload = json.loads(base64.b64decode(token))
print(f"TunnelID: {payload['t']}")
print(f"AccountTag: {payload['a']}")
print(f"Secret: {payload['s']}")
```

### Token 转 Config 模式

如果需要本地 ingress 规则但只有 token：

1. 解码 token 获取 tunnel ID 和 secret
2. 创建 credentials 文件 `~/.cloudflared/<tunnel-id>.json`：
   ```json
   {
     "AccountTag": "解码的account_tag",
     "TunnelID": "解码的tunnel_id",
     "TunnelSecret": "secret的base64"
   }
   ```
3. 写 `/etc/cloudflared/config.yml` 包含 ingress 规则
4. 修改 service 改用 `cloudflared tunnel run --config /etc/cloudflared/config.yml`

**注意**：`s`（secret）字段可能又是一层 base64 编码，两种都试试。

## 多 cloudflared 实例共存

同一台服务器可以同时跑多个 cloudflared（比如一个 token 隧道跑主服务 + 一个 quick tunnel 跑测试服务）：

```bash
# 实例1：现有 token 隧道（metrics 端口 20241）
/usr/bin/cloudflared --no-autoupdate tunnel run --token <token>

# 实例2：quick tunnel 给不同服务（自动选 metrics 端口 20242+）
/usr/bin/cloudflared tunnel --url http://localhost:22217
```

第二个实例会自动选择不同的 metrics 端口。日志确认：
```
Starting metrics server on 127.0.0.1:20242/metrics
```

### 位置信息

Tunnel 连接日志显示 Cloudflare 边缘节点位置：
```
Registered tunnel connection ... location=lax01 protocol=quic
                    location=atl13
```

常见位置代码：`lax`（洛杉矶）、`atl`（亚特兰大）、`sfo`（旧金山）、`hkg`（香港）、`nrt`（东京）

## 已知坑

| 坑 | 说明 | 解法 |
|------|------|------|
| 服务器改了但外网 404 | ingress 规则没覆盖新路径 | 检查 Dashboard ingress |
| 改了文件但显示旧版 | Cloudflare 缓存 | 硬刷新或 Purge Everything |
| kernel: icmp csum error | cloudflared UDP 校验和警告，不影响功能 | 忽略 |
| tunnel 注册 token | 命令行带 `--token`，无本地 config.yml | token 在 /etc/init.d/cloudflared 启动参数中 |
| **Alpine 上 localhost 解析为 IPv6** | Alpine 的 `localhost` 默认解析到 `::1`（IPv6）。如果后端只监听 IPv4（`0.0.0.0:PORT`），cloudflared 报 `dial tcp [::1]:PORT: connect: connection refused` | 方案A：在后端服务监听 `::`（IPv6 双栈）；方案B：在 Dashboard ingress 规则中用 `127.0.0.1` 代替 `localhost`（需要 Cloudflare Zero Trust Dashboard 访问权限） |
