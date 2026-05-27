# 详情页 DOM 结构 + CSS 选择器速查

> 版本：2026-05-20 · Chart.js 4.4.7 + 克隆 stats-bar + 无分类标题

## DOM 樹

```
div.page#app
├── nav.navbar (in-detail 时 display:none)
├── div.container (共享 stats-bar, padding:0.35rem 0 0)
│   └── div.stats-grid#stats-bar (4列, 始终可见, 仅一个 DOM 元素)
├── div#list-view (detail 时 hidden) → filters → grid
└── div.detail-view#detail-view (list 时 hidden)
    ├── div.detail-nav (sticky, z-index:100, min-height:48px)
    │   └── div.container
    │       └── div.detail-nav-inner (flex, align-items:center, gap:10px, height:48px)
    │           ├── button.back-btn (inline-flex, 32×32, radius:full, glass-bg, glass-border, aria-label="返回")
    │           │   └── svg (16×16, ← 箭头)
    │           └── div.detail-title-area (flex, gap:8px, flex:1, min-width:0)
    │               ├── span.detail-name#detail-name (font-weight:600, 15px)
    │               └── span.detail-meta#detail-meta (font-size:12px, text-muted, text-overflow:ellipsis)
    │
    ├── ★ div.stats-grid#stats-bar (克隆副本 — 仅进入详情页时 window._statsClone 存在)
    │   └── 4 × div.stat-card (与列表视图共享的 stats-bar)
    │
    ├── main.container.main (flex:1, padding-top:0.5rem)
    │   └── div.detail-content-wrap (flex:1)
    │       └── div.detail-content (max-width:var(--container-max), margin:0 auto)
    │           ├── div.detail-loading#detail-loading (flex, center, text-muted, font-size:14px)
    │           ├── div.detail-error#detail-error (hidden, color:var(--danger))
    │           └── div.detail-body#detail-content (hidden, grid 1fr 1.2fr, gap:var(--gap))
    │               ├── div.detail-left (flex column, gap:var(--gap))
    │               │   ├── div.sysinfo-card#detail-hw (glass-bg, glass-border, radius:12px, padding:12px 14px, backdrop-filter:blur)
    │               │   │   └── div.sysinfo-single (flex column)
    │               │   │       ├── div.sysinfo-row × N [CPU型号 / 核心数 / 架构 / 虚拟化 / OS / 内存 / Swap / 磁盘  / GPU]
    │               │   │       │   ├── span.lbl (font-size:13px, text-muted)
    │               │   │       │   └── span.val (font-size:13px, text-primary, font-mono, text-align:right)
    │               │   │       └── ...（无分类标题行）
    │               │   │
    │               │   ├── div.sysinfo-card#detail-status
    │               │   │   ├── div.sysinfo-single
    │               │   │   │   └── div.sysinfo-row × N [进程数 / 负载(如有) / 更新 / 到期]
    │               │   │   │       ├── span.lbl (font-size:13px, text-muted)
    │               │   │   │       └── span.val (font-size:13px, text-primary, font-mono)
    │               │   │   └── div.sysinfo-bill (flex, gap:8px, border-top:glass-border)
    │               │   │       ├── span.bill-chip → "¥XX/月"（价格/周期）
    │               │   │       ├── span.bill-chip → "📊 XX/XX"（已用/限额 — 流量限额仅在此处展示）
    │               │   │       └── span.bill-chip.danger → "📅 N天"（到期 ≤15天 变红）
    │               │   │
    │               │   └── div.tags-card#detail-tags (glass-bg, glass-border, radius:12px, padding:12px 14px)
    │               │       ├── div.tags-title → "标签 · 连接"
    │               │       ├── div.tags-list (flex wrap, gap:4px)
    │               │       │   └── span.tag-chip × N
    │               │       └── div.conn-row (flex, gap:8px) ← TCP/UDP 连接数**仅在此处展示**
    │               │           ├── span.conn-item → "N TCP"
    │               │           └── span.conn-item → "N UDP"
    │               │
    │               └── div.detail-right (flex column, gap:var(--gap))
    │                   ├── div.chart-card (position:relative, padding:12px 14px, radius:12px, glass-bg, glass-border)
    │                   │   ├── ::before (absolute, top:0, left:14px, right:14px, height:2px, 渐变 90deg #10b981→transparent)
    │                   │   ├── div (flex align-items:center, gap:6px)
    │                   │   │   ├── div.chart-title → "CPU 占用率" (font-size:13px, text-muted, letter-spacing:0.03em)
    │                   │   │   └── div.chart-badge#badge-cpu (font-family:mono, font-weight:600, font-size:13px, color:var(--accent))
    │                   │   └── div.chart-canvas (width:100%, height:130px)
    │                   │       └── canvas#chart-cpu (Chart.js 4.4.7, 透明背景)
    │                   │
    │                   ├── div.chart-card ::before (渐变 90deg #818cf8→transparent)
    │                   │   ├── chart-title → "内存占用率"
    │                   │   ├── chart-badge#badge-mem (color:#818cf8)
    │                   │   └── canvas#chart-mem (Chart.js)
    │                   │
    │                   └── div.chart-card ::before (渐变 90deg #f59e0b→transparent)
    │                       ├── div.chart-header (flex column)
    │                       │   ├── div.chart-header-row (flex, space-between, align-items:center)
    │                       │   │   ├── div.chart-header-left (flex, gap:6px)
    │                       │   │   │   ├── div.chart-title → "网络速率"
    │                       │   │   │   └── div.chart-badge#badge-net (color:text-secondary)
    │                       │   │   └── div.chart-legend (flex, gap:8px, font-size:11px, text-muted)
    │                       │   │       ├── span.legend-up → "↑ 上行" (color:#f59e0b, font-weight:bold)
    │                       │   │       └── span.legend-down → "↓ 下行" (color:#10b981, font-weight:bold)
    │                       │   └── div.chart-canvas.net-chart (height:200px)
    │                       │       └── canvas#chart-net (Chart.js, 双数据集)
```

## JS 渲染规则

### leftRows（detail-hw 卡片, 无分类标题）

```javascript
var leftRows = [
  {l:'CPU 型号', v:node.cpu_name||'-'},
  {l:'核心数',   v:node.cpu_cores?'× '+node.cpu_cores:'-'},
  {l:'架构',     v:node.arch||'-'},
  {l:'虚拟化',   v:node.virtualization||'-'},
  {l:'操作系统', v:(node.os||'-').split(' ').slice(0,2).join(' ')},
  {l:'内存',     v:bytes(node.mem_total)},        // ← 2026-05-20 新增
  {l:'Swap',     v:(node.swap_total||0)>0?bytes(node.swap_total):'无'},
  {l:'磁盘',     v:bytes(node.disk_total)}
];
if(node.gpu_name && ...) leftRows.push({l:'GPU', v:node.gpu_name});
```

### rightRows（detail-status 卡片, 无分类标题）

```javascript
var rightRows = [
  {l:'进程数', v:latest.process||'-'},
  // 负载（动态插入在"更新"后面，如果有数据）
  {l:'更新',   v:age(latest.updated_at)},
  {l:'到期',   v:node.expired_at?...}
];
// 流量限额 → 仅在 bill-chip 展示（📊 已用/限额）
// TCP/UDP 连接数 → 仅在 tags-card conn-row 展示
```

### stats-bar 克隆（跨视图共享）

```javascript
// showDetailView 中：
if(!window._statsClone){
  var sb = document.getElementById('stats-bar');
  var clone = sb.cloneNode(true);
  var wrap = document.getElementById('detail-content-wrap');
  wrap.parentNode.insertBefore(clone, wrap);
  window._statsClone = clone;
}

// showListView 中：
if(window._statsClone){
  window._statsClone.parentNode.removeChild(window._statsClone);
  window._statsClone = null;
}

// updateStats 用 querySelectorAll 更新所有匹配 ID 的元素：
document.querySelectorAll('#stat-online-value').forEach(function(e){ e.textContent = ... });
```

## 关键 CSS 选择器

| 选择器 | 作用 | 关键属性 |
|--------|------|---------|
| `.detail-body` | 主网格容器 | `grid-template-columns: 1fr 1.2fr; gap: var(--gap);` |
| `.chart-canvas` | 画布容器 | `width:100%; height:130px;` |
| `.chart-canvas.net-chart` | 网络图更高 | `height:200px;` |
| `.chart-card::before` | 顶部渐变装饰条 | `absolute; top:0; left:14px; right:14px; height:2px;` |
| `.chart-header` | 网络图标题区 | `flex-direction: column;` |
| `.chart-header-row` | 标题+图例同行 | `display:flex; justify-content:space-between;` |
| `.back-btn` | 返回按钮 | `inline-flex; padding:6px; min-h/w:32px; border-radius:9999px;` |
| `.navbar.in-detail` | 详情页隐藏导航 | `display: none;` |
| `.detail-nav` | 详情 sticky 导航 | `position:sticky; top:0; z-index:100; min-height:48px;` |
| `.sysinfo-header` | 分组标题（保留但未使用） | `font-size:11px; letter-spacing:0.05em;` |
| `.sysinfo-row` | 信息行 | `display:flex; justify-content:space-between; padding:6px 0;` |

## 数据展示位置规则（禁止重复）

| 数据 | 展示位置 | 禁止重复的位置 |
|------|---------|--------------|
| CPU/内存/DISK 使用率% | 右侧图表卡片 | 左侧 sysinfo 里不重复 |
| 流量限额 | bill-chip `📊 已用/限额` | rightRows 不重复 |
| TCP/UDP 连接数 | tags-card conn-row | rightRows 不重复 |
| 价格/周期 | bill-chip 第一项 | 不重复 |
| 到期天数 | bill-chip 第三项 | rightRows 的到期行保留 |
| 内存总量 | leftRows | 不重复 |
| 物理内存使用率% | 图表 + 图表顶部 badge | 不在 leftRows 里 |
