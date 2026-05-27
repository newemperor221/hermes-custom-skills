# GalaxyGlass 视觉规范（卡片视图 + 详情页）

> 用户对 `stat.357561.xyz` 探针面板的视觉要求。覆盖卡片列表视图和服务器详情页。

## 核心原则

用户偏好**极简、实用、去装饰**的设计。任何没有实际交互价值的元素都是多余的。

## 动画规则（优先遵循）

| 规则 | 原因 | 示例 |
|------|------|------|
| 没有循环动画 | 纯视觉噪音，无信息价值 | ~~在线绿点 pulse~~ |
| 没有骨架屏 shimmer | 数据加载太快（<1s），动画白写 | ~~skeleton shimmer~~ |
| 过渡 ≤0.1s | 慢过渡产生"闪"感，用户指出"闪一下" | navbar blur 0.35s→0.1s |
| hover 只上移，不缩放 | scale(1.012) 肉眼看不见 | ~~card hover scale~~ |
| 下拉菜单 0.12s | 足够快且不为零 | dropdown fadeIn |

## 卡片视图布局规则

### 导航栏
- **不要**滚动切换毛玻璃效果（用户明确要求去掉）
- 要么永远透明（sticky，无背景），要么永远毛玻璃（sticky，永远 blur(24px)）
- 过渡必须设 `backdrop-filter: blur(0px)` 基线值，否则从 `none` 到 `blur(Npx)` 会闪

### 统计卡片（stats-grid）
- 四张卡片必须**完全一致**（background/border/padding）
- **不要** nth-child 差异化 tint（用户指出"前两张和后两张效果不一样"）
- 必须始终有 `.stat-card { display: flex; ... background: var(--glass-bg); border: 1px solid ... }` 基础样式（曾被遗漏）

### 节点卡片（node-card）
- NET 行必须保留 `.cm-bar` 占位（不可 `display:none`），否则 NET 数值贴着标签对齐不一致
- 离线时：只降状态灯(35%) 和进度条(25%)，文字保持正常可读（不可整体 opacity:0.4）
- 底部 padding 比顶部略小（`1rem 1rem 0.65rem`）以平衡视觉重心
- cm-label 字体 11px（不可用 10px，基准 14px 下太小）

### 筛选 chip
- 显示文字编码（"US 7"）而非 emoji 字符（"🇺🇸 7"），emoji 渲染和数字字体系不一致

## 细节页布局规则

详情页由 `renderDetailView(node, recent)` 函数渲染，结构为左右两栏（`.detail-body` 的 `grid-template-columns: 1.2fr 0.8fr`）。

### 左侧栏
- **顶部 metrics-grid**（3列网格）：CPU / 内存 / 磁盘 / 在线 / 网络 / 流量 共6个小指标卡
- **系统信息 sysinfo-card**：`leftRows` + `rightRows` 两个数组，渲染为左右两列 `sysinfo-grid`
- **标签 tags-card**：服务器标签 + TCP/UDP 连接数

### 右侧栏
- 三个 chart-card，每个包含：
  - 标题（如"CPU 占用率"）
  - 当前值 badge（如 `17.6%`）
  - Canvas 图表（`drawLineChart` / `drawNetChart`）

### 6 个小指标（metrics-grid）
放在 `.detail-metrics` 中，由 `metrics-grid` CSS 排版为 3 列网格。每个指标卡包含 label、value、可选 sub 文本、可选进度条。前三个（CPU/内存/磁盘）有进度条，后三个只有数值。sub 字段显示如 `170.8MB / 967.9MB`。

### 规格信息（sysinfo-grid）
`leftRows` 和 `rightRows` 分别对应左右两列：
- **左列**：CPU 型号 / 核心数 / 架构 / 虚拟化 / 操作系统 / Swap / 磁盘
- **右列**：流量限额 / 进程数 / TCP / 更新 / 到期
- 负载行：由 `l1!=null && l1!==undefined` 条件控制是否插入 `rightRows`
- **GPU 行**：仅当 `gpu_name` 存在且非 `None/'-'` 时才 push
- **禁止冗余**：metrics 区已有的「在线」「内存」等，规格区不可重复出现

### 负载值显示
每个负载值做兜底，防止 agent 上报字段缺失：
```js
'15m '+(r.v15!==undefined?r.v15:'--')+''
```

### Footer 贴底（flex 链）

详情页加载过程中 footer 会自动浮起，因为 `.detail-view` 没有 `flex: 1`。需要在 `.page`（`display:flex;flex-direction:column;min-height:100vh`）内部建立完整 flex 链：

```css
.detail-view { display: flex; flex-direction: column; flex: 1; }
#detail-view .container.main { flex: 1; }
/* ⚠️ .main 必须有 padding-top/bottom longhand，不可用缩写 padding: X 0 */
.detail-content-wrap { flex: 1; padding-top: 0.5rem; }
```

链式关系：
```
.page (flex column, min-height:100vh)
  .detail-view (flex:1)           ← 撑满 .page 剩余空间
    main.container.main (flex:1)   ← 撑满 .detail-view（不含 .detail-nav）
      .detail-content-wrap (flex:1) ← 撑满 main，即使加载时只有一行文字
```

### 底栏（bill-chip）
位于 sysinfo-grid 底部，跨两列：
- 价格 chip（如 `¥10/年`）
- 流量 chip（如 `📊 4.2GB/1000.0GB`，使用率≥80% 变 danger 红）
- 到期 chip（如 `📅 352天`，<15 天变 danger 红）

### 图表颜色管理
Canvas 图表颜色硬编码在 JS 中（不能依赖 CSS 变量，因为 Canvas 需要解析具体颜色值）：
- CPU 图表：线条 `#10b981`，填充 `rgba(16,185,129,0.12)`
- 内存图表：线条 `#818cf8`，填充 `rgba(129,140,248,0.12)`
- 网络上行：`#f59e0b`（橙色线条）
- 网络下行：`#10b981`（绿色线条）

### 返回按钮
- 使用毛玻璃样式（`var(--glass-bg)` + `backdrop-filter: blur(12px)` + `1px solid var(--glass-border)`）
- 圆角 `var(--radius-full)`，与导航栏风格统一

### 标签区域（tags-card）
- 标签使用胶囊样式（`border-radius: var(--radius-full)` + 毛玻璃 `backdrop-filter: blur(8px)`），与筛选 chip 统一
- `.tag-chip` 样式：`padding: 3px 9px; border-radius: var(--radius-full); background: var(--glass-bg); color: var(--text-primary); border: 1px solid var(--glass-border); backdrop-filter: blur(8px);`

## 响应式断点（已合并为 3 层）

| 断点 | 说明 | 卡片列数 | 详情页 |
|:----:|:-----|:--------:|:------:|
| **≥1024px**（桌面） | 默认 auto-fill minmax(280px,1fr) → 4列 | 4 | 双栏 1.2fr 0.8fr |
| **640-1023px**（平板） | 固定2列过渡，详情单栏 | 2 | 单栏 |
| **<640px**（手机） | 单列、统计2列、导航压缩、筛选可滑动 | 1 | 单栏 |

### 桌面端 grid 计算（坑）
```css
.nodes-grid { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
```
`minmax(Npx, 1fr)` 的 N 值必须小于 `(容器宽度 - gap×3) / 4`。1280px 容器实宽约 1231px（减 padding），N=300px 时 `300×4+16×3=1248 > 1231` → 退化到 3 列。**N=280px 时 `280×4+48=1168 < 1231` → 4 列正常。**

⚠️ **每次修改 minmax 值时先算一下容器实宽再定 N 值。**

### 小屏子断点（<480px，嵌套在 <640px 内）

```css
@media (max-width: 480px) {
  --container-pad: 0.75rem;
  .node-card { padding: var(--space-3) var(--space-3); gap: var(--space-2); }
  .card-metric { height: 18px; }
  .card-metric .cm-value { font-size: 12px; width: 34px; }
  .card-metric.net-row .cm-value { font-size: 11px; }
  .stats-grid { gap: 6px; }
  .stat-card { padding: var(--space-2) var(--space-3); gap: 6px; }
  .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: var(--space-2); }
  .metric-card .metric-value { font-size: 14px; }
  .metric-card .metric-sub { font-size: 10px; }
  .sysinfo-grid { grid-template-columns: 1fr; gap: 0; }
}
```

### 移动端布局注意
⚠️ 每次修响应式，必须同时修**列表页 + 详情页**。只修列表页忘记详情页是曾被用户指出过的错误。

| 项目 | 桌面（≥1024px） | 手机（<640px） | 小屏（<480px） |
|:-----|:--------------:|:--------------:|:--------------:|
| 详情导航栏高 | 48px | 42px | 42px |
| 详情标题字号 | 15px | 14px | 14px |
| 详情元数据 | 12px | 11px | 11px |
| 指标卡数值 | 16px | 16px | 14px |
| 指标副文本 | 11px | 11px | 10px |
| 系统信息 | 2列 | 2列 | 1列 |

## 模块化架构（2026-05-15重构）

GalaxyGlass 已从单文件内联 HTML 重构为模块化架构。部署后每个文件独立存在，不合并。

### 文件结构

```
/opt/komari/data/theme/           ← 部署目录
├── index.html                    ← HTML 骨架（无内联 CSS/JS）
├── styles/
│   ├── tokens.css                ← CSS 变量（配色、间距、圆角、字体）
│   ├── reset.css                 ← 基础重置
│   ├── layout.css                ← 导航、容器、网格、页脚、滚动条
│   ├── components.css            ← 卡片、统计栏、筛选、搜索、详情页、图表
│   └── responsive.css            ← 3个断点（<640 / 640-1023 / ≥1024 + ≥1600）
└── scripts/
    ├── config.js                 ← 常量、工具函数（$、bytes、uptime）、连接通知
    ├── data.js                   ← API 请求（fetchJSON、loadData）、数据合并
    ├── render.js                 ← 卡片渲染、统计更新、筛选构建
    ├── charts.js                 ← Canvas 图表（drawLineChart、drawNetChart）
    └── events.js                 ← 事件绑定、详情视图、路由、初始化
```

### 加载顺序（重要）
```html
<!-- 按此顺序加载，不可调换 -->
<link rel="stylesheet" href="styles/tokens.css?v=2">
<link rel="stylesheet" href="styles/reset.css?v=2">
<link rel="stylesheet" href="styles/layout.css?v=2">
<link rel="stylesheet" href="styles/components.css?v=2">
<link rel="stylesheet" href="styles/responsive.css?v=2">

<script src="scripts/config.js?v=2"></script>   <!-- 先定义 $, bytes, showConnToast -->
<script src="scripts/data.js?v=2"></script>     <!-- 引用 showConnToast（在 config.js） -->
<script src="scripts/render.js?v=2"></script>
<script src="scripts/charts.js?v=2"></script>
<script src="scripts/events.js?v=2"></script>
<script>
  // init: setupEvents, setupScroll, loadData, startClock, startFooterUptime, setupRouter
</script>
```

`showConnToast()` 必须在 `config.js` 中（最优先加载），因为 `data.js` 中的 `fetchJSON` 覆盖函数会在 API 错误时调用它。若放 `events.js` 中会报 ReferenceError。

### 开发

源码在 `~/galaxy-glass/src/`，编辑对应文件后运行：
```bash
cd ~/galaxy-glass
./deploy.sh     # tar → scp → 解压 → 重启 proxy
```

### Proxy 服务静态文件

`galaxy-proxy.py` 需要做两个改动才能支持外部分文件：

1. 在 `do_GET` 中新增静态文件路由：
```python
if clean_path.startswith("/styles/") or clean_path.startswith("/scripts/"):
    rel = clean_path.lstrip("/")
    return self._serve_static(rel)
```

2. 使用 `_serve_static` 方法（非 `super().do_GET()`）保证正确的 Content-Type 和 Cache-Control 头。

3. 所有引用加 `?v=2` 参数绕过 Cloudflare 缓存。每次修改 CSS/JS 后更新版本号（如 `?v=3`）。

### 代理完整代码位置
`/opt/komari/galaxy-proxy.py` - 带 _serve_static 方法和静态文件路由的版本。

## CSS 陷阱

### `.container` + `.main` 的 padding 覆盖
`.container` 类设定了水平 `padding: 0 var(--container-pad)`，但 `.main { padding: 1.5rem 0 }` 使用缩写会**覆盖**掉 `.container` 的水平 padding。必须用 longhand：
```css
.main { padding-top: 1.5rem; padding-bottom: 1.5rem; }
```

### 根 CSS 变量与 Canvas 图表颜色硬编码脱节
Canvas 图表颜色硬编码在 JS 中（`drawLineChart` 和 `drawNetChart`）。修改 `--accent`/`--accent-2` 时必须同步更新 JS。grep 全项目清除旧色值。

### 全局文字对比度
```css
--text-muted: rgba(240, 253, 244, 0.55);  /* 原0.48，提高后小字更清晰 */
```

### 间距系统
```css
--space-1: 4px; --space-2: 8px; --space-3: 12px; --space-4: 16px; --space-5: 24px; --space-6: 32px;
--gap: var(--space-4); --gap-sm: var(--space-3);
```
新样式优先用 `var(--space-N)` 而非硬编码 px。保留已在用的 5px/6px/7px/10px 等微调值不改。

## JS 陷阱

### `||` 短路导致合法值 0 被丢弃
```js
var l1 = latest.load && latest.load.load1 || latest.load1;  // 0 || undefined → undefined
// ✅ 用 !==undefined 明确判断
var l1 = latest.load && latest.load.load1 !== undefined ? latest.load.load1 : latest.load1;
```

### `findIndex` + 已删除数组元素
```js
// 若 '在线' 行已被从 rightRows 删除，findIndex 返回 -1 → splice(0,0,...) 插到开头
rightRows.splice(rightRows.findIndex(r => r.l === '在线') + 1, 0, loadRow);
// ✅ 改用仍在数组中的元素作为锚点
rightRows.splice(rightRows.findIndex(r => r.l === '更新') + 1, 0, loadRow);
```

### 详情页 resize 监听泄漏
```js
// ❌ 每次 renderDetailView 都添加新监听
window.addEventListener('resize', redrawDetailCharts);
// ✅ 加标志位
if (!window._dc) { window.addEventListener('resize', redrawDetailCharts); window._dc = true; }
```

### hasError 永不重置
```js
var nodeData = await fetchJSON('/api/nodes');
if (!nodeData || !nodeData.data) { hasError = true; /* 错误态 */; return; }
hasError = false;  // ← 成功时清除
```

### 详情页 sysinfo 负载字段读取
```js
// l1 可能来自 latest.load.load1 或 latest.load1（旧格式兼容）
var l1 = latest.load && latest.load.load1 !== undefined ? latest.load.load1 : latest.load1;
```

### 网络图表颜色转换
```js
// hex → rgba 用 _hc helper（定义在 drawNetChart 内）
g.addColorStop(0, _hc(color, '0.15'));
```
