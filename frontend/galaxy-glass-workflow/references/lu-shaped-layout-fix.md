# 「吕字形」布局修复

## 什么是吕字形

用户用「吕」字（两个口上下叠）来形容布局缺陷——页面上下分成两大块厚实的水平区块，缺乏节奏感和呼吸空间。

### 主页「正吕」

顶部区域分为两个紧贴的厚水平条：
1. Navbar（GG探针品牌 + 搜索/排序/登录）
2. 统计卡片行（4个 stat-card 横排）

**修复方案**：
- 增大 `.main { padding-top: 1.5rem → 2.5rem }` 拉开 navbar 和统计卡片的距离
- 增大 `.main { gap: 1rem → 1.5rem }` 拉开各区块间距
- 缩小 stat-card padding（14px 16px → 10px 14px）、图标缩小（1.6rem → 1.4rem），降低视觉重量
- 节点卡片改为 `repeat(4, 1fr)` 和统计卡片对齐，避免宽窄不一

### 详情页「倒吕」

进入详情页后出现两层导航栏叠在一起：
1. Navbar「GG 探针」（本应隐藏但没隐藏）
2. Detail-nav「← 返回 节点名」

**原因**：CSS 选择器写错。

```js
// app.js 中给 navbar 自身添加 in-detail 类
$('navbar').classList.add('in-detail');
```

```css
/* ❌ 错误：后代选择器——找 .in-detail 内部的 .navbar，不匹配 */
.in-detail .navbar { display: none; }

/* ✅ 正确：交集选择器——找同时有 navbar 和 in-detail 类的元素 */
.navbar.in-detail { display: none; }
```

**关键原则**：当 JS 给元素自身添加类来控制自身样式时，必须使用无空格的交集选择器 `.element.classToToggle`。

## 统计卡片不在 Grid 内（同级元素陷阱）

### 现象

统计卡片（stat-card）渲染为全宽竖排，而不是4列横排。看起来像4个全宽方块叠在一起，而不是4格仪表盘。

### 原因

HTML 结构错误：stat-card 是 stats-grid 的**同级兄弟元素**，而不是**子元素**。

```html
<!-- ❌ 错误：stat-card 在 grid 外面，作为 flex 子元素全宽渲染 -->
<div class="stats-grid" id="stats-bar"></div>     ← 空的 grid
<div class="stat-card">...</div>                   ← flex 子元素，全宽
<div class="stat-card">...</div>                   ← flex 子元素，全宽
<div class="stat-card">...</div>                   ← flex 子元素，全宽
<div class="stat-card">...</div>                   ← flex 子元素，全宽
```

```html
<!-- ✅ 正确：stat-card 在 grid 内部，作为 grid 子元素按 4 列渲染 -->
<div class="stats-grid" id="stats-bar">
  <div class="stat-card">...</div>
  <div class="stat-card">...</div>
  <div class="stat-card">...</div>
  <div class="stat-card">...</div>
</div>
```

### 预防

修改 HTML 布局时，**永远检查子元素是否真的是 DOM 子节点而不是同级兄弟**。一个快速验证方法：

```javascript
// 在浏览器控制台检查
document.querySelectorAll('#stats-bar > .stat-card').length
// 返回 4 → ✅ stat-card 是子元素
// 返回 0 → ❌ stat-card 在外面
```

## 删除 HTML 元素但保留 JS 引用（静默崩溃陷阱）

### 现象

点击节点进入详情页后永远显示「加载详情…」，sysinfo、图表全部不渲染，控制台无明确报错（promise 内的 TypeError 被吞掉）。

### 原因

从 `body.html` 删除了 `<div class="metrics-grid" id="detail-metrics">`，但在 `app.js` 中仍有 `$('detail-metrics').innerHTML=''`。

`document.getElementById('detail-metrics')` 返回 `null`，`null.innerHTML` 抛出 TypeError。由于这行在 `renderDetailView` 函数中间——一个 `promise.then()` 回调里——异常不会冒泡到控制台的 `window.onerror`，而是被 promise 链吞掉。函数后续所有代码（sysinfo、图表渲染）都不会执行。

### 修复

删除元素的 3 步操作必须在**同一轮修改**中完成：

1. **`body.html`** — 删除 HTML 标签
2. **`scripts/app.js`** — 删除或注释所有引用该 ID 的代码（用 `grep 'detail-metrics'` 确认无残余）
3. **`styles/components.css`** — 删除对应的 CSS 类

## 移除详情页暂停按钮

用户要求去掉图表上的「⏸ 暂停」按钮。删除涉及 3 个文件 + JS 逻辑链清理：

### 1. `body.html`

每个 chart-card 里的 `<button class="chart-pause-btn" id="pause-{cpu|mem|net}">⏸ 暂停</button>` 删除。注意 network card 的暂停按钮在 `.chart-header` 内的一个独立 flex 容器中，删除后该容器退化，直接 chart-header-left + chart-legend。

```html
<!-- ❌ 删除前 -->
<div class="chart-header">
  <div class="chart-header-left">
    <div class="chart-title">网络速率</div>
    <div class="chart-badge">...</div>
  </div>
  <div style="display:flex;align-items:center;gap:6px">
    <button class="chart-pause-btn" id="pause-net">⏸ 暂停</button>
    <div class="chart-legend">...</div>
  </div>
</div>

<!-- ✅ 删除后 -->
<div class="chart-header">
  <div class="chart-header-left">
    <div class="chart-title">网络速率</div>
    <div class="chart-badge">...</div>
  </div>
  <div class="chart-legend">...</div>
</div>
```

### 2. `styles/components.css`

删除整个 `.chart-pause-btn` 及其所有变体（`.chart-pause-btn:hover`, `.chart-pause-btn.paused`）。

### 3. `scripts/app.js`

删除 pause 逻辑链（按顺序，删除依赖链路）：

1. `var _chartPaused = {}` — 状态存储
2. `function toggleChartPause(id)` — 切换函数
3. `function wirePauseButtons()` — 事件绑定
4. `setupEvents()` 中的 `wirePauseButtons()` 调用
5. `drawLineChart` override — 跳过暂停的图表渲染
6. `drawNetChart` override — 跳过暂停的网络图渲染
7. `redrawDetailCharts` override — 跳过暂停的 resize 重绘

删除后，原生的 `drawLineChart`、`drawNetChart`、`redrawDetailCharts`（位于 override 之前的原始定义）继续正常工作。

### 验证

```javascript
document.querySelectorAll('.chart-pause-btn').length
// → 0 ✅
```

## 响应式断点：节点网格列数

节点卡片网格改为 `repeat(4, 1fr)` 后，需要同步更新响应式断点：

| 断点 | 列数 | 文件 |
|------|------|------|
| ≥1600px | `repeat(5, 1fr)` | `web.css`（min-width: 1600px） |
| 1001–1599px | `repeat(4, 1fr)` | `layout.css`（默认） |
| 681–1000px | `repeat(2, 1fr)` | `mobile.css`（max-width: 1000px） |
| ≤680px | `1fr` | `mobile.css`（max-width: 680px） |

不加 tablet 2 列断点会导致 680–1000px 范围内 4 列挤爆、内容溢出。

### 验证

部署后打开浏览器控制台，运行：

```javascript
// 检查 JS 是否报错
'errors: ' + (window.__errorCount || 0)

// 检查元素是否存在（被删除的应为 null）
document.getElementById('detail-metrics')
// → null ✅

// 检查详情页渲染状态
document.getElementById('detail-name')?.textContent
// → '无聊云 | 洛杉矶' ✅ 不是 'null'

document.getElementById('detail-loading')?.classList.contains('hidden')
// → true ✅ 加载态已隐藏
```
