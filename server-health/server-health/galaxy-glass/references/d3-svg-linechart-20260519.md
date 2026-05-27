# D3/SVG LineChart 实现记录（2026-05-19）

## 背景

GalaxyGlass 详情页的三个图表（CPU/内存/网络速率）从 Canvas 2D 手绘迁移到 D3.js + SVG。

## 迁移原因

- **Canvas 2D 缺点**：需手动 DPR 适配、resize 重新绘制、线条模糊、无端点圆点
- **SVG 优势**：矢量无限清晰、CSS 动画原生、viewBox 自动响应式、SVG filter 辉光
- **关键决策**：不用 ECharts（~1MB，对 60 数据点过度设计）、不用 WebGL（杀鸡牛刀）

## 组件结构

```
src/components/LineChart.tsx
```

### 数据流

```
DetailContent.tsx 中 fetchRecentData(uuid)
  → pts.reverse()（时间正序）
  → 计算 cpuPts/memPts/upPts/downPts
  → setState → LineChart re-render
```

### SVG 结构（viewBox=400x160）

```
<svg viewBox="0 0 400 160" preserveAspectRatio="xMidYMid meet">
  <defs>
    <filter>     — feGaussianBlur 辉光
    <linearGradient>  — 线下渐变填充
  </defs>
  <line>         — 3 条网格线（25%/50%/75%）
  <path>         — 线下区域填充
  <path>         — 折线（curveMonotoneX）
  <circle>       — 端点圆点 r=3
  <circle>       — 脉冲环 r=6 透明度呼吸
  <text>         — Y 轴最大值标签
  <text>         — X 轴起止时间
  <line>+<text>  — 图例（仅双线图）
</svg>
```

### D3 Scale + Generator

```tsx
const xScale = d3.scaleLinear()
  .domain([0, data.length - 1])
  .range([0, chartWidth]);  // iw = 400 - 28 - 8

const yScale = d3.scaleLinear()
  .domain([0, maxVal])      // maxVal = Math.max(...all, 1)
  .range([chartHeight, 0]); // ih = 160 - 8 - 22

// 折线生成器
const lineGen = d3.line<number>()
  .x((_, i) => xScale(i))
  .y(d => yScale(d))
  .curve(d3.curveMonotoneX);  // 自然样条

// 区域填充生成器
const areaGen = d3.area<number>()
  .x((_, i) => xScale(i))
  .y0(chartHeight)
  .y1(d => yScale(d))
  .curve(d3.curveMonotoneX);
```

### CSS 动画

```css
@keyframes drawLine {
  to { stroke-dashoffset: 0; }
}
@keyframes fadeIn {
  to { opacity: 1; }
}
@keyframes ringPulse {
  0%, 100% { opacity: 0.35; r: 6; }
  50% { opacity: 0.1; r: 10; }
}

.chart-line {
  stroke-dasharray: 2000;
  stroke-dashoffset: 2000;
  animation: drawLine 0.6s ease forwards;
}
.chart-dot { animation: fadeIn 0.4s 0.5s ease forwards; }
.chart-ring { animation: ringPulse 2s 0.6s ease-in-out infinite; }
```

### 性能

- SVG 单张图表约 60 个数据点 → 60 个路径段 + 2 个 circle + 2-3 个 text
- DOM 节点数 <100/图表，即使 3 图表同时渲染也微不足道
- D3 `useMemo` 确保 scale/generator 不随普通 re-render 重建
- Chart 无 ResizeObserver — viewBox 自动适配
- 对比 Canvas：不需要 DPR 缩放、resize 处理、清理画布

### SSR 注意事项

- D3 在 Next.js 静态导出中完全客户端运行
- `"use client"` 确保组件只在浏览器中 hydrate
- SSR 时 viewBox 已设置但无数据（data=[]），显示"数据不足" SVG 文本
- 客户端 hydrate 后状态更新触发 re-render → 图表出现

### 旧 Canvas 代码清除

从 `DetailContent.tsx` 中移除了：
- `drawLine()` — CPU/内存单线图
- `drawNet()` — 网络双线图
- `canvasId` props → 不再需要 canvas refs
- ChartCard 组件 → 直接用 `<LineChart>`
