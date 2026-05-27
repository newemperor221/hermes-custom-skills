# Overflow Container + Absolute Positioning Coordinate Principle

## The Bug
`.filter-slider` (`position: absolute` inside `.filters` with `overflow-x: auto; position: relative`) wouldn't align with the active chip after scrolling. All coordinate approaches failed until web research revealed the root cause.

## Root Cause
When a container has **both** `overflow: auto` AND `position: relative`, its `position: absolute` children **scroll with the content**, not the viewport.

Ben Nadel explanation: https://www.bennadel.com/blog/3409-using-position-absolute-inside-a-scrolling-overflow-container.htm

### Coordinate Systems Summary

| Approach | Formula | Result | Why |
|----------|---------|--------|-----|
| Viewport diff | `ar.left - fr.left` (getBoundingClientRect) | ❌ | Absolute element scrolls with content, so viewport-relative position = wrong after scroll |
| Visual coord | `a.offsetLeft - f.scrollLeft` | ❌ | Subtracting scrollLeft sends slider in wrong direction |
| **Content coord** | **`a.offsetLeft`** | **✅** | **Slider and chip share the same coordinate origin (`.filters` padding box), same scroll behavior** |

## Correct Code (as of 2026-05-16)

```javascript
function positionFilterSlider(){
  var s=$('filter-slider'), a=document.querySelector('.chip.active'), f=$('filters-container');
  if(!s||!a||!f)return;
  s.style.left = a.offsetLeft + 'px';
  s.style.width = a.offsetWidth + 'px';
}
```

Chip click handler:
```javascript
b.addEventListener('click', function(){
  if(this.classList.contains('active')) return;
  filterRegion = this.dataset.region || null;
  c.querySelectorAll('.chip').forEach(function(ch){ch.classList.remove('active')});
  this.classList.add('active');
  this.scrollIntoView({inline:'center'});     // instant sync scroll
  positionFilterSlider();                      // uses offsetLeft = content coords
  render(true);                                // skip filter DOM rebuild
});
```

## Key Conditions
- `.filters` must have `position: relative` — this establishes it as the containing block
- `.filter-slider` must be a DIRECT child of `.filters` — otherwise offsetParent changes
- Chips must also be direct children — same offsetParent for correct `a.offsetLeft`
- CSS `transition: left` on slider MUST be removed — otherwise JS-set values animate instead of landing immediately

## What Doesn't Work
- `getBoundingClientRect` — gives viewport coordinates, absolute elements in overflow containers don't use viewport coords
- `scrollIntoView({behavior:'smooth'})` — async scroll causes coordinate mismatch; use default (instant) or `{behavior:'auto'}`
- Nested `requestAnimationFrame` — creates timing window where scroll hasn't settled
- `setTimeout` — unnecessary if scrollIntoView is instant; adds jank delay
