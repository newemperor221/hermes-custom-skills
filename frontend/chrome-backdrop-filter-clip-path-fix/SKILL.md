---
name: chrome-backdrop-filter-clip-path-fix
description: Chrome backdrop-filter + clip-path compositing bug — fix by separating glass layer into child element
tags: [chrome, css, backdrop-filter, clip-path, glassmorphism, squircle]
related_skills: [css-glassmorphism-backdrop-filter]
references:
  - references/golden-proportions.md — 各卡片黄金比例速查表（8px网格 + 嵌套圆角公式）
---

# Chrome backdrop-filter + clip-path 毛玻璃失效修复

## 根因

Chrome 渲染管线中，`backdrop-filter` 和 `clip-path` 放到**同一个元素**上时，Chrome 会丢弃 `backdrop-filter` 效果。表现为：毛玻璃直接消失，背景纯色。

这个问题在以下情况都会触发：
- SVG `clipPath: url(#id)`（figma-squircle 生成）
- CSS `clip-path: polygon(...)` / `clip-path: inset(...)`
- `mask-image` 可能也会受影响（但程度较轻）

## 正确方案：玻璃层独立子元素

**不要把 `backdrop-filter` 和 `clip-path` 放在同一个元素上。** 把毛玻璃放到 clip-path 容器内部的绝对定位子元素里：

```tsx
{/* 外层：clip-path ONLY — backdrop-filter 和 bg 都不在这里 */}
<SquircleClip
  radius={20}
  smoothing={0.6}
  className="relative border border-[rgba(255,255,255,0.08)]"
>
  {/* 玻璃层：backdrop-filter + bg — 绝对定位填充，无 clip-path */}
  <div className="absolute inset-0 pointer-events-none
    bg-[rgba(255,255,255,0.04)]
    backdrop-blur-[80px] saturate-[1.2]
  " />

  {/* 内容层：z-index 在玻璃层之上 */}
  <div className="relative z-[1] flex flex-col gap-3 px-5 py-5">
    {children}
  </div>
</SquircleClip>
```

### 为什么有效

| 元素 | 负责 | 存在冲突？ |
|------|------|-----------|
| `SquircleClip` (外层) | `clipPath: url(#sq-nnn)` | 只有 clip-path |
| `absolute inset-0` (玻璃层) | `backdrop-filter`, `background-color` | 只有 backdrop-filter |
| 内容层 | 普通内容 | 什么都没有 |

Chrome 渲染管线在每个元素上独立执行 backdrop-filter → clip-path。由于两个属性不在同一元素，**不会冲突**。

## SquircleClip 组件

```tsx
"use client";
import { useRef, useState, useEffect } from "react";
import { getSvgPath } from "figma-squircle";

interface SquircleClipProps {
  children: ReactNode;
  radius?: number;
  smoothing?: number;
  className?: string;
  style?: React.CSSProperties;
}

export function SquircleClip({
  children, radius = 20, smoothing = 0.6,
  className, style,
}: SquircleClipProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 0, h: 0 });
  const id = useRef(`sq-${Math.random().toString(36).slice(2, 9)}`).current;

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver((entries) => {
      for (const entry of entries) {
        const { width, height } = entry.contentRect;
        if (width > 0 && height > 0) {
          setDims({ w: Math.ceil(width), h: Math.ceil(height) });
        }
      }
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const path = dims.w > 0 && dims.h > 0
    ? getSvgPath({ width: dims.w, height: dims.h, cornerRadius: radius, cornerSmoothing: smoothing })
    : null;

  return (
    <div
      ref={ref}
      className={className}
      style={{
        ...style,
        clipPath: path ? `url(#${id})` : undefined,
        willChange: "transform",    // 必须从一开始就设置，强制 GPU 合成层
        position: "relative",
      }}
    >
      {path && (
        <svg width={0} height={0} style={{ position: "absolute", pointerEvents: "none" }}>
          <defs>
            <clipPath id={id} clipPathUnits="userSpaceOnUse">
              <path d={path} />
            </clipPath>
          </defs>
        </svg>
      )}
      {children}
    </div>
  );
}
```

⚠️ **`willChange: "transform"` 必须从一开始就设置**（不能条件性延迟）。条件性设置（仅 ResizeObserver 回调后才加上）会导致 Chrome 在首次绘制时没有合成层，毛玻璃在第一帧就丢了。

## 组件应用模式

### StatsBar（统计卡片）

```tsx
// 每个统计卡片用 SquircleClip 包裹，玻璃层独立
function GlassCard({ children }: { children: React.ReactNode }) {
  return (
    <SquircleClip radius={20} className="relative border border-[rgba(255,255,255,0.08)] group">
      <div className="absolute inset-0 pointer-events-none
        bg-[rgba(255,255,255,0.10)] backdrop-blur-[60px] saturate-[1.2]
        transition-opacity duration-300 ease-out
        group-hover:opacity-80" />
      <div className="relative z-[1] flex items-center gap-3 px-4 py-3.5">
        {children}
      </div>
    </SquircleClip>
  );
}
```

⚠️ **Hover 效果迁移**：玻璃层移到子元素后，父元素的 `group-hover/card:bg-[rgba(...)]` 无法直接控制子元素的背景。用 `transition-opacity` + `group-hover:opacity-NN` 替代：

```diff
- ❌ group-hover/card:bg-[rgba(255,255,255,0.12)]
+ ✅ 玻璃层上加: transition-opacity, group-hover:opacity-80
```

### NodeCard（服务器卡片）

| 背景类型 | 推荐白底不透明度 | 视觉效果 |
|----------|-----------------|----------|
| 浅色/中等壁纸 | `rgba(255,255,255,0.03-0.05)` | 极淡毛玻璃，壁纸清晰可见 |
| 深色壁纸（luma ~50-80） | `rgba(255,255,255,0.06-0.08)` | 毛玻璃可见，不喧宾夺主 |
| 极暗壁纸（luma ~20-30） | `rgba(255,255,255,0.08-0.12)` | 毛玻璃明显，才显得不是纯黑实心 |

**关键：** 暗色背景会吸收白底透明度。4% 白底在极暗壁纸上看起来像纯黑实心卡片，**视觉上像没有毛玻璃**。至少需要 8-10% 才能在暗色背景上显出玻璃效果。

可以用 js 测量壁纸平均亮度：
```js
// 在 canvas 上采样壁纸的 luma
const avg = arr => arr.reduce((a,b) => a+b) / arr.length;
// RGB → luma: 0.299*R + 0.587*G + 0.114*B
// luma < 30 → 用 0.08-0.12
// luma 30-80 → 用 0.06-0.08
// luma > 80 → 用 0.03-0.05
```

### NodeCard（服务器卡片）

外层结构：
```
motion.div → transform（frame motion 动画）
  shadow wrapper → filter: drop-shadow（hover 变化）
    SquircleClip → clip-path ONLY
      absolute inset-0 div → backdrop-filter + bg
      relative z-[1] div → 卡片内容
```

## 2026-05-20 更新：放弃 @squircle-js/react，全面转向 CSS 方案

**结论：在 14-16px 这个尺寸区间，Squircle clip-path 和 CSS border-radius 的视觉差异肉眼不可辨别。** 为了消除 blur 兼容性隐患 + 减少 JS 依赖 + 代码更简单，全面采用 CSS 方案。

### 最终方案：CSS border-radius + overflow:hidden + 渐进增强

```tsx
<motion.div
  className="relative cursor-pointer overflow-hidden sq-card"
  style={{ borderRadius: 14 }}
>
  {/* 阴影 */}
  <div className="absolute inset-0 pointer-events-none"
    style={{ boxShadow: "0 0 0 1px rgba(...), 0 8px 32px rgba(0,0,0,0.25)" }}
  />
  
  {/* 玻璃层 — backdrop-filter + border-radius 天然兼容，无冲突 */}
  <div className="absolute inset-0 bg-glass-bg/6 backdrop-blur-[80px] saturate-150" />

  {/* 内容 */}
  <a className="relative block p-[24px] flex flex-col gap-[8px] z-[1]">
    ...
  </a>
</motion.div>
```

### 渐进增强：Chrome 139+ 原生 squircle

```css
@supports (corner-shape: squircle) {
  .sq-card { corner-shape: squircle; }
  .sq-chip { corner-shape: squircle; }
}
```

`corner-shape: squircle` 是 CSS 原生属性（Chrome 139+, 2025-08），不需要 JS 计算。Safari 26 beta 开始支持，Firefox 讨论中。

**浏览器兼容：** Chrome 用户看到真 squircle 曲线，其他浏览器退回到 `border-radius: 14px`。因为用的是 CSS 圆角（不是 SVG clip-path），backdrop-filter 在所有浏览器都正常工作。

### 为什么不再需要 @squircle-js/react

| 对比项 | @squircle-js/react | CSS border-radius + corner-shape |
|--------|-------------------|----------------------------------|
| 圆角曲线 | 完美 squircle (SVG clip-path) | Chrome 真squircle, 其他≈ border-radius |
| 14px 下差异 | 完美 | **肉眼不可辨** |
| backdrop-filter 兼容 | clip-path 冲突需分层 | 天然兼容 |
| JS 大小 | 2.1kB gzipped + ResizeObserver | 0 (CSS only) |
| 运行时 | ResizeObserver + SVG path 计算 | 无需计算 |
| 渐进增强 | 无 | @supports 自动降级 |

### 保留 @squircle-js/react 的适用场景

如果 cornerRadius ≥ 24px **且** 没有 backdrop-filter（或 blur < 20px），squircle 的视觉优势才值得额外依赖。

## 强模糊场景（blur≥40px）：推荐用 CSS border-radius 替代 Squircle clip-path

**关键发现（2026-05-20）：** 即使遵循「玻璃层独立子元素」原则，Squircle（SVG clip-path）和 `backdrop-filter: blur(40px+)` 仍然冲突。原因是 SVG clip-path 在元素边缘截断 backdrop-filter 的采样区域，产生肉眼可见的边角伪影。模糊越强（80px），伪影越明显。

**Chrome 的渲染行为：** backdrop-filter 在大半径模糊时会采样元素边界外的像素。clip-path 虽然裁剪了元素的视觉输出，但不改变采样范围——模糊计算仍然跨越了 clip-path 边界，然后在裁剪边界上产生不自然的截断。

**推荐方案：** 对于任何 `backdrop-filter: blur(40px+)` 的元素，**放弃 Squircle clip-path**，改用 CSS `border-radius` + `overflow: hidden`：

```tsx
{/* ✅ 强模糊 + 圆角 — 无冲突 */}
<motion.div
  className="overflow-hidden"
  style={{ borderRadius: 14 }}
>
  {/* 阴影 */}
  <div className="absolute inset-0 pointer-events-none"
    style={{ boxShadow: "0 0 0 1px rgba(...), 0 8px 32px rgba(0,0,0,0.25)" }}
  />
  
  {/* 玻璃层 — backdrop-filter 和 border-radius 无冲突 */}
  <div className="absolute inset-0 bg-glass-bg/6 backdrop-blur-[80px] saturate-150" />

  {/* 内容 */}
  <div className="relative z-[1] p-[24px]">
    {children}
  </div>
</motion.div>
```

### 适用场景判断

| 条件 | 用 Squircle clip-path | 用 CSS border-radius + overflow |
|------|----------------------|--------------------------------|
| blur < 20px (弱模糊) | ✅ 兼容，需要分两层 | ❌ 浪费，squircle 更精确 |
| blur 20-40px (中模糊) | ✅ 兼容，两层结构 | ✅ 视觉差异微小 |
| blur ≥ 40px (强模糊) | ❌ 边角伪影可见 | ✅ **推荐** — 无伪影，blur正常 |
| blur ≥ 80px (极强模糊) | ❌ 边角伪影明显 | ✅ **必须用** — 伪影无法忽视 |
| 无 backdrop-filter | ✅ Squircle 完美 | ❌ 可用但失去真 squircle |

### 视觉差异评估

在 290px 宽的卡片上，`border-radius: 14px` 和 `Squircle cornerRadius=14 cornerSmoothing=0.6` 的视觉差异**肉眼几乎不可辨别**。只有在超大半径（>24px）时，squircle 的连续曲线优势才明显。

### 黄金公式（不管用哪种方案）

```
padding >= cornerRadius
```

内容（图标、标签、状态点）必须离边缘至少 `cornerRadius` 像素远，否则被圆角裁切。绝对定位的装饰元素（离线角标、ping动画）也要内缩 `padding` 同等距离。

**嵌套圆角公式（Apple HIG）：** `内圆角半径 = 外圆角半径 - padding`。当 padding ≥ 外圆角半径时，内元素不需要额外圆角。

| cornerRadius | 最小 padding | 安全 padding | 8px网格值 |
|-------------|-------------|-------------|----------|
| 8 | 8px | 12px | 16px |
| 12 | 12px | 16px | 16px |
| 14 | 14px | 20px ✅ 实测 | — (不在8px网格) |
| 16 | 16px | **24px** ✅ **推荐** | 24px ✅ |
| 20 | 20px | 24px | 24px |
| 24 | 24px | 32px | 32px |

**推荐：cornerRadius 和 padding 都取 8px 网格值**（16, 24, 32...），方便设计系统统一。

**绝对定位元素**（离线角标 `top-[] right-[]`、ping 动画）也要用 padding 同等数值，不能比 padding 小。

### 各卡片黄金比例速查表

见 `references/golden-proportions.md`。

### cornerSmoothing 选择

```tsx
{/* ✅ Apple iOS 标准 */}
<Squircle cornerRadius={14} cornerSmoothing={0.6}>

{/* ❌ 最大平滑 — 曲线更激进，吃更多空间 */}
<Squircle cornerRadius={14} cornerSmoothing={1.0}>
```

`@squircle-js/react` 的默认值是 `0.6`（iOS 标准）。`1.0` 是 Figma 最大平滑值，实际消耗的有效半径 ≈ `cornerRadius + 30-40%`。**不要用 1.0 做内容卡片。**

### 嵌套元素圆角公式

```
innerBorderRadius = outerCornerRadius - padding
```

如果 `padding >= outerCornerRadius`，内层元素不需要额外圆角（圆角曲线完全在 padding 区域内）。

## 验证方法

```js
// 检查 clip-path 元素本身没有 backdrop-filter
const clip = document.querySelector('[style*="clip-path"]');
getComputedStyle(clip).backdropFilter  // → "none" ✅
getComputedStyle(clip).willChange      // → "transform" ✅

// 检查内部玻璃层有 backdrop-filter
const glass = clip.querySelector('[class*="absolute"]');
getComputedStyle(glass).backdropFilter // → "blur(80px)" ✅
```

## 参考资料

- Chromium Issue 41465359 — backdrop-filter doesn't respect clip-path
- Chromium Issue 41237172 — backdrop-filter conflicts with hover transforms
- figma-squircle npm package — https://github.com/tranbathanhtung/figma-squircle
