# figma-squircle 最终实现方案 (2026-05-16)

## 最终代码

`src/components/SquircleClip.tsx`:

```tsx
"use client";

import { useRef, useEffect, useState, type ReactNode } from "react";
import { getSvgPath } from "figma-squircle";

interface SquircleClipProps {
  children: ReactNode;
  radius?: number;
  className?: string;
  style?: React.CSSProperties;
}

export function SquircleClip({
  children,
  radius = 20,
  className,
  style,
}: SquircleClipProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [id] = useState(() => `sq-${Math.random().toString(36).slice(2, 10)}`);
  const [dims, setDims] = useState({ w: 0, h: 0 });

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    let pending = false;
    const update = () => {
      if (pending) return;
      pending = true;
      requestAnimationFrame(() => {
        pending = false;
        const { width, height } = el!.getBoundingClientRect();
        setDims({ w: Math.ceil(width), h: Math.ceil(height) });
      });
    };
    update();
    const ro = new ResizeObserver(update);
    ro.observe(el);
    return () => ro.disconnect();
  }, []);

  const { w, h } = dims;
  const path =
    w > 0 && h > 0
      ? getSvgPath({
          width: w,
          height: h,
          cornerRadius: radius,
          cornerSmoothing: 0.6,
        })
      : "";

  return (
    <div
      ref={ref}
      className={className}
      style={{
        ...style,
        clipPath: w > 0 && path ? `url(#${id})` : undefined,
      }}
    >
      <svg
        width={w || 1}
        height={h || 1}
        style={{
          position: "absolute",
          top: 0,
          left: 0,
          pointerEvents: "none",
          zIndex: -1,
        }}
        aria-hidden="true"
      >
        <defs>
          <clipPath id={id} clipPathUnits="userSpaceOnUse">
            <path d={path || "M 0,0"} />
          </clipPath>
        </defs>
      </svg>
      {children}
    </div>
  );
}
```

## 弃用 @squircle-js/react 的原因

`@squircle-js/react` 的 `<Squircle>` 组件在 style 中强制设置 `borderRadius: cornerRadius`（内联样式，不可由外部覆盖）。这导致：

1. `border-radius` + `clip-path: path(...)` + `backdrop-filter: blur(60px)` 组合
2. 在 CSS transition 过程中（如 `group-hover` 背景色变化）
3. Chromium 渲染 `backdrop-filter` 时采样到 clip-path 边界外的像素
4. 视觉效果：hover 时卡片看起来变透明

**解决：** `figma-squircle.getSvgPath()` + SVG `<clipPath>` + `url(#)`。
SVG clipPath url() 不会引入 border-radius 内联样式，backdrop-filter 过渡正常。

## figma-squircle 路径格式

生成的路径在 292×87 卡片上（R=14）的实际格式：

```
M 269.6 0
  C 277.441 0 281.361 0 284.356 1.5259          // 贝塞尔上坡
  A 14 14 0 0 1 290.474 7.6441                   // 圆弧（恒定曲率）
  C 292 10.6389 292 14.5592 292 22.4              // 贝塞尔下坡
  L 292 64.6                                      // 右边缘
  C 292 72.4407 292 76.3611 290.474 79.3559       // 下右角贝塞尔
  A 14 14 0 0 1 284.356 85.4741                   // 下右角圆弧
  C 281.361 87 277.441 87 269.6 87                // 下右角贝塞尔
  L 22.4 87                                       // 下边缘
  ... (对称)
```

## 迭代历程

| 版本 | 方法 | 问题 |
|------|------|------|
| v2 | 单段贝塞尔 C + k=0.461 | 端点曲率≠0，G2不连续 |
| v3 | 25点超椭圆 L 采样 | 边缘90°折角 |
| v4 | @squircle-js/react | hover透明度 |
| **v5** | **figma-squircle + SVG clipPath** | **✅ 正确** |
