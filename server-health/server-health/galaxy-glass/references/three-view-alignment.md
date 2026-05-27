# Three-View Horizontal Alignment

> GalaxyGlass 的卡片页、表格页、详情页三者的内容左/右边缘必须在同一条竖直线上。

## Architecture

```html
<main class="container main">          ← .main { padding: 1.5rem 0 } 覆盖了 .container 的 padding
                                          → 父容器水平 padding = 0
  ├── .stats-grid                      ← 通栏（无 padding）— 顶部统计栏
  ├── #region-filters { padding: 0 1.5rem }
  ├── .nodes-grid { padding: 0 1.5rem } ← 卡片视图，独立 padding
  ├── .table-view { padding: 0 1.5rem } ← 表格视图，独立 padding
  └── <div id="detail-content"> 
        └── .detail-content-wrap { padding: 0 1.5rem } ← 详情页也需独立 padding！
              ├── .metrics-grid
              └── .detail-body
</main>
```

## Why Each View Needs Its Own padding

`.main { padding: 1.5rem 0 }` 是简写属性，完全覆盖 `.container { padding: 0 1.5rem }`（同优先级，源序靠后胜出）。结果是 `<main>` 的左右 padding = 0。

所以每个子元素必须自己声明 `padding: 0 1.5rem` 来获得缩进。

## Common Mistakes

### ❌ 以为表格视图 padding 是"多余的"

```css
/* 错误推论：.table-view 在 .container 内部，所以已有 padding */
.table-view {  /* 去掉 padding */ }
```

### ❌ 忘记详情页也需要 padding

```css
/* 错误：详情页内容直接挨着 <main> 边缘 */
#detail-content { /* 没有 padding */ }
.metrics-grid { /* 没有 padding */ }
.detail-body { /* 没有 padding */ }
```

### ❌ 只测试了卡片和表格

三视图对齐必须全部验证。如果只检查卡片页和表格页就以为对齐了，详情页的内容会偏移。

## 验证方法

在浏览器 Console 中执行：

```js
// 卡片页内容左边缘
document.querySelector('.node-card')?.getBoundingClientRect().left
// 表格行内容左边缘
document.querySelector('.table-row')?.getBoundingClientRect().left
// 详情页指标卡内容左边缘
document.querySelector('#detail-metrics .metric-card')?.getBoundingClientRect().left
// 页脚内容左边缘
document.querySelector('.footer-brand')?.getBoundingClientRect().left
```

差值必须 ≤ 1px。

## Fix Template

如果发现详情页未对齐，在 `#detail-content` 的内部加入 padding：

```css
#detail-content { padding: 0 1.5rem; }
/* 或者包一层 div：<div class="container" style="padding:0 1.5rem"> */
```

如果卡片/表格页未对齐，检查它们的父级是否继承了 `.main` 的 0 padding：
```css
.nodes-grid { padding: 0 1.5rem; }
.table-view { padding: 0 1.5rem; }
#region-filters { padding: 0 1.5rem; }
```
