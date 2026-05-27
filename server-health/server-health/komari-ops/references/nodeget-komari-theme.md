# NodeGet Komari Theme — 布局与样式笔记

## 项目路径
- 本地：`/tmp/nodeget-komari-theme/dist/index.html`
- 部署：`root@<洛杉矶2_IP>:/opt/komari/data/theme/NodeGetGlass/dist/index.html`
- 部署命令：`scp -P 52137 /tmp/nodeget-komari-theme/dist/index.html root@<洛杉矶2_IP>:/opt/komari/data/theme/NodeGetGlass/dist/index.html`

## 布局容器
- 全局宽度：`max-width: 1124px`，`.container` 类
- 顶部栏、主体、底部栏全部用同一个 `.container`
- 三块宽度严格对齐

## 底部栏布局

### 当前最终方案（grid 布局）

nodeget-status 风格：`rgba(0,0,0,0.2)` 背景 + `border-top rgba(255,255,255,0.1)` + `1rem 1.5rem` padding。

```css
.footer {
  background: rgba(0, 0, 0, 0.2);
  border-top: 1px solid rgba(255,255,255,0.1);
  padding: 1rem 1.5rem;
}
.footer-inner {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  align-items: center;
  font-size: 12px;
  color: rgba(255,255,255,0.6);
  text-shadow: 0 1px 4px rgba(0,0,0,0.6);
}
.footer-inner > *:first-child { justify-self: start; }
.footer-inner > *:nth-child(2) { justify-self: center; }
.footer-inner > *:last-child  { justify-self: end; }
```

grid 三列（1fr auto 1fr）比 flex 更适合分布：左右对齐容器边缘，中间自动居中。

### 历史教训

**`.footer-brand` 不要加 `flex: 1`**。加了 `flex: 1` 后该元素占满整行（实测 894px/1124px），但里面只有一小段文字，视觉反而失调。

**`padding-left` 继承问题**：`display:grid` 的 `.footer-inner` 会被父级 `.footer` 的 `padding-left: 1.5rem` 推出 21px。解决方案：父级 `.footer` 设水平 padding，`.footer-inner` 不再单独设 padding。

**底部栏颜色**：统一为链接色 `rgba(255,255,255,0.6)`，不用更浅的 0.85。

**链接 hover**：加 `pointer-events: none` 禁用点击高亮：
```css
.footer a { pointer-events: none; }
```

## 顶部栏下滑毛玻璃

nodeget-status 原版：当 `scrollY > 25` 时 navbar 加 `scrolled` 类，变成 `bg-black/20 backdrop-blur-xl border-white/10`。

**关键**：`.navbar.scrolled` 的 `background` 必须加 `!important`，否则可能被内联 style 覆盖（browser_console 的 `setProperty` 会写 `style="background: rgba(...) !important"`）。

```css
.navbar.scrolled {
  background: rgba(0, 0, 0, 0.4) !important;  /* !important 必须 */
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255,255,255,0.1);
}
```

滚动监听 JS（`setupScroll` 函数，line ~1179）理论上：
```javascript
window.addEventListener('scroll', () => {
  navbar.classList.toggle('scrolled', window.scrollY > 25);
}, { passive: true });
```

### ⚠️ Cloudflare overlay 拦截 + JS 错误

**已验证（2026-05-04）**：Cloudflare challenge/overlay 拦截了所有 scroll 相关事件，`setupScroll` 的监听器**永远不会被调用**。

**更常见的原因：JS 错误提前终止 `init()`**。

Console 报错 `ReferenceError: searchBtn is not defined at setupEvents` → `setupEvents()` 抛出异常 → `init()` 捕获后继续但 setupScroll 永远没执行。

验证方法（browser console）：
```javascript
// 1. 先检查 setupScroll 有没有执行
typeof setupScroll === 'function'  // 应该是 true

// 2. 检查 navbar 是否有 scrolled 类（手动 toggle 验证 CSS）
document.getElementById('navbar').classList.add('scrolled')
// 如果背景变深 → CSS 没问题，问题在 JS 检测逻辑

// 3. 检查 window.scrollY 值（Cloudflare 会劫持，值永远是 0）
window.scrollY  // 永远返回 0 = Cloudflare 劫持了 scroll 读数
```

**已试过且失效的方案**：
1. `IntersectionObserver` 监听 sentinel 元素 — 不触发（overlay 干扰 root）
2. `requestAnimationFrame` + scroll listener — 同样被拦截
3. `wheel` 事件（`passive:true`）— 被拦截（headless + 真机均验证）
4. `touchstart`/`touchmove` 监听 — 同理被拦截
5. `setInterval` 轮询 `scrollY` — **scrollY 本身被劫持，永远是 0**

**根因**：Cloudflare challenge.js 在页面上层劫持了 `window.scrollY` 读数，使所有依赖 `scrollY` 判断滚动的 JS 均失效。

**修复步骤**：
1. 打开 browser console，排除 JS 错误（`searchBtn is not defined` 等）
2. 确认 CSS 本身可用（`classList.add('scrolled')` 背景变深）
3. 如果 CSS 可用但 scroll 不触发 → Cloudflare 劫持了 scroll，计算题无解

## 底部栏毛玻璃

在 `rgba(0,0,0,0.2)` 背景上加毛玻璃：

```css
.footer {
  background: rgba(0, 0, 0, 0.2);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-top: 1px solid rgba(255,255,255,0.1);
  padding: 1rem 1.5rem;
}
```

## 表格视图（table-view）毛玻璃行

nodeget-status 的表格不是 `<table>` 而是 div flex/grid 模拟。改造 Komari 主题 HTML 结构：

```html
<div class="table-view" id="table-view">
  <div class="table-header">
    <span>状态</span><span>名称</span><span>系统</span>...
  </div>
  <div id="table-body"></div>
</div>
```

```css
.table-view {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 0 1.5rem;
}
.table-header {
  display: grid;
  grid-template-columns: 48px 1fr 80px 70px 70px 70px 100px 90px;
  gap: 8px;
  padding: 8px 16px;
  font-size: 11px;
  font-weight: 500;
  color: rgba(255,255,255,0.35);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}
.table-row {
  display: grid;
  grid-template-columns: 48px 1fr 80px 70px 70px 70px 100px 90px;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 16px;
  background: rgba(0, 0, 0, 0.22);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}
.table-row:hover {
  background: rgba(0, 0, 0, 0.3);
  border-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.3);
}
.table-cell {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: rgba(255,255,255,0.85);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.table-row.offline { opacity: 0.5; }
```

`renderRow` JS 输出改为 div 而非 `<tr>`：
```javascript
function renderRow(n) {
  return `
    <div class="table-row${n.online ? '' : ' offline'}">
      <span class="table-cell">...</span>
      ...
    </div>
  `;
}
```

### ⚠️ 切换筛选分组时页面抖动（底部栏上下跳）

**问题**：从"全部"切换到服务器少的分组（如 HK 1台），底部栏突然上移；切回全部时底部栏下移。反复切换造成持续抖动。

**根因**：网格高度由卡片数量决定 → 卡片少时网格变矮 → 底部栏位置上移。没有固定高度的容器约束它。

**正确修复**：给 `.nodes-grid` 加 `min-height: calc(100vh - 380px)`（380px ≈ 顶部导航 + 统计栏 + 筛选区 + 底部栏高度），让网格区域始终保持足够高度，底部栏位置固定：
```css
.nodes-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  align-content: start;
  min-height: calc(100vh - 380px);  /* ← 固定底部栏位置 */
}
```

**⚠️ 不要用 `align-content: space-between`**：这会把最后一行卡片均匀分布到整个网格高度，卡片本身被拉伸（用户明确说"不要拉卡片"）。

**⚠️ 不要用 `min-height` 撑卡片**：给 `.node-card` 加 `min-height` 是对的，但不要用 `align-content: center` 或 `space-between`，否则最后一排卡片会被不必要地拉长。

**验证**：切换分组后底部栏位置不变，页面不抖动。

---

## 地区筛选按钮 active 状态不更新

**问题**：点击非"全部"按钮后，"全部"仍显示绿色激活样式。

**根因**：`buildRegionFilters()` 只在 `init()` 时调用一次。点击按钮只改 `filterRegion` 变量并 `render()`，按钮 HTML 没重建，active 样式停留在旧状态。

**修复**：点击事件中加 `buildRegionFilters()` 重建按钮：
```javascript
btn.addEventListener('click', () => {
  filterRegion = btn.dataset.region || null;
  buildRegionFilters();  // ← 重建按钮，保持 active 状态同步
  render();
});
```

## 节点卡片网格（nodes-grid）

当前最终参数（2026-05-04 迭代确定）：
```css
.nodes-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 16px;
  align-content: start;
  min-height: calc(100vh - 380px);  /* 固定底部栏位置，防止筛选切换时抖动 */
}
@media (min-width: 640px)  { .nodes-grid { grid-template-columns: repeat(2, 1fr); } }
@media (min-width: 1024px) { .nodes-grid { grid-template-columns: repeat(3, 1fr); } }
@media (min-width: 1280px) { .nodes-grid { grid-template-columns: repeat(4, 1fr); } }
```

```css
.node-card {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 1rem;
  border-radius: 16px;
  background: var(--glass-blur-bg);
  backdrop-filter: blur(80px) saturate(180%);
  -webkit-backdrop-filter: blur(80px) saturate(180%);
  border: 1px solid rgba(255,255,255,0.1);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: pointer;
  min-height: 160px;  /* 防止卡片被 align-content 拉伸 */
}
.node-card:hover {
  transform: translateY(-6px) scale(1.02);
  box-shadow: 0 20px 40px rgba(0,0,0,0.3);
  border-color: rgba(255,255,255,0.15);
}
```

## 顶部栏标题字号

当前值：20px。
