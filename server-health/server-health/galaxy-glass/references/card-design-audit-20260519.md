# GalaxyGlass 卡片设计审计（2026-05-19）

## 审计方法
1. `browser_navigate` → 加载 stat.357561.xyz
2. `browser_vision` with `annotate=true` → 获取精确元素尺寸（box 坐标）
3. 读取源代码（render.js + CSS）分析元素生成逻辑
4. 对比代码逻辑 vs 实际视觉呈现

## 发现的 8 个问题（2026-05-19 前 7 个，后补充 1 个）

### ① 状态点重复
**位置：** `src/scripts/render.js` 的 `renderCard()` 函数
**根因：** header 中有 `.node-status`（9px 圆圈，`--accent` 绿），同时 `.node-name` 内又有 `.status-dot`（8px 圆圈，`--online` 绿带脉冲动画）。两个独立绿点，颜色值也不同。
**修复：** 删掉 `<div class="node-status ...">`，保留 `.status-dot` 作为唯一指示器。`.status-dot` 尺寸提升为 9px，颜色改为 `--accent`。

### ② ~~NET 行无进度条（用户明确要求不修）~~

### ③ 价格徽章视觉权重过大
**位置：** `src/styles/components.css` 的 `.price-badge`
**根因：** 所有价格（¥0.18 ~ ¥297）共用 `accent-gradient` 渐变底 + 白字 + `text-shadow`，¥0.18 的徽章比它的 CPU 条更抢眼。
**修复：** 渐变底 → `accent-subtle` 背景 + `accent-border` 边框 + `color: var(--accent)` + `font-weight: 600`。不再用白色文字和渐变。

### ④ 标签区高度不稳定
**位置：** `src/scripts/render.js` + `src/styles/components.css`
**根因：** `.card-tags` 只在有标签时才渲染（条件 `<div>`），导致有标签的卡片多一行高。而且 CSS 用 `margin-top/margin-bottom` 而非在 gap 流中。
**修复：** `.card-tags` 始终渲染（含空内容），CSS 改为 `min-height: 22px`（`min-height` 让空 div 保持高度）。删掉 margin，让 card 的 `gap: 10px` 统一控制间距。

### ⑤ uptime 与 "刚刚" / "1分钟前" 混在一起
**位置：** `src/scripts/render.js` 的 footer 部分
**根因：** footer 只有 uptime（运行时长）和 price badge，最新上报时间（age）没有独立展示，而是从 accessibility 标签中混杂出现。
**修复：** footer 新增 `<span class="node-footer-time">`，用 `age(n.updated_at)` 显示 "刚刚" / "1分钟前"。CSS: `font-size: 11px; color: var(--text-muted); opacity: 0.6` 使其从属地位。n.updated_at 在 `mergeNodeData()` 中已存在。

### ⑥ Squircle 半径与 CSS 不一致
**位置：** `src/scripts/squircle.js` 的 `applySquircles()`
**根因：** squircle JS 硬编码 `rad=16`（node-card）和 `rad=12`（stat/metric），而 CSS `--radius-lg: 22px`、`--radius-md: 16px`。JS 跑之前先显示 CSS 圆角，JS 加载后 clip 成不同半径 → visual flash。
**修复：** node-card/skeleton-card/chart-card → 22px（匹配 `--radius-lg`）；stat-card/metric-card/sysinfo-card/tags-card → 16px（匹配 `--radius-md`）。metric-card 的独立分支也从 12 改为 16。

### ⑦ 卡片 padding 不对称
**位置：** `src/styles/components.css` 的 `.node-card`
**根因：** `padding: 14px 16px`，上下比左右少 2px，在 296px 宽的 4 列网格中产生微妙水平拉伸感。
**修复：** `padding: 16px` 统一。

### ⑧ Chart 暂停按钮移除（2026-05-19）
**位置：** `src/index.html` 中 detail 视图的三个 chart-card
**改动：** 删除 CPU/MEM/NET 三个图表卡片 header 中的 `<button class="chart-pause-btn">⏸ 暂停</button>`。NET 卡的结构略有不同（`chart-header` + `chart-legend`），删除时注意保留 legend。
**CSS 清理：** `.chart-pause-btn` 相关样式改为 `display: none`。无 JS 引用需清理（events.js 中没有 pause 相关的监听器）。

### ⑨ 详情页暂停按钮移除（2026-05-19 第二 session）
**位置：** `src/index.html` 中 detail 视图的三个 chart-card
**改动：** 删除 CPU/MEM/NET 三个图表卡片 header 中的 `<button class="chart-pause-btn">⏸ 暂停</button>`。NET 卡的结构略有不同（`chart-header` + `chart-legend`），删除时注意保留 legend。
**CSS 清理：** `.chart-pause-btn` 相关样式改为 `display: none`。无 JS 引用需清理（events.js 中没有 pause 相关的监听器）。

## 工作流偏好（更新于 2026-05-19）
- 当用户说"行"同意改动后，**直接执行所有计划中的改动**，不要分步征求意见
- 设计审计找到 N 个问题，用户说"除了 X，都修" → 一次性修完其余 N-1 个，commit 为一条
- 每个修改点都要在代码中有精确记录（CSS 行号、JS 函数名、具体旧值→新值）
- 推送 GitHub + 线上部署是两回事：本地 git push 后记得同步部署到服务器
- **用户说"你要不自己去看看呢"** → 说明应该先自己打开页面检查，不要依赖之前的截图或描述来下结论
- **用户说"不错，有没有推送github"** → 检查 git log，如果已推送则直接告知 commit hash，不需要再推一次
