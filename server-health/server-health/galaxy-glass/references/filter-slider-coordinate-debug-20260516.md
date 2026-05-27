# Filter Slider 坐标调试记录（2026-05-16）

## 问题

移动端筛选胶囊栏（`.filters` 用 `overflow-x: auto`），点击后排地区（KP/NL）时，绝对定位的 `.filter-slider` 只移动了一点点，没有正确跟随到选中 chip。

## 坐标方案对比

| 方案 | 公式 | 结果 | 原因 |
|------|------|------|------|
| getBoundingClientRect | `ar.left - fr.left` | ✅ 正确 | viewport 坐标系，不受 scroll/offsetParent 影响 |
| offsetLeft - scrollLeft | `a.offsetLeft - f.scrollLeft` | ❌ 错误 | offsetParent 不是 `.filters` 而是 `.filters-wrap`（也有 `position:relative`），坐标不一致 |
| scrollIntoView + rAF | scrollIntoView + nested rAF → positionFilterSlider | ❌ 时序问题 | smooth 滚动还没完成，嵌套 rAF 读到的是半途坐标 |
| scrollLeft 手动计算 | `me.offsetLeft - fc.clientWidth/2 + me.offsetWidth/2` | ❌ offsetParent 错误 | 同上，offsetLeft 坐标系和 scrollLeft 坐标系不同 |

## 最终方案

```javascript
// 点 chip 时
this.classList.add('active');
this.scrollIntoView({inline:'center'});  // instant scroll, sync
positionFilterSlider();                    // immediate, no rAF
render(true);
```

同时移除 slider 的 CSS `transition`（否则 `positionFilterSlider()` 设置的 `left` 变成动画 target 而非即时值，导致滑块跑到中间位置）。

## 关键教训

1. `offsetLeft` 不是相对于父元素而是相对于 `offsetParent`（最近 `position:relative` 祖先）。如果有多层 `position:relative`，`offsetLeft` 可能指向错误容器。
2. `getBoundingClientRect()` 在 viewport 坐标系里永远可靠，因为所有元素的 viewport 位置都基于同一个原点。
3. `scrollIntoView` 的默认 behavior 是 `auto`（instant），不是 `smooth`。`smooth` 会在后续 rAF 里才生效，导致坐标读取提前。
4. CSS `transition` 和 JS 即时定位互斥。如果有 transition，设置 style 属性只设定目标值，当前帧取到的坐标是过渡起点。
5. chip 自身不要加背景/边框做 active 指示——用户拒绝。slider 是唯一视觉指示器，必须可靠。
