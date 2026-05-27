# GalaxyGlass 移动端响应式模式

## Stat 卡片溢出修复

Stats 网格在 4 列桌面 → 2 列手机时，值文字容易溢出。

**问题：** 流量概览 "↑ 98.5GB · ↓ 188.6GB" / 月度开销 "¥94 · 剩余 ¥904" 在手机 150px 宽卡片中 16px 字体溢出。

**修复模式：**
```css
@media (max-width: 639px) {
  .stats-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .stat-card { padding: 10px 12px; gap: 8px; }
  .stat-card .value { font-size: 13px; }   /* 默认 16px */
  .stat-card .value.small { font-size: 11px; } /* 流量/费用值 */
  .stat-card .stat-sub { font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .stat-card svg { width: 1.2rem; height: 1.2rem; } /* 默认 1.6rem */
}
```

## 筛选栏窄屏可滚动

6 个区域筛选项在 <360px 手机上刚好撑满，更窄的屏幕溢出。

```css
@media (max-width: 480px) {
  .filters { overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
  .filters::-webkit-scrollbar { display: none; }
}
```

## 详情页手机紧凑

详情页 2 列 → 1 列时间距和 padding 应缩小：

```css
@media (max-width: 639px) {
  .detail-body { gap: 12px; }  /* 默认 16px */
}
@media (max-width: 480px) {
  .metrics-grid { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .metric-card { padding: 10px 12px; }
  .sysinfo-card, .chart-card { padding: 10px 12px; }
}
```

## 加载状态背景处理

⚠️ **区分两种 loading 态：**

**1. 列表页 loading（骨架屏/初始加载）**
应在首次加载数据时显示，加深色背景防止闪白：
```css
.loading-state, .empty-state, .error-state { background: var(--bg-deep); }
```

**2. 详情页 loading（点击节点后的加载过程）**
数据加载很快（毫秒级），不应显示大色块。去掉背景和 padding，只保留一行小字：
```css
.detail-loading, .detail-error { display: flex; align-items: center; justify-content: center; gap: 8px; color: var(--text-muted); font-size: 14px; }
```
不要加 `background` 和 `padding: 3rem 0`，否则会在详情页出现可见的"长方块"。
来源：用户反馈"能不能不要这个长方块"。

## 毛玻璃可见性

默认 `--bg-glass: 0.025` / `--glass-bg: 0.03` 在深色背景下几乎不可见。建议提升到 `0.06` 以获得可感知的玻璃质感。
