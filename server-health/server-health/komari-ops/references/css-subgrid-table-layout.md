# CSS Subgrid 表格布局研究（2026-05-05）

## 核心问题

每行独立 `display:grid` → 每行自己计算列宽 → 内容长度不一时列错位。

## 解决方案：`<table>` + CSS Grid + Subgrid

### 为什么用 table 而非纯 div

| 特性 | 纯 div | `<table>` + Grid |
|------|--------|-----------------|
| 整行 hover | 需 JS 或 hack | `tr:hover` 原生支持 |
| 无障碍（屏幕阅读器） | 差（需 role 属性） | 好（语义原生） |
| 列对齐 | 各自为政 | subgrid 统一 |
| fr/max-content 列宽 | 可以 | 可以 |

### Subgrid 关键语法

```css
/* 表层：定义列结构 */
table {
  display: grid;
  gridTemplate-columns: 160px 1px repeat(6, minmax(0, 1fr));
}

/* 子层：继承父级列 */
thead, tbody, tr {
  display: grid;
  gridColumn: 1 / -1;          /* 占满整行 */
  gridTemplateColumns: subgrid; /* 继承父级列定义 */
}
```

**注意**：`grid-column: 1 / -1` 表示从第1条线到倒数第1条线（整行）。

### Subgrid 行对齐需显式声明

子元素默认只占 1 cell，`grid-row` 不会自动跨行：

```css
/* ❌ 不声明 span：所有内容挤在一行 */
tr { display: grid; grid-template-rows: subgrid; }

/* ✅ 声明要跨几行 */
tr { display: grid; grid-row: span 3; grid-template-rows: subgrid; }
```

### @supports Fallback

```css
@supports not (grid-template-columns: subgrid) {
  tr { display: flex; flex-direction: column; }
}
```

### 关键参考

- Josh Comeau: https://www.joshwcomeau.com/css/subgrid/
- Frontend Engineering: https://frontendengineering.substack.com/p/better-tables-with-grid-css-and-subgrid
- MDN: https://developer.mozilla.org/en-US/docs/Web/CSS/CSS_grid_layout/Subgrid_size_alignment_and_tracking
