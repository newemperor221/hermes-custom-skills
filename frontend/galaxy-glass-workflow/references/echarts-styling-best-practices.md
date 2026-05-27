# ECharts Styling Best Practices

> 探针面板详情页 ECharts 图表美化方案。设计原则：透明背景融入毛玻璃、无 Y 轴、数据在卡片顶部显示。

## 配置总览

```
// 通用配置
backgroundColor: 'transparent'      // 透明背景
grid: { left: 1, right: 32, top: 4, bottom: 20 }  // right:32 给 endLabel 留空间

// X 轴 — 极淡显示时间标签
xAxis: {
  type: 'category', boundaryGap: false,
  axisLine:   { show: false },
  axisTick:   { show: false },
  axisLabel:  { color: 'rgba(255,255,255,0.35)', fontSize: 11, margin: 4, fontWeight: 500 },
  splitLine:  { show: true, lineStyle: { color: 'rgba(255,255,255,0.06)', width: 1 } }
}

// Y 轴 — 完全隐藏
yAxis: { type: 'value', show: false, min: 0 }

// 线条 — 厚 + 发光 + 悬浮高亮
series: [{
  type: 'line', smooth: true,
  symbol: 'circle', symbolSize: 0, showSymbol: false,  // 隐藏数据点，hover 时显示
  lineStyle: { width: 2.5, color: '#10b981',
    shadowBlur: 8, shadowColor: 'rgba(16,185,129,0.25)' },
  areaStyle: { color: gradient('rgba(16,185,129,0.2)') },
  emphasis: {
    itemStyle: { color: '#10b981', borderWidth: 0 },
    lineStyle: { width: 3 },
    focus: 'series'
  }
}]

// 末端标签（显示最新值）
endLabel: {
  show: true,
  formatter: function(p) { return p.value.toFixed(1)+'%' },
  color: '#10b981', fontSize: 13, fontWeight: 700,
  fontFamily: '12px Inter,-apple-system,system-ui,sans-serif',
  distance: 0, verticalAlign: 'middle',
  padding: [2,6,2,6],
  backgroundColor: 'rgba(16,185,129,0.12)',
  borderRadius: 4
}

// 最新数据点标记
markPoint: {
  data: [{
    coord: [labels.length-1, lastValue],
    symbol: 'pin', symbolSize: 40,
    label: { show: false },
    itemStyle: { color: '#10b981' }
  }],
  silent: true
}

// 悬浮提示 — 十字准星 + 粗体格式化
tooltip: {
  trigger: 'axis', borderWidth: 0,
  axisPointer: { type: 'cross',
    crossStyle: { color: 'rgba(255,255,255,0.12)' },
    label: { backgroundColor: 'rgba(0,0,0,0.6)',
      borderColor: 'rgba(255,255,255,0.1)', borderWidth: 1,
      borderRadius: 4, padding: [3,8], fontSize: 11,
      fontFamily: '12px Inter,-apple-system,system-ui,sans-serif' }
  },
  formatter: function(p) {
    return '<span style="font-weight:600;font-size:12px">'+p[0].axisValue+'</span>'+
      '<br/>CPU <span style="color:#10b981;font-weight:700">'+p[0].value.toFixed(1)+'%</span>';
  }
}
```

## 颜色方案

| 图表 | 色值 | 渐变起点 | 渐变中段(60%) | 发光 |
|------|------|---------|--------------|------|
| CPU | `#10b981`（绿） | `rgba(16,185,129,0.2)` | `rgba(16,185,129,0.08)` | `rgba(16,185,129,0.25)` |
| 内存 | `#818cf8`（紫） | `rgba(129,140,248,0.2)` | `rgba(129,140,248,0.08)` | `rgba(129,140,248,0.25)` |
| 上行 | `#f59e0b`（琥珀） | `rgba(245,158,11,0.2)` | `rgba(245,158,11,0.08)` | `rgba(245,158,11,0.25)` |
| 下行 | `#10b981`（绿） | `rgba(16,185,129,0.2)` | `rgba(16,185,129,0.08)` | `rgba(16,185,129,0.25)` |

## 渐变填充（3-stop，更细腻）

```javascript
function gd(col) {
  // col 格式: 'rgba(16,185,129,1)' — 必须能正确解析 rgba 参数
  var parts = col.replace('rgba(', '').replace(')', '').split(',').map(Number);
  return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    {offset: 0, color: col},                                           // 100% 色值
    {offset: 0.6, color: 'rgba(' + parts[0] + ',' + parts[1] + ',' + parts[2] + ',0.08)'}, // 8% 中段
    {offset: 1, color: 'rgba(0,0,0,0)'}                               // 完全透明
  ]);
}
```

3-stop 比 2-stop（color → transparent）更自然：上方保留更久色值，底部才渐隐。
⚠️ `rgba(0,0,0,0)` 比 `'transparent'` 在某些浏览器上渲染更可靠。

### ⚠️ 颜色解析陷阱（2026-05-20 修复）

**核心规则：绝对不要对 `rgba()` 格式的颜色字符串做 `replace(')', ...)` 操作。**

```javascript
// ❌ 致命 bug — 对 'rgba(16,185,129,1)' 执行：
col.replace(')', ',0.08)')
// 结果：'rgba(16,185,129,1,0.08)' — 5 个参数！非法颜色值！

// ❌ 另一个变体：
col.replace(')', ',0.25)')
// 结果：'rgba(16,185,129,1,0.25)' — 同样非法
```

因为 `rgba(r,g,b,a)` 格式中，第一个 `)` 出现在 a（alpha）后面。`replace(')', ...)` 匹配了这个右括号，把 alpha 值 1 误当做通道值处理。

**对调仅含 3 个 RGB 值的格式如 `rgb(16,185,129)` 时，这种操作是安全的，因为第一个 `)` 在第三个值后面。但传入带 alpha 的 `rgba()` 格式时就炸了。**

**正确做法**：解析出 R,G,B 数字，然后重新组装：

```javascript
// ✅ 正确 — 解析出 RGB 再重新组装
var parts = col.replace('rgba(', '').replace(')', '').split(',').map(Number);
// parts = [16, 185, 129, 1]
var newColor = 'rgba(' + parts[0] + ',' + parts[1] + ',' + parts[2] + ',0.08)';
// newColor = 'rgba(16,185,129,0.08)' ✅

// 同样用于 shadowColor:
var rgb = parts.slice(0, 3).join(',');
// rgb = '16,185,129'
var shadowColor = 'rgba(' + rgb + ',0.25)';
// shadowColor = 'rgba(16,185,129,0.25)' ✅
```

**此 bug 的症状**：ECharts 系列完全消失（`seriesLen: 0`）。CanvasGradient.addColorStop 抛出非法颜色异常，导致整个 setOption 调用静默失败。控制台无报错（异常被 ECharts 内部吞掉）。详情页显示 loading 完成（图表容器可见）但没有任何线或填充渲染。

**受影响的内容**（所有用到 `rgba()` 作为 col 参数的地方）：
- `gd()` 的渐变颜色
- `lineStyle.shadowColor`
- 任何其他通过字符串替换生成 rgba 的地方

## tooltip formatter 示例

单线（CPU/内存）：
```javascript
formatter: function(p) {
  return '<span style="font-weight:600;font-size:12px">'+p[0].axisValue+'</span>'+
    '<br/>CPU <span style="color:#10b981;font-weight:700">'+p[0].value.toFixed(1)+'%</span>'
}
```

双线（网络）：
```javascript
function bl(v) { /* bytes → 可读格式 */ }
formatter: function(p) {
  return '<span style="font-weight:600;font-size:12px">'+p[0].axisValue+'</span>'+
    '<br/><span style="color:#f59e0b">↑ '+bl(p[0].value)+'</span> <span style="color:#10b981">↓ '+bl(p[1].value)+'</span>'
}
```

## 曲线平滑度：`smooth` 参数选择

ECharts 提供两种平滑模式：

| 值 | 算法 | 效果 | 适用场景 |
|----|------|------|---------|
| `smooth: true` | MonotoneX（单调保形） | 不产生过冲，尊重原始数据趋势 | 数据有明确单调趋势 |
| `smooth: 0.5` | Cardinal 样条（张力 0.5） | 适度弯曲，视觉柔和 | 波动数据，折中 |
| `smooth: 0.8` | Cardinal 样条（张力 0.8） | **强烈弯曲**，视觉效果突出 | 数据量少、想要曲线美感的监控图 |

**用户偏好**：`smooth: 0.8` — 用户明确要求「曲线」，默认值不够弯。张力 0.8 在数据点之间产生明显的贝塞尔弧线。

```javascript
series: [{
  type: 'line',
  smooth: 0.8,    // ← 高张力弯曲，不是 smooth: true
  ...
}]
```

注意：数据完全平坦（所有点值相同）时，任何 smooth 值都不会产生曲线。这是数学限制 — 直线连接同一 Y 值的点永远是直线。

## 动画

```javascript
animationDuration: 600,       // 数据加载时的入场动画
animationEasing: 'cubicOut',  // 缓出效果，更流畅
```

## 数据点符号（hover 时显示）

```javascript
symbol: 'circle',     // 圆形符号
symbolSize: 0,        // 默认隐藏（不显示数据点）
showSymbol: false,    // 不自动显示
// hover 时通过 emphasis 高亮显示
emphasis: {
  lineStyle: { width: 3 },  // hover 时线条加粗
  focus: 'series'           // 聚焦当前系列
}
```

## 关键注意：canvas DPI 与尺寸

### devicePixelRatio

```javascript
echarts.init(canvasEl, null, {
  devicePixelRatio: Math.ceil(window.devicePixelRatio || 1) || 2
});
```

不设此参数时，低 DPR 屏幕（1x）canvas 内部 buffer 可能不够清晰。

### ⚠️ Canvas 尺寸陷阱（隐藏容器 → 0 尺寸）

**问题**：当 ECharts 在 `display:none` 容器（如详情页初始隐藏）中 init 时，容器 clientWidth/clientHeight 为 0。ECharts 设置 canvas.width=0, canvas.height=0，此时：
- canvas 的 HTML 属性 width="0" → CSS 尺寸也是 0px
- 后续 CSS 的 `width: 100% !important` 强制拉伸 display 尺寸到 629px
- 内部 buffer 仍为 0×0 → **渲染模糊/不可见**

**解决方案（修复时间线 2026-05-20）：**

1. **CSS 层**（`components.css`）：
   ```css
   .chart-canvas { width: 100%; height: 130px; }
   .chart-canvas canvas { display: block; width: 100%; height: 100%; }  /* 无 !important！*/
   .chart-canvas.net-chart { height: 200px; }
   ```
   - `display: block` — canvas 需要块级布局
   - `width: 100%; height: 100%` — 提供 fallback 尺寸（无 !important，ECharts 的内联 style 优先级更高）
   - ❌ 不要 `!important` — 否则 ECharts 无法通过内联 style 覆盖 canvas 的 HTML 属性

2. **JS 层**（`app.js` `ec()` 函数）：
   ```javascript
   function ec(id) {
     if (window._echarts[id]) window._echarts[id].dispose();
     var el = document.getElementById(id);
     // ★ 在 echarts.init 之前预设置 canvas 尺寸
     var p = el.parentElement;
     if (p && p.clientWidth > 0) {
       el.style.width = p.clientWidth + 'px';
       el.style.height = p.clientHeight + 'px';
     }
     window._echarts[id] = echarts.init(el, null, {
       devicePixelRatio: Math.ceil(window.devicePixelRatio || 1) || 2
     });
     // ★ 延迟 resize 确保容器渲染完成后图表适配
     setTimeout(function() { window._echarts[id].resize(); }, 50);
   }
   ```

3. **验证**（浏览器控制台）：
   ```javascript
   // canvas 内部分辨率应 ≈ CSS 尺寸
   var c = document.getElementById('chart-cpu');
   c.width + ' x ' + c.height           // → "629 x 130" ✅
   c.clientWidth + ' x ' + c.clientHeight  // → "629 x 130" ✅
   
   // ECharts 实例宽度应匹配
   window._echarts['chart-cpu'].getWidth()  // → 629 ✅
   ```

**根本原因**：两个 `requestAnimationFrame` 嵌套不保证容器已完成 layout。详情页的 #detail-content 从 `display:none` 变为可见后，浏览器需要一帧才能计算 clientWidth。

**自测清单**：
- [ ] canvas 的 `width` HTML 属性 ≠ 0（应为容器 CSS 宽度）
- [ ] `getComputedStyle(canvas).display` ≠ `'inline'`（应为 `'block'`）
- [ ] chart-canvas 容器无 canvas 的 `!important` CSS 规则
- [ ] `ec()` 中调用了 `.resize()` 延迟

## 调研来源

- [ECharts 官方示例 - Gradient Stacked Area Chart](https://echarts.apache.org/examples/en/editor.html?c=area-stack-gradient) — 渐变填充方案
- [ECharts 官方示例 - Line Gradient](https://echarts.apache.org/examples/en/editor.html?c=line-gradient) — 渐变色线条
- [ECharts 官方文档 - Area Chart](https://echarts.apache.org/handbook/en/how-to/chart-types/line/area-line/) — areaStyle 配置
- [ECharts 官方文档 - Style](https://apache.github.io/echarts-handbook/en/concepts/style/) — shadowBlur/itemStyle
- [ECharts 5 新增 endLabel](https://echarts.apache.org/en/option.html#series-line.endLabel) — 末端标签（v5.0+）
- [ECharts markPoint](https://echarts.apache.org/en/option.html#series-line.markPoint) — 数据标记点
