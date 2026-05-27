# Mobile Filter Chip Scroll Fix — 2026-05-15

## Problem
On mobile (639px), tapping a filter chip at the far right of `.filters` (e.g. KP, NL) caused erratic scrolling. The scroll position would reset and the bar would jump unpredictably.

## Root Causes

### 1. `-webkit-overflow-scrolling: touch`
**Deprecated CSS property** that causes erratic touch scrolling on iOS. The `.filters` container had:
```css
overflow-x: auto; -webkit-overflow-scrolling: touch;
```
**Fix:** Replace with `auto`:
```css
overflow-x: auto; -webkit-overflow-scrolling: auto;
```

### 2. Full DOM rebuild on every chip click
`buildRegionFilters()` was called from `render()` on EVERY render, which:
1. Removed all chip DOM elements: `c.querySelectorAll('.chip').forEach(e => e.remove())`
2. Re-inserted new ones: `c.insertAdjacentHTML('beforeend', h)`
3. This reset `scrollLeft` to 0

Then `scrollIntoView()` ran via rAF — but fighting the user's manual scroll position.

**Fix:** Chip clicks should only toggle `active` class + reposition slider + re-render node cards. Don't rebuild filter DOM.

### 3. `overflow-x: hidden` on `.container` / `.page`
At 639px, both `.container` and `.page` had `overflow-x: hidden` (added to fix card overflow). This **clipped the absolutely positioned `.dropdown-menu`** (sort dropdown) and also interfered with `.filters` scroll container behavior.

**Fix:** Remove container/page-level `overflow-x: hidden`. Card overflow is handled at the component level (`.stat-card { min-width: 0; overflow: hidden; }`).

## Implementation

### `render()` signature
```javascript
function render(skipFilters) {
  // ... render nodes ...
  updateStats();
  if (!skipFilters) { buildRegionFilters(); }
  positionBackToTop();
}
```

### All callers:
| Trigger | Call | Why |
|---------|------|-----|
| Chip click | `render(true)` | Toggle class only, keep filter DOM+scroll |
| Initial load | `render(false)` | Full rebuild needed |
| Search input | `render(false)` | Filter bar unaffected by search |
| Sort change | `render(false)` | Filter bar unaffected by sort |
| showListView | `render(false)` | Coming back from detail, rebuild all |

### Chip click handler in `buildRegionFilters()`:
```javascript
c.querySelectorAll('.chip').forEach(function(b) {
  b.addEventListener('click', function() {
    if (this.classList.contains('active')) return;
    filterRegion = this.dataset.region || null;
    // Toggle active class — no DOM rebuild
    c.querySelectorAll('.chip').forEach(function(ch) { ch.classList.remove('active') });
    this.classList.add('active');
    requestAnimationFrame(function() { positionFilterSlider() });
    render(true);  // skipFilters=true
  })
});
```

### No scrollIntoView needed
Once DOM stops being rebuilt, scroll position is naturally preserved. No `scrollIntoView()` required.

## Verification
- Tap far-right chip → no jump, scroll stays put
- Tap back to "全部" → slider moves, scroll stays
- Scroll to KP, tap NL → content re-filters, scroll stays
- Sort dropdown on mobile → opens fully (not clipped)
