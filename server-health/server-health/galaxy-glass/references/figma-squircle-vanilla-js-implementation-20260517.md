# GalaxyGlass Vanilla JS Squircle 实现记录

> 2026-05-17 实施。将 `figma-squircle@1.1.0` 集成到纯 HTML/CSS/JS 的 GalaxyGlass 探针面板（<监控面板域名>）。

## 背景

GalaxyGlass 源文件（`src/` 目录）为纯 HTML/CSS/JS 架构，无框架依赖。卡片（node-card / stat-card）由 `render.js` 动态渲染为 HTML 字符串，通过 `grid.innerHTML = ...` 注入。

**目标：** 所有卡片边角从 `border-radius` 替换为 Figma 风格的 Squircle（连续 G2 曲率，类 iOS app icon）。

**之前尝试过的方案：**
1. 手工贝塞尔 clip-path（`M 0.1,0 ...`）- 不是真正 Squircle
2. CSS `corner-shape: squircle` - 仅 Chrome 139+ 支持
3. `@squircle-js/react` - 框架组件，不适用于 vanilla JS

## 方案：figma-squircle 内联脚本 + 运行时 clip-path 生成

### 文件

**`scripts/squircle.js`**（10KB，自包含 IIFE）

将 figma-squircle 的 CJS `dist/index.js` 转为浏览器可直接加载的脚本：
- 删除 `export { getSvgPath }`，改为 `global.getSvgPath = getSvgPath`
- 删除 TypeScript 类型注解
- 用 `var` 替换 `const`/`let`
- 用 `function` 替代箭头函数
- **关键修复：** tagged template literal `rounded()` 改为直接字符串拼接（见下方踩坑）

### 调用的入口

**`scripts/render.js`**：在 `render()` 函数的 `positionBackToTop()` 后加一行：
```js
setTimeout(applySquircles, 50);
```

**`index.html`**：在 `<script src="scripts/config.js">` 前加入：
```html
<script src="scripts/squircle.js?v=1"></script>
```

### applySquircles() 工作流

```js
function applySquircles() {
  // 1. 找到所有卡片
  var cards = document.querySelectorAll('.node-card, .stat-card, .metric-card, .skeleton-card');
  if (!cards.length) return;

  // 2. 创建/获取 SVG defs 容器
  var defs = document.querySelector('svg#sq-defs defs');
  // 如不存在，创建 <svg id="sq-defs"> + <defs> 注入 <body>

  // 3. 清除旧动态 clip-paths（id^="sq-dyn-"）
  // 4. 遍历卡片，生成新 clip-paths
  cards.forEach(function(card, idx) {
    var w = card.offsetWidth;      // 像素
    var h = card.offsetHeight;
    if (!w || !h) return;

    var rad = card.classList.contains('node-card') ? 16 : 12;
    // node-card 和 skeleton-card 用 16px，其余 12px

    var path = getSvgPath({ width: w, height: h, cornerRadius: rad, cornerSmoothing: 1 });
    var id = 'sq-dyn-' + idx;
    // 创建 <clipPath id="sq-dyn-N" clipPathUnits="userSpaceOnUse"><path d="..." /></clipPath>
    // 设置 card.style.clipPath = 'url(#sq-dyn-N)'
  });
}
```

### 样本输出

一张 295×240px 卡片（cornerRadius=16, cornerSmoothing=1）的 clip-path 路径：
```
M 263 0 c 15.0849 0 22.6274 0 27.3137 4.6863 a 16.0000 16.0000 0 0 1 0.0000 0.0000 c 4.6863 4.6863 4.6863 12.2288 4.6863 27.3137 L 295 208 ...
```

- `M 263 0`：起点在距左边 263px 处（`p = 295-263 = 32`，即 `(1+1)*16`）
- `a 16 16 0 0 1 0 0`：当 cornerSmoothing=1 时 arcSectionLength=0，弧段退化为零长度点（平滑过渡不需要圆弧）
- `L 295 208`：右侧直边到 `208 = 240-32`

## 🔴 核心踩坑

### 1. tagged template literal 参数错位

**问题：** `figma-squircle` 使用 ES6 tagged template `rounded\`...\`` 生成 SVG 路径，其中 `strings.length = values.length + 1`。我尝试用数组模拟时传参数量不匹配，导致路径后半段（`b+c`, `a+b+c` 等参数）被丢弃。

**症状：** 卡片 clip-path 路径不完整 → 视觉上卡片被裁切消失，只显示部分或完全空白。

**排查方法：**
```js
// 检查生成的路径是否包含预期的末端坐标
var el = document.getElementById('sq-dyn-0');
var d = el.querySelector('path').getAttribute('d');
// 正确路径应包含 "L <cardWidth> <cardHeight - cornerP>" 和最后的 "Z"
```

**修复：** 完全放弃 `rounded()` tagged template，改用直接字符串拼接 + `toFixed(4)` 数值格式。

### 2. Cloudflare 缓存旧版 HTML

**问题：** 部署后浏览器加载的仍是旧版 `index.html`（无 `squircle.js` 引用），即使服务器文件已更新。

**原因：** Cloudflare 边缘节点缓存了 HTML。`<监控面板域名>` 通过 cloudflared 隧道访问，但 Cloudflare CDN 仍可能缓存。

**修复：** 在 URL 后加查询参数强制回源：`?_cb=N` 或 `?_t=1`。浏览器硬刷新（`Ctrl+F5`/`Cmd+Shift+R`）也有效。

### 3. `clipPathUnits="userSpaceOnUse"` 坐标系统

**确认：** `userSpaceOnUse` 的坐标原点在引用元素的左上角（不是 SVG 容器的左上角）。所以路径 `M 263 0` 表示距卡片左边缘 263px，距卡顶上边缘 0px，正确。

## 验证结果

部署并修复所有问题后（2026-05-17 16:10 UTC）：

| 检查项 | 结果 |
|--------|------|
| 13 张 node-card 有 clip-path | ✅ `url("#sq-dyn-4")` 等 |
| 4 张 stat-card 有 clip-path | ✅ `url("#sq-dyn-0")` 等 |
| SVG defs 内容 | ✅ ~12KB |
| 所有卡片在视口中 | ✅ x:25-957, y:223-992, 295×240px |
| 无 JS 错误 | ✅ |
| 视觉正确（Squircle 圆角） | ✅ 用户确认正常显示 |

## 相关文件

- `src/scripts/squircle.js` — figma-squircle 浏览器端口 + applySquircles
- `src/scripts/render.js` — 第 47 行 `setTimeout(applySquircles, 50)`
- `src/index.html` — 第 178 行 `<script src="scripts/squircle.js?v=1">`

## 后续改进方向

1. 用 `ResizeObserver` 替代 `window.resize` 更精确（当前 debounce 150ms）
2. 预生成常见尺寸的 clip-path 减少运行时计算量
3. 如果所有卡片同宽高，可以只生成单个 clip-path 复用
