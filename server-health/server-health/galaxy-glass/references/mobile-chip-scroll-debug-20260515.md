# Filter chip scroll + slider positioning fix (2026-05-15)

## Problem
On mobile (639px), clicking far-right filter chips (KP, NL) caused the `.filter-slider` to only move "a little bit" instead of tracking to the clicked chip. The chip's own `scrollIntoView` and subsequent `positionFilterSlider()` produced wrong coordinates.

## Failed approaches
1. **scrollIntoView + nested rAF** — `scrollIntoView` with `behavior:'smooth'` is animated, nested rAF runs before scroll completes → `getBoundingClientRect()` returns in-transit coordinates
2. **scrollIntoView + setTimeout(50)** — Same root cause, scroll not settled
3. **manual scrollLeft + nested rAF** — Correct approach in principle but absolute-positioned slider inside overflow:auto container has complex coord transformation
4. **offsetLeft - scrollLeft** — Equivalent equation to getBoundingClientRect, no improvement

## Final state
- Chip click handler: synchronous scrollLeft set + `positionFilterSlider()` called in same frame via direct call (no rAF)
- `.chip.active` given its own background (`background: rgba(255,255,255,0.08); backdrop-filter: blur(8px);`) so it's self-visible regardless of slider position
- Slider is now decorative only, not relied upon for state indication

## Root cause
`position: absolute` children inside `overflow: auto` containers do NOT scroll with the content. The slider stays at its CSS `left` value while chips move. The `getBoundingClientRect()` / `offsetLeft - scrollLeft` math IS correct, but the full solution requires:
1. Active chip having self-visual (can't depend on slider)
2. Synchronous scrollLeft + positionFilterSlider (no rAF gap)
3. Removing CSS transition on slider (conflicts with JS positioning)

## Key code
```javascript
this.classList.add('active');
var me=this;
var fc=$('filters-container');
if(fc){
  var target = me.offsetLeft - (fc.clientWidth/2) + (me.offsetWidth/2);
  fc.scrollLeft = Math.max(0, target);
}
positionFilterSlider();
render(true);
```
