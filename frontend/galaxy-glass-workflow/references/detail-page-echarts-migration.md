# ECharts 迁移：Chart.js → Apache ECharts

> 日期：2026-05-20 · 动机：用户说 Chart.js「不够美」，要求「美观第一」
> 
> 迁移路径：手绘 Canvas → Chart.js → **ECharts 5.x**（当前方案）

## ⚠️ 关键教训：不要用 ECharts dark 主题

**用户明确拒绝 ECharts 内置 'dark' 主题。** 理由：暗色主题的纯色背景与页面的毛玻璃卡片（`rgba(255,255,255,0.06)`）不搭，chart 背景色突兀。

**当前方案**：`echarts.init(dom)` 无主题（默认 light），但设置 `backgroundColor: 'transparent'` 让图表背景透出玻璃卡片底色。

```javascript
// ❌ 用户拒绝
echarts.init(document.getElementById(id), 'dark')

// ✅ 当前方案
echarts.init(document.getElementById(id))
// 加上 backgroundColor: 'transparent'
```

同时需要**手动设置坐标轴颜色**（默认 light 主题的轴文字是黑色，在深色页面上看不见）：

```javascript
axisLabel: {color: 'rgba(240,253,244,0.35)', fontSize: 9}
splitLine: {lineStyle: {color: 'rgba(255,255,255,0.06)', type: 'dashed'}}
```

## 迁移理由

用户明确要求「美观第一」，愿意接受更大 bundle 体积换取视觉效果。

| | Chart.js 4.x | ECharts 5.x |
|---|---|---|
| 动画 | ✅ 简单 | ✅ 丰富（入场、更新、tooltip 均内置） |
| 曲线平滑 | `tension: 0.3` | `smooth: true`（MonotoneX）或 `smooth: 0.8`（Cardinal 高张力） |
| 更新模式 | `chart.data=...; chart.update()` 复用 | `dispose() → init()` 重建 |
| gzip | ~60KB | ~300KB |

## CDN 接入

```html
<script src="https://cdn.jsdelivr.net/npm/echarts@5.6.0/dist/echarts.min.js"></script>
```

## 核心模式（当前最新配置）

```javascript
// 全局存储图表实例 + resize 监听
if (!window._echarts) {
  window._echarts = {};
  window.addEventListener('resize', function(){
    for (var k in window._echarts) window._echarts[k].resize();
  });
}

// 创建/重建（无主题，透明背景）
function ec(id) {
  if (window._echarts[id]) window._echarts[id].dispose();
  window._echarts[id] = echarts.init(document.getElementById(id));
}

// 渐变色（⚠️ 只能用于 rgb() 输入，不要对 rgba() 做 replace(')',...) ——见 echarts-styling-best-practices.md）
function grad(col) {
  return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    {offset: 0, color: col},
    {offset: 1, color: 'transparent'}
  ]);
}

// 正确写法（支持 rgba 输入）：
function gd(col) {
  var parts = col.replace('rgba(','').replace(')','').split(',').map(Number);
  return new echarts.graphic.LinearGradient(0, 0, 0, 1, [
    {offset: 0, color: col},
    {offset: 0.6, color: 'rgba('+parts[0]+','+parts[1]+','+parts[2]+',0.08)'},
    {offset: 1, color: 'rgba(0,0,0,0)'}
  ]);
}

// 基础配置（坐标轴可见 + 平衡边距）
function baseOpt(labels) {
  return {
    backgroundColor: 'transparent',              // ← 透明背景，融入毛玻璃
    grid: {left: 45, right: 20, top: 8, bottom: 18},  // ← 平衡左右边距，图表居中
    xAxis: {
      type: 'category', data: labels, show: true,
      axisLine: {show: false},
      axisTick: {show: false},
      axisLabel: {color: 'rgba(240,253,244,0.35)', fontSize: 9}
    },
    yAxis: {
      type: 'value', show: true, min: 0,
      splitLine: {lineStyle: {color: 'rgba(255,255,255,0.06)', type: 'dashed'}},
      axisLabel: {color: 'rgba(240,253,244,0.35)', fontSize: 9}
    },
    animationDuration: 300
  };
}

// 使用
ec('chart-cpu');
window._echarts['chart-cpu'].setOption(Object.assign(baseOpt(labels), {
  yAxis: {type: 'value', show: true, min: 0, max: cpuMax},
  series: [{
    type: 'line', data: values, smooth: true, symbol: 'none',
    lineStyle: {width: 2, color: '#10b981'},
    areaStyle: {color: grad('rgba(16,185,129,0.12)')}
  }],
  tooltip: {trigger: 'axis'}
}));
```

## 坐标系配置（用户反馈添加）

2026-05-20 用户反馈「没有坐标系」后添加（最初 `show: false` 隐藏了坐标轴）。

**各参数作用：**
- `grid.left: 45` — 给 Y 轴数值标签留空间（后调至45以居中）
- `grid.right: 20` — 加入右侧边距平衡，避免图表内容被「挤在左边」
- `grid.bottom: 18` — 给 X 轴时间标签留空间
- `axisLine.show: false` — 不显示轴线只留文字（更干净）
- `splitLine.type: 'dashed'` — 虚线网格，不干扰数据线
- `axisLabel.color: 'rgba(...0.35)'` — 半透明文字，不抢数据线的视觉权重

**⚠️ 坐标轴边距平衡教训**：2026-05-20 用户反馈「全部挤在左边」。根因是 `grid.left: 40, right: 6` 左侧给 Y 轴标留空间但右侧没有对应边距，视觉上整个图表区域偏左。修正为 `left: 45, right: 20` 后图表居中。

注意 `Object.assign(baseOpt(labels), {yAxis: {...})` 会覆盖 `baseOpt` 中的 yAxis——每个图表可以单独覆写 `max` 值。

## 不同图表不同高度

2026-05-20 用户要求「网络速率的卡片高度适当调高」。

CSS 方案：为特定图表 canvas 添加独立类。

```css
.chart-canvas { width: 100%; height: 130px; }
.chart-canvas canvas { display: block; width: 100%; height: 100%; }  /* 无 !important！*/
.chart-canvas.net-chart { height: 200px; }
```

⚠️ `!important` 会导致 ECharts 无法通过内联 style 覆盖 canvas 的 HTML `width`/`height` 属性。当 ECharts 在隐藏容器中 init（canvas 被设 0 尺寸）后，`!important` 强制 CSS 显示 629px，但内部 buffer 仍是 0×0，图表不可见。

```html
<div class="chart-canvas net-chart">
  <canvas id="chart-net"></canvas>
</div>
```

ECharts `init()` 自动读取 canvas 容器尺寸，无需额外配置。

## 关键区别：Chart.js vs ECharts

| 方面 | Chart.js | ECharts |
|------|---------|---------|
| 创建 | `new Chart(ctx, cfg)` | `echarts.init(dom, theme)` |
| 更新 | `chart.data = ...; chart.update()` | `chart.setOption(opts)` |
| 销毁 | `chart.destroy()` | `chart.dispose()` |
| resize | 自动 | 需手动 `chart.resize()` |
| 主题 | 无内置 | 内置 'dark', 'vintage', 'macarons' 等（但用户拒绝 dark 主题） |
| 渐变色 | Canvas 2D context gradient | `new echarts.graphic.LinearGradient(...)` |
| tooltip | `callbacks.label` | `formatter` 函数或字符串模板 |
| 工具提示格式化 | `callbacks.label: ctx => val` | `formatter: params => html` |

## 当前线上一键验证

```javascript
// ECharts 实例是否存在
Object.keys(window._echarts)  // → ['chart-cpu', 'chart-mem', 'chart-net']

// 每个图表的类型
window._echarts['chart-cpu'].getOption().series[0].type  // → 'line'
window._echarts['chart-cpu'].getOption().series[0].smooth  // → true

// 透明背景（不是 dark 主题）
window._echarts['chart-cpu'].getOption().backgroundColor  // → 'transparent'
```
