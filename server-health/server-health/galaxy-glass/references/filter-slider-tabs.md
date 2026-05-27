# 筛选标签切换为胶囊滑动标签栏 (2026-05-14)

## 背景

用户要求将独立的 chip 按钮改成「一个大胶囊包裹小胶囊，点一个滑过去」的交互。从独立药丸按钮改为统一胶囊容器内的滑动高亮 tab 栏。

## 设计目标

- 所有筛选选项放在一个毛玻璃大胶囊容器内
- 点击切换时，淡绿色渐变滑块平滑滑动到目标 tab
- 无多余空白，紧凑不浪费空间
- 交互反馈清晰流畅

## HTML 结构

```html
<!-- 在 index.html 模板中，替换原来的 <div id="region-filters"></div> -->
<div class="region-filters-wrap" id="region-filters">
  <div class="filters-wrap">
    <div class="filter-slider" id="filter-slider"></div>
    <div class="filters" id="filters-container"></div>
  </div>
</div>
```

**关键**：`.filter-slider` 在 HTML 模板中，不在 JS 中创建。这样每次 `render()` 调用 `buildRegionFilters()` 时，`$('filters-container').innerHTML = ...` 只替换 chips，slider 元素保持存活，CSS transition 才能从旧位置滑到新位置。

## CSS

```css
/* ── Filters ── */
.region-filters-wrap { padding: 0 var(--container-pad); }

.filters-wrap { position: relative; }

.filters {
  display: flex; position: relative; z-index: 1;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  border-radius: var(--radius-full);   /* 大胶囊 */
  padding: 3px;
  backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
}

.filter-slider {
  position: absolute; z-index: 0;
  top: 3px; bottom: 3px; left: 3px;
  border-radius: var(--radius-full);
  background: linear-gradient(135deg, rgba(45,158,107,0.15), rgba(201,169,78,0.1));
  transition: left 0.2s cubic-bezier(0.34, 1.56, 0.64, 1),
              width 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  pointer-events: none;               /* 让点击穿透到 chips */
}

.chip {
  flex: 1; padding: 5px 8px; font-size: 13px;
  border: none; background: transparent;
  color: var(--text-secondary); cursor: pointer;
  text-align: center; white-space: nowrap;
  transition: color 0.2s;
  border-radius: var(--radius-full);
  user-select: none;
}
.chip:hover { color: var(--text-primary); }
.chip.active { color: var(--accent); }
```

## JS

```js
// buildRegionFilters 操作 filters-container，保留 filter-slider 元素
function buildRegionFilters() {
  var m = {};
  nodesList.forEach(function(n) {
    if (n.region) m[n.region] = (m[n.region] || 0) + 1;
  });
  var r = Object.keys(m).sort(function(a, b) { return m[b] - m[a]; });

  var c = $('filters-container');
  if (!c) return;
  if (r.length === 0) { c.innerHTML = ''; return; }

  var h = '';
  // "全部" chip
  h += '<button class="chip' + (filterRegion === null ? ' active' : '') + '" data-region="">全部 ' + nodesList.length + '</button>';
  // 各区域 chip
  r.forEach(function(k) {
    var fc = flagEmoji(k);
    var fi = fc
      ? '<img src="https://flagcdn.com/' + fc + '.svg" alt="" style="width:18px;height:13px;object-fit:cover;border-radius:2px;" loading="lazy">'
      : '';
    var label = fc ? fc.toUpperCase() : k;
    h += '<button class="chip' + (filterRegion === k ? ' active' : '') + '" data-region="' + k + '">'
      + fi + label + ' ' + m[k] + '</button>';
  });

  c.innerHTML = h;

  // 绑定点击事件
  c.querySelectorAll('.chip').forEach(function(b) {
    b.addEventListener('click', function() {
      filterRegion = this.dataset.region || null;
      render();  // render() 内部调用 buildRegionFilters()
    });
  });

  // 定位 slider（下一帧保证 DOM 已渲染）
  requestAnimationFrame(function() {
    positionFilterSlider();
  });
}

// 计算并设置滑动指示器的位置
function positionFilterSlider() {
  var s = $('filter-slider');
  var a = document.querySelector('.chip.active');
  var w = document.querySelector('.filters-wrap');
  if (!s || !a || !w) return;

  var wr = w.getBoundingClientRect();
  var ar = a.getBoundingClientRect();

  s.style.left = (ar.left - wr.left) + 'px';
  s.style.width = a.offsetWidth + 'px';
}
```

## 踩坑

### ❌ slider 在 JS 中随 chips 一起创建

**错误做法**：
```js
var h = '<div class="filters">';
h += '<div class="filter-slider"></div>';  // slider 写在 h 里面
h += '<button class="chip">...</button>';
// ...
c.innerHTML = h;
```

每次 `innerHTML` 会创建新的 slider 元素，CSS transition 找不到「旧位置→新位置」的起止，只会在目标位置闪现。

**正确做法**：slider 在 HTML 模板中，chips 容器只包含 chip 元素。

### ❌ `overflow: hidden` 在 `.filters` 上

滑块需要被裁切吗？不需要——slider 自带 `border-radius: var(--radius-full)`，与父容器一致。加上 `overflow: hidden` 会裁切 dropdown 菜单。

### ❌ 直接设 `left: active.offsetLeft`

`active.offsetLeft` 是相对 `.filters` 的定位。而 slider 是 `.filters-wrap` 的子元素。需要用 `getBoundingClientRect()` 坐标差值来计算：
```js
var wr = w.getBoundingClientRect();
var ar = a.getBoundingClientRect();
s.style.left = (ar.left - wr.left) + 'px';
```

### 首次加载的初始位置

slider CSS 初始为 `left: 3px`（父容器的 padding），无 explicit width（auto → 0）。首帧 `positionFilterSlider()` 通过 `requestAnimationFrame` 设置到首个 `.chip.active`。在请求帧回调之前浏览器已完成一次布局，所以用户看到的就是正确位置，没有闪烁。

## 对比：旧设计 vs 新设计

| 方面 | 旧设计（独立 chip） | 新设计（胶囊滑动 tab） |
|------|-------------------|---------------------|
| 容器 | 无，chip 散放在 flex wrap row | 统一毛玻璃大胶囊 |
| 每个 chip | 独立 border/background/backdrop | 无背景，只有文字 |
| 选中态 | random border + gradient bg | 颜色变化 + 滑块指示 |
| 切换动画 | 无（瞬间切换） | 滑块滑过，0.2s bounce |
| chip 宽度 | inline-flex 随内容 | flex:1 等宽 |
| min-height | 36px（强制撑高） | 无（内容决定） |
