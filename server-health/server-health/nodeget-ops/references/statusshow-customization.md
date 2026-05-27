# StatusShow 自定义样式参考

## 项目结构

```
src/
├── components/
│   ├── Background.tsx    # 背景组件（默认纯色/渐变）
│   ├── Navbar.tsx        # 顶部导航栏
│   ├── NodeCard.tsx      # 节点卡片
│   ├── NodeDetail.tsx    # 节点详情弹窗
│   ├── NodeTable.tsx     # 节点表格视图
│   ├── Search.tsx        # 搜索框
│   ├── TagFilter.tsx     # 标签过滤器
│   └── Footer.tsx        # 页脚
├── styles/
│   └── global.css        # 全局样式（Tailwind CSS）
├── hooks/
│   ├── useNodes.ts       # 数据获取（KV + 动态数据）
│   └── useConfig.ts      # 加载 config.json
└── types.ts              # 类型定义
```

## ⚠️ config.json 字段名（踩坑）

**config.json 用的是 `site_name` 和 `site_tokens`，不是 `title` 和 `nodes`！**

写错字段名会导致标题显示"你没设置"，节点列表为空。

```json
{
  "site_name": "银河探针",
  "site_tokens": [
    {
      "name": "56idc-LA",
      "backend_url": "wss://statapi.357561.xyz",
      "token": "SUPER_TOKEN:AGENT_TOKEN"
    }
  ]
}
```

- `site_name` — 站点标题（显示在导航栏左上角）
- `site_tokens` — 数组，每个元素有 `name`、`backend_url`、`token`
- `token` 格式必须是 `super_token:agent_token`（冒号分隔）
- 类型定义在 `src/types.ts` 第 87-90 行：`site_name?: string`、`site_tokens: { name, backend_url, token }[]`

## 本地定制流程（不走 Cloudflare Pages）

当需要本地修改样式并预览时：

```bash
# 1. 克隆仓库
git clone https://github.com/newemperor221/nodeget-status-custom.git
cd nodeget-status-custom
npm install

# 2. 手动写 config.json（不依赖环境变量）
cat > public/config.json << 'EOF'
{
  "site_name": "你的站名",
  "site_tokens": [
    {
      "name": "节点名",
      "backend_url": "wss://你的API域名",
      "token": "super_token:agent_token"
    }
  ]
}
EOF

# 3. 修改样式文件（见下方改造文件清单）

# 4. 构建
npm run build

# 5. 本地预览
npx vite preview --host 0.0.0.0 --port 4173
```

⚠️ `build-config.mjs` 会检查 `SITE_n` 环境变量，如果没有就保留已有的 `public/config.json`。所以手动写 config.json 是可以的，不会被覆盖。

## 添加更多节点

在 `site_tokens` 数组中追加即可，每个节点对应一个 Server 实例：

```json
{
  "site_name": "银河探针",
  "site_tokens": [
    { "name": "56idc-LA", "backend_url": "wss://api1.example.com", "token": "tk1:ag1" },
    { "name": "RackNerd-NY", "backend_url": "wss://api2.example.com", "token": "tk2:ag2" }
  ]
}
```

StatusShow 会自动合并所有 Server 的节点数据，`showSource` 属性会在卡片上显示来源标签。

## 样式系统

- **Tailwind CSS** + CSS 变量（HSL 格式）
- **暗色模式**: `dark` class on `<html>`，默认暗色
- **卡片样式**: `.card-soft` class（global.css）
- **背景样式**: `.bg-soft` class

## Liquid Glass 效果改造要点

### 动态背景（Background.tsx）

**方案一：Canvas 光球动画**（默认，纯前端无外部依赖）

```tsx
// Canvas 绘制 5 个彩色光球，不同速度/相位浮动
// 外层 <canvas style={{ filter: 'blur(60px)' }} />
// 光球用 radialGradient，rgba 半透明
// requestAnimationFrame 循环，每个光球有 x, y, vx, vy, radius, color
```

**方案二：视频动态壁纸**（效果更好，但需注意文件大小）

```tsx
export function Background() {
  return (
    <div className="fixed inset-0 -z-10 overflow-hidden">
      <video
        autoPlay loop muted playsInline
        src="/wallpaper.mp4"           // 放在 public/ 目录下
        className="w-full h-full object-cover"
        style={{ filter: 'blur(2px) brightness(0.4)' }}
      />
      <div className="absolute inset-0 bg-black/40" />  {/* 暗色遮罩保证文字可读 */}
    </div>
  )
}
```

⚠️ **视频背景注意事项：**
- 视频文件必须放在 `public/` 目录，构建时会原样复制到 `dist/`
- **不能用需要认证的 URL**（如 WebDAV Basic Auth）—— 浏览器无法直接播放带认证的跨域视频，会静默失败（readyState=0，无任何错误提示）
- 解决方案：①下载视频到 `public/` 目录打包进 dist ②将视频设为公开可访问（无需认证）
- `brightness(0.4)` + `bg-black/40` 双重暗化，确保白色文字在视频上可读
- `object-cover` 让视频填满屏幕并裁剪多余部分
- 移动端注意视频文件大小，建议压缩到 <10MB 或用低分辨率
- **⚠️ 必须用 `src` 属性，不要用 `<source>` 子元素** — `<source>` 方式在 Vite 构建后 src 会变空（readyState=0），直接用 `src="/wallpaper.mp4"` 最可靠

### 毛玻璃卡片（global.css）
```css
.glass-card {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(40px) saturate(180%) brightness(110%);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  transition: all 0.3s ease;
}
.glass-card:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}
/* 鼠标跟随高光：::after 用 radial-gradient + CSS 变量 --mouse-x/--mouse-y */
```

### 毛玻璃导航栏
```css
.glass-nav {
  background: rgba(255, 255, 255, 0.06);
  backdrop-filter: blur(40px) saturate(180%);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}
```

### 触摸光效
```tsx
// App.tsx 中添加 mousemove 监听，跟随鼠标显示 radial-gradient 光晕
<div className="touch-glow" /> // position: fixed, pointer-events: none
```

### 进度条
替换 shadcn Progress 为自定义 div：
```tsx
<div className="glass-progress">
  <div className="glass-progress-indicator" style={{ width: `${value}%` }} />
</div>
```

## 改造文件清单

1. `src/components/Background.tsx` — Canvas 动态光球 或 视频壁纸
2. `src/styles/global.css` — Liquid Glass 全局样式
3. `src/components/NodeCard.tsx` — 鼠标跟随高光
4. `src/components/Navbar.tsx` — glass-nav class
5. `src/components/Search.tsx` — glass-input class
6. `src/components/TagFilter.tsx` — 玻璃标签
7. `src/components/NodeDetail.tsx` — glass-overlay + glass-modal
8. `src/components/Footer.tsx` — 细边框
9. `src/App.tsx` — 触摸光效 + glass-card 错误提示

## 本地预览陷阱

**⚠️ `vite preview` 只监听 localhost** — 用户从外网打开会空白或连接拒绝。

```bash
# 本地预览只能服务器本地访问 http://localhost:4173
npx vite preview --host 0.0.0.0 --port 4173
# --host 0.0.0.0 让局域网可访问，但外网仍不行
```

**让用户看效果的正确方式：**
1. **打包 dist 发给用户** — `tar czf dist.tar.gz dist/`，用户自己部署
2. **部署到 Cloudflare Pages** — 最稳，自动 HTTPS
3. **cloudflared quick tunnel** — 临时演示用（服务器需装 cloudflared）
4. **不要假设用户能访问 localhost** — 用户说"空白"大概率是这个原因

**⚠️ file:// 协议不工作** — 双击 `index.html` 打开会空白，浏览器拦截 JS 模块和 fetch 请求。必须用本地服务器：

```bash
cd dist && python3 -m http.server 8080
# 或
npx serve dist
```

## 进阶定制

### 动态页面标题（从 config.json 读取）

默认标题是 "NodeGet - StatusShow"，要改成从 `site_name` 读取：

```tsx
// App.tsx 中添加 useEffect
useEffect(() => {
  if (config?.site_name) {
    document.title = config.site_name
  }
}, [config?.site_name])
```

### 移除亮暗切换按钮

```tsx
// Navbar.tsx 中删除 ThemeToggle 相关代码
import { ThemeToggle } from './ThemeToggle'  // 删除这行
<ThemeToggle />                                // 删除这行
```

### 自定义 Footer（运行时间计数器）

替换 "Powered by NodeGet" 为站点运行时间：

```tsx
// Footer.tsx
import { useEffect, useState } from 'react'

const LAUNCH_DATE = new Date('2025-01-01T00:00:00+08:00')  // 按需修改

function calcUptime() {
  const now = new Date()
  let years = now.getFullYear() - LAUNCH_DATE.getFullYear()
  let months = now.getMonth() - LAUNCH_DATE.getMonth()
  let days = now.getDate() - LAUNCH_DATE.getDate()
  let hours = now.getHours() - LAUNCH_DATE.getHours()
  let minutes = now.getMinutes() - LAUNCH_DATE.getMinutes()

  if (minutes < 0) { minutes += 60; hours-- }
  if (hours < 0) { hours += 24; days-- }
  if (days < 0) {
    const prevMonth = new Date(now.getFullYear(), now.getMonth(), 0)
    days += prevMonth.getDate(); months--
  }
  if (months < 0) { months += 12; years-- }

  return { years, months, days, hours, minutes }
}

export function Footer() {
  const [uptime, setUptime] = useState(calcUptime)
  useEffect(() => {
    const timer = setInterval(() => setUptime(calcUptime()), 60_000)
    return () => clearInterval(timer)
  }, [])

  const parts: string[] = []
  if (uptime.years > 0) parts.push(`${uptime.years} 年`)
  if (uptime.months > 0) parts.push(`${uptime.months} 月`)
  parts.push(`${uptime.days} 日`, `${uptime.hours} 时`, `${uptime.minutes} 分`)

  return (
    <footer className="border-t border-white/5">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex justify-center text-xs text-muted-foreground">
        本站已稳定运行 {parts.join(' ')}
      </div>
    </footer>
  )
}
```

### 视频背景：只有卡片模糊，其余清晰

**用户明确要求：** "我只希望卡片有模糊，其它地方是清晰的"

这是最常见的最终形态 — 视频完全清晰，只有卡片区域因 `backdrop-filter: blur(40px)` 自动模糊背后的视频。

```tsx
// Background.tsx — 最终形态，无任何滤镜
export function Background() {
  return (
    <video
      autoPlay loop muted playsInline
      src="/wallpaper.mp4"
      className="fixed inset-0 w-full h-full object-cover -z-10"
    />
  )
}
```

**配套改动（去掉所有非卡片元素的 backdrop-filter）：**

```css
/* global.css — 导航栏改为纯半透明底，无 blur */
.glass-nav {
  background: rgba(0, 0, 0, 0.4);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  /* 不要 backdrop-filter！否则导航栏后面也模糊 */
}
```

```tsx
// ViewToggle.tsx — 切换按钮也改为纯半透明底
<div className="relative inline-grid grid-cols-2 p-0.5 rounded-xl"
     style={{ background: 'rgba(0,0,0,0.4)', border: '1px solid rgba(255,255,255,0.1)' }}>
  {/* 滑块也用半透明 */}
  <div style={{ background: 'rgba(255,255,255,0.12)' }} />
</div>
```

**⚠️ 三层结构很重要：**
| 元素 | 背景 | backdrop-filter | 效果 |
|---|---|---|---|
| 视频 | 无（纯 video） | 无 | 完全清晰 |
| 导航栏/按钮/页脚 | `rgba(0,0,0,0.4)` | **无** | 半透明黑底，视频清晰可见 |
| 卡片 | `rgba(255,255,255,0.06)` | `blur(40px)` | 卡片后面模糊，其余清晰 |

**⚠️ 用户发现的突兀问题：** 如果只有卡片用毛玻璃，而导航栏/切换按钮用实色 `bg-muted`，视觉上非常突兀。所有浮在视频上的元素都必须用半透明底，保持一致。

### 从 WebDAV 下载视频（需要认证）

```bash
# WebDAV Basic Auth 下载
curl -u "username:password" "https://pan.example.com/webdav/wallpaper.mp4" \
  -o public/wallpaper.mp4

# 然后构建，视频会打包进 dist/
npm run build
```

### 哪吒风格卡片布局（Nezha-style）

用户常要求把卡片改成哪吒监控（nezha.probes.cc）的风格。核心布局：

```
┌──────────────────────────┐
│ 🇯🇵  StatusDot  节点名称  │  ← 顶部：国旗 + 状态 + 名称
│      Debian 12 · KVM     │  ← 系统 + 虚拟化
├──────────────────────────┤
│ CPU     内存      磁盘    │  ← 三列进度条
│ 3.0%    45.1%    58.2%   │
│ ▓▓░     ▓▓▓░     ▓▓▓▓░  │
│ 1核     123/497  1.7/8G  │  ← 详细数值
├──────────────────────────┤
│ ↑ 2.0 kB/s  ↓ 3.8 kB/s  │  ← 实时网速
│ 上传: 15.7 GB            │  ← 总流量
│ 下载: 21.8 GB            │
├──────────────────────────┤
│ ⏱ 7天 16小时    [tag][tg]│  ← 运行时间 + 标签
└──────────────────────────┘
```

**改造要点：**
1. **顶部区域** — `Flag` + `StatusDot` + `displayName()` + OS/virt 信息，紧凑排列
2. **中部区域** — `grid grid-cols-3` 三列，每列一个 `MiniBar` 组件（标签 + 百分比 + 进度条 + 详细数值）
3. **网速区域** — 用 `ArrowUp`/`ArrowDown` 图标 + `bytes()` 格式化，颜色区分（emerald-400 上传，sky-400 下载）
4. **总流量** — 从 `node.dynamic.total_transmitted` / `total_received` 读取，用 `bytes()` 格式化
5. **底部区域** — 运行时间 `uptime()` + 标签 `tags`

**MiniBar 组件：**
```tsx
function MiniBar({ label, value, extra }: { label: string; value: number | undefined; extra?: string }) {
  return (
    <div className="min-w-0">
      <div className="text-[11px] text-muted-foreground mb-0.5">{label}</div>
      <div className="text-sm font-semibold">{pct(value)}</div>
      <div className="glass-progress mt-1 h-1.5">
        <div className={`glass-progress-indicator h-full ${loadColor(value)}`}
          style={{ width: `${Math.min(value ?? 0, 100)}%` }} />
      </div>
      {extra && <div className="text-[10px] text-muted-foreground mt-0.5 truncate">{extra}</div>}
    </div>
  )
}
```

**数据来源：**
- CPU: `deriveUsage(node).cpu`，核心数: `cpuLabel(node)`
- 内存: `deriveUsage(node).mem` / `memUsed` / `memTotal`
- 磁盘: `deriveUsage(node).disk` / `diskUsed` / `diskTotal`
- 网速: `deriveUsage(node).netIn` / `netOut`
- 总流量: `node.dynamic.total_received` / `total_transmitted`
- 运行时间: `deriveUsage(node).uptime`
- 标签: `node.meta?.tags`

## 踩坑记录（自定义改造）

### 🔴 TableView 总上传/总下载显示 0

**症状：** 表格视图的"总上传""总下载"列全部显示 0，但详情页的"累计发送""累计接收"有数据。

**根因：** `deriveUsage()` 只返回了 `netIn`/`netOut`（速率），没有返回 `netInTotal`/`netOutTotal`（累计总量）。表格列读的是累计值，但 `Usage` 类型里没有对应字段。

**修复：**
```typescript
// src/types.ts — Usage 接口添加字段
export interface Usage {
  // ...existing fields...
  netInTotal?: number   // 累计接收
  netOutTotal?: number  // 累计发送
}

// src/utils/derive.ts — deriveUsage 返回累计值
return {
  // ...existing...
  netInTotal: d?.total_received,
  netOutTotal: d?.total_transmitted,
}
```

⚠️ **规则：** `deriveUsage()` 是所有组件的单一数据源，新增显示字段时必须同步更新 `Usage` 类型 + `deriveUsage()` + 消费组件。

### 🔴 详情页出现两个顶部栏

**症状：** 进入服务器详情页后，主页的 Navbar 和详情页自己的顶部栏同时显示。

**根因：** `App.tsx` 中 Navbar 始终渲染，不区分主页/详情页。`NodeDetail` 内部有自己的 `glass-nav` 顶部栏（返回按钮+服务器信息）。

**修复：** 条件渲染 Navbar：
```tsx
// App.tsx
{!selectedNode && (
  <Navbar
    siteName={config.site_name || '你没设置'}
    logo={logo}
    query={query}
    onQuery={setQuery}
    view={view}
    onView={setView}
  />
)}
```

### 🔴 详情页滑到底部自动弹回顶部

**症状：** 在详情页滚动到底部后，页面立即跳回顶部。每次 WebSocket 数据更新都会触发。

**根因：** `useEffect` 的依赖数组包含 `onClose`（每次渲染生成新引用），导致 `scrollTo({top:0})` 在每次数据更新时重新执行。

**修复：** 拆分 useEffect，scrollTo 只依赖 `node.uuid`（稳定值）：
```tsx
// NodeDetail.tsx
useEffect(() => {
  if (!node) return
  window.scrollTo({ top: 0 })
}, [node?.uuid])  // ✅ 只在切换服务器时滚动

useEffect(() => {
  const onKey = (e: KeyboardEvent) => {
    if (e.key === 'Escape') onClose()
  }
  document.addEventListener('keydown', onKey)
  return () => document.removeEventListener('keydown', onKey)
}, [onClose])  // ✅ 键盘监听单独管理
```

⚠️ **规则：** useEffect 依赖中不要放函数引用（除非用 useCallback）。用 ID/UUID 等原始值做依赖。

### ⚠️ 源码分享前必须清理敏感信息

config.json 包含后端地址和 token。发给别人之前必须替换为占位符：

```bash
# 替换 config.json 为占位符
cat > public/config.json << 'EOF'
{
  "site_name": "银河探针",
  "site_tokens": [
    {
      "name": "your-backend-name",
      "backend_url": "wss://your-backend.example.com",
      "token": "your-token-here"
    }
  ]
}
EOF

# 打包
zip -r src.zip . -x "node_modules/*" "dist/*" ".git/*" "*.zip" "public/wallpaper.mp4"

# 恢复原始 config.json
git checkout public/config.json
```

⚠️ wallpaper.mp4 通常很大（30-40MB），打包时排除。

## 🔴 Token 安全红线

**严禁把真实 token 写入 GitHub**。NodeGet StatusShow 用 `scripts/build-config.mjs` 在构建时注入环境变量到 `public/config.json`。正确流程：

1. **GitHub 源码**：始终放占位符
   ```json
   {
     "site_name": "银河探针",
     "site_tokens": [
       {
         "name": "56idc-LA",
         "backend_url": "wss://statapi.357561.xyz",
         "token": "***"
       }
     ]
   }
   ```
2. **Vercel Dashboard**：Settings → Environment Variables，加入
   ```
   SITE_NAME = 银河探针
   SITE_1    = name="56idc-LA",backend_url="wss://statapi.357561.xyz",token="真实token"
   ```
   Production / Preview / Development 全部勾选，Save 后触发重新部署
3. **构建时**：`build-config.mjs` 读取环境变量，覆盖 `config.json`

### 真实 token 获取位置

⚠️ **两个配置文件路径，不要搞混：**

| 路径 | 内容 | 状态 |
|------|------|------|
| `/etc/nodeget-agent.conf` | Agent 安装时的旧配置 | **已失效**，不要用 |
| `/root/.config/nodeget-agent/config.toml` | 当前运行的 Agent 配置 | **真实可用 token** |

从服务器获取 token：
```bash
ssh -p PORT root@SERVER_IP "cat /root/.config/nodeget-agent/config.toml | grep -E 'token|ws_url'"
```

### 部署前验证 token

用 curl 直接测 token 是否可用，再部署：
```bash
curl -s -X POST -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"nodeget-server_list_all_agent_uuid","params":{"token":"真实token"},"id":"1"}' \
  https://statapi.357561.xyz
# 返回 {"uuids":[...]} = 可用；返回 error = token 已失效
```

### token 泄露处理流程（如果已经泄露）

```bash
# 1. 硬重置到干净版本（不保留任何敏感修改）
git reset --hard 7144d11   # 指向已知的干净版本
git push --force origin main

# 2. 立刻去 Vercel Dashboard 更新环境变量中的 token
# 3. 验证新 token 可用后再继续开发
```

## 构建

```bash
npm install
npm run build
# 产物在 dist/
```
