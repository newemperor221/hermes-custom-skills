---
name: nodeget-ops
description: "NodeGet 探针面板全栈运维 — Server 安装、Agent 部署、cloudflared HTTPS 隧道、故障排查。触发：\"NodeGet\"、\"nodeget\"、\"探针面板\"、\"服务器监控面板\"。"
tags: [nodeget, monitoring, probe, rust, websocket, cloudflared]
---

# NodeGet 探针面板运维

## 何时加载
- 用户提到 NodeGet / 探针面板安装
- 需要在新服务器部署监控 agent
- NodeGet Server 或 Agent 故障排查

## 项目概况
- **语言:** Rust（性能优于 Go 写的哪吒/Komari）
- **架构:** 前后端分离（Server 只提供 API，前端独立部署）
- **通信:** WebSocket + JSON-RPC
- **数据库:** SQLite 或 PostgreSQL
- **许可证:** AGPLv3

## ⚠️ 核心警告：小磁盘（≤1.5G）绝对不能跑 Server

NodeGet Server 用 **SQLite WAL 模式**存数据。WAL（Write-Ahead Logging）文件会无限增长，直到手动 checkpoint 或 VACUUM。

**实测数据（56idc 1.2G LXC）：**
- nodeget-server.db main: 2.7G
- nodeget-server.db-wal: 2.6G
- **结果：磁盘 100% 满，无法 VACUUM（disk full 时不能 vacuum）**
- IP Sentinel Master 同样用 SQLite WAL，同一问题

**结论：1.2G 磁盘 + SQLite WAL = 必满盘。** 任何在本地存数据库的监控工具都不适合这台机器。

**适用于所有同类工具：** 哪吒（SQLite）、Komari（数据库）、NodeGet（SQLite WAL）—— 只要是本地数据库 + 小磁盘，早晚爆。

**唯一安全方案：**
- 这台机器只跑 Agent + cloudflared 隧道
- Server 放在磁盘大的机器上
- 或用纯外部轮询（UptimeRobot / Better Stack），这台机器零服务端

### 🔴 踩坑记录（56idc 1.2G LXC）
- **2026-05-03：** nodeget-server WAL 膨胀至 5G+，磁盘满，VACUUM 失败（disk full），被迫卸载
- **2026-05-03：** IP Sentinel Master 同理（SQLite WAL），已卸载
- 56idc 这台只保留：SSH、cloudflared 隧道、cron（轻量监控脚本外推数据）

---

## Server 安装（踩坑版）

### ⚠️ 关键踩坑
1. **安装脚本参数用下划线不是连字符** — 文档写的 `--server-ws` 但脚本实际解析的是 `--server_ws`
2. **v0.0.6 无 release 二进制** — 截至 2026-05，最新 release v0.0.6 没有 assets，需用 v0.0.2
3. **脚本需要 TTY** — SSH 非交互式运行会静默失败（exit 1 无输出）
4. **Super Token 只在首次 init 显示** — 丢失后需从 SQLite 数据库手动提取
5. **VPS 端口限制** — 部分便宜 VPS（如 LXC 容器）40000 以下端口不可用，需改 `ws_listener` 到高位端口如 `0.0.0.0:42211`，同时更新 cloudflared 隧道映射
6. **StatusShow 必须推源码** — 推编译产物会导致环境变量不生效，config.json 保持默认占位符
7. **推荐 fork 官方仓库** — 直接 `gh repo fork` 比手动复制代码更干净，方便后续更新
7. **🔴 推代码前确认分支是 main** — 用户对 master 分支很反感，推前先 `git branch -M main`
9. **🔴 config.json 字段名是 `site_name` + `site_tokens`** — 不是 `title` + `nodes`，写错标题显示"你没设置"、节点列表为空
10. **🔴 视频背景不能用认证 URL** — 浏览器无法播放需要 Basic Auth 的跨域视频（如 WebDAV），静默失败 readyState=0。必须下载到 `public/` 打包进 dist，或设为公开可访问
11. **🔴 `<source>` 子元素方式 src 会变空** — Vite 构建后 `<source src="...">` 的 src 属性会丢失，必须直接在 `<video>` 上用 `src` 属性
12. **🔴 vite preview 只能本地访问** — 用户外网打开会空白，需打包 dist 发给用户或部署到 Cloudflare Pages
13. **🔴 file:// 协议不工作** — 双击 index.html 打开会空白（JS 模块和 fetch 被浏览器拦截），必须用本地服务器 `python3 -m http.server 8080`
14. **🔴 只有卡片模糊时，导航栏/按钮必须也改** — 如果卡片用 `backdrop-filter: blur()` 而导航栏/ViewToggle 用实色 `bg-muted`，视觉上非常突兀。所有浮在视频上的 UI 元素都必须改为半透明底（`rgba(0,0,0,0.4)`），去掉 backdrop-filter

### 方法一：安装脚本（需 TTY）
```bash
# 必须用交互式终端！非交互式会静默失败
bash <(curl -sL https://install.nodeget.com)
# 选 1. 安装 Server
# 记下 Super Token、用户名、密码（只显示一次）
```

### 方法二：手动安装（推荐，可脚本化）
```bash
# 1. 下载二进制（v0.0.2 有二进制）
curl -sL "https://github.com/NodeSeekDev/NodeGet/releases/download/v0.0.2/nodeget-server-linux-x86_64-gnu" \
  -o /usr/local/bin/nodeget-server
chmod +x /usr/local/bin/nodeget-server

# 2. 下载配置模板
curl -s -o /etc/nodeget-server.conf \
  "https://install.nodeget.com/config/nodeget-server.toml"

# 3. 修改监听地址（默认只监听端口号，需改成 IP:端口）
# ⚠️ 部分 VPS（LXC 容器等）40000 以下端口不可用，用高位端口
sed -i 's/ws_listener = "2211"/ws_listener = "0.0.0.0:42211"/' /etc/nodeget-server.conf

# 4. 创建数据目录
mkdir -p /var/lib/nodeget-server

# 5. 安装 systemd 服务
cd /tmp && cp /usr/local/bin/nodeget-server .
APP_NAME=nodeget-server APP_USER=root BIN_NAME=nodeget-server \
  START_AFTER_INSTALL=false \
  SERVICE_ARGS="serve -c /etc/nodeget-server.conf" \
  bash <(curl -s "https://install.nodeget.com/install-daemon.sh")

# 6. 初始化数据库（生成 Super Token）
nodeget-server init -c /etc/nodeget-server.conf
# ⚠️ 记下输出的 Super Token！

# 7. 启动
systemctl start nodeget-server
systemctl enable nodeget-server
```

### Super Token 丢失找回
```bash
# 方法一：从日志提取（推荐，不需要装 sqlite3）
grep -i 'super token' /var/log/nodeget-server/app.log
# 输出: Super Token: xxxxxx

# 方法二：从 SQLite 数据库提取
apt install sqlite3
sqlite3 /var/lib/nodeget-server/nodeget-server.db "SELECT * FROM token;"
# 输出格式: id|type|token_value|hash|||permissions|...
# 超级 token 是第三列（如 iePL8J9iJQEr1xoG）
# Agent 用的完整 token 格式: super_token:agent_token
```

## 批量 Agent 部署（多服务器）

批量部署时，**SSH 端口必须从 `servers.yaml` / 库存文件读取**，不能用简化数字（如只用 22 或猜测的端口）。端口搞错会导致 SSH timeout，白耗时间。

### 批量部署模板
```bash
# 从 inventory 读取 IP:PORT，逐台部署
while IFS=: read -r ip port; do
  echo "=== $ip:$port ==="
  ssh -o ConnectTimeout=5 -p "$port" root@"$ip" '
    # 检查是否已装
    if systemctl is-active nodeget-agent &>/dev/null; then
      echo "already running"
    else
      # 下载 binary（若不存在）
      [ -f /usr/local/bin/nodeget-agent ] || \
        curl -sL "https://github.com/NodeSeekDev/NodeGet/releases/download/v0.0.2/nodeget-agent-linux-x86_64-gnu" \
          -o /usr/local/bin/nodeget-agent && chmod +x /usr/local/bin/nodeget-agent
      
      # 写配置（用 heredoc 或 scp）
      mkdir -p /root/.config/nodeget-agent
      cat > /root/.config/nodeget-agent/config.toml << TOML
agent_uuid = "auto_gen"
log_level = "info"

[[server]]
name = "节点名"
server_uuid = "YOUR_SERVER_UUID"
ws_url = "wss://statapi.yourdomain.com"
token = "YOUR_TOKEN"
TOML
      
      # 写 systemd service 并启动
      cat > /etc/systemd/system/nodeget-agent.service << SVCEOF
[Unit]
Description=NodeGet Agent
After=network-online.target
Wants=network-online.target

[Service]
User=root
ExecStart=/usr/local/bin/nodeget-agent -c /root/.config/nodeget-agent/config.toml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF
      systemctl daemon-reload
      systemctl enable --now nodeget-agent
    fi
  '
done < servers.txt
```

### ⚠️ 批量部署踩坑
1. **SSH 端口必须从库存文件读取** — 简化数字会导致 timeout
2. **Agent 连接不等于数据可见** — agent 显示 `Connected` 但 status page 可能无数据，需等 agent 上报第一次心跳
3. **低配机器（1c1g）需确认 DNS 解析** — 部分 LXC/小内存机器 DNS 配置不完整，`curl statapi.example.com` 可能超时，需检查 `/etc/resolv.conf`
4. **🔴 UUID 冲突（auto_gen）** — `auto_gen` 基于系统特征生成 UUID，相似系统（同厂商、同模板）会生成相同 UUID！导致状态页只显示 5 台但实际有 10 台。**必须手动指定唯一 UUID**，用 `uuidgen` 或 Python `uuid.uuid5()` 生成
5. **🔴 SSH heredoc 破坏 TOML 引号** — 通过 SSH heredoc 写 config.toml 时，引号会被 shell 吞掉，导致 `string values must be quoted` 错误。**安全写法：用 base64 编码传输**
   ```bash
   CONFIG_B64=$(echo "$CONFIG" | base64)
   ssh root@server "echo $CONFIG_B64 | base64 -d > /root/.config/nodeget-agent/config.toml"
   ```
6. **woioeow 用户 sudo 需要 `-S`** — 非交互式 SSH 无法输入密码，用 `echo "password" | sudo -S command 2>/dev/null`

## Agent 安装

### 手动安装（推荐，可脚本化）
```bash
# 1. 下载二进制
curl -sL "https://github.com/NodeSeekDev/NodeGet/releases/download/v0.0.2/nodeget-agent-linux-x86_64-gnu" \
  -o /usr/local/bin/nodeget-agent
chmod +x /usr/local/bin/nodeget-agent
```

### Agent 配置（TOML 格式）
⚠️ **默认文件名是 config.yaml 但实际是 TOML 格式！** 解析器会报 TOML parse error。

配置路径：`/root/.config/nodeget-agent/config.toml`

```toml
agent_uuid = "auto_gen"        # 自动生成 UUID
log_level = "info"

[[server]]                      # ⚠️ 单数 [[server]]，不是 [[servers]]
name = "节点名称"               # 显示名称
server_uuid = "xxxx-xxxx-xxxx"  # NodeGet Server 的 UUID（从 Server 日志获取）
ws_url = "wss://域名:端口"      # ⚠️ 字段名是 ws_url 不是 url
token = "your_token"            # Super Token 或受限 Token
```

**⚠️ Agent 配置必填字段（缺一不可，会报 missing field）：**
- `agent_uuid` — 设 `"auto_gen"` 自动生成
- `[[server]]` 下的 `name`、`server_uuid`、`ws_url`、`token`

### 获取 Server UUID
```bash
# 方法一：从 Server 日志获取
journalctl -u nodeget-server --no-pager | grep -i uuid

# 方法二：从 Server 配置文件（auto_gen 时数据库里有）
# Server UUID 在启动日志和首页 HTML 里都有
curl -s https://statapi.yourdomain.com/ | grep -oP 'UUID: <span>\K[^<]+'
```

### Systemd 服务（root 用户）
```bash
mkdir -p /root/.config/nodeget-agent

cat > /etc/systemd/system/nodeget-agent.service << 'EOF'
[Unit]
Description=NodeGet Agent
After=network-online.target
Wants=network-online.target

[Service]
User=root
ExecStart=/usr/local/bin/nodeget-agent -c /root/.config/nodeget-agent/config.toml
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable --now nodeget-agent
```

### 非 root 用户部署
如果用户是 `woioeow` 而非 root：
```bash
# 下载二进制（需要 sudo）
sudo mv /tmp/nodeget-agent /usr/local/bin/nodeget-agent

# 配置文件放在 root 下（systemd 以 root 运行）
sudo mkdir -p /root/.config/nodeget-agent
sudo cp config.toml /root/.config/nodeget-agent/config.toml

# systemd 服务同上
```

### 验证 Agent 连接
```bash
# 检查服务状态
systemctl status nodeget-agent

# 检查日志确认连接成功
journalctl -u nodeget-agent --no-pager | tail -5
# 应看到: [节点名] Connected successfully

# 从 Server API 验证（⚠️ token 格式必须是 key:secret）
curl -s -X POST https://statapi.yourdomain.com/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"nodeget-server_list_all_agent_uuid","params":{"token":"SUPER_TOKEN:AGENT_TOKEN"},"id":1}'
# 返回 {"uuids":["xxx"]} 表示有 Agent 在线
```

### 设置 StatusShow 显示名称（KV metadata）

StatusShow 的节点名称**不来自** agent config 的 `name` 字段，而是从 KV 存储读取 `metadata_name`。

```bash
# ⚠️ KV namespace 必须先存在！agent 连接并上报数据后才会自动创建 namespace
# 如果报 "Namespace not found"，需要先重启 agent 等它连接
systemctl restart nodeget-agent
sleep 5

# 查询所有已存在的 namespace
curl -s -X POST https://statapi.yourdomain.com/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"kv_list_all_namespace","id":1,"params":{"token":"SUPER_TOKEN:AGENT_TOKEN"}}'

# 设置节点显示名称
curl -s -X POST https://statapi.yourdomain.com/ \
  -H 'Content-Type: application/json' \
  -d '{"jsonrpc":"2.0","method":"kv_set_value","id":1,"params":{"token":"SUPER_TOKEN:AGENT_TOKEN","namespace":"AGENT_UUID","key":"metadata_name","value":"自定义名称"}}'

# 其他可用的 metadata 字段：
# metadata_region — 地区代码（如 US、JP）
# metadata_tags — 标签数组
# metadata_virtualization — 虚拟化类型
# metadata_latitude / metadata_longitude — 经纬度
# metadata_hidden — 隐藏节点（boolean）
```

**⚠️ KV namespace 不存在的排查：**
1. 检查 agent 是否真的连接了：`journalctl -u nodeget-agent | grep Connected`
2. 检查 agent UUID 是否在 server 注册：`nodeget-server_list_all_agent_uuid`
3. 如果 UUID 注册了但 namespace 不存在 → agent 可能还没上报 static data，重启 agent 等待
4. `auto_gen` UUID 冲突时，多个 agent 共享同一 UUID，只有第一个创建的 namespace 能用

## HTTPS 方案（NodeGet 必须用 wss://）

### 方案一：Cloudflare Quick Tunnel（临时体验）
```bash
# 安装 cloudflared
curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
  -o /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared

# 作为 systemd 服务运行
cat > /etc/systemd/system/cf-tunnel.service << EOF
[Unit]
Description=Cloudflare Quick Tunnel
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/cloudflared tunnel --url http://127.0.0.1:2211 --protocol http2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload && systemctl start cf-tunnel

# 获取分配的域名（重启会变！）
journalctl -u cf-tunnel --no-pager | grep -oE "[a-zA-Z0-9.-]+\.trycloudflare\.com" | head -1
```

### 方案二：固定域名隧道（生产用）
```bash
# 在 Cloudflare Dashboard 创建命名隧道后，拿到 token
# 写入 systemd service
cat > /etc/systemd/system/cloudflared.service << EOF
[Unit]
Description=cloudflared
After=network-online.target
Wants=network-online.target

[Service]
TimeoutStartSec=15
Type=notify
ExecStart=/usr/bin/cloudflared --no-autoupdate tunnel run --token YOUR_TUNNEL_TOKEN
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload && systemctl enable --now cloudflared
```

#### ⚠️ 命名隧道配置在 CF 仪表盘，不在本地
命名隧道的 ingress 规则（hostname → 端口映射）存储在 Cloudflare 基础设施中，不在本地文件。
修改端口映射必须去 **Cloudflare Dashboard → Networks → Tunnels → Configure → Public Hostname**。

**常见坑：端口映射错误**
- 症状：cloudflared 运行正常、tunnel 显示 Healthy，但 API 不通
- 原因：隧道配置里的 Service 指向了错误端口（如 quick tunnel 遗留的随机端口）
- 排查：`journalctl -u cloudflared | grep "Updated to new configuration"` 查看实际映射
- 修复：在 CF 仪表盘改 Service 为 `http://localhost:2211`（NodeGet 默认端口）

#### ⚠️ StatusShow 卡在"连接后端中…"排查

**症状：** StatusShow 页面一直显示"连接后端中…"，不显示节点数据。

**排查顺序（按概率）：**

1. **🥇 最常见：没有 Agent 连接** — 如果 `listAgentUuids` 返回 `{"uuids":[]}`，StatusShow 没数据可显示，会一直卡在"连接后端中…"。**先装 Agent，再看状态页。**
2. **config.json 未正确部署** — `curl https://stat.yourdomain.com/config.json` 确认 backend_url 和 token。如果用 Cloudflare Pages，环境变量需在 build 前设置，改完必须重新部署。
3. **cloudflared 端口映射错误** — 隧道 Service 指向了错误端口。`journalctl -u cloudflared | grep "Updated to new configuration"` 确认。
4. **WebSocket 连接问题** — 浏览器 Console 测试：
   ```js
   const ws = new WebSocket('wss://statapi.yourdomain.com');
   ws.onopen = () => console.log('OK');
   ws.onerror = (e) => console.log('FAIL', e);
   ```

**⚠️ 不要轻易归因于 Cloudflare Bot Fight Mode** — CF 默认不会对隧道子域名开 Bot 验证。curl 返回 200 而非 101 是正常的，因为 NodeGet Server 对普通 HTTP 请求也返回 200（HTML 页面）。真正的 WebSocket 握手需要在浏览器里测试。

#### 验证隧道配置
```bash
# 查看 cloudflared 收到的配置（含 hostname → port 映射）
journalctl -u cloudflared --no-pager | grep "Updated to new configuration"
# 输出示例: "ingress":[{"hostname":"ng.<用户域名>","service":"http://localhost:2211"},...]

# 验证 WebSocket 是否通（应返回 101）
curl -s -o /dev/null -w "%{http_code}" \
  -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  -H "Sec-WebSocket-Protocol: nodeget-jsonrpc" \
  https://statapi.<用户域名>/
# 101 = 正常，200 = 被 CF challenge 拦截
```

### 方案三：Nginx 反代（有 80/443 端口时）
```nginx
server {
    listen 443 ssl;
    server_name api.yourdomain.com;
    # SSL 配置...

    location / {
        proxy_pass http://127.0.0.1:2211;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;  # WebSocket 长连接
    }
}
```

## 跨机器编译前端（小内存服务器）

当 Server 机器内存 < 1GB 时无法 build 前端。解决方案：
1. 在其他有 Node.js 的机器上 clone 源码
2. 把源码推到 GitHub（不是编译产物！）
3. Cloudflare Pages 在部署时自动 build，注入环境变量

⚠️ **必须推源码，不能推 dist/** — StatusShow 的环境变量（SITE_1 等）在 build 时由 `scripts/build-config.mjs` 注入，推编译产物会导致环境变量不生效。该脚本读取 `SITE_1`~`SITE_n` 环境变量，写入 `public/config.json`。

Board 部署细节见 `references/board-deploy.md`。
StatusShow 部署细节见 `references/cloudflare-pages-deploy.md`。
StatusShow 详情页/表格页样式（导航栏、卡片间距、表格对齐、统计栏合并）见 `references/komari-theme-styling.md`。
StatusShow 自定义样式（Liquid Glass、哪吒风格卡片、视频背景等）见 `references/statusshow-customization.md`。
WebSocket 调试方法见 `references/websocket-debug.md`。
JSON-RPC API 方法见 `references/jsonrpc-api.md`。

## 前端面板（三组件架构）

NodeGet 是完全前后端分离，有三个独立组件：

1. **Server（后端主控）** — Rust，WebSocket + JSON-RPC API，存数据、收上报
2. **Board（管理面板）** — Vue.js SPA，你登录管理节点/看图表/配置用的
3. **StatusShow（公开状态页）** — 纯静态前端，给外部用户看的公开展示页

### 域名规划（推荐）
- `statapi.example.com` → NodeGet Server（后端 API）— 用户偏好 `statapi` 而非 `tzapi`
- `dash.example.com` → Board 管理面板（前端）
- `stat.example.com` → StatusShow 状态页（前端）

⚠️ **用户常混淆：** 以为 `dash` 是后端，其实 `dash` 是前端面板。后端 API 用单独的子域名。

⚠️ **Git 分支强偏好：永远用 `main`，不要用 `master`。** 用户对 `master` 分支很反感。
- 推代码前先 `git branch -M main`
- 如果 GitHub 仓库默认是 `master`，先用 API 改默认分支再删：
  ```bash
  # 改默认分支为 main
  curl -s -X PATCH -H "Authorization: token $(gh auth token)" \
    https://api.github.com/repos/OWNER/REPO -d '{"default_branch":"main"}'
  # 然后才能删 master
  curl -s -X DELETE -H "Authorization: token $(gh auth token)" \
    https://api.github.com/repos/OWNER/REPO/git/refs/heads/master
  ```

### Board 管理面板
- **官方:** https://dash.nodeget.com（填你的 Server wss:// 地址 + Token 登录）
- **自建:** GitHub 仓库 NodeSeekDev/NodeGet-board，Vue + TypeScript + pnpm
- **⚠️ 必须用 Vercel 部署**（Board 依赖 WebSocket 连接 statapi，CF Pages 不支持 WS）
- **⚠️ 需要 Node.js 编译** — 小内存机器（<1G）无法本地 build，需在其他机器推源码让 Vercel build
- **⚠️ Board 不读构建时环境变量** — 与 StatusShow 不同，Board 启动后仍需手动添加主控：打开 `dash.yourdomain.com` → 弹出 "Add Server" 填 Name / WSS URL / Token。`VITE_BACKEND_WS` 和 `VITE_BACKEND_TOKEN` 对 Board 无效
- **⚠️ Board 需要 Node ^20.19.0 || >=22.12.0** — Vercel 默认 Node 版本足够，但建议在项目设置中确认
- **⚠️ StatusShow 显示主机名，不是 agent name** — config.toml 里的 `name` 字段不会显示在状态页，StatusShow 取的是系统 hostname
- **⚠️ 用户偏好：推源码，用户自己配置 Vercel** — 不要替用户在 Vercel Dashboard 操作

### StatusShow 公开状态页
- **GitHub:** NodeSeekDev/NodeGet-StatusShow
- **必须用 Vercel 部署**（CF Pages 不支持 WebSocket 代理，会导致"连接后端中…"超时）
- 用受限 Token（仅查阅权限），不暴露 Super Token
- **⚠️ 必须推源码** — 环境变量在 build 时由 `scripts/build-config.mjs` 注入，推编译产物不生效
- **⚠️ 推代码前先 fork 官方仓库** — `gh repo fork` 比手动复制更干净
- **⚠️ 永远用 main 分支** — 推前 `git branch -M main`，如果是新仓库先用 API 改默认分支再删 master

**环境变量格式（Cloudflare Pages）：**

⚠️ **StatusShow 环境变量格式因版本而异**，部署前先看仓库的 `example.env.development`：
- v0.0.2+ 用 `VITE_BACKEND_WS` 和 `VITE_BACKEND_TOKEN`
- 旧版用 `SITE_1` 格式

⚠️ **页面标题需动态设置** — 默认硬编码 "NodeGet - StatusShow"，需在 App.tsx 添加 `useEffect` 设置 `document.title = config.site_name`

**⚠️ config.json 字段名是 `site_name` + `site_tokens`，不是 `title` + `nodes`！** 写错会导致标题显示"你没设置"、节点列表为空。

```bash
# v0.0.2+ 格式
VITE_BACKEND_WS=wss://statapi.example.com
VITE_BACKEND_TOKEN=your_token
NODE_VERSION=20  # engines 要求 ^20.19.0 || >=22.12.0
```

⚠️ **Cloudflare Pages 部署要点：**
1. 构建命令：`npm run build`
2. 输出目录：`dist`
3. 环境变量必须在**首次 build 前**设置
4. 改环境变量后必须**重新部署**（Retry deployment）

### 登录
填 Server 的 `wss://` 地址 + Super Token 即可连接

## 资源占用参考
- Server: ~16MB 内存（Rust，极轻）
- Agent: ~5-10MB 内存
- 磁盘: Server 二进制 ~4MB + SQLite 数据库

## 管理命令
```bash
# 服务管理
systemctl status nodeget-server
systemctl restart nodeget-server
journalctl -u nodeget-server -f

# 查看 UUID
nodeget-server get-uuid -c /etc/nodeget-server.conf

# 轮换 Super Token（需交互确认）
nodeget-server roll-super-token -c /etc/nodeget-server.conf

# 更新版本
systemctl stop nodeget-server
curl -sL "https://github.com/NodeSeekDev/NodeGet/releases/download/v0.0.2/nodeget-server-linux-x86_64-gnu" \
  -o /usr/local/bin/nodeget-server
chmod +x /usr/local/bin/nodeget-server
systemctl start nodeget-server
```

## 与其他探针对比
| | 哪吒 | Komari | NodeGet |
|---|---|---|---|
| 语言 | Go | Go | Rust |
| 内存占用 | ~30MB | ~25MB | ~16MB |
| 架构 | 前后端一体 | 前后端一体 | 前后端分离 |
| 扩展性 | 插件 | 一般 | JS Worker + KV |
| 多 Server | ❌ | ❌ | ✅ |
| 成熟度 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐（早期） |
