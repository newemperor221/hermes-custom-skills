# 监控面板图表渲染技术调研（2026-05-19）

## 背景

GalaxyGlass 详情页有 3 个实时折线图（CPU/内存/网络），每个图 ~60 数据点，30 秒轮询刷新。
当前使用 **Canvas 2D 原生 API** 手绘（~170 行），零依赖。

## 与主流方案对比

### 前提：当前规模下"问题不存在"

> "SVG 和 Canvas 在 **10,000 个元素以下几乎没差别**"（yWorks 研究论文）
> "性能下降从 ~10,000 个图形元素才开始，Canvas 和 SVG 在这个阈值以下表现相近"

GalaxyGlass 每个图表 ~60 个点 × 3 图表 = 180 个数据点，远低于 10K 阈值。

### 技术方案横评

| 方案 | 性能 | 依赖体积 | 复杂度 | 适用场景 |
|------|------|---------|--------|---------|
| **Canvas 2D**（✅ 当前） | 极好（<10K 点无压力） | 0 KB | 低 | ✅ **60点折线图，完美** |
| **SVG** | 好（<10K 点同 Canvas） | 0 KB | 中（需手写 path） | 静态图/交互 hover |
| **ECharts 5** | 极好（渐进渲染至千万点） | ~1 MB (min) | 低（配置式 API） | 需要 tooltip/zoom/交互时 |
| **Chart.js** | 好 | ~200 KB | 低 | 简单图表，无需交互时 |
| **WebGL** | 极好（百万级） | +shader lib | 极高 | 大量点/实时 3D 场景 |
| **WebGPU** | 最好 | +shader lib | 极高 | 下一代，兼容性~70% |
| **OffscreenCanvas** | WebWorker 离屏 | 0 KB | 中（Worker 通信） | 大量点+高频刷新 |

### ECharts 能带来什么（旧版哪吒探针使用的方案）

| 特性 | 当前 Canvas 手绘 | ECharts 5 |
|------|-----------------|-----------|
| 端点圆点 | ❌ 无 | ✅ 自带，可配置 |
| Tooltip hover | ❌ 无 | ✅ |
| Y 轴标签 | ⚠️ 仅网络图有 | ✅ 全自动 |
| 缩放/选择 | ❌ 无 | ✅ |
| 动画 | ✅ `requestAnimationFrame` | ✅ 内置 |
| 自适应 | ✅ ResizeObserver | ✅ 自动 |
| 代码量 | ~170 行 | ~30 行配置 |
| 移植代价 | — | 引入 ~1MB 包 |

### 结论

**保持当前 Canvas 2D 方案。** 理由：
1. 数据量极小（180 点），任何方案都无性能差异
2. 零依赖 = 零风险（ECharts 1MB 对监控面板体积影响不大但无必要）
3. 如果要加视觉细节（端点圆点、Y 轴标签），在现有 Canvas 代码上增加即可

### 端点圆点实现参考（如需添加）

在 drawLine 函数中，画完线和渐变填充后追加：

```typescript
// 端点处画圆
ctx.beginPath();
ctx.arc(linePoints[linePoints.length - 1].x, linePoints[linePoints.length - 1].y, 3, 0, Math.PI * 2);
ctx.fillStyle = color;
ctx.fill();

// 外发光圈
ctx.beginPath();
ctx.arc(linePoints[linePoints.length - 1].x, linePoints[linePoints.length - 1].y, 5, 0, Math.PI * 2);
ctx.strokeStyle = color;
ctx.globalAlpha = 0.3;
ctx.lineWidth = 2;
ctx.stroke();
ctx.globalAlpha = 1;
```

### 未来升级路径

如果以后需要更多交互（tooltip 取值、zoom 缩放）：
```
Canvas 2D 手绘 → 考虑 ECharts（30 行配置，但 ~1MB）
                 → 或考虑轻量 SVG 库（recharts ~350KB, visx 可 tree-shake）
```
