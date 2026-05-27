# figma-squircle 在 Vanilla JS 中的应用

> 2026-05-17 撰写。squircle.js.org 的框架组件库（React/Vue/Svelte/Solid）底层是 `figma-squircle`（vanilla JS, MIT, 8.9KB）。对于非框架页面，直接使用 `figma-squircle`。

## 架构选择

| 方案 | 适用 | 备注 |
|------|------|------|
| `@squircle-js/react` | React/Next.js | 自动 ResizeObserver，方便 |
| `figma-squircle` 直接调用 | 任何页面（vanilla, jQuery, 等） | 需要自行处理尺寸变化 |
| CSS `corner-shape: squircle` | Chrome 139+ 渐进增强 | 无需 JS，但浏览器支持有限 |

## 基础用法

```js
const { getSvgPath } = require('figma-squircle');

// 生成精确 Squircle 路径
const path = getSvgPath({
  width: 300,
  height: 200,
  cornerRadius: 16,
  cornerSmoothing: 1, // 0~1, 1=最平滑（iOS app icon 同款）
  preserveSmoothing: false
});
// → "M 284 0 ... Z"
```

## 集成到 Vanilla HTML 页面

### 方法 A：CDN 加载（推荐起步用）

```html
<script src="https://cdn.jsdelivr.net/npm/figma-squircle@1.1.0/dist/index.min.js"></script>
<script>
  // figma-squircle 是 CJS 格式，需要 UMD 包装
  // 或直接内联核心算法（见下文）
</script>
```

⚠️ `figma-squircle@1.1.0` 发布为 CJS 格式（`dist/index.js`，无 UMD/ESM CDN 构建）。浏览器直接引用需要：
1. 用 esbuild/rollup 打包为浏览器脚本
2. 或者手动提取核心算法内联
3. 或者用 unpkg 的 `?module` 参数（仅实验性）

### 方法 B：内联算法（推荐生产用）

核心算法 ~3KB gzipped，可以直接提取 `getSvgPath` 函数内联到页面 `<script>` 中：

```js
// 从 figma-squircle 提取的核心函数
function getSvgPath({ cornerRadius = 0, cornerSmoothing = 1, width, height, preserveSmoothing }) {
  // ... 约 200 行算法，见 https://github.com/phamfoo/figma-squircle
}
```

### 方法 C：npm install + 构建脚本

```bash
npm install figma-squircle
```

然后写一个构建脚本打包：

```js
// build-squircles.js
const { getSvgPath } = require('figma-squircle');
const fs = require('fs');

// 预生成所有卡片类型的路径
const configs = {
  'sq-lg': { width: 350, height: 180, cornerRadius: 16, cornerSmoothing: 1 },
  'sq-md': { width: 280, height: 90, cornerRadius: 12, cornerSmoothing: 1 },
  'sq-sm': { width: 200, height: 60, cornerRadius: 8, cornerSmoothing: 1 },
};

let svgDefs = '';
for (const [id, cfg] of Object.entries(configs)) {
  const path = getSvgPath(cfg);
  svgDefs += `<clipPath id="${id}"><path d="${path}"/></clipPath>\n`;
}
// 然后写入 HTML 或 CSS
```

## 在运行时生成（响应式）

对于响应式卡片（grid 布局中卡片尺寸不固定），需要在运行时根据实际像素尺寸生成：

```js
function applySquircles() {
  const cards = document.querySelectorAll('.node-card, .stat-card, .metric-card');
  const svgDefs = document.querySelector('svg defs') || createDefs();
  
  cards.forEach((card, i) => {
    const w = card.offsetWidth;
    const h = card.offsetHeight;
    // 根据卡片类型选择半径
    const radius = card.classList.contains('node-card') ? 16 : 12;
    
    const path = getSvgPath({
      width: w, height: h,
      cornerRadius: radius,
      cornerSmoothing: 1,
    });
    
    const id = `sq-dynamic-${i}`;
    // 创建或更新 clipPath
    let clip = document.getElementById(id);
    if (!clip) {
      clip = document.createElementNS('http://www.w3.org/2000/svg', 'clipPath');
      clip.id = id;
      clip.setAttribute('clipPathUnits', 'userSpaceOnUse');
      svgDefs.appendChild(clip);
    }
    clip.innerHTML = `<path d="${path}"/>`;
    card.style.clipPath = `url(#${id})`;
  });
}

// 页面加载 + resize 时 debounce
document.addEventListener('DOMContentLoaded', applySquirrels);
window.addEventListener('resize', debounce(applySquirrels, 200));
```

### ⚠️ 重要：必须用 `userSpaceOnUse``

`figma-squircle` 返回像素坐标路径，所以 clipPath 必须用 `clipPathUnits="userSpaceOnUse"`（不是 `objectBoundingBox`）。这意味着：
- 路径坐标 = 卡片的实际像素坐标
- 每次卡片 resize 后必须重新生成路径
- 配合 `ResizeObserver` 比 `window.resize` 更精确

```js
const ro = new ResizeObserver(entries => {
  entries.forEach(entry => {
    const card = entry.target;
    const w = card.offsetWidth;
    const h = card.offsetHeight;
    // ... 重新生成 clipPath
  });
});
cards.forEach(card => ro.observe(card));
```

## 与 `@squircle-js/react` 的关系

```
@squircle-js/react ─── wraps ──→ figma-squircle ─── based on ──→ figma-squircle 论文算法
                                     ↑
                              (Figma "Desperately Seeking Squircles")

@squircle-js/react 做的事（如果自己实现 vanilla 版需要替代）：
1. 包装 figma-squircle 的 getSvgPath()
2. ResizeObserver 自动检测尺寸变化
3. SVG clipPath 的自动注入/清理
4. JS-off 降级方案（<SquircleNoScript />）

vanilla 版需要自己实现 2 和 3，但很简单（~20 行）。
```

## 算法原理（简要）

每个 90° 角拆为 3 段：
1. **Cubic bezier** — 曲率从 0 平滑升到 1/R
2. **SVG arc** — 恒定曲率 1/R 的圆弧
3. **Cubic bezier** — 曲率从 1/R 平滑降到 0

→ 曲率全程连续（G2），这正是 Figma/Apple 的 "continuous corner" 效果。

**参数影响：**
- `cornerRadius`: 像素值，等同 border-radius
- `cornerSmoothing: 0` → 纯圆角（正圆弧，和 border-radius 一样）
- `cornerSmoothing: 1` → 苹果 iOS app icon 同款（最平滑）

## 对比：clipPath 方法 vs CSS border-radius

| | clip-path: url(#sq) | border-radius: 16px |
|---|---|---|
| 真 Squircle | ✅ G2 连续 | ❌ 正圆弧 |
| backdrop-filter | ⚠️ Chrome 需 willChange | ✅ 完美 |
| box-shadow | ❌ 被切（需 drop-shadow）| ✅ 跟随 |
| border | ❌ 被切 | ✅ 跟随 |
| 浏览器支持 | 所有浏览器 | 所有浏览器 |
| 性能 | 额外合成层 | 原生 |

**折中方案（推荐）：** 
1. 用 `figma-squircle` + clip-path 做 Squircle
2. box-shadow 改用 `filter: drop-shadow()`
3. border 用 `box-shadow: inset 0 0 0 1px rgba(...)` 模拟
4. 对不支持 clip-path 的极老浏览器不提供 polyfill（自然降级为直角）

## GalaxyGlass 实际实施

具体在 <监控面板域名> 上的集成过程、代码、踩坑（特别是 tagged template 参数错位导致路径截断的 bug）详见 `references/figma-squircle-vanilla-js-implementation-20260517.md`。
