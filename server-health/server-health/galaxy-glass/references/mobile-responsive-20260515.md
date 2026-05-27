# 2026-05-15 移动端修复

## 改动清单

### 1. 搜索框移动端可见性
- **问题**：搜索框在 639px 以下 `display: none`，用户找不到搜索按钮
- **修复**：折叠为 36px 图标，点击展开为 200px 覆盖在导航栏上
- **文件位置**：`index.html` line 120
- **CSS**：
  ```css
  @media (max-width: 639px) {
    .search-box { max-width: 36px; }
    .search-box.open, .search-box:focus-within {
      max-width: 200px; position: absolute; right: 0; z-index: 300;
    }
  }
  ```

### 2. Stat 卡片 480px 收紧
- **问题**：用户反馈"主页四个卡片没有适配移动端"
- **修复**：在现有 639px 断点基础上增加 480px 断点
- **文件位置**：`index.html` lines 172-174
- **CSS**：
  ```css
  @media (max-width: 480px) { .stats-grid { grid-template-columns: 1fr 1fr; gap: 6px; } }
  @media (max-width: 480px) { .stat-card { padding: 8px 10px; gap: 6px; } }
  @media (max-width: 480px) { .stat-card svg { width: 1rem; height: 1rem; flex-shrink: 0; } }
  ```

### 3. 筛选栏 639px 全宽滚动
- **问题**：用户反馈"分组标签没有适配移动端"
- **修复**：将横向滚动断点从 480px 扩大到 639px
- **文件位置**：`index.html` lines 199-200
- **CSS**：
  ```css
  @media (max-width: 639px) { .filters { width: 100%; overflow-x: auto; scrollbar-width: none; } }
  @media (max-width: 639px) { .region-filters-wrap { margin: 0 -12px; padding: 0 12px; } }
  ```

### 4. Footer Powered by 居中
- **问题**：用户反馈"Powered by Komari 没有居中"
- **根因**：`.footer-powered` 默认 `text-align: right` 覆盖了父容器 `text-align: center`
- **修复**：显式覆盖
- **文件位置**：`index.html` line 427
- **CSS**：
  ```css
  @media (max-width: 639px) { .footer-powered { text-align: center; } }
  ```

### 5. 详情页图表移动端适配
- **文件位置**：`index.html` lines 374-375
- **CSS**：
  ```css
  @media (max-width: 480px) { .chart-legend { margin-left: 6px; font-size: 11px; } }
  @media (max-width: 480px) { .chart-badge { font-size: 11px; } }
  ```

## 笔记

- 用户对「背景色的框」非常敏感——任何突兀的色块都会被指出
- 移动端测试最好在真机上进行（浏览器模拟的 viewport resize 可能不全）
- 所有改动都集中在 CSS media queries，无 JS 改动
