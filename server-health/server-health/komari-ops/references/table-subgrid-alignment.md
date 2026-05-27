# 表格列对齐：CSS Grid + subgrid 方案

## 问题

komari 主题表格视图用两个独立 `<fieldset>`（legend 行 + data 行），各自 `grid-template-columns: repeat(6, 1fr)`，导致列宽分别计算，列对齐错位。

## 解决方案：CSS Grid + subgrid

### 核心思想

父级 `.table-row` 声明 **8 列**网格，两个 fieldset 用 `grid-template-columns: subgrid` 继承父级列宽，实现跨行对齐。

### CSS 改动

```css
/* 父级：声明 8 列网格 */
.table-row {
  display: grid;
  grid-template-columns: 160px 1px repeat(6, minmax(0, 1fr));
  grid-template-rows: auto auto;  /* legend 行 + data 行 */
}

/* 左侧固定区 */
.row-title {
  grid-column: 1;
  grid-row: 1 / 3;
}

/* 分隔线 */
.table-sep {
  grid-column: 2;
  grid-row: 1 / 3;
}

/* fieldset：subgrid 继承父 6 列 */
.table-row .legend-row {
  grid-column: 3 / -1;
  grid-row: 1;
  grid-template-columns: subgrid;
}
.table-row .data-row {
  grid-column: 3 / -1;
  grid-row: 2;
  grid-template-columns: subgrid;
}
```

### JS 改动

```javascript
// renderRow() 中给 fieldset 加 class
`<fieldset class="legend-row">`  // 原来无 class
`<fieldset class="data-row">`
```

### 关键参数

| 参数 | 值 | 说明 |
|------|-----|------|
| 名称列 | 160px | 固定宽度 |
| 分隔线 | 1px | grid-column: 2 |
| 数据列 | `minmax(0, 1fr)` × 6 | `minmax(0,` 防止 fr 被内容撑大 |
| 父级列 | 8 列 | 160px + 1px + 6×subgrid |
| subgrid 父 | `grid-column: 3 / -1` | fieldset 从第 3 列开始，跨 6 列 |

### 为什么不用 `1fr` 而用 `minmax(0, 1fr)`

`1fr` 会被内容撑大（例如长节点名让第一列变宽）。`minmax(0, 1fr)` 强制列宽不超过分配空间，内容溢出用 `overflow: hidden`。

### 验证方法

用 PIL 量截图像素：
```python
from PIL import Image
img = Image.open('screenshot.png')
# 检查所有行的同一列 x 坐标是否一致
xs = [row['x'] for row in rows]  # 所有行同一列 x 坐标
print(f"All x={xs[0]}? {len(set(xs)) == 1}")  # True = 对齐
```

所有行同一列 x 位置完全一致（x=92, width=1082px），行间距均匀（348px/行）→ subgrid 生效。

---

**2026-05-05 实测**：10 行表格，所有行 x 位置完全一致，列对齐正常。
