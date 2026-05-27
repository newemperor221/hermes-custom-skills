# 筛选胶囊滚动 + 滑块定位调试

## 问题

移动端 639px 下 `.filters` 启用 `overflow-x: auto` 后，用户滑到尾部点 KP/NL 芯片，滑块（`.filter-slider`）只移动了一点点，没有跟到选中标签下。

## 根因链

### 第一层：DOM 重建导致滚动重置

`buildRegionFilters()` 每次 render 都 `remove()` 所有 chip 再 `insertAdjacentHTML()` 重建 → 容器的 `scrollLeft` 被重置为 0 → 用户滑到后面后点 chip → 滚动跳回开头。

**修复**：chip click 只切换 `active` 类，不重建 DOM。`render()` 加 `skipFilters` 参数，chip 传 `render(true)` 跳过 `buildRegionFilters()`。

### 第二层：scrollIntoView 时 slider 位置算错

chip click 后用 `scrollIntoView({behavior:'smooth',inline:'center'})` 让 chip 居中 → 内层 rAF 跑 `positionFilterSlider()`。但 smooth scroll 不会在 rAF 回调运行前完成 layout → `getBoundingClientRect()` 读到的是滚动前的坐标 → slider 定位到错误位置。

**修复**：不用 scrollIntoView，手动算：
```
targetScrollLeft = chip.offsetLeft - container.clientWidth/2 + chip.offsetWidth/2
fc.scrollLeft = Math.max(0, targetScrollLeft)
```
`scrollLeft` 赋值是**同步**的，立即更新 layout → 嵌套 rAF 里 `getBoundingClientRect()` 读到正确坐标。

### 第三层：position:absolute + overflow:auto 的坐标系统

`.filter-slider` 是 `position: absolute` 在 `position: relative` 的 `.filters` 内。`.filters` 有 `overflow-x: auto`。

关键：`position: absolute` 子元素**不随**父容器滚动——它定位在父元素 padding box 坐标系中，不受 `scrollLeft` 影响。所以 `positionFilterSlider()` 中的坐标计算：
```
ar.left - fr.left  // 均用 getBoundingClientRect()（viewport 坐标系）
```
在滚动后仍然正确，因为减去滚动偏移量后得到的是 chip 相对于 `.filters` padding box 的视觉位置。

## 最终代码

```js
// chip click handler (buildRegionFilters 内)
this.classList.add('active');
var me = this;
requestAnimationFrame(function(){
  var fc = $('#filters-container');
  if(fc){
    var target = me.offsetLeft - (fc.clientWidth / 2) + (me.offsetWidth / 2);
    fc.scrollLeft = Math.max(0, target);
  }
  requestAnimationFrame(function(){
    positionFilterSlider();
  });
});
render(true);
```

## render(skipFilters) 调用矩阵

| 触发点 | 参数 | 说明 |
|--------|------|------|
| chip click | `true` | 只切换 active + 重渲节点，跳过 filter rebuild |
| 初始 loadData | `false` | 全量重建 filters + nodes |
| search input | `false` | 搜索要重建 filters（计数变化） |
| sort change | `false` | 排序不影响 filters 但也全量重建 |
| showListView | `false` | 从详情返回，全量重建 |
