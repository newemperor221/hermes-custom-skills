# 移动端响应式修复 (2026-05-14)

## 背景

用户要求检查 GalaxyGlass 在移动端视图下的表现。发现以下问题并修复：

## 问题 1: Stat 卡片文字溢出

**症状**：4 个统计卡片在手机 2 列布局下，值文字（"↑ 98.5GB · ↓ 188.6GB"）在 16px monospace 下溢出卡片。

**计算**（360px 宽手机）：
- 卡片宽度: (360 - 2×24.5 - 8) / 2 = 151.5px
- 内容区: 151.5 - padding(12×2) - gap(8) - icon(16) ≈ 103.5px
- 文字 "↑ 98.5GB · ↓ 188.6GB" 在 16px monospace ≈ 200px ❌ 溢出

**修复**：
```css
/* ☆ 主值 16px→13px，小值 12px→11px，辅助信息 12px→10px+ellipsis */
@media (max-width: 639px) {
  .stat-card .value { font-size: 13px; }
  .stat-card .value.small { font-size: 11px; }
  .stat-card .stat-sub { font-size: 10px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
}
```

**注意**：去掉原行 `@media (max-width: 639px) { .stat-card { padding: 12px 14px; } }`，被新的 `padding: 10px 12px` 替代。

## 问题 2: 筛选栏在极窄屏溢出

**症状**：6 个地区筛选项在 ≤320px 手机上总宽 ≈320px，无滚动支持导致溢出。

**修复**：
```css
@media (max-width: 480px) {
  .filters { overflow-x: auto; -webkit-overflow-scrolling: touch; scrollbar-width: none; }
  .filters::-webkit-scrollbar { display: none; }
}
```

## 问题 3: SVG 图标在手机占空间太大

**修复**：
```css
@media (max-width: 639px) {
  .stat-card svg { width: 1.2rem; height: 1.2rem; }  /* 从 1.6rem 缩小 */
}
```

## 问题 4: 详情页手机 padding 和间距优化

**修复**：
```css
@media (max-width: 639px) {
  .detail-body { gap: 12px; }  /* 从 16px 缩小 */
}
@media (max-width: 480px) {
  .metrics-grid { gap: 8px; }           /* 从 10px 缩小 */
  .metric-card { padding: 10px 12px; }  /* 紧凑化 */
  .sysinfo-card, .chart-card { padding: 10px 12px; }
}
```

## 总计改动

| 区域 | 改动点 | 效果 |
|------|--------|------|
| stats-grid | value 16→13px, value.small 12→11px, stat-sub 12→10px+ellipsis | 防文字溢出 |
| stat-card | SVG 1.6→1.2rem, padding 12→10px, gap 12→8px | 释放更多内容空间 |
| filters | overflow-x: auto | 极窄屏可横向滑动 |
| detail-body | gap 16→12px | 手机端更紧凑 |
| metric/chart/sysinfo cards | padding 12→10px | 手机端更紧凑 |
