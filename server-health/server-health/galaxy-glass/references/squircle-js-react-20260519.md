# @squircle-js/react 集成记录（2026-05-19）

## 背景

GalaxyGlass 所有卡片需要 Apple 风格 Squircle（连续曲线圆角）。

## 方案对比

| 方案 | 状态 | 问题 |
|------|------|------|
| CSS corner-shape: squircle | ❌ Chrome 139+ 才支持 | 兼容性不足 |
| figma-squircle + SVG clipPath | ❌ 手写过复杂 | clip-path + backdrop-filter 冲突 |
| `@squircle-js/react` | ✅ **采用** | 2.1kB gzipped，现成可用 |

## 安装

```bash
npm install @squircle-js/react
```

layout.tsx 中：
```tsx
import { SquircleNoScript } from "@squircle-js/react";
// 在 <body> 内添加：
<SquircleNoScript />
```

## 关键教训

### ❌ 错误：样式在子元素上

```tsx
<Squircle cornerRadius={22}>
  <div className="bg-glass-bg/6 backdrop-blur-[12px] border ...">
    content
  </div>
</Squircle>
```

背景/边框在子 div 上，Squircle wrapper 是透明背景。clip-path 裁切 wrapper 后，子元素的直角背景/边框从透明区域**透出来** → 用户看到"透明的直角边角"。

### ✅ 正确：通过 className 传入样式

```tsx
<Squircle cornerRadius={22} cornerSmoothing={1}
  className="bg-glass-bg/6 backdrop-blur-[12px] border ..."
>
  content
</Squircle>
```

### ❌ 错误：阴影在外层元素上

```tsx
<motion.div className="shadow-[0_8px_32px...]">
  <Squircle>content</Squircle>
</motion.div>
```

Squircle clip-path 只裁切其自身 div 内部。外层的 box-shadow 不受影响 → 阴影显示直角边角。

### ✅ 正确：阴影在 Squircle 内部

```tsx
<Squircle cornerRadius={22} cornerSmoothing={1}>
  <div className="absolute inset-0 pointer-events-none"
    style={{ boxShadow: "0 8px 32px rgba(0,0,0,0.25)" }}
  />
  <div className="relative z-[1]">{content}</div>
</Squircle>
```

## SSR 输出特征

```html
<div data-squircle="16" style="border-radius:16px;clip-path:path('')">
  ...
</div>
```

- SSR 时 `clip-path:path('')` — 空路径，客户端 hydrate 后填充
- `data-squircle="N"` — N = cornerRadius，用于 noscript CSS 降级

## 卡片半径对照表

| 组件 | cornerRadius |
|------|-------------|
| NodeCard（VPS 卡片） | 22 |
| StatCard（统计栏） | 16 |
| FilterChip（筛选标签） | 12 |
| MetricCard（详情指标卡） | 16 |
| 系统信息卡（详情左栏） | 22 |
| 图表卡（详情右栏 CPU/MEM/NET） | 22 |
