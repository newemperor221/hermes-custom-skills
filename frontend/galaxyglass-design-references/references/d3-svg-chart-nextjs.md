# D3.js + SVG 图表在 Next.js 静态导出中的模式

> GalaxyGlass 探针详情页实时折线图（3 图：CPU/内存/网络），60数据点，30s刷新

## 设计原则

1. **Zero-dependency rendering**: 用 D3 的 scale/line/area 生成 SVG path 字符串，不要图库
2. **viewBox 响应式**: 固定 400×160 viewBox，`preserveAspectRatio="xMidYMid meet"`，自动适配容器
3. **CSS 动画代替 JS**: SVG 元素用 CSS keyframes (stroke-dashoffset, opacity)，不用 D3 transition
4. **SVG filters 代替 shadowBlur**: `<feGaussianBlur>` 做线条辉光，比 Canvas shadowBlur 更清晰

## 组件结构

```
nextjs/src/components/LineChart.tsx
  ├── Props: data, data2?, color, color2?, showY?, timeStart?, timeEnd?, unit?, height?
  ├── D3 scaleLinear for x/y axes  
  ├── D3 line() + area() generators with curveMonotoneX
  └── SVG rendering: defs(filters/gradients) → grid lines → areas → lines → dots → labels
```

## 关键模式

### 自动 Y 轴缩放
```typescript
const maxVal = Math.max(...data, data2 ? [...data, ...data2] : [], 1);
const yScale = d3.scaleLinear().domain([0, maxVal]).range([chartH, 0]);
```

### 渐变填充
```tsx
<linearGradient id={gradId} x1="0" y1="0" x2="0" y2="1">
  <stop offset="0%" stopColor={color} stopOpacity="0.18" />
  <stop offset="100%" stopColor={color} stopOpacity="0" />
</linearGradient>
```

### 线条辉光
```tsx
<filter id={filterId}>
  <feGaussianBlur stdDeviation="2" result="blur" />
  <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
</filter>
```

### 端点圆点 + 脉冲动画
```tsx
<circle cx={lastX} cy={lastY} r="3" fill={color} className="chart-dot" />
<circle cx={lastX} cy={lastY} r="6" fill="none" stroke={color} className="chart-ring" />
```
```css
@keyframes ringPulse { 0%,100% { opacity:0.35; r:6; } 50% { opacity:0.1; r:10; } }
```

### 线条绘制动画
```css
.chart-line { stroke-dasharray: 2000; stroke-dashoffset: 2000; animation: drawLine 0.6s forwards; }
@keyframes drawLine { to { stroke-dashoffset: 0; } }
```

### 加载时重置
每次数据更新时，React 组件重新挂载（key 变化）触发重播动画。

## 为什么用 D3 scale 而不是 CSS

D3 负责**数学计算**（scale、line generator、area generator），输出纯 SVG path 作为`<path d="...">`属性。CSS 只负责**视觉动画**。分工清晰：

| 职责 | D3 | CSS |
|------|----|-----|
| 坐标映射 | scaleLinear | — |
| 线条路径计算 | line generator | — |
| 填充区域路径 | area generator | — |
| 线条动画 | — | stroke-dashoffset |
| 端点闪烁 | — | keyframes |
| 颜色渐变 | — | linearGradient |

## 双线图（网络上下行）

渲染两组 `<path>`（上行橙色、下行绿色），共用一个 Y 轴 scale（取两组数据的 max），用两个 linearGradient 分别填充。

## D3 版本

`d3@7` (npm 最新)，Next.js 静态导出兼容——D3 只在客户端运行（`"use client"`）。
