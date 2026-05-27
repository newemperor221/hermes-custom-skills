---
name: Glass-workflow
description: Glass Komari 探针面板的工程化工作流 — src/ 源码结构、build.sh 编译、deploy.sh 部署、release 打包、服务器路径、踩坑记录
tags: [glass, komari, build-pipeline, deployment, static-site, frontend]
---

# Glass 工程化工作流

> stat.357561.xyz 探针面板 · 纯静态单文件 · 零依赖

## 前置要求

UI 修改前：`browser_navigate(url)` → 截图分析 → 一次性修复所有问题 → 部署 → 发截图验证。**不要逐个问「这个要不要改」**。

## 核心工作流：先看再改，不问直接修

**这是最重要的规则。用户对「边做边问」深恶痛绝。**

每次 UI 类请求的正确处理顺序：

1. **浏览器打开页面** → `browser_navigate(url)` → 先看实际情况
2. **截图分析** → `browser_vision(question='完整页面截图，指出所有布局问题')` → 一次性识别所有问题
3. **批量修复** → 把所有问题一次性改完，不要逐个问"这个要不要改"
4. **构建部署** → `build.sh && deploy.sh`
5. **截图验证** → 再打开页面截图，通过 MEDIA 发送给用户看
6. **控制台验证**（非纯视觉修改时）→ `browser_console` 执行：
   - `document.querySelectorAll('.new-class').length` 确认元素存在
   - `document.getElementById('removed-element')` 确认已删除的元素返回 null
   - 详情页修改时：`document.getElementById('detail-loading')?.classList.contains('hidden')` → `true`

**绝对不要做的事：**
- ❌ 问用户"你指的是哪个问题"——直接去看
- ❌ 问用户"要不要改这个"——一次改完
- ❌ 只改了一半就问"你看这样行不行"——全改完再展示
- ❌ 用文字描述修改结果——发截图

**用户典型不耐烦信号**（一旦出现以下任一，立刻停止问问题，直接去页面看）：
- "你他妈……"
- "我很满意吗？不及格"
- "都干了快20天了"
- "我倒要看看你要学多久"
- "你自己不会去看？"

## 项目结构

\`\`\`
glass/
├── build.sh                # 编译：src/ → 单文件 index.html
├── deploy.sh               # 构建 + 部署到 Komari 面板
├── release.sh              # 构建 + 打包 + GitHub Release 一键发布
├── komari-theme.json       # Komari 主题元数据（name: "Glass"）
├── icon.svg                # 主题图标
├── preview.png             # 预览截图
├── ARCHITECTURE.md         # 架构说明（ITCSS 分层、开发流程、记忆点）
├── ARCHITECTURE.md         # 架构说明（ITCSS 分层、开发流程、记忆点）
├── .gitignore
├── README.md
└── src/
    ├── index.html          # HTML 模板（{{CSS}} {{JS}} {{BODY}} 占位符）
    ├── body.html           # HTML body 内容
    ├── styles/             # ITCSS 分层（settings → base → layout → components → states → utilities → web → mobile）
    │   ├── settings.css    # CSS 变量（配色/尺寸/字体/间距令牌）
    │   ├── base.css        # 裸元素样式（reset + body/a/img）
    │   ├── layout.css      # 页面骨架（navbar/container/footer/bg-layer/grid）
    │   ├── components.css  # 可复用 UI 组件（search/card/filter/detail/chart/toast）
    │   ├── states.css      # 状态覆盖（loading/error/paused/online/offline）
    │   ├── utilities.css   # 工具类（.hidden/::-webkit-scrollbar/@keyframes）
    │   ├── web.css         # 桌面端覆盖（≥640px）
    │   └── mobile.css      # 手机端覆盖（≤800px）
    └── scripts/
        └── app.js          # 全部脚本（单文件，因原始代码是 IIFE 无模块边界）
```

## 开发流程

```bash
# 修改源码
vim src/styles/components.css    # 改组件样式
vim src/styles/web.css           # 桌面端微调
vim src/styles/mobile.css        # 手机端适配
vim src/scripts/app.js           # 改逻辑/图标等

# 编译 → 部署
./build.sh          # src/ → 根目录 index.html
./deploy.sh         # build + scp 到服务器
```

## CSS 分拆规则（ITCSS 分层）

> 顺序决定构建层级：settings → base → layout → components → states → utilities → web → mobile
> 低特异性 → 高特异性，通用 → 具体

| 文件 | ITCSS 层 | 作用 | 修改场景 |
|------|----------|------|---------|
| `settings.css` | Settings | CSS 变量（配色/字体/spacing/圆角） | 改品牌色/全局间距/字体栈 |
| `base.css` | Generic + Elements | Reset + 裸标签样式（`*`, `body`, `a`, `img`） | 改全局字体/背景/链接颜色 |
| `layout.css` | Objects | 页面骨架（navbar/container/footer/grid/bg-layer） | 改导航/页脚/背景层/容器宽度 |
| `components.css` | Components | 可复用 UI 组件（search/card/filter/detail/chart/toast/live） | 该卡片/搜索框/筛选栏/详情页/图表 |
| `states.css` | — | 状态覆盖（`.loading-state`, `.paused`, `.online/offline`） | 改加载态/暂停态/在线状态样式 |
| `utilities.css` | Utilities | 工具类（`.hidden`/`::-webkit-scrollbar`/`@keyframes`） | 改滚动条/全局动画 |
| `web.css` | — | `@media (min-width)` 桌面专用 | 桌面大屏网格/内边距调整 |
| `mobile.css` | — | `@media (max-width)` 手机专用 | 手机单列/搜索折叠/字号缩小 |

> **为什么 web.css 和 mobile.css 拆开？** 用户要求区分 Web 端和手机端。拆成独立文件后每端目标更清晰，避免混在同一个 @media 块里。
>
> **为什么 tokens.css 拆成了 settings.css + base.css + layout.css？** 遵循 ITCSS 分层原则：CSS 变量（无实际输出）→ 裸元素样式（低特异性）→ 页面骨架。每层职责单一，方便定位。

## 编译管道（build.sh）

1. 读取 `src/index.html` 模板（含 `{{CSS}}` `{{JS}}` `{{BODY}}` 占位符）
2. 按 ITCSS 顺序内联 CSS：`settings.css` → `base.css` → `layout.css` → `components.css` → `states.css` → `utilities.css` → `web.css` → `mobile.css`
3. 内联 JS：`src/scripts/app.js`（单文件，IIFE 无模块边界）
4. 内联 Body：`src/body.html`
5. 替换占位符输出到根目录 `index.html`
6. 验证：确认所有占位符已被替换，`<style>` 和 `<script>` 标签存在

使用 Python heredoc 嵌入模板替换逻辑（`python3 << 'PYEOF'`），避免 shell 变量替换干扰 `{{...}}` 占位符。

## 部署架构（重要：双机模型）

```
Cloudflare ─→ cloudflared tunnel ─→ 波兰主控 (31.58.51.127:25774) → komari 直接服务（内嵌主题）
                                                                         └→ 读取 SQLite 数据库

本地开发机 (CCS LA 198.46.147.71) → galaxykit/ 仓库 → build.sh → scp → 波兰主控
```

### ⚠️ 核心规则：Komari 直接服务是唯一受支持的架构

**重要：Glass 是纯 Komari 主题，不涉及任何 NodeGet 元素。** 代码、文档、Release 包中不得出现 "NodeGet" 字样。服务器上的 `/opt/komari/data/theme/NodeGetGlass/` 是旧主题残留目录，非项目内容。

**当前线上状态（2026-05-19，经用户多次确认）：komari 直接在 :25774 提供服务，使用其内嵌的 Glass 主题。**

```
stat.357561.xyz → Cloudflare → cloudflared tunnel → 波兰主控 :25774 → komari 内嵌主题
```

**galaxy-proxy.py 已被用户明确拒绝。** 不要部署 galaxy-proxy 替代 komari 直接服务。

原因：galaxy-proxy.py 从磁盘读取 `/opt/komari/data/theme/index.html` 来提供前端页面。但这个磁盘上的 theme 文件与 komari 二进制内嵌的 Glass 主题版本不同。切换后会导致：
- 页面标题从 "GG 探针" 变为 "Komari Monitor"
- 卡片标题行布局变成「吕字型」（两行错位）
- 用户每次因此发火并要求立即恢复

**用户已因 galaxy-proxy 导致「吕字型」而臭骂我两次。保持 Glass 源码与 komari 布局一致后再部署 galaxy-proxy。**

### galaxy-proxy.py（当前部署方案）

galaxy-proxy.py 读取磁盘 `index.html`，代理 `/api/` 请求到 komari 后端。用于绕过 komari 内嵌模板的 JS 渲染 bug。

部署：参见「部署路径」一节。

⚠️ 注意：galaxy-proxy 的 CSS 必须与 komari 内嵌主题一致，否则出现「吕字型」。

### Cloudflare 缓存注意事项

- `cf-cache-status: DYNAMIC` → Cloudflare 不主动缓存此页面
- 但浏览器可能有本地缓存 → 通知用户 Ctrl+F5 硬刷新
- 无 Cloudflare API key 时可添加 `?_=<timestamp>` 缓存破坏参数

## 部署路径（galaxy-proxy 架构）

galaxy-proxy 在 :25774 提供静态页面，komari 在 :25776 做后端 API。部署时需确保两者都更新。

```bash
# 1. 编译
./build.sh

# 2. SCP 到波兰主控
scp -i ~/.ssh/hermes_admin -P 46748 index.html root@31.58.51.127:/opt/komari/data/theme/

# 3. 如果 galaxy-proxy 已在运行，文件更新立即生效（galaxy-proxy 每次请求读磁盘）
#    不需要重启 galaxy-proxy

# 4. 验证内部
ssh -i ~/.ssh/hermes_admin -P 46748 root@31.58.51.127 "curl -s http://127.0.0.1:25774/ | head -c 200"

# 5. 验证公网
curl -sI https://stat.357561.xyz/
```

**如果 galaxy-proxy 没在跑，从零部署：**
```bash
# 波兰主控上：
kill $(lsof -ti :25774) 2>/dev/null   # 停旧服务
cd /opt/komari
nohup ./komari server -d ./data/komari.db -l 0.0.0.0:25776 > /dev/null 2>&1 &  # komari 后端
cd /opt/komari/data/theme
nohup python3 galaxy-proxy.py > /dev/null 2>&1 &  # galaxy-proxy 前端
/etc/init.d/cloudflared restart  # 隧道
```

## 常见操作

### 添加新地区图标

修改 `app.js` 中的 `flagEmoji` 函数：

```javascript
var m = {'🇺🇸':'us','🇯🇵':'jp','🇭🇰':'hk','🇳🇱':'nl',
         '🇰🇵':'kp','🇩🇪':'de','🇸🇬':'sg','🇬🇧':'gb',
         '🇰🇷':'kr','🇨🇳':'cn','🇷🇺':'ru','🇨🇦':'ca',
         '🇦🇺':'au','🇹🇼':'tw'};
```

加一行 `'🇸🇪':'se'` 编译部署即可。

### 替换登录按钮为在线人数

1. 在 `body.html` 的 navbar 中找到 `<a class="sort-btn" id="login-btn"`... 替换为 `<span id="online-count">`
2. 在 `app.js` 中添加 `localStorage + BroadcastChannel` 心跳统计逻辑

### 删除 UI 元素（通用模式）

删除任何界面元素（如 Live badge、登录按钮、统计卡片）时，必须**同步修改 3 个源文件**，否则构建产物会出错或留下死代码：

1. **`src/body.html`** — 删除对应的 HTML 标签/容器
2. **`src/styles/components.css`** — 删除对应的 CSS 类/动画/关键帧（同时检查 `mobile.css` 里有没有同名覆盖）
3. **`src/scripts/app.js`** — 删除对应的 JS 函数和所有调用点（用 `grep` 确认没有其他引用）

**⚠️ 常见陷阱：删除 HTML 元素后 JS 引用会导致静默崩溃**

如果从 `body.html` 删除了一个有 ID 的元素（如 `#detail-metrics`），但在 `app.js` 中仍有 `getElementById('detail-metrics')` 的引用，会导致：
- `getElementById` 返回 `null`
- `null.something = ...` 抛出 TypeError
- 如果这个代码在 promise `.then()` 回调内，异常被 promise 链吞掉，**控制台看不到错误**
- 函数剩余代码（sysinfo、图表渲染等）全部不执行
- 用户看到「加载详情…」永远转圈

**预防**：删除 HTML 元素后，用 `grep -n 'detail-metrics' src/scripts/app.js` 确认 JS 中无残留引用。

**验证**：部署后打开浏览器控制台运行：
```javascript
// 被删除的元素应为 null
document.getElementById('detail-metrics') // → null ✅

// 详情页渲染检查
document.getElementById('detail-name')?.textContent // → 不是 'null' ✅
document.getElementById('detail-loading')?.classList.contains('hidden') // → true ✅
```

**示例**（删除 Live badge）：
- `body.html`：删除 `<div class="live-badge" id="live-badge">...Live</div>` 所在的 flex 容器
- `components.css`：删除 `.live-badge`、`.live-dot`、`@keyframes live-pulse`、`.live-badge.paused` 全部声明
- `app.js`：删除 `updateLiveBadge()` 函数和 `updateLiveBadge()` 调用行（位于 `togglePauseBtn` 内）

**验证**：build 后 grep 搜索旧类名/ID 确认无残余，部署后 browser_vision 截图确认。

**额外验证（非视觉类修改）**：如果修改涉及 JS 逻辑或 DOM 元素增删，打开浏览器控制台运行：

```javascript
// 检查 JS 是否报错
'JS errors: ' + (window.__errorCount || '(none)')

// 检查元素是否存在
document.getElementById('deleted-element') // → 应该为 null

// 检查结构正确性
document.querySelectorAll('#container > .child-selector').length // 应该 > 0

// 检查详情页渲染（如果有）
document.getElementById('detail-name')?.textContent // → 节点名，不是 'null'
document.getElementById('detail-loading')?.classList.contains('hidden') // → true
```

### 详情页移除指标卡片

当用户要求「把详情页的服务器卡片去掉」时，指的是详情页左侧 metrics-grid 中的 6 个指标卡片（CPU、内存、磁盘、在线、网络、流量）。

**3 步删除**：

1. **`src/scripts/app.js`** — 将 `$('detail-metrics').innerHTML=[...].map(...).join('')` 替换为 `$('detail-metrics').innerHTML=''`
2. **`src/body.html`** — 删除 `<div class="metrics-grid" id="detail-metrics"></div>` 行
3. **`src/styles/components.css`** — 删除 `.metrics-grid`、`.metric-card` 及其所有子选择器

注意：保持 `$('badge-cpu').textContent`、`$('badge-mem').textContent`、`$('badge-net').textContent` 这三行，因为图表（chart-card）的标题栏仍需要显示当前数值。

### 布局宽度一致性检查

如果用户反馈"内容宽度和顶部栏/底部栏不一致"，优先检查 `.container` 类：

- 顶部 navbar、中间 main、底部 footer 全部使用同一个 `.container` 类（`max-width: var(--container-max)` + `padding: 0 var(--container-pad)`）
- 默认 `--container-max: 1280px`，`--container-pad: 1.75rem`（在 `settings.css` 中）
- **三者宽度天然一致**，不需要额外样式。用户说不对齐时，先用 browser_vision 截图确认视觉偏差再动手。
- 常见误报：统计卡片行（stat-card）用了 `style="flex:1"` 撑满容器，视觉上可能看起来比 navbar 窄，实际是卡片内边距的错觉。用开发者工具 inspect `.container` 的实际 box-model 确认。

## UI 改进模式

### NET 行：纯文字 → 可视化进度条

卡片内 NET 行原来只有文字 `↑416B/s ↓720B/s`，视觉重量不如 CPU/MEM/DSK 的进度条。

**做法**：在 NET 行插入 `.cm-bar > .cm-fill`，宽高同 CPU 指标条。上行比例用 `up/(up+down)` 计算。CSS 中 `.cm-fill.up` 用绿色渐变 `linear-gradient(90deg, var(--accent), #34d399)`，与上行色一致。

```javascript
// app.js renderCard() — NET 行
+'<div class=\"card-metric net-row\">'
+'<span class=\"cm-label\">NET</span>'
+'<div class=\"cm-bar\"><div class=\"cm-fill up\" '
+  'style=\"transform:scaleX('+Math.min(1,(up||0)/Math.max(1,up+down))+')\"></div></div>'
+'<span class=\"cm-value\">'
+  '<span class=\"up\">↑'+bytes(up)+'/s</span>'
+  '<span class=\"down\">↓'+bytes(down)+'/s</span>'
+'</span></div>'
```

CSS 对应类：

```css
.card-metric.net-row .cm-bar { flex: 1; height: 6px; ... }
.card-metric.net-row .cm-fill.up { background: linear-gradient(90deg, var(--accent), #34d399); }
```

### 价格标签：高亮 → 弱化

原来价格标签用 `background: var(--accent-gradient)` 渐变背景，每个卡片都有，反而没有重点。

**做法**：去掉渐变背景，改成 `border: 1px solid var(--glass-border)` 细边框 + `color: var(--text-secondary)` 弱色。只有"即将到期"的节点才用醒目标签（如需要则添加 `.price-badge.danger` 变体）。

```css
.price-badge {
  margin-left: auto; font-weight: 600; color: var(--text-secondary);
  padding: 2px 7px; border-radius: var(--radius-full);
  border: 1px solid var(--glass-border);
  font-size: 11px; line-height: 1.4;
}
```

### 手机端 chip 缩小

9+ 个地区筛选 chip 在手机上撑满屏，需左右滑动。缩小 chip 尺寸改善体验：

```css
@media (max-width: 480px) {
  .chip { font-size: 11px; padding: 0 8px; height: 26px; gap: 2px; }
  .chip img { width: 16px; height: 11px; }
}
```

## 架构状态变更记录

**当前状态（2026-05-20）**：galaxy-proxy 在 :25774 提供修复后的 Glass 页面，komari 在 :25776 做后端 API。

**历史：**
- **2026-05-18**：部署 galaxy-proxy → 页面变「吕字型」→ 回退到 komari 直接服务
- **2026-05-19**：再次部署 galaxy-proxy → 又变吕字型 → 用户臭骂后回退
- **2026-05-20**：修掉 Glass 源码的 `'` 前缀和双圆点 bug → 部署 galaxy-proxy → 成功验证 ✅

**关键教训**：吕字型的根因不是 galaxy-proxy 本身，而是磁盘 index.html 与 komari 内嵌模板的 CSS 不一致。保持 Glass 源码与 komari 的 CSS 一致后，galaxy-proxy 可正常使用。

如需修改主题，正确的做法是：
1. 在本地开发机的 `Glass/src/` 下修改源码
2. `./build.sh` 编译
3. `./deploy.sh` scp 到波兰主控的 `/opt/komari/data/theme/index.html`
6. 如果需要让修改生效，通过 galaxy-proxy 部署（参见「galaxy-proxy.py」一节）——2026-05-20 已验证可行。

**当前架构无法修改前端布局，能做的只有：**
- 改数据库数据（节点名、价格、地区等）
- 重启服务
- 调整 cloudflared 隧道

## 推送当前状态到 GitHub

当用户要求「把现在的推送到 GitHub」时：

```bash
cd ~/glass
git add -A
git commit -m "chore: sync current deployed theme state"
git push origin main
```

注意：`index.html` 是 build 产物（src/ → build.sh 生成）。如果同时修改了 src/ 下的源文件，commit 会同时包含 src/ 修改和编译产物修改。直接全部提交即可。

## GitHub Release 工作流

当用户要求「打包 release」时：

### 方式一：一键发布（推荐）

```bash
./release.sh v1.0.1
```

自动完成：构建 → 打包（正确格式的 zip）→ 推 tag → 创建 GitHub Release 并上传附件。

### 方式二：手动打包（备用）

如果 `release.sh` 尚未提交到仓库，或需要手动控制：

### 1. 确认版本

```bash
# 查看 komari-theme.json 当前版本
cat komari-theme.json | grep version

# 查看已有 tags
git tag -l | sort -V
```

### 2. 版本升级

```bash
# 修改 komari-theme.json 中的 version 字段，按语义化版本递增
# 如 2.5.0 → 2.6.0（小功能/修复变更）

# 提交版本变更
git add komari-theme.json
git commit -m "chore: bump version to 2.6.0"
git tag v2.6.0
git push origin main --tags
```

### 3. 打包 release 包

> ⚠️ **2026-05-20 重要修正**：Komari 主题 web UI 上传（设置 → 主题管理 → 上传主题）要求特定目录结构。**错误的包结构会导致上传后无法正确导入。**

Komari 主题 release 包的正确结构（参考官方 `komari-next` release）：

```
Glass-vX.Y.Z.zip
├── komari-theme.json      ← zip 根目录（Komari 读取元数据）
├── icon.svg               ← 主题图标
├── preview.png            ← 预览图
└── dist/
    └── index.html         ← 主题主页（Komari 服务此目录下的静态文件）
```

```bash
rm -rf /tmp/Glass
mkdir -p /tmp/Glass/dist
cp index.html /tmp/Glass/dist/
cp komari-theme.json icon.svg preview.png /tmp/Glass/
cd /tmp
zip -r Glass-v1.0.0.zip Glass/
```

| 文件 | 位置 | 用途 | 来源 |
|------|------|------|------|
| `index.html` | `dist/` | 核心主题入口（单文件，所有 CSS/JS 内联） | build.sh 编译产物 |
| `komari-theme.json` | 根目录 | Komari 主题元数据（名称/版本/预览/作者） | 仓库根目录 |
| `icon.svg` | 根目录 | 主题图标 | 仓库根目录 |
| `preview.png` | 根目录 | 预览截图（主题管理界面展示） | 仓库根目录 |

**注意**：
- `.gitignore` 可能排除了 `*.png`，但不影响打包（preview.png 只在工作目录存在，不被 git 跟踪但可被 zip 打包）。
- **绝对不要**把 `index.html` 放在 zip 根目录（如旧格式 `Glass/index.html`），那样 Komari 主题上传界面无法识别。
- 如果已上传了错误的 release 包，用 `gh release delete-asset vX.Y.Z filename.zip -y && gh release upload vX.Y.Z /tmp/newfile.zip --clobber` 替换资产。

### 4. 创建 GitHub Release

```bash
cd ~/glass
gh release create v2.6.0 \
  --title "Glass v2.6.0" \
  --notes "## Glass v2.6.0

### ✨ 变更内容

(列出本版本的修改项)

### 📦 安装

解压到 Komari 主题目录：

\`\`\`bash
unzip Glass-v2.6.0.zip -d /opt/komari/data/theme/
\`\`\`

然后重启 Komari 或刷新页面即可。" \
  /tmp/Glass-v2.6.0.zip
```

### 5. 验证

```bash
gh release view v2.6.0 --repo newemperor221/glass
# 确认：title、asset 名称、url 正确

# 额外验证：下载 zip 确认内部结构
curl -sL -o /tmp/verify.zip "https://github.com/newemperor221/glass/releases/download/v2.6.0/Glass-v2.6.0.zip"
unzip -l /tmp/verify.zip
# 确认结构：komari-theme.json 在根目录，index.html 在 dist/ 下
```

### 版本号对照

| komari-theme.json | git tag | Release 名称 |
|-------------------|---------|--------------|
| 1.0.0 | v1.0.0 | Glass v1.0.0 |

注意：komari-theme.json 的版本号应始终与 git tag 一致。如果已存在该版本的 tag，需要先递增再创建 release。

## 项目重命名工作流（通用）

当用户要求更改主题名称（包括 GitHub 仓库名和所有引用）时，按此流程执行：

### 1. 更新所有源文件中的名称引用

```bash
# 需修改的文件清单：
# komari-theme.json  — name, short, url, description, version（全新开始则重置为 1.0.0）
# README.md          — 标题、描述、打包示例
# build.sh           — echo 消息
# deploy.sh          — 注释、REMOTE 路径、STATIC_FILE 路径
# release.sh         — 注释、PKG_NAME/PKG_DIR、title、echo 消息、GitHub URL
# ARCHITECTURE.md    — 标题、部署路径、项目结构说明
```

使用 `patch` 工具逐个替换，或 `replace_all: true` 批量替换。

**关键字段**：
- `komari-theme.json` version：如果是全新品牌更名，重置为 `1.0.0`
- `deploy.sh` REMOTE 路径：`/opt/komari/data/theme/新名/dist`
- `release.sh` PKG_NAME/PKG_DIR：`新名-${VERSION}`
- GitHub URL：`https://github.com/用户名/新库名`

### 2. 提交并推送代码

```bash
git add -A
git commit -m "rename: Glass → Glass"
git push origin main
```

### 3. 重命名 GitHub 仓库

```bash
gh repo rename 新名 --repo 用户名/旧名
git remote set-url origin git@github.com:用户名/新名.git
```

### 4. 推送 tag 并创建 release（全新开始）

```bash
# 删除旧 release/tag
gh release delete v旧版 --repo 用户名/新名 -y
git tag -d v旧版
git push origin --delete v旧版

# 构建 + 打包 + 发版
./build.sh
mkdir -p /tmp/新名-v1.0.0/dist
cp index.html /tmp/新名-v1.0.0/dist/
cp komari-theme.json icon.svg preview.png /tmp/新名-v1.0.0/
cd /tmp && zip -r 新名-v1.0.0.zip 新名-v1.0.0/

# 创建新 tag 和 release
git tag v1.0.0 && git push origin v1.0.0
gh release create v1.0.0 --title "新名 v1.0.0" --notes "..." /tmp/新名-v1.0.0.zip
```

### 5. 更新服务器目录

```bash
ssh -i ~/.ssh/hermes_admin -p 端口 root@服务器 \
  "mv /opt/komari/data/theme/旧名 /opt/komari/data/theme/新名 && \
   cp /opt/komari/data/theme/新名/dist/index.html /opt/komari/data/theme/index.html"
```

### 6. 重命名本地目录（可选但推荐）

```bash
cd ~ && mv ~/旧名 ~/新名
```

⚠️ 注意：重命名后需确认所有脚本中的绝对路径都已更新（如 deploy.sh 的 STATIC_FILE）。

## 主题命名原则

**不要凭空取名。** 先用 vision 工具实际看截图，再根据视觉特征来命名。

1. 打开页面 (`browser_navigate(url)`)
2. 截图分析 (`browser_vision(question='描述视觉风格: 颜色、质感、氛围')`)
3. 提取核心视觉要素（底色、玻璃效果、点缀色、整体感觉）
4. 基于实际特征取名，避免空洞的「星/银河/宇宙」类词汇
5. 名字应该让其他开发者在看到主题截图时能联想到

**用户偏好**：名称必须精确反映视觉特征。如果主题底色是深黑（`#020203`），就用 Dark/Deep/Void 之类的词，而不是 Galaxy。如果卡片有毛玻璃效果，就用 Frost/Glass。名称不是用来好听，是用来准确描述。用 vision 工具实际看截图才能准确判断。`

## JS 模板调试：检查 HTML 字符串拼接中的转义字符

当渲染结果出现意外的多余字符（如名字前多出 `'`、多余标签、重复元素）时，**不要先查数据源**——先查 `renderCard()` 等 HTML 拼接函数。

**调试步骤：**

1. `curl -s https://stat.357561.xyz/ | grep -oP 'node-name">[^<]*'` — 检查 SSR 渲染结果
2. `sed -n '31p' src/scripts/app.js | cat -v` — 查看模板源码，`cat -v` 显示转义字符的原始字节
3. 特别检查 JS 字符串中的 `\\'`（反斜杠+单引号）→ 在 JS 字符串中产生一个字面量 `'`
4. 特别检查 `\"` 和 `\\"` 多层转义 → 检查实际渲染的 HTML 属性

**典型模式：**
```javascript
// ❌ 会渲染为：<div class="node-name">'Name</div>
+'...<div class=\"node-name\">\\''+(n.name||'—')+'</div>...'

// ✅ 正确：<div class="node-name">Name</div>
+'...<div class=\"node-name\">'+(n.name||'—')+'</div>...'
```

**检查重复元素的命令：**
```bash
# 检查 JS 模板中是否渲染了两次同类元素
grep -c 'status-dot\|node-status' src/scripts/app.js
# 检查 CSS 是否定义了同名类两次
grep -c '\.node-status\b\|\.status-dot\b' src/styles/components.css
```

## Komari API 兼容性检查

当 Glass 主题需要确认 API 端点兼容性时，直接请求 komari 服务：

```bash
ssh 波兰主控 "curl -s http://127.0.0.1:25774/api/nodes | head -c 500"
ssh 波兰主控 "curl -s http://127.0.0.1:25774/api/public | head -c 500"
ssh 波兰主控 "curl -s http://127.0.0.1:25774/api/recent/ccs-la2 | head -c 500"
```

| 端点 | komari 原生 | 响应格式 | 说明 |
|------|------------|---------|------|
| `/api/nodes` | ✅ | `{status, data: [{uuid, name, region: "🇺🇸", ...}]}` | nodes_list，region 是 emoji |
| `/api/public` | ✅ | `{status, data: {sitename, theme_settings, ...}}` | 站点配置 |
| `/api/recent/{uuid}` | ✅ | `{status, data: [{cpu:{usage}, ram:{total,used}, ...}]}` | 历史记录 |
| `/api/proxy/exchange-rate` | ❌ | galaxy-proxy 自定义 | 无汇率时回退 6.82 |
| `/api/clients` | ⚠️ | 仅 WebSocket | HTTP 返回 400 |

**关键发现：komari 的 region 字段是 emoji 格式（如 `🇺🇸`），不是国家代码**。`flagEmoji` 函数用 emoji → 国家代码映射，需要保持与 komari API 返回的 emoji 一致。

## 关键架构发现：SSR 与 JS 模板的不一致

**这是 Glass 主题最隐蔽、也最常引发混淆的问题。**

Komari 二进制的页面渲染分两层：

1. **SSR（服务端渲染）** — Go 模板在服务端生成初始 HTML。这层通常是*干净*的（无多余字符、无重复元素）。
2. **JS 模板（客户端渲染）** — 嵌入在 HTML 中的 JavaScript `renderCard()` 函数在数据更新时重新生成卡片 HTML。**这层可能有 bug。**

这意味着：
- 用户**首次打开页面**看到的可能是干净的（SSR 已运行）
- 但等几秒 JS 数据轮询更新后，**所有卡片被 JS 模板重新渲染**，bug 就出现了
- 所以用 `curl` 检查 SSR 可能看不出问题，需要检查 HTML `<script>` 中的 JS 模板字符串

**调试步骤：**

```bash
# 1. 检查 SSR 渲染（首次加载）——可能干净
curl -s https://stat.357561.xyz/ | grep -oP 'node-card-header">.*?</div></div>' | head -1

# 2. 检查 JS 模板（数据更新后使用）——bug 可能在这里
curl -s https://stat.357561.xyz/ | grep -oP "renderCard.*?function" 
# 查找 renderCard 后面跟着的 HTML 拼接字符串

# 3. 对比两者差异
# SSR 有 1 个圆点 → JS 模板可能有 2 个
# SSR 名字无 ' 前缀 → JS 模板可能有
```

**已验证的两个 JS 模板 bug（komari 二进制内嵌）：**
```javascript
// Bug 1: \' 前缀 — 渲染出 'Name
\\''+(n.name||n.uuid||'—')

// Bug 2: 双状态圆点 — node-status（外部）+ status-dot（node-name 内部）
<div class=\"node-status '+(on?'online':'offline')+'\"></div>         ← 圆点1
...
<span class=\\"status-dot '+(on?'online pulse':'offline')+'\\"></span>  ← 圆点2（冗余）
```

**修复方案：**

1. 在 Glass 源码的 `app.js` 中删除 `\'` 前缀和多余 `status-dot` span
2. 通过 `build.sh` 编译生成干净的 `index.html`
3. 通过 galaxy-proxy 部署（此时 galaxy-proxy 读磁盘文件，不再受 komari 内嵌模板的限制）

**2016-05-20 验证：galaxy-proxy + 修复后的 Glass 源码成功工作，单引号和双圆点均消失。**

### 15. `detail-content-wrap` 缺少 id 导致 JS 克隆插入失败

当 JS 代码使用 `document.getElementById('detail-content-wrap')` 时，如果 HTML 中对应的 div 只有 class 没有 id，返回 `null` 导致整个插入操作静默失败。

**症状**：详情页正常加载（导航栏 + 加载指示器 + 内容），但 JS 动态插入的元素（如克隆的 stats-bar）不出现。控制台无错误（仅 `document.getElementById` 返回 null 不触发异常）。

**修复**：给目标元素显式添加 `id` 属性：
```html
<!-- ❌ 只有 class -->
<div class="detail-content-wrap">

<!-- ✅ 加上 id -->
<div class="detail-content-wrap" id="detail-content-wrap">
```

**预防**：在 body.html 中新增任何计划被 JS 通过 `$('id')` 访问的容器时，必须同时添加 class 和 id。

### 16. `updateStats` 必须更新全部匹配元素（处理 JS 克隆）

当使用 JS 克隆模式将 stats-bar 克隆到详情页时，DOM 中存在两个相同 ID 的 stats-bar 及其子元素。
`getElementById` 只返回第一个（DOM 顺序靠前的隐藏元素），克隆的可见 stats-bar 不会被更新。

**修复**：用 `document.querySelectorAll('#id')` 替换 `$(id)`，遍历更新全部匹配元素：
```javascript
// ❌ 只更新原始 stats-bar
$('stat-online-value').textContent = '5/10';

// ✅ 更新所有匹配元素（包括详情页的克隆）
document.querySelectorAll('#stat-online-value').forEach(function(e){
  e.textContent = '5/10';
});
```

### 17. 共享 UI 元素跨视图：JS 克隆而不是改 HTML 结构

当两个视图（列表/详情）需要共享同一个 UI 元素时（如 stats-bar），**绝对不要修改 HTML 布局结构**。之前把 stats-bar 从 list-view 的 main.container 移到 navbar 外面的尝试导致了 DOM 结构损坏（丢失 region-filters-wrap 打开标签）。

**正确做法**：JS 动态克隆 + 销毁，不碰 HTML：
```javascript
function showDetailView(uuid){
  // ...切换视图显示
  if(!window._statsClone){
    var sb = document.getElementById('stats-bar');
    var clone = sb.cloneNode(true);
    var wrap = document.getElementById('detail-content-wrap');
    wrap.parentNode.insertBefore(clone, wrap);
    window._statsClone = clone;
  }
  // ...加载数据
}

function showListView(){
  // ...切回列表
  if(window._statsClone){
    window._statsClone.parentNode.removeChild(window._statsClone);
    window._statsClone = null;
  }
}
```

**克隆后裁剪**：如果只需要部分子元素（如只保留时间卡片、去掉统计卡片），克隆后从 DOM 移除多余子节点：
```javascript
var kids = clone.querySelectorAll('.stat-card');
for(var i = kids.length-1; i >= 1; i--) kids[i].parentNode.removeChild(kids[i]);
clone.style.gridTemplateColumns = '1fr';  // 单列布局
```

## 踩坑记录

1. **不要合并 JS 文件，也不要强行拆分**：原始代码是一个 IIFE，函数间通过 `var` 共享作用域。强行按文件名拆分会导致函数找不到变量而白页。最佳实践是保持单文件 `app.js`。

2. **不要从 git 历史恢复旧 JS 文件**：不同版本的 JS 函数签名/变量名不同，混用会导致页面空白。

3. **const 重复声明报错**：多文件合并在一个 `<script>` 块中时，`const` / `let` 重复声明会抛出 `SyntaxError`。所有变量应该用 `var`。

4. **部署路径二重性**：`Glass/dist/` 和 `theme/` 根目录都有 `index.html`，旧根目录文件会挡住新版本。两个都要覆盖。

5. **build.sh 的 Python heredoc**：使用 `python3 << 'PYEOF'` 嵌入 Python，避免 shell 变量展开干扰 `{{...}}`。

6. **build 产物与源文件一致性**：不要直接修改根 `index.html`，改 `src/` 下的源文件然后 build。直接修改产物下次 build 会丢失。

7. **HTML 层级结构验证**：修改布局时，子元素**必须是 DOM 子节点，不是同级兄弟**。例如 stats-grid 下的 stat-card 必须是 `.stats-grid > .stat-card`（后代选择器匹配），而不是 `.stats-grid + .stat-card`（相邻兄弟选择器匹配）。典型的错误是 stat-card 和 stats-grid 同级并列：
   - ✅ `.stats-grid { display: grid }` + `.stats-grid > .stat-card` 作为 grid 子项
   - ❌ `.stats-grid` 空 + `.stat-card` 作为 flex 容器的独立子项（全宽渲染，不是网格）
   - 快速验证：浏览器控制台 `document.querySelectorAll('#stats-bar > .stat-card').length` 应该等于卡片数量

8. **删除元素后的 JS 引用检查**：从 body.html 删除任何有 ID 的元素后，必须 `grep -n 'element-id' src/scripts/app.js` 确认 JS 无残留。`getElementById(nullElement).innerHTML` 会抛出 TypeError，如果位于 promise `.then()` 回调内部，异常被吞掉导致函数剩余代码不执行（详情页一直转圈但控制台无报错）。

9. **CSS 类切换选择器：无空格 vs 空格**（最常踩的坑）：
   - 当 JS 给元素自身添加类（`$('navbar').classList.add('in-detail')`），然后想隐藏这个元素自身：
     - ✅ **正确**：`.navbar.in-detail { display: none }` — 交集选择器，无空格
     - ❌ **错误**：`.in-detail .navbar { display: none }` — 后代选择器，有空格
   - 后代选择器 `.in-detail .navbar` 的意思是：「找 .in-detail 内部的 .navbar 后代」，而不是「找同时有这两个类的元素」
   - 这是导致详情页「倒吕」的直接原因——CSS 规则从不生效，navbar 原地不动

10. **调试模板导致的视觉问题时：查渲染模板，不要怪数据源**

    当用户报告所有卡片名都带有同一个多余字符（如每个名字前面都有 `'`）时：
    - ❌ 查数据库/API 数据 → 数据是干净的
    - ❌ 改数据 → 问题是模板导致的
    - ✅ **检查 renderCard() 等 HTML 拼接函数中的字符串字面量**

    **⚠️ 特别记住：komari 二进制的「单引号」问题**
    
    这个 `'` 前缀来自 **komari 二进制的内嵌 JS 模板**（编译在 Go binary 内），不是数据库数据，也不是 Glass 主题的磁盘文件：
    
    ```
    // komari Go 源码中的内嵌模板（无法修改，除非重新编译二进制）
    // Go 模板源码：\'+(n.name||n.uuid||'—')
    // 这被编译成 JavaScript：\'+(n.name||n.uuid||'—')
    // 运行时产生：'name（单引号 + 节点名）
    ```
    
    Glass 主题磁盘文件（`/opt/komari/data/theme/index.html`）已经修复了这个 `'`——用的是 `''+(n.name||n.uuid||'—')`（两个单引号 = 空字符串）。
    
    然而磁盘主题文件**不被 komari 使用**（komari 用内嵌模板）。所以：
    - komari 直接服务（线上架构）→ 有单引号（内嵌模板的问题）
    - galaxy-proxy 读磁盘文件（已弃用）→ 无单引号
    
    这是一个**接受它**的限制，因为用户拒绝了 galaxy-proxy 方案。
    
    判断法则：
    - **所有条目都有的多余字符** → 模板问题（字符串拼接中硬编码了字符）
    - **部分条目有的多余字符** → 数据源问题（数据库或配置中某些条目带有该字符）

11. **调试线上问题时检查完整链路，不只是本地**

    当 curl 本地正常但浏览器不正常时，路由可能是：
    ```
    浏览器 → Cloudflare → cloudflared tunnel → 远程服务器 :25774 → komari 内嵌主题
    ```

    正确调试顺序：
    1. `curl http://localhost:25774/` — 本地代理
    2. `curl https://stat.357561.xyz/` — 通过 Cloudflare
    3. `ssh 波兰主控 "curl http://127.0.0.1:25774/"` — 远程服务器实际服务的版本
    4. 如果第 3 步和第 1 步结果不同 → 远程服务器文件未同步
    5. 如果第 2 步和第 3 步结果不同 → Cloudflare 缓存问题

    常见问题：本地开发机改了文件，但远程服务器（波兰主控）仍是旧版本。

12. **galaxy-proxy 部署前提**：保持 Glass 源码 CSS 与 komari 内嵌主题一致，否则导致「吕字型」。2026-05-20 验证通过。

    **已确认的 komari JS 模板 bug**（`\\'` 前缀 + 双状态圆点）只能通过 galaxy-proxy 绕过（不能改 komari 二进制）。修复后见 `references/ssr-js-template-mismatch.md`。

13. **Chart.js CanvasGradient 需要 chartArea**：Chart.js 的 `backgroundColor` 如果用 CanvasGradient，不能直接创建（因为初始化时 `chartArea` 还没计算好）。必须传入函数形式，让 Chart.js 在绘制时再调用。

    ```javascript
    // ❌ 在函数外直接创建 — chartArea 未就绪
    var g = ctx.createLinearGradient(0, 0, 0, 130);
    
    // ✅ 作为函数传入 — chartArea 已就绪
    backgroundColor: function(c) {
      if (!c.chart.chartArea) return;
      return gd(c.chart.ctx, c.chart.chartArea.top, c.chart.chartArea.bottom, 'rgba(16,185,129,1)');
    }
    ```

    **验证**：打开详情页，控制台检查：
    ```javascript
    document.getElementById('chart-cpu').width  // → 应 > 0（canvas 实际像素宽度）
    window._charts && Object.keys(window._charts).length  // → 3（charts: cpu/mem/net）
    ```

    详见 `references/detail-page-chartjs-migration.md`。

14. **rgba() 颜色字符串解析陷阱（2026-05-20 致命 bug）**：

    > **绝对不要对 `rgba()` 格式的颜色做 `.replace(')', ',0.08)')` 操作。**

    原因：`rgba(16,185,129,1)` 的第一个 `)` 在 `1`（alpha 值）后面。`replace(')',',0.08)')` → `rgba(16,185,129,1,0.08)`（5 参数 = 非法颜色）。

    **症状**：ECharts CanvasGradient.addColorStop 抛出 `invalid color` 异常 → 整个 setOption 的 series 静默丢失（seriesLen: 0）→ 图表不可见（无任何线和填充）→ 控制台无报错（异常被 ECharts 内部吞掉）。

    **涉及内容**：
    - `gd()` 函数（渐变填充的第二 stop）
    - `lineStyle.shadowColor`
    - 任何其他通过 `replace(')', ...)` 修改 rgba 字符串的代码

    **正确做法**：解析出 R,G,B 数字再重新组装：
    ```javascript
    var parts = col.replace('rgba(','').replace(')','').split(',').map(Number);
    // parts = [16, 185, 129, 1]
    var safeColor = 'rgba(' + parts[0] + ',' + parts[1] + ',' + parts[2] + ',0.08)';
    ```

    **验证**：打开详情页，控制台检查：
    ```javascript
    window._echarts['chart-cpu'].getOption().series.length  // → 应该 > 0
    ```

## 详情页 UI 审计与优化

> 探针详情页的 UI 审计方法是本会话确立的标准化流程。每次收到详情页优化需求时，按此流程执行。

### 审计方法论（4 层分析法）

不只看截图，必须结合 4 层信息源交叉分析：

```
1. browser_vision()     → 肉眼感知（布局失衡、字体过小、颜色突兀）
2. browser_snapshot()   → DOM 结构（grid 列数、元素顺序、嵌套层级）
3. CSS 源码             → 设计意图（grid-template-columns、padding、font-size）
4. JS 模板 (app.js)     → 渲染逻辑（哪些数据被展示、如何拼接 HTML）
```

**审计的每一步输出一个表**：

| 层 | 工具 | 发现什么 | 示例 |
|----|------|---------|------|
| 视觉 | `browser_vision(question='...')` | 布局失衡、信息密度、颜色突兀、字体可读性 | "左宽右窄，右侧图表被压扁" |
| 结构 | `browser_snapshot()` | 元素顺序、嵌套深度、缺失/冗余元素 | "系统信息 18 行堆在一起" |
| CSS | `read_file(src/styles/components.css)` | 实际 CSS 值（列比、字号、间距） | `grid-template-columns: 1.2fr 0.8fr` |
| 逻辑 | `read_file(src/scripts/app.js)` | 哪些数据被渲染、顺序、是否硬编码 | "只画了 CPU/MEM/NET 三图" |

### 详情页核心优化项（按优先级排列）

基于对 Glass 详情页的完整审计，以下是分类好的优化维度：

#### 🥇 P0 — 单行 CSS 改动，影响大

```css
/* 1. 左宽右窄比例不合理 → 右侧图表需要更大空间 */
.detail-body { grid-template-columns: 1fr 1.2fr; }
/*   原值 1.2fr 0.8fr，右侧被压扁 */

/* 2. sysinfo 字号提升可读性 */
.sysinfo-row .lbl, .sysinfo-row .val { font-size: 13px; }
/*   原值 12px，深色玻璃下阅读吃力 */

/* 3. 导航栏返回按钮精简：纯图标版 */
.back-btn {
  display: inline-flex; align-items: center; justify-content: center;
  padding: 6px; min-height: 32px; min-width: 32px;
  border-radius: var(--radius-full);
  background: var(--glass-bg); border: 1px solid var(--glass-border);
}
.back-btn svg { width: 16px; height: 16px; }
/* HTML: <button class="back-btn" id="detail-back" aria-label="返回"><svg>←</svg></button> */

/* 4. 图表卡片顶部渐变色装饰条 */
.chart-card { position: relative; }
.chart-card::before {
  content: ''; position: absolute; top: 0;
  left: 14px; right: 14px; height: 2px;
  border-radius: 0 0 2px 2px;
}
.chart-card:nth-child(1)::before { background: linear-gradient(90deg, #10b981, rgba(16,185,129,0.2)); }
.chart-card:nth-child(2)::before { background: linear-gradient(90deg, #818cf8, rgba(129,140,248,0.2)); }
.chart-card:nth-child(3)::before { background: linear-gradient(90deg, #f59e0b, rgba(245,158,11,0.2)); }
```

#### 🥈 P1 — 需改 CSS + 少量 JS

**a) sysinfo 分组 + 视觉层级（2026-05-20: 用户要求移除分类标题）**

> **当前线上状态：分类标题行（`💻 硬件` `📡 网络` `⚡ 状态`）已被移除。** 用户认为标题行是多余的信息噪声，直接展示数据行即可。
>
> 如果未来需要恢复分组，sysinfo-header 的 CSS 定义仍保留在 components.css 中，可随时启用。

当前线上实现（无标题行）：

```javascript
// leftRows — 无 header，直接硬件数据
var leftRows = [
  {l:'CPU 型号', v:node.cpu_name||'-'},
  {l:'核心数', v:node.cpu_cores?'× '+node.cpu_cores:'-'},
  {l:'架构', v:node.arch||'-'},
  {l:'虚拟化', v:node.virtualization||'-'},
  {l:'操作系统', v:(node.os||'-').split(' ').slice(0,2).join(' ')},
  {l:'内存', v:bytes(node.mem_total)},      // ← 2026-05-20 新增
  {l:'Swap', v:(node.swap_total||0)>0?bytes(node.swap_total):'无'},
  {l:'磁盘', v:bytes(node.disk_total)}
];

// rightRows — 无 header，无冗余行
var rightRows = [
  {l:'进程数', v:latest.process||'-'},
  {l:'更新', v:age(latest.updated_at)},
  {l:'到期', v:node.expired_at?...}
];
```

**关键：移除分类标题的同时，也移除了冗余的数据行。** 流量限额只在 bill-chip 展示（`📊 已用/限额`），TCP 只在 tags-card 展示。sysinfo-row 里不重复。`rr()` 函数中对 `type==='header'` 的处理逻辑保持可用，但当前线上不传 header 类型的 row。`

#### 左侧 layout 拆分：sysinfo-grid → 3 张独立卡片（2026-05-20 建立）

**当前布局（2026-05-20 最新）：**

```text
左侧三卡片（flex column）：
  sysinfo-card#detail-hw       → CPU型号 / 核心数 / 架构 / 虚拟化 / OS / 内存 / Swap / 磁盘 / GPU
  sysinfo-card#detail-status   → 进程数 / 负载 / 更新 / 到期 + bill-chip（价格/流量/剩余天数）
  tags-card#detail-tags        → 标签 / TCP·UDP 连接数
```

**关键原则：一个数据只有一个展示位置。**
- 流量限额 → 只在 bill-chip `📊 已用/限额` 中展示，不在上方 sysinfo-row 重复
- TCP/UDP 连接数 → 只在 tags-card 的 conn-row 展示，不在右侧状态区重复
- CPU/MEM/DSK 使用率 → 只在右侧图表展示，不在左侧 sysinfo 重复
- 分类标题行 `💻 硬件` `📡 网络` `⚡ 状态` 已被移除（2026-05-20 用户要求）
- 内存用量（`bytes(node.mem_total)`）在左侧硬件列展示

`tags-card` 里标签和连接数在同一块。标签太多时（20+）占空间大。

做法：标签超 6 个时折叠，展开可看全部。

```javascript
// app.js 中渲染 tags
var maxVisible = 6;
var more = tags.length - maxVisible;
var tagsHtml = tags.slice(0, maxVisible).map(t => `<span class="tag-chip">${t}</span>`).join('');
if (more > 0) tagsHtml += `<span class="tag-chip more" onclick="this.parentElement.innerHTML=tags.map(...)">+${more}</span>`;
```

### 共享 UI 元素跨视图显示：详情页保留 navbar，只隐藏操作按钮

这是本会话确立的标准做法。当用户说「把顶部栏/页眉/标题栏也放到详情页」时：

**「顶部栏」= navbar（导航栏），不是 stats-bar（统计卡片栏）。「右边的三个组件」= navbar-actions（搜索/排序/登录），不是 stats-bar 右边的统计卡片。**

```javascript
// ✅ 详情页：保留 navbar，只隐藏操作按钮
function showDetailView(uuid) {
  $('navbar').querySelector('.navbar-actions').classList.add('hidden');
  $('detail-view').classList.remove('hidden');
  $('list-view').classList.add('hidden');
  window.scrollTo(0, 0);
  loadDetailData(uuid);
}
function showListView() {
  hasError = false;
  render(false);
  $('navbar').querySelector('.navbar-actions').classList.remove('hidden');
  $('detail-view').classList.add('hidden');
  $('list-view').classList.remove('hidden');
  window.scrollTo(0, 0);
}
```

**不要做的事：**
- ❌ 把 stats-bar 从 list-view 移到 HTML 外部 → 破坏 DOM 结构
- ❌ 用 JS 克隆 stats-bar 到详情页 → 用户没要求加 stats-bar
- ❌ 给 navbar 加 `in-detail` 类隐藏整个 navbar → 用户希望保留页眉
- ❌ 猜「右边的三个组件」是哪个 → 用 browser_vision 截图问用户

**这条教训的来源（本会话）：**
1. 用户说「把顶部栏移植过来」→ 我以为是 stats-bar → 移 HTML 结构 → 布局坏了
2. 用户说「不要右边的三个组件」→ 我以为是 stats-bar 右边三个卡片 → 只留了时间卡片
3. 用户说「你他妈把时间那个卡片加上干什么」→ 用户根本没想让 stats-bar 在详情页
4. 用户说「我说页眉你听得懂吗 / 或者说标题栏」→ 终于明白是 navbar

---

### 共享 UI 元素跨视图显示：JS 克隆模式（2026-05-20 确立）

当两个视图（列表/详情）需要共享同一个 UI 元素时（如 stats-bar），**不要修改 HTML 布局结构**。用 JS 动态克隆：

```javascript
function showDetailView(uuid){
  // ... 切换视图
  // 克隆 stats-bar 到详情页（仅第一次进入详情页时克隆）
  if(!window._statsClone){
    var sb = document.getElementById('stats-bar');
    var clone = sb.cloneNode(true);
    var wrap = document.getElementById('detail-content-wrap');
    wrap.parentNode.insertBefore(clone, wrap);  // 插入到 detail-nav 和内容之间
    window._statsClone = clone;
  }
  loadDetailData(uuid);
}

function showListView(){
  // ... 切换回列表
  // 移除克隆
  if(window._statsClone){
    window._statsClone.parentNode.removeChild(window._statsClone);
    window._statsClone = null;
  }
}
```

**为什么不用 HTML 方式？** 之前尝试把 stats-bar 从 list-view 的 main.container 移到 navbar 和两个视图之间，结果丢失了 `region-filters-wrap` 的打开标签，DOM 结构被破坏（nodes-grid-wrap 从 main 里掉出来），导致「布局都给改乱了」。

**关键约束**：克隆的元素有相同 ID。`getElementById` 按 DOM 顺序返回第一个，所以：
- 列表视图（隐藏）中的原始 stats-bar 在 DOM 中靠前
- 详情视图（可见）中的克隆 stats-bar 在 DOM 中靠后
- `updateStats` 不能再用 `$(id).textContent`，必须用 `document.querySelectorAll('#id')` 更新全部匹配元素

```javascript
// ❌ 只更新第一个匹配元素（隐藏的原始元素）
$('stat-online-value').textContent = '5/10';

// ✅ 更新所有匹配元素（包括可见的克隆）
document.querySelectorAll('#stat-online-value').forEach(function(e){
  e.textContent = '5/10';
});
```

**每次返回列表时销毁克隆**，避免重复克隆导致 DOM 膨胀。

#### ⚠️ 大括号平衡陷阱（单行深度嵌套对象）

写 Chart.js 的 `options` 对象时，如果全部放在一行，大括号很难数对。**这类配置一定用多行格式**。

上次踩坑：把 `mk()` 函数的 Chart.js 配置全塞在一行，brace balance 多出 2 个 `}`。调试方法：

```bash
# 1. 语法检查
node --check src/scripts/app.js

# 2. 大括号计数（注意：会算上字符串内的 {}，仅供参考）
node -e "
var fs=require('fs');
var lines=fs.readFileSync('src/scripts/app.js','utf8').split('\n');
var bc=0;
for(var l of lines){
  for(var c of l){if(c==='{')bc++;if(c==='}')bc--;}
  if(bc!==0) console.log('Line: bal='+bc, l.substring(0,60));
}
"

# 3. 逐段二分法找到问题行
```

### 返回按钮行与内容间距（像素级精确）

详情页顶部从外到内的垂直间距分为两层：

1. **`.detail-nav { margin-top: 20px }`** — 返回按钮行到页面顶部（或 navbar 底部）的距离。这个值不是由 padding 控制的，而是 margin。用户对这个距离极其敏感，改完后必须问"这行不行"让用户验证。

2. **`#detail-view .container.main { padding-top }`** — 返回按钮行底边到内容卡片（detail-body）的距离。**当前线上值 24px**（2026-05-20 最终确认值，迭代路径：0.5rem=8px -> 16px -> 24px）。如果用户说「返回行和下行之间的距离加到Npx」，指的就是这个 padding-top 值。

**迭代教训（本会话确立）：**
- 用户说「远了一点」或「又远了一点」 -> 减小 `margin-top` 值（通常是 `.detail-nav` 或 `.detail-view .container.main` 的 padding-top）
- 用户说「会不会对齐啊」 -> 之前改的间距值不对，需要重新调整
- 用户明确说「加到Npx」 -> 直接设 Npx，不要问「Npx可以吗」
- 改完后必须部署 + 让用户刷页面验证，不要只改代码不发出去
- **不要回滚无关的样式**：只动目标间距值，其他 CSS 不动。用户对间距敏感，但对其他无关改动引发的布局偏移同样敏感。
- **最终确定的值**：详情页返回行到内容间距 **24px**，与主页 stats-bar ↔ 过滤器 的 gap (1.5rem=24px) 一致。这个值是通过多次迭代（0.5rem→16px→24px）逐步找到用户满意的。

**典型初始值对照表（记得先查线上再改）：**

| 间距位置 | 初始值 | 当前线上 | CSS 属性 |
|---------|--------|---------|---------|
| 返回行距页面顶部 | 20px | 20px | `.detail-nav { margin-top }` |
| 返回行与内容卡片间距 | 0.5rem (8px) | **24px** | `#detail-view .container.main { padding-top }` |
| 卡片之间间隔（同列内） | var(--gap) = 16px | 16px | `.detail-left, .detail-right { gap }` |
| 左右列之间间隔 | var(--gap) = 16px | 16px | `.detail-body { gap }` |

⚠️ 注意：改 `src/styles/components.css` 后还要改 `index.html`（因为 index.html 是内联编译产物，有独立的 CSS 副本）。只改一个会导致编译前后不一致。

### 主页组件间距速查

用户可能会问「主页的组件之间的间隔是多少」。参考表：

| 间距位置 | 值 | CSS 属性 |
|---------|-----|---------|
| Navbar ↔ stats-bar | `2.5rem` (40px) | `.main { padding-top }` |
| stats-bar ↔ 过滤器 | `1.5rem` (24px) | `.main { gap }` (flex column) |
| 过滤器 ↔ 卡片网格 | `1.5rem` (24px) | `.main { gap }` (flex column) |
| 卡片 ↔ 卡片（网格内） | `var(--gap)` = **16px** | `.nodes-grid { gap }` |
| 网格 ↔ footer | `1.5rem` (24px) | `.main { gap }` + `.footer { margin-top }` |

与详情页对比：

| 详情页间距 | 值 | CSS 属性 |
|-----------|-----|---------|
| 返回行距页面顶部 | 20px | `.detail-nav { margin-top }` |
| 返回行 ↔ 内容卡片 | **24px** | `#detail-view .container.main { padding-top }` |
| 卡片之间（同列内） | 16px | `.detail-left, .detail-right { gap }` |
| 左右列之间 | 16px | `.detail-body { gap }` |

## 详情页关键 CSS 结构速查（2026-05-20 更新：共享 stats-bar + 无分类标题）

```
div.page#app
├── nav.navbar (hidden when in-detail)
├── div.container (共享 stats-bar, padding:0.35rem 0 0)
│   └── div.stats-grid#stats-bar (4列, 始终可见)
├── div#list-view (hidden when in detail)
│   └── main.container.main → filters → nodes-grid
├── div.detail-view (hidden when in list)
│   ├── div.detail-nav (sticky, z-index:100, min-height:48px)
│   │   └── div.detail-nav-inner (flex, height:48px)
│   │       ├── button.back-btn (纯图标←, aria-label="返回", 32×32)
│   │       └── div.detail-title-area
│   │           ├── span.detail-name (font-weight:600, 15px)
│   │           └── span.detail-meta (font-size:12px, text-muted)
│   └── div.detail-content-wrap
│       └── div.detail-content (max-width: var(--container-max))
│           ├── div.detail-loading
│           ├── div.detail-error
│           └── div.detail-body (grid, 1fr 1.2fr)
│               ├── div.detail-left (flex column)
│               │   ├── div.sysinfo-card#detail-hw    ← 无分类标题，直接硬件行
│               │   │   └── div.sysinfo-single → sysinfo-row × N
│               │   ├── div.sysinfo-card#detail-status ← 无分类标题，进程数/负载/更新/到期
│               │   │   ├── div.sysinfo-single → sysinfo-row × N
│               │   │   └── div.sysinfo-bill → bill-chip × 3（价格/流量/到期）
│               │   └── div.tags-card#detail-tags
│               │       └── div.tags-title + div.tags-list + div.conn-row
│               └── div.detail-right (flex column)
│                   ├── div.chart-card → ::before 渐变色装饰条 2px
│                   │   ├── chart-title + chart-badge#badge-cpu
│                   │   └── div.chart-canvas → canvas#chart-cpu
│                   ├── div.chart-card → ::before 渐变色装饰条 2px
│                   │   ├── chart-title + chart-badge#badge-mem
│                   │   └── div.chart-canvas → canvas#chart-mem
│                   └── div.chart-card → ::before 渐变色装饰条 2px
│                       ├── chart-title + chart-badge#badge-net + legend
│                       └── div.chart-canvas.net-chart → canvas#chart-net
├── footer.footer
└── div.conn-toast + button.back-to-top\n```\n\n### 图表库接入 (flex, height:48px)
│       ├── button.back-btn (纯图标←, aria-label="返回", 32×32)
│       └── div.detail-title-area
│           ├── span.detail-name (font-weight:600, 15px)
│           └── span.detail-meta (font-size:12px, text-muted)
├── div.detail-content-wrap
│   └── div.detail-content (max-width: var(--container-max))
│       ├── div.detail-loading
│       ├── div.detail-error
│       └── div.detail-body (grid, 1fr 1.2fr)  ← 右宽左窄
│           ├── div.detail-left (flex column)
│           │   ├── div.sysinfo-card#detail-hw    ← 💻 硬件（CPU型号/核心数/架构/OS等）
│           │   │   └── div.sysinfo-single → sysinfo-row × N
│           │   ├── div.sysinfo-card#detail-status ← 📡 网络 + ⚡ 状态
│           │   │   ├── div.sysinfo-single → sysinfo-row × N
│           │   │   └── div.sysinfo-bill → bill-chip × 3（价格/流量/到期）
│           │   └── div.tags-card#detail-tags
│           │       └── div.tags-title + div.tags-list + div.conn-row
│           └── div.detail-right (flex column)
│               ├── div.chart-card → ::before 渐变色装饰条 2px
│               │   ├── div.chart-header (flex column!)  ← ⚠️ 必须 column 排列，文字在图表上方
│               │   │   ├── chart-header-left (flex row) → chart-title + chart-badge
│               │   │   └── chart-legend (flex row) → legend-up + legend-down（仅NET卡）
│               │   └── div.chart-canvas → canvas#chart-cpu
│               ├── div.chart-card → ::before 渐变色装饰条 2px
│               │   ├── chart-title + chart-badge#badge-mem
│               │   └── div.chart-canvas → canvas#chart-mem
│               └── div.chart-card → ::before 渐变色装饰条 2px
│                   ├── chart-title + chart-badge#badge-net
│                   └── div.chart-canvas → canvas#chart-net
```

### 图表库接入（2026-05-20: Chart.js 4.4.7 当前方案）

**当前线上实现是 Chart.js 4.4.7**（用户 2026-05-20 要求从 ECharts 切回 Chart.js）。

> **历程**：手绘 Canvas（用户说「潦草」）→ Chart.js（用户说「不够美」）→ ECharts 5.x → 用户又说「用 charts.js 绘制吧」
> 
> 结论：用户对图表的偏好是**变动**的，要快速响应切换指令。不要固化「当前方案」，当前线上用哪个就是哪个。

| 方案 | 当前状态 |
|------|---------|
| 手绘 Canvas | ❌ 用户说「潦草」|
| Chart.js 4.x | ✅ **当前线上（2026-05-20）** |
| ECharts 5.x | ❌ 已被用户要求换掉 |

实现细节见 `references/detail-page-chartjs-migration.md`（已更新至当前线上版本）。

#### ⚠️ 核心规则：Y轴完全隐藏，X轴极淡显示时间标签

**用户多次严厉要求：不要Y轴，所有数值数据放在卡片顶部。** X轴可以极淡显示时间标签用于上下文，但不是必须的。

### 历史教训

这条规则是在多次用户发火后确立的：

1. 「Y轴和数据都在左边很挤」→ 缩小左边距
2. 「我让你把数据从左边放在上面，你懂不懂哦」→ 数值移到图表上方
3. 「把这几个放上面，放上面，不要放左边，你他妈设计学到狗肚子里去了」
4. 「这个图怎么画你去网上学，怎么画好看」→ 调研后再动手

### 配置规范

- **Y轴**：`show: false`（完全隐藏，不显示数值刻度和轴线）
- **X轴**：`show: true`（极淡显示时间标签，提供上下文参考）
  ```javascript
  xAxis: {
    show: true, boundaryGap: false,
    axisLine:  { show: false },
    axisTick:  { show: false },
    axisLabel: { color: 'rgba(255,255,255,0.2)', fontSize: 10, margin: 4 },
    splitLine: { show: true, lineStyle: { color: 'rgba(255,255,255,0.04)', width: 1 } }
  }
  ```
  注意：X轴必须加 `bottom: 18` 的 grid 边距以容纳标签
- 图表 `grid` 边距：`{ left: 2, right: 2, top: 4, bottom: 18 }`（bottom 留空间给 x 轴标签）

### 图表卡片标题区布局（`chart-header`）

#### 单行标题（CPU/内存）
```html
<div class="chart-card">
  <div style="display:flex;align-items:center;gap:6px">
    <div class="chart-title">CPU 占用率</div>
    <div class="chart-badge" id="badge-cpu">—</div>
  </div>
  <div class="chart-canvas"><canvas id="chart-cpu"></canvas></div>
</div>
```

#### 双行标题（网络 — 标题行 + 图例行）
```html
<div class="chart-card">
  <div class="chart-header">  <!-- flex column -->
    <div class="chart-header-row">  <!-- flex row, space-between -->
      <div class="chart-header-left">  <!-- 网络速率 + badge -->
      </div>
      <div class="chart-legend">       <!-- ↑上行 ↓下行 右对齐 -->
      </div>
    </div>
    <div class="chart-canvas net-chart">
      <canvas id="chart-net"></canvas>
    </div>
  </div>
</div>
```

CSS：
```css
.chart-header { display:flex; flex-direction:column; gap:2px; }
.chart-header-row { display:flex; justify-content:space-between; align-items:center; }
.chart-header-left { display:flex; align-items:center; gap:6px; }
.chart-legend { display:flex; gap:8px; font-size:11px; color:var(--text-muted); }
.legend-up { color:#f59e0b; font-weight:bold; font-size:12px; }
.legend-down { color:#10b981; font-weight:bold; font-size:12px; }
```

渲染效果：
```
┌────────────────────────────────────┐
│ 网络速率 · —         ↑上行    ↓下行  │ ← 同一行 space-between
│                                    │
│      ╱╲    ╱╲                     │ ← 图表满宽
│     ╱  ╲  ╱  ╲                    │
│    ╱    ╲╱    ╲                   │
└────────────────────────────────────┘
```

#### Chart.js CDN 接入

`src/index.html` 的 `<head>` 中（替换 ECharts CDN）：
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
```

#### ⚠️ `\\\"` HTML 属性溢出（2026-05-20 发现并修复）

**不要在单引号 JS 字符串中使用 `\\\"` 来试图转义 HTML 双引号。**

```javascript
// ❌ 错误的写法 — 运行时输出错误 HTML
span style=\\"font-weight:600\\">

// ✅ 正确的写法 — 单引号字符串内双引号无需转义
span style="font-weight:600">
```

原因：JavaScript 单引号字符串 `'...'` 中，双引号不需要转义。`\\\"` 在 JS 解析中产生的是字面量 `\"`（反斜杠+引号），而 HTML 中 `\"` 不是合法转义，会导致 `style` 属性值被截断为 `\`。

**影响范围**：tooltip formatter 函数、innerHTML 模板字符串中的 `class=""` 和 `style=""` 属性。

**验证方法**：
```javascript
// 控制台检查渲染后的 tooltip HTML
document.querySelector('#chart-cpu').chart.tooltip._options.callbacks.label(...) 
// 或直接检查生成的 HTML 字符串
'<span style="font-weight:600">'.replace(/\\"/g, '✔')  // 不应该有 \" 残留
```

#### Chart.js 创建/更新模式

当前 `renderDetailCharts` 的实现是一个 `mk()` 函数创建 Chart 实例，不再有 ECharts 的 `ec()`/`gd()`/`spline()` 等函数。

**核心函数**：

```javascript
// mk() — 统一创建 Chart 实例（每次重建，不复用）
function mk(id, labels, datasets, isNet) {
  // 1. 获取 canvas
  var el = document.getElementById(id);
  if (!el) return;
  var ctx = el.getContext('2d');
  
  // 2. 创建新 Chart 实例
  new Chart(ctx, {
    type: 'line',
    data: { labels: labels, datasets: datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          backgroundColor: 'rgba(0,0,0,0.75)',
          callbacks: {
            title: function(its) { return its[0].label; },
            label: function(it) {
              if (isNet) return it.dataset.label + ': ' + bytes(it.raw);
              return it.raw.toFixed(1) + '%';
            }
          }
        }
      },
      scales: {
        x: { display: true, grid: { display: false }, ticks: { color: 'rgba(255,255,255,0.3)', fontSize: 10 } },
        y: { display: false, beginAtZero: true, min: 0 }
      },
      interaction: { mode: 'index', intersect: false }
    }
  });
}

// gd() — CanvasGradient 渐变填充
function gd(ctx, top, bottom, col) {
  var c = col.replace('rgba(','').replace(')','').split(',').map(Number);
  var g = ctx.createLinearGradient(0, top, 0, bottom);
  g.addColorStop(0, 'rgba('+c[0]+','+c[1]+','+c[2]+',0.18)');
  g.addColorStop(0.5, 'rgba('+c[0]+','+c[1]+','+c[2]+',0.04)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  return g;
}

// backgroundColor 参数传入函数（动态获取 chartArea）
backgroundColor: function(c) {
  if (!c.chart.chartArea) return;
  return gd(c.chart.ctx, c.chart.chartArea.top, c.chart.chartArea.bottom, 'rgba(16,185,129,1)');
}
```

**关键变化**：
- Chart.js 用 `backgroundColor: function(context){...}` 动态创建 CanvasGradient（因为 chartArea 在初始化时未知）
- `tension: 0.4` 控制曲线平滑度（Chart.js 的 tension 范围 0-1，0.4 相当于 ECharts 的 smooth: 0.8）
- Chart.js 自动处理 resize（`responsive: true`），不再需要手动监听 resize
- 每次切换节点时 `destroy()` 旧实例再创建新的（`renderDetailCharts` 开头清理 `window._charts`）
- 网络图双数据集共用 Y 轴，通过 `displayColors: isNet` 控制 tooltip 色块显示（网络图显示，单线图不显示）

**详见 `references/detail-page-chartjs-migration.md`（已更新至当前线上版本）。**

## 详情页优化原则（探针面板专用）

从多次用户反馈和设计修正中凝练的原则：

1. **数据密度优先，零装饰** — 不要毛玻璃、saturate、视频背景。详情页要的是信息，不是视觉炫技。
2. **图表 > 仪表** — 折线图展示趋势，比圆形仪表盘更有效。不要在详情页加 radial gauge。
3. **信息灰显不分级** — 不要用红色/绿色标注正常运行指标（如 CPU 1% 是绿色→正常，不用强调）。红色只留给出问题的地方（到期 < 15天、负载 > 80%）。
4. **图表库用当前线上方案即可** — 历程：手绘 Canvas → Chart.js → ECharts → Chart.js。用户对图表的偏好会变，快速执行切换命令，**不要固化「某库是唯一方案」的说法**。
5. **行高紧凑** — sysinfo-row 的 padding 6px 0 已经够用，不要加大。用户在多台服务器间切换时需要一眼扫完。
6. **首屏原则** — 最重要的信息（服务器状态、CPU、内存、网络、到期日）必须在首屏可见，不需要滚动。次要信息（Swap、进程数、TCP/UDP 连接数）可放下方。

## 用户偏好（必须遵守）

- **不要过度工程化**：保持 src/ → build → deploy 的简单管道。不要引入 package.json、webpack、框架。用户明确批评过"感觉你越来越蠢了"，根源是技能系统和系统规则带来的上下文膨胀。**简单直接，不要绕。**
- **零依赖**：纯静态 HTML/CSS/JS，不用 npm 安装任何东西。
- **干净的项目结构**：旧实验版本（Astro/Next.js/Svelte）必须清理，不留 node_modules 和构建缓存。
- **纯 Komari 主题，不涉 NodeGet**：代码、文档、Release 包中不得出现"NodeGet"字样。这是 Komari 主题，不是 NodeGet 主题。服务器上旧主题残留目录需在用户同意后清理。项目内任何地方都不能有 NodeGet 引用。
- **JS 不强行拆分**：如果原始代码是单 IIFE，保持单文件 `app.js`，不要为了分文件而分文件导致白页。
- **内存减负**：只保存持久有用的信息（服务器清单、API 配置、部署架构），不要记录任务进度、PR 编号、会话范围的 TODO。
- **先看再改，不问直接修**：用户极度反感逐项确认。收到 UI 修改需求后：打开页面看 → 截图分析 → 一次性全部改完 → 部署 → 截屏发过去。不要逐个问「这个要不要改」。
- **图表库跟着当前线上走** — 历程：手绘 Canvas（被拒）→ Chart.js（被说不够美）→ ECharts → Chart.js（再次采用）。用户偏好会变，线上用啥就说啥。如果用户要求切换，立刻换不要争。
- **HTML属性引号转义**：在单引号 JS 字符串中写 HTML 属性时，双引号不需要转义。`\"` 会产生字面量反斜杠+引号，导致 HTML 属性截断为 `\`。
- **Chart.js 语法陷阱**：`new Chart(ctx, {...})` 作为单行函数体内时注意大括号平衡。用多行格式化调试语法错误。`backgroundColor` 作为函数传入以动态获取 `chartArea`。
- **修改后发截图**：不要用文字描述改了什么，直接 MEDIA 发送截图。用户看到截图才知道你改的对不对。
- **详情页布局规范**（2026-05-20 确认）：
  - 左侧三张卡片：💻 硬件 / 📡网络+⚡状态 / 🏷️标签 — 填满纵向空间，底部不留白
  - 右侧三张图表卡片：顶部 2px 渐变色装饰条（CPU绿/内存紫/网络橙）
  - 网格比例 `1fr 1.2fr`（右宽）
  - 返回按钮纯图标 `←`（aria-label="返回"），无文字
  - sysinfo 字体 13px，分组标题带 emoji + `letter-spacing: 0.05em`
  - 不要在上方额外重复使用率 CPU/MEM/DSK 行（右侧图表已有）
- **命名必须精确**：用 vision 截图实际看视觉风格再取名，不使用「星/银河」等不准确词汇。名称应准确反映视觉特征（底色、玻璃效果、点缀色）。
- **文档同步更新**：改名、改功能后要同步更新 README 和 ARCHITECTURE.md。

## 相关技能

- `galaxyglass-design-references` — 设计参考（配色、令牌、Design System）
- `Glass-table-redesign` — 表格视图历史演变
- `log-search` — 跨服务器日志搜索（排查部署问题）

## 参考资料

> 技能目录下有 reference 文件，详见链接文件列表。

- `references/extract-deployed-to-src.md` — 从线上单文件提取 src/ 结构的脚本和步骤
- `references/ARCHITECTURE.md` — 架构说明快照（完整版在项目根目录 ARCHITECTURE.md）
- `references/Glass-table-redesign.md` — 表格视图三阶段演变
- `references/lu-shaped-layout-fix.md` — 「吕字型」布局修复记录
- `references/ssr-js-template-mismatch.md` — SSR 与 JS 模板不一致调试全记录
- `references/detail-page-dom-structure.md` — 详情页完整 DOM 结构 + CSS 选择器速查 + 图表渲染参数
- `references/detail-page-chartjs-migration.md` — Chart.js CDN 接入、参数配置、渐变创建、更新模式
- `references/komari-theme-packaging.md` — Komari 主题打包格式（zip 结构、web UI 上传要求、官方参考）
