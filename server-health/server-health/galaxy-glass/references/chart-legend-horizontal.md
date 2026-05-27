# 网络速率图表图例水平排布

> 2026-05-15 session：用户要求「应该和网络速率那行平行，上下之间六点空隙」

## Canvas drawNetChart 图例位置演进

| 版本 | 布局 | y坐标 | 间距 | 用户反馈 |
|------|------|-------|------|---------|
| 原始 | 竖直：↑在上，↓在下 | y=10, y=22 | ~12px | 「应该和网络速率那行平行」 |
| 第1轮 | 竖直上移 | y=8, y=19 | ~11px | 不够水平 |
| **最终** | **水平并排** | **y=8 同一行** | **6px** | ✅ 确认 |

## 最终渲染代码

```js
ctx.font='10px sans-serif';
ctx.fillStyle='#f59e0b';
ctx.fillText('↑ 上行',w-126,8);
ctx.fillRect(w-88,6,12,2);
ctx.fillStyle='#10b981';
ctx.fillText('↓ 下行',w-70,8);
ctx.fillRect(w-32,6,12,2);
```

## ⚠️ 后续演进（2026-05-14）：Canvas → HTML 迁移

2026-05-14 session 中，用户要求「↑上行和网络速率字样水平对齐，↓下行和速率数据对齐」。Canvas 内定位无法满足跨元素的精确对齐需求。

**当前线上版本已不再使用 Canvas 图例**，改为 HTML span 嵌入 card title+badge：
- ↑上行 → 嵌入标题区 `<div class="chart-title">网络速率 <span class="legend-up">↑ 上行</span></div>`
- ↓下行 → 嵌入 badge 区 `<div class="chart-badge">— <span class="legend-down">↓ 下行</span></div>`
- Canvas 中的 `fillText` / `fillRect` 图例代码全部删除

详见 `galaxy-glass` SKILL.md 的「drawNetChart 图表图例：Canvas → HTML 迁移」章节。

## 位置验证

在浏览器 console 中验证图例位置：
```js
var c = document.getElementById('chart-net');
if (c) {
  var ctx = c.getContext('2d');
  ctx.font = '10px sans-serif';
  console.log('↑上行宽:', ctx.measureText('↑ 上行').width);
  console.log('↓下行宽:', ctx.measureText('↓ 下行').width);
  console.log('canvas宽:', c.width);
  // 预期：w-126 到 w-20 之间，两组间距6px
}
```

## 注意
- 硬编码位置以 w-126 为起始，以「↑上行」≈36px 宽度为基准
- 条形与文字的 2px 间隙要均匀，否则视觉上条形像「贴」在文字上
- 右侧保留 w-20 边距，不与 canvas 边界紧贴
