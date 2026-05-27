# 详情页空余 div 清理（2026-05-14）

## 问题

`detail-left` 中有 `<div class="traffic-card" id="detail-traffic"></div>`，但 JS 的 `renderDetailView()` 从未向这个容器填充任何内容。它是一个空卡片（有 padding/border/background），在页面中显示为一段空白区域。

## 修复

直接从 HTML 模板中删除该元素：

```bash
sed -i '/<div class="traffic-card" id="detail-traffic"><\/div>/d' index.html
```

CSS 规则 `.traffic-card` 与其他卡片共用（`.sysinfo-card, .tags-card, .traffic-card, .chart-card`），所以保留 CSS 不影响。

## 教训

- 每次在 HTML 模板中声明静态容器时，检查 JS 是否真的有对应的 `innerHTML` 赋值
- 特别留意 `renderDetailView()` 这类集中渲染函数——如果函数的变量引用没覆盖所有静态容器，就是死代码
- 排查路径：`grep -n 'id="detail-' index.html` 列出所有 detail 容器 → 再 grep JS 中 `$('detail-xxx')` 确认每个都有赋值
