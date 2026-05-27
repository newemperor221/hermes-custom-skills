# Komari Theme（NodeGetGlass）样式改造要点

## 文件位置

- **dist 路径**: `/opt/komari/data/theme/NodeGetGlass/dist/`
- **主页**: `index.html`
- **详情页**: `detail.html`
- **本地备份**: `/tmp/nodeget-komari-theme/dist/`（推送前从这里改）、`/tmp/nodeget-status-dist/dist/`（detail.html 备份）

## 部署命令

```bash
scp -P 52137 /tmp/nodeget-komari-theme/dist/index.html root@<洛杉矶2_IP>:/opt/komari/data/theme/NodeGetGlass/dist/index.html
scp -P 52137 /tmp/nodeget-status-dist/dist/detail.html root@<洛杉矶2_IP>:/opt/komari/data/theme/NodeGetGlass/dist/detail.html
```

## 滚动透明 → 毛玻璃导航栏

主页 `.navbar-inner` 和详情页 `.detail-nav` 统一用：

```css
/* 初始：完全透明 */
.navbar, .detail-nav {
  position: sticky; top: 0; z-index: 10;  /* detail-nav 用 z-index: 20 */
  background: transparent;
  border-bottom: 1px solid transparent;
  padding: 0.75rem 0;  /* 不要 1.5rem，太高 */
  transition: background 0.3s, backdrop-filter 0.3s, border-color 0.3s;
}
/* 滚动后：毛玻璃 */
.navbar.scrolled, .detail-nav.scrolled {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
```

JS 滚动监听（在 `</script>` 末尾，`init()` 之前）：

```js
window.addEventListener('scroll', () => {
  const nav = document.querySelector('.detail-nav');
  if (!nav) return;
  nav.classList.toggle('scrolled', (window.scrollY || document.documentElement.scrollTop) > 10);
});
```

## 详情页 `#detail-content` 内部间距

详情页的 `current-metrics`、`info-grid`、`.chart-card` 默认没有间距，在 HTML 上加：

```html
<div id="detail-content" style="display: flex; flex-direction: column; gap: 16px;">
```

## 表格页 `.table-view` 布局（含关键坑）

```css
.table-view {
  display: flex;
  flex-direction: column;
  gap: 16px;          /* 表头与 body 之间的间距 */
  padding: 0 2.5rem;  /* 比统计栏稍宽，给表格列留呼吸空间 */
}
/* 行与行之间的间距必须加在 #table-body 上（gap 不跨嵌套继承） */
#table-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
```

**⚠️ 常见错误：**
- `.table-view` 没有 `max-width` 约束会窄于上方组件——必须显式加 `max-width: 1124px; margin: 0 auto; width: 100%` 使其与 `.container` 同宽
- 只在 `.table-view` 加 gap 不够——gap 不会跨 `#table-body` 继承到子元素（`.table-row`）之间，`#table-body` 本身要单独加 `gap: 16px`

## 表格列布局（✅ 正确值，不要改）

10 列 grid（状态/名称/OS/CPU/内存/磁盘/流量/价格/到期/运行时间）：

```css
grid-template-columns: 48px 1fr 70px 65px 65px 65px 100px 65px 85px 80px;
/*  状态  名称   系统  CPU  内存  磁盘   流量   价格    到期   运行 */
gap: 8px;
```

**这些值是经多次迭代后的正确状态，不要改动。**
- 表格外层 `.table-view` 已有 `max-width: 1124px; margin: 0 auto; padding: 0 1.5rem; width: 100%`，与 `.container` 完全对齐
- 如果流量/价格列字符被遮挡，不要改 grid 列宽，而是检查 `overflow: hidden` / `text-overflow: ellipsis` 是否在 `.table-cell` 上生效

## 统计栏「流量 / 速率」合并 + 「总价值」

统计栏原本两张卡（流量概览 + 网络速率），合并为一张，并新增总价值：

```html
<!-- 流量 / 速率：下行总流量 + 出口速率 -->
<div class="stat-card">
  <svg ... />
  <div>
    <div class="label">流量 / 速率</div>
    <div class="stat-sub-row">
      <div class="stat-sub">↓ <span id="stat-received">0 B</span></div>
      <div class="stat-sub">↑ <span id="stat-netout">0 B/s</span></div>
    </div>
  </div>
</div>
<!-- 总价值：汇总所有节点 price -->
<div class="stat-card">
  <svg ... />
  <div>
    <div class="label">总价值</div>
    <div class="value" id="stat-total-value">¥0</div>
  </div>
</div>
```

JS 中 `updateStats()` 更新逻辑：

```js
const totalValue = nodesList.reduce((sum, n) => sum + (parseFloat(n.price) || 0), 0);
document.getElementById('stat-total-value').textContent = '¥' + totalValue.toFixed(0);
```

## 表格 `renderRow` 中的流量、价格、到期字段

```js
function renderRow(n) {
  const trafficUsed = (n.network_total_received || 0) + (n.network_total_transmitted || 0);
  const priceText = n.price
    ? `${n.currency || '¥'}${n.price}/${n.billing_cycle === 365 ? '年' : n.billing_cycle === 30 ? '月' : '期'}`
    : '-';
  const expireText = n.expired_at ? new Date(n.expired_at).toLocaleDateString('zh-CN') : '-';
  // ... 输出 10 列
}
```

## 卡片 footer 第三行（流量/价格/到期）

```html
<div class="node-footer-row">
  <span class="node-footer-item">
    <svg ...流量图标.../>
    ${n.traffic_limit ? `${bytes((n.network_total_received||0)+(n.network_total_transmitted||0))}/${bytes(n.traffic_limit)}` : '-'}
  </span>
  <span class="node-footer-price">${n.price ? `${n.currency||'¥'}${n.price}/${n.billing_cycle===365?'年':n.billing_cycle===30?'月':'期'}` : '-'}</span>
  <span class="node-footer-expire">${n.expired_at ? new Date(n.expired_at).toLocaleDateString('zh-CN') : '-'}</span>
</div>
```

```css
.node-footer-price { margin-left: auto; font-weight: 500; color: rgba(255,255,255,0.6); }
.node-footer-expire { margin-left: 8px; color: rgba(255,255,255,0.5); }
```

## 视频壁纸（detail.html）

```js
const video = document.getElementById('bg-video');
if (video) {
  video.src = 'https://img.<用户域名>/wallpaper.mp4';
  video.style.opacity = '1';
}
```

## ⚠️ 修改原则

1. **每做好一个功能，一份上传 GitHub，一份传到 56idc 测试。** GitHub 仓库：`newemperor221/nodeget-komari-theme`（main 分支）。56idc 路径：`/opt/komari/data/theme/NodeGetGlass/dist/`。本地工作副本：`/tmp/nodeget-komari-theme/dist/`。
2. **用 DOM 测量而非截图** — `browser_vision` 有时不返回正确结果。用 `browser_console` 的 `getBoundingClientRect()` 量实际像素，或用 `python3 + PIL` 直接量截图像素。
3. **表格 grid 值是正确状态，不要改** — 见上方"表格列布局"节。
4. **改样式前先看效果** — 每次改完立即推送，不要积累多个修改。
5. **推送前检查语法** — 标签闭合、JS 语法错误会直接导致页面空白。
