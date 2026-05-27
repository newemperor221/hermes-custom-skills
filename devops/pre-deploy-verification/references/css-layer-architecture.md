# GalaxyGlass CSS 6 层架构

## 背景
GalaxyGlass 探针页面是单一 HTML 文件（~680 行），所有 CSS 在 `<style>` 块中。修改一处 CSS 可能因选择器冲突误伤其他地方。

## 目标
在不改变任何 CSS 属性值、类名、HTML 结构的前提下，按层级组织 CSS，使后续修改有明确的作用域预期。

## 6 层结构

```
┌─ LAYER 1: 设计令牌 (Design Tokens)
│   :root { --accent: ... }  — CSS 变量，改这里影响全局
├─ LAYER 2: 全局重置 (Global Reset)
│   *, html, body, a, img, ::selection, ::-webkit-scrollbar
├─ LAYER 3: 布局组件 (Layout)
│   .page, .container, .bg-layer, .navbar, .main, .footer, 
│   .back-to-top, .detail-view, .detail-body
├─ LAYER 4: UI 组件 (UI Components)
│   .search-box, .sort-btn, .dropdown, .chip, .filters,
│   .skeleton, .stat-card, .loading-state, .back-btn,
│   .metric-card, .sysinfo-card, .chart-card, .traffic-card,
│   .tags-card, .detail-loading, .detail-meta
├─ LAYER 5: 业务组件 (Business Components)
│   .nodes-grid, .node-card, .node-status, .node-os-icon,
│   .node-name, .card-metrics, .node-footer, .price-badge
└─ LAYER 6: 动画 & 工具类
    @keyframes, .hidden
```

## 维护规则

1. 改 Layer 1 影响全局（颜色/间距/字体）
2. 改 Layer 3 只影响布局，不影响组件样式
3. 改 Layer 4 不影响 Layer 5 的业务组件
4. `@media` 规则跟随其父组件，不集中放在底部
5. 响应式覆盖写在对应组件的最后一个规则之后
6. 不去重、不改名、不改变任何 CSS 值 — 纯重组

## 实施方法

使用 `sed` 精确替换整个 `<style>...</style>` 块：
1. 从公网 `curl -s https://<监控面板域名>/` 抓取当前部署版
2. 在本地按 6 层重组
3. `scp -P 46748` 直推至远程
