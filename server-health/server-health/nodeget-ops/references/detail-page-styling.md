# NodeGet 详情页与表格页样式要点

## 主页顶部栏 `.navbar-inner`

```css
.navbar-inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.5rem;
  padding: 0.75rem 0;   /* 不要 1.5rem，太高 */
}
```

初始透明，滚动 >10px 后变为毛玻璃：
```css
.navbar {
  position: sticky; top: 0; z-index: 10;
  background: transparent;
  border-bottom: 1px solid transparent;
  transition: background 0.3s, backdrop-filter 0.3s, -webkit-backdrop-filter 0.3s, border-color 0.3s;
}
.navbar.scrolled {
  background: rgba(0, 0, 0, 0.4) !important;
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
```

## 详情页顶部栏 `.detail-nav`

与主页统一，差异仅在 z-index：
```css
.detail-nav {
  position: sticky; top: 0; z-index: 20;
  background: transparent;
  border-bottom: 1px solid transparent;
  padding: 0.75rem 0;
  transition: background 0.3s, border-color 0.3s, backdrop-filter 0.3s;
}
.detail-nav.scrolled {
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
```

JS 滚动监听（两页共用）：
```js
window.addEventListener('scroll', () => {
  const nav = document.querySelector('.navbar, .detail-nav');
  if (!nav) return;
  nav.classList.toggle('scrolled', (window.scrollY || document.documentElement.scrollTop) > 10);
});
```

## 详情页内容区卡片间距

详情页 `#detail-content` 内部各组件（当前指标、概览卡片、图表）默认没间距，需要手动加：
```html
<div id="detail-content" style="display: flex; flex-direction: column; gap: 16px;">
  <!-- current-metrics、info-grid、chart-card 全在这里 -->
</div>
```

## 表格视图 `.table-view` 布局

⚠️ **常见问题：表格宽度没对齐、间距太紧**

```css
.table-view {
  display: flex;
  flex-direction: column;
  gap: 16px;              /* 表头与 body 之间的间距 */
  padding: 0 1.5rem;      /* 与 .container 的 padding 一致 */
}
/* 表格行之间的间距必须加在 #table-body 上（gap 不跨嵌套继承） */
#table-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
```

主页 `.container { max-width: 1124px; padding: 0 1.5rem; }` 决定内容宽度。表格在 `.container` 内，`#table-body` 是 flex 列，但没有自己的宽度约束——**必须显式加 `max-width: 1124px; margin: 0 auto; padding: 0 1.5rem; width: 100%` 才能与上方统计卡对齐**，不加会明显比统计卡窄。

**注意：** `.table-view` 的 gap 控制表头与 body 之间距离；`#table-body` 的 gap 控制行与行之间的距离。

## 三层 UI 结构（视频壁纸场景）

| 元素 | 背景 | backdrop-filter | 效果 |
|---|---|---|---|
| 视频 | 无（纯 video） | 无 | 完全清晰 |
| 导航栏/按钮/页脚 | `rgba(0,0,0,0.4)` | **无** | 半透明黑底，视频清晰可见 |
| 卡片 | `rgba(255,255,255,0.06)` | `blur(40px)` | 仅卡片后模糊 |

**⚠️ 常见错误：** 只有卡片用 backdrop-filter，而导航栏/切换按钮用实色背景，视觉上非常突兀。所有浮在视频上的元素都必须统一用半透明底。
