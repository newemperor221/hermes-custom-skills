# CSS Grid Subgrid 表格布局研究 — 2026-05-05

## 核心问题

每行独立 `display:grid`（或 flex）导致列宽各自计算，内容长度不一致时列错位。

**经典场景**：节点名称列（如 "ColoCrossing | 洛杉矶2" vs "Akile"）宽度不同，后面所有列起始位置歪掉。

## 解决方案对比

### 方案 A：`<table>` + CSS Grid + Subgrid（最优）

**HTML**：保持语义 `<table>` 不变
```html
<table style="display: grid; grid-template-columns: 160px 1px repeat(6, 1fr);">
  <thead style="display: grid; grid-column: 1 / -1; grid-template-columns: subgrid; visibility: collapse;">
    <tr style="display: grid; grid-column: 1 / -1; grid-template-columns: subgrid;">
      <th scope="col">节点</th><th scope="col">CPU</th>...
    </tr>
  </thead>
  <tbody style="display: grid; grid-column: 1 / -1; grid-template-columns: subgrid; gap: 16px;">
    <tr style="display: grid; grid-column: 1 / -1; grid-template-columns: subgrid;">
      <td>...</td><td>...</td>
    </tr>
  </tbody>
</table>
```

**优势**：语义正确 + 整行 hover + 列完美对齐 + `fr` 语法
**劣势**：Subgrid 支持率约 90%+（2025），需 `@supports` fallback

**参考**：Josh W. Comeau "Brand New Layouts with CSS Subgrid" (2025-12)

### 方案 B：JS 动态计算列宽

遍历所有行，取每列最大宽度，统一应用。komari-status-theme 已有此方案（`alignTableColumns()`）。

**劣势**：需要 JS、FOUC 闪烁风险、复杂易错

### 方案 C：固定列宽（现有方案）

左侧固定 160px/180px，其余 `flex: 1` 或 `grid-template-columns: repeat(6, 1fr)`。

**劣势**：固定宽度无法响应内容变化，长名称被截断

## Subgrid 关键语法

```css
/* 父级：定义完整列结构 */
table {
  display: grid;
  grid-template-columns: 160px 1px repeat(6, minmax(0, 1fr));
}

/* 子级：继承父级列定义 */
thead, tbody, tr {
  display: grid;
  grid-column: 1 / -1;           /* 占据所有列 */
  grid-template-columns: subgrid; /* 继承父级列结构 */
}

/* 行内列：line 编号在 subgrid 内重置为 1 */
td:nth-child(1) { grid-column: 1; } /* subgrid 第1列，不是父表第1列 */
```

**已知坑**：
1. Subgrid 默认只占 1 行/列，必须配合 `grid-row: span N` 预留空间
2. line 编号在 subgrid 内重置为 1（不是父 grid 的编号）
3. 与 `auto-fill`/`auto-fit` 不兼容，需要固定列数

## 实践结论

对于 komari 主题（单文件 HTML，无构建工具）：
- 方案 B（JS 动态）仍然是当前生产方案
- 如果迁移到 React 构建，方案 A 明显更优
- 方案 C（固定宽度）是最简方案，但牺牲灵活性

## 参考资料

- [CSS Subgrid on web.dev](https://web.dev/articles/css-subgrid)
- [Josh Comeau — CSS Subgrid](https://www.joshwcomeau.com/css/subgrid/)
- [Frontend Engineering — Better Tables With Grid CSS and Subgrid](https://frontendengineering.substack.com/p/better-tables-with-grid-css-and-subgrid)
- [CSS subgrid is super good — David Bushell](https://dbushell.com/2026/04/02/css-subgrid-is-super-good/)
