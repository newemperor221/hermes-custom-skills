# 2026-05-14 响应式 + 图表修复 Session

## 修改概览

### 1. Canvas 图例 → HTML 图例（网络速率卡片）
- 移除 `drawNetChart` 中的 `ctx.fillText` 图例绘制（第650行）
- 添加 HTML `.chart-header` + `.chart-legend` 容器
- 图例右对齐，↑上行与标题同行，↓下行与badge数值同行
- Colors: `#f59e0b` (上行黄), `#10b981` (下行翠绿), both bold

### 2. CPU badge 修复
- 原本缺少 `$('badge-cpu').textContent=cpu.toFixed(1)+'%'` 行
- 只更新了 badge-mem 和 badge-net，漏了 badge-cpu → 一直显示 "—"
- fix: 在 renderDetailView 中 badge-mem 赋值前插入 badge-cpu 赋值

### 3. JS 语法错误修复
- Canvas 图例修改时把 `"` 引号错写成 `.` 点号（第650行）
- 导致整个 inline script 语法错误，JS 全部停摆
- 页面能渲染（HTML+CSS）但交互全挂
- fix: 还原为正确引号

### 4. 搜索框移动端适配
- 原 CSS：`@media (max-width: 639px) { .search-box { display: none; } }` — 手机完全隐藏
- 改为：`flex-direction: row-reverse; max-width: 36px` → 展开时向左弹出
- 使用 `row-reverse` 让 input 在 icon 左边

### 5. 空状态背景框修复
- `.empty-state` 原本有 `background: var(--bg-deep)` 
- 搜索无结果时"没有匹配的节点"显示在深蓝色背景方块中
- fix: 移除该 background，保持透明

### 6. fade-out 过渡移除
- `render()` 函数用 `grid.classList.add('fade-out')` → 0.25s 透明过渡
- 搜索时旧 DOM 移除、新 DOM 渲染过程中透明网格暴露容器背景
- fix: 删除 CSS `.nodes-grid.fade-out` 规则，删除 JS 中 add/remove fade-out 的行

### 7. CSS 媒体查询集中管理
- 原 26 条 `@media (max-width)` 散落在各组件间
- 集中到文件末尾 `/* ── Responsive Overrides ──` 区块
- 按断点分组：800px / 680px / 639px / 480px

## 移动端最终断点覆盖

| 断点 | 组件 | 改动 |
|------|------|------|
| 800px | .detail-body | 单列布局 |
| 680px | .nodes-grid | 1列 |
| 639px | .search-box | 36px收缩+向左展开 |
| 639px | .stats-grid | 2列 |
| 639px | .stat-card | 缩小padding/gap/字号 |
| 639px | .filters | 100%宽度+横向滚动 |
| 639px | .footer | 居中 |
| 480px | .stat-card | 进一步缩小 |
| 480px | .chart-legend | 缩小margin-left和字号 |
| 480px | .chart-badge | 缩小字号 |
