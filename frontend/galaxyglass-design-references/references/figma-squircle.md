# Figma Squircle Apple 连续曲线圆角

> GalaxyGlass 所有卡片使用 figma-squircle 算法生成的 SVG clip-path，替代 CSS `border-radius`

## 算法来源

移植自 `figma-squircle`（[phamfoo/figma-squircle](https://github.com/phamfoo/figma-squircle)），输出 Figma 风格的**连续角（continuous corner）**SVG path。

## 文件结构

```
nextjs/src/lib/figmaSquircle.ts    — 核心算法：getSvgPath(opts)
nextjs/src/components/Squircle.tsx  — React 组件：自动测量+应用clip-path
```

## 使用方式

```tsx
import Squircle from "@/components/Squircle";

// 替换 CSS rounded classes
<Squircle radius={22}>
  <div className="...">   {/* 不要 rounded-[22px] */}
    ...
  </div>
</Squircle>
```

## 圆角值对应

| 组件 | CSS 旧值 | Squircle radius |
|------|---------|----------------|
| NodeCard（主卡片） | `rounded-[16px]` | 22px |
| StatCard（统计栏） | `rounded-[12px]` | 16px |
| FilterChip（筛选标签） | `rounded-[12px]` | 12px |
| Detail MetricCard | `rounded-[22px]` | 16px |
| 图表卡片 / 信息面板 | `rounded-[22px]` | 22px |

## Squircle 组件工作原理

1. 挂载后双 `requestAnimationFrame` 等待布局稳定
2. 读取 `offsetWidth/offsetHeight`
3. 调用 `getSvgPath({ width, height, cornerRadius, cornerSmoothing: 1 })` 生成 path
4. 设置 `<path d="..." />` 到 SVG clipPath 内部
5. 应用 `el.style.clipPath = url(#sq-xxx)`
6. 通过 `ResizeObserver` 监听尺寸变化自动重算

## 关键差异

| 特性 | CSS border-radius | Squircle |
|------|------------------|----------|
| 曲线类型 | 圆形弧 | 连续曲线（Figma） |
| 直线段保留 | 从边缘立刻弯曲 | 先走一段直线再平滑过渡 |
| 渲染方式 | GPU 原生 | SVG clipPath |
| 响应式 | 自动 | ResizeObserver 监听 |
| 浏览器支持 | 全支持 | clipPath 全支持（IE 除外） |

## cornerSmoothing 参数

- `1.0` — Apple 最大平滑（默认）
- `0.0` — 等同于标准圆角
- 通常在 `0.6~1.0` 之间可见明显区别
