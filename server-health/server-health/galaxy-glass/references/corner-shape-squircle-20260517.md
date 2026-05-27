# CSS corner-shape: squircle — 原生 Squircle 实现

> 发现日期：2026-05-17
> Chrome 139+ 支持

## TL;DR

```css
.card {
  border-radius: 16px;
  corner-shape: squircle;
  overflow: hidden;
}
```

**不需要任何 JS 库。不会和 backdrop-filter 冲突。** Chrome 139+（2025年底）原生支持。

## 浏览器支持

| 浏览器 | 支持版本 |
|--------|---------|
| Chrome | 139+ ✅ |
| Edge | 139+ ✅ (Chromium) |
| Firefox | ❌ 未实现 |
| Safari | ❌ 未实现 |

**渐进增强策略：**
```css
@supports (corner-shape: squircle) {
  .card { corner-shape: squircle; }
}
```
不支持的浏览器降级到 `border-radius` 圆角。

## 语法

```css
corner-shape: squircle;          /* 超椭圆（Apple iOS 图标同款） */
corner-shape: round;             /* 默认 border-radius 圆角 */
corner-shape: bevel;             /* 切角 */
corner-shape: scoop;             /* 内凹 */
corner-shape: notch;             /* 缺口 */
corner-shape: square;            /* 直角（覆盖 border-radius） */

/* 每个角分别指定（同 border-radius 语法） */
corner-shape: bevel round scoop squircle;

/* 超级椭圆精细控制 */
corner-shape: superellipse(2);   /* = squircle */
corner-shape: superellipse(0.5); /* 介于 round 和 squircle 之间 */
corner-shape: superellipse(0);   /* = bevel */
corner-shape: superellipse(-1);  /* = scoop */
corner-shape: superellipse(-infinity); /* = notch */
corner-shape: superellipse(infinity);  /* = square */
```

`corner-shape` 本身定义**形状的曲线类型**，`border-radius` 定义**曲线的大小**。两者配合使用。

## 历史（为什么之前走了弯路）

2026-05-17 session 中，用户要求给 <监控面板域名> 的卡片加 Squircle 圆角。

**尝试过的方案（时间顺序）：**

| 方案 | 问题 | 结论 |
|------|------|------|
| SVG `clip-path: url(#sq-lg)` | Chrome backdrop-filter 冲突 → 毛玻璃失效 | ❌ |
| `@squircle-js/react` 两层分离 | 复杂，clip-path 遮挡内容 | ❌ |
| `figma-squircle` + SVG clipPath | 同上，且需 ResizeObserver | ❌ |
| **`corner-shape: squircle`** | **零冲突，零 JS，零问题** | ✅ **最终采用** |

**教训：** 做复杂方案之前先查浏览器支持。`corner-shape` 2025年底就 ship 了 Chrome，2026年5月已经可以用。

## 参考

- [MDN: corner-shape](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/corner-shape)
- [Smashing Magazine: Beyond border-radius](https://www.smashingmagazine.com/2026/03/beyond-border-radius-css-corner-shape-property-ui/)
- [CSS-Tricks: superellipse()](https://css-tricks.com/almanac/functions/s/superellipse/)
- [Chrome Platform Status](https://chromestatus.com/feature/5357329815699456)
