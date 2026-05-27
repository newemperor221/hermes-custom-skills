# Chromium backdrop-filter + transform + transition bug

## 症状

hover 卡片时 `backdrop-filter: blur()` 短暂消失，卡片看起来"变透明"。

## 根因

Chromium issue #1194050 / #40175472：当同一元素同时有：

1. `backdrop-filter: blur(...)` 
2. `transition: all`（或任何 transition on `transform`）
3. `transform` 在 hover 时变化（如 `translateY`）

Chrome 在 CSS transition 期间丢弃 backdrop-filter 的渲染层。Firefox、Safari 无此问题。

## 触发条件

```css
/* ❌ 触发 bug */
transition-all duration-300
group-hover:-translate-y-[3px]
backdrop-filter: blur(60px)
```

## 修复

```css
/* ✅ 不触发 bug */
transition-[filter,background-color,border-color,opacity] duration-300
group-hover:-translate-y-[3px]
backdrop-filter: blur(60px)
```

`transform`（translateY）仍然生效，但**不参与 transition 动画**，hover 时瞬间跳变。blur 全程稳定。

## @squircle-js/react 加重此问题

`@squircle-js/react` 的 `<Squircle>` 组件强制写入 `borderRadius` 内联样式且不可覆盖。`border-radius` + `clip-path: path()` + `backdrop-filter` + transition 的组合在 Chromium 中更容易触发渲染层丢弃。

修复方案：用 `figma-squircle` + SVG `<clipPath url(#)>` 方式，Figma 算法不变，但不用 CSS `path()` 函数。

## 参考

- https://issues.chromium.org/p/chromium/issues/detail?id=1194050
- https://issues.chromium.org/40175472
- https://stackoverflow.com/questions/66879420
