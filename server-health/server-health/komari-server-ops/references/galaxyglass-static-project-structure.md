# GalaxyGlass 静态版工程结构与工作流

> 适用于 `stat.357561.xyz` 的 Komari 探针面板。静态版 = 纯前端单页应用，无框架依赖，源码拆分在 `src/` 目录，编译为单文件 `index.html` 部署。

## 工程架构

```
galaxy-glass/
├── src/                          # ★ 源文件（改这里，不改根目录 index.html）
│   ├── index.html                HTML 模板（引用外部 CSS/JS）
│   ├── styles/
│   │   ├── tokens.css            CSS 变量（配色、间距、圆角、字体）
│   │   ├── reset.css             基础重置
│   │   ├── layout.css            导航、容器、网格、页脚、滚动条
│   │   ├── components.css        卡片、统计栏、筛选、搜索、详情页、图表
│   │   └── responsive.css        断点响应式
│   ├── scripts/
│   │   ├── config.js             常量、工具函数（$、bytes、uptime）
│   │   ├── data.js               API 请求（fetchJSON、loadData）、数据合并
│   │   ├── render.js             卡片渲染、统计更新、筛选构建
│   │   ├── charts.js             Canvas 图表（drawLineChart、drawNetChart）
│   │   └── events.js             事件绑定、详情视图、SPA 路由、初始化
│   └── squircle.svg              图标
│
├── index.html                    # ★ 编译产物（单文件内联版，不动它）
├── deploy.sh                     部署脚本
├── README.md
└── nextjs/                       Next.js 版本（项目的另一套，不是静态版）
```

### 编译流程

`src/` 下的多个文件需要编译成单文件 `index.html`（将 CSS 文件内容插入 `<style>`，JS 文件内容插入 `<script>`）。

**编译方式：** 目前没有自动化 build 脚本，每次修改 `src/` 后需手动将 CSS 内联进 `<style>` 标签、JS 内联进 `<script>` 标签，替换掉 `src/index.html` 中的外部引用。更推荐用内联工具或手写 build 脚本。

### 关键文件引用顺序

HTML 中 CSS 和 JS 的加载顺序不可调换：

```html
<!-- CSS：tokens → reset → layout → components → responsive -->
<link rel="stylesheet" href="styles/tokens.css">
<link rel="stylesheet" href="styles/reset.css">
<link rel="stylesheet" href="styles/layout.css">
<link rel="stylesheet" href="styles/components.css">
<link rel="stylesheet" href="styles/responsive.css">

<!-- JS：config → data → render → charts → events（config.js 必须先加载） -->
<script src="scripts/config.js"></script>      <!-- 定义 $, bytes, uptime, showConnToast -->
<script src="scripts/data.js"></script>        <!-- 引用 showConnToast（定义在 config.js） -->
<script src="scripts/render.js"></script>
<script src="scripts/charts.js"></script>
<script src="scripts/events.js"></script>      <!-- 最后 init -->
```

## 部署架构

```
用户浏览器 → stat.357561.xyz (Cloudflare)
  → Cloudflare Tunnel (cloudflared on 波兰机)
    → Komari server (127.0.0.1:25774)
      → 从 /opt/komari/data/theme/GalaxyGlass/dist/index.html 服务静态页面
```

**关键路径：** `/opt/komari/data/theme/GalaxyGlass/dist/index.html`

- Komari v1.2.0 的主题系统从 `GalaxyGlass/dist/` 子目录读取文件
- **不是**直接从 `/opt/komari/data/theme/` 根目录读取
- 主题配置文件：`GalaxyGlass/komari-theme.json`

## 开发与部署流程

### 正确的修改步骤

```bash
# 1. 编辑源文件（src/ 下）
vim src/styles/components.css    # 改样式
vim src/scripts/config.js        # 改 JS 逻辑

# 2. 编译 → 生成单文件 index.html
# （手动或跑 build 脚本，见下方）

# 3. 部署
bash deploy.sh
```

### 禁止

- ❌ 直接改根目录的 `index.html`（编译产物，改完不回源，下次编译覆盖）
- ❌ 直接改远程服务器上的文件（路径：`/opt/komari/data/theme/GalaxyGlass/dist/index.html`）
- ❌ 下载 GitHub Release asset 直接改（不是工程源，无法长期维护）

### deploy.sh

```bash
# 脚本位置：galaxy-glass/deploy.sh
# 从本地 index.html 部署到波兰机的 GalaxyGlass/dist/
# 需要 SSH 密钥：~/.ssh/hermes_admin
# 如果需要编译，先编译再跑 deploy
```

## 常见踩坑

### 1. 部署到错误路径

| 路径 | 效果 |
|------|------|
| `/opt/komari/data/theme/index.html` | ❌ Komari 不读这里 |
| `/opt/komari/data/theme/GalaxyGlass/dist/index.html` | ✅ 正确位置 |

### 2. 源文件 vs 编译产物

`src/` 下的文件使用外部引用（`<link href="styles/tokens.css">`），根目录 `index.html` 使用内联（`<style>` + `<script>`）。**开发改 `src/`，部署用根 `index.html`。**

### 3. 编译后的版本管理

根目录 `index.html` 是生成的，不应提交 git 变更。或者提交时只在发版时更新。当前 git HEAD 的 `index.html` 是 96846 字节的已提交版本。

### 4. `flagEmoji()` 缺失映射

如果新地区的 flag 图标不显示，需要修改 `src/scripts/config.js` 中的 `flagEmoji()` 函数（如果使用编译版，则改内联版中的对应函数）。

```javascript
// 添加台湾等映射
'🇹🇼':'tw', '🇰🇷':'kr', '🇸🇬':'sg'
```

### 5. 登录按钮 → 在线人数

如需替换，涉及三个文件：
- **HTML**：`src/index.html` 中找到 `<a class="sort-btn" id="login-btn"...>` 替换
- **CSS**：`src/styles/components.css` 或 `layout.css` 中加 `.online-badge` 样式
- **JS**：`src/scripts/config.js` 或 `events.js` 中加 `startHeartbeat()` 函数
