# Cloudflare Pages 部署 NodeGet 前端

## 适用场景
- 自建前端，不依赖 `dash.nodeget.com`
- 前端是纯静态 SPA，不需要服务器端渲染
- 小内存 VPS（<1GB）无法本地 build，需在其他机器编译后推到 GitHub

## 前置条件
- GitHub 账号 + gh CLI 已认证
- Cloudflare 账号 + 域名在 CF 托管

## GitHub 仓库
- Board: `newemperor221/NodeGet-board`（fork 自 NodeSeekDev/NodeGet-board）
- StatusShow: `newemperor221/nodeget-status`（fork 自 NodeSeekDev/NodeGet-StatusShow）

## 部署流程

### ⚠️ 关键：必须推源码，不能推编译产物
StatusShow 的环境变量在 **build 时** 注入。推编译产物会导致环境变量不生效。

**正确做法：推源码到 GitHub，让 Cloudflare Pages 在部署时 build。**

### 1. 推送源码到 GitHub

**推荐方式：直接 fork 官方仓库**
```bash
gh repo fork NodeSeekDev/NodeGet-StatusShow --clone --remote-name origin
cd NodeGet-StatusShow
git push -u origin main
```

### 2. Cloudflare Pages 配置
1. dash.cloudflare.com → Workers 和 Pages
2. 创建 → Pages → 连接到 Git
3. 选仓库
4. 构建设置：
   - 构建命令：`npm run build`
   - 输出目录：`dist`
   - Node 版本：环境变量加 `NODE_VERSION=20`（或 22）
5. 保存并部署

### 3. 绑定自定义域
- 部署成功后 → 自定义域 → 添加子域名
- 例：`<监控面板域名>`（StatusShow）、`dash.<用户域名>`（Board）

### 4. 环境变量配置

**⚠️ StatusShow 环境变量格式因版本而异，部署前先看仓库的 `example.env.development`：**

#### v0.0.2+ 格式（VITE_ 前缀）
```
VITE_BACKEND_WS=wss://statapi.example.com
VITE_BACKEND_TOKEN=your_token
NODE_VERSION=20
```

#### 旧版格式（SITE_ 前缀）
```
SITE_NAME=我的探针
SITE_1=name="东京",backend_url="wss://statapi.example.com",token="your_token"
```

**⚠️ 环境变量在 build 时注入，改了必须重新部署（Retry deployment）**

### 5. Board 管理面板特殊说明

**Board 不读环境变量！** 配置存在浏览器 localStorage，部署后在 UI 手动添加主控：
- Name: 随便填
- WSS URL: `wss://statapi.example.com`
- Token: `super_token`（不是 `super_token:agent_secret`）

Board 需要 Node ^20.19.0 || >=22.12.0，Cloudflare Pages 必须设 `NODE_VERSION=20` 或 `22`。

## ⚠️ 禁止在 Cloudflare Pages 部署任何 NodeGet 前端

**Cloudflare Pages 不支持 WebSocket 代理。** CF Pages 边缘节点无法建立到 statapi 的 WebSocket 长连接，导致两个前端都失效：
- **StatusShow** 部署在 CF Pages → 卡在"连接后端中…"，后端报错 `nodeget-server_list_all_agent_uuid 超时`
- **Board** 部署在 CF Pages → 同样无法连接 statapi，后端同样报超时

**两个前端都必须用 Vercel 部署。** Vercel serverless function 原生支持 WebSocket 代理，可正常连接到 statapi。

禁止用：Cloudflare Pages、GitHub Pages、其他纯静态托管。

**验证 WS 代理是否正常（浏览器 Console）：**
```js
const ws = new WebSocket('wss://statapi.yourdomain.com');
ws.onopen = () => console.log('WS OK');
ws.onerror = () => console.log('WS FAIL - 平台不支持 WS 代理');
```

## ⚠️ 注意事项
- **必须推源码** — 推编译产物会导致环境变量不生效
- **.env 变量在 build 时注入** — 改了要重新 build
- **小内存机器无法 build** — 需要在别的机器推源码，让 CF Pages build
- **公开状态页用受限 Token** — 不要用 Super Token
