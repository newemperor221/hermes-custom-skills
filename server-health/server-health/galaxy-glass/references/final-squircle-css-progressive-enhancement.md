# Squircle CSS 最终方案：border-radius + overflow + corner-shape 渐进增强

## 核心发现

**SVG clip-path（无论来自哪个库）和 backdrop-filter: blur() 有根本性的渲染冲突。** Chrome 在 composite 阶段处理 clip-path 和 backdrop-filter 的顺序导致边缘 blur 采样被截断，80px 强模糊时伪影明显。CSS `corner-shape`（原生属性）在浏览器合成层内统一处理，不冲突。

## 浏览器支持（截至2026-05-19）

| 浏览器 | corner-shape 支持 | 状态 |
|--------|------------------|------|
| Chrome | 139+ ✅ (2025-08-05) | 稳定版 |
| Edge | 139+ ✅ | Chromium 内核 |
| Safari | 26 beta 🚧 | 未稳定 |
| Firefox | 讨论中 ❌ | [Issue #823](https://github.com/mozilla/standards-positions/issues/823) |
| Opera | ✅ | Chromium 内核 |

全局使用率（2026-04）：约 65-70%（Chrome/Edge 份额）

## 推荐方案

```css
/* 基础：所有浏览器 */
.card {
  border-radius: 14px;
  overflow: hidden;
}

/* 渐进增强：Chrome 139+ 看到真 squircle */
@supports (corner-shape: squircle) {
  .card {
    corner-shape: squircle;
  }
}
```

## 注意事项

1. **`padding >= cornerRadius`** — 黄金规则。corner-shape 的连续曲线比普通 border-radius 更吃空间，padding 必须 >= radius 确保内容不被切
2. **`overflow: hidden` 必须** — 确保 backdrop-filter 的子元素渲染被圆角剪裁
3. **阴影** — CSS `box-shadow` 正常跟随 border-radius ✅（clip-path 方案阴影会被裁切）
4. **border** — CSS `border` 正常跟随 ✅（clip-path 方案不会跟随）
5. **backdrop-filter** — 完美工作 ✅（clip-path 方案有边缘伪影）
6. **不要和 clip-path 混用** — 两套不同的圆角机制会导致不可预见的渲染问题

## Chromium bug 背景

Chrome 中 `clip-path: path('...')` + `backdrop-filter: blur(...)` + `transform` + `transition` 同时作用时，Chrome 在 CSS transition 期间丢弃 backdrop-filter 渲染层（Chromium #1194050）。这是 @squircle-js/react 无法在强模糊场景下工作的根本原因。
