# Mobile: Search width halved, padding & card overflow grid fix (2026-05-16)

## Problems & Iterations

### Round 1: Search too wide, cards overflow
- **Search**: At 639px, `.search-box.open` had `max-width: 200px` — user said halve it to 100px
- **Cards**: Node/stat cards overflow right edge on mobile after JS data loads

### Round 2: Cards still overflowed after refresh
- Root cause: `min-width: 0` was added to flex children (`.stat-card > *`), but **CSS Grid** requires it on the grid item itself
- `.stat-card` is a grid item in `.stats-grid { grid-template-columns: repeat(2, 1fr); }` — grid default `min-width: auto` prevents shrinking below content width
- Fix: `.stat-card { min-width: 0; overflow: hidden; }` — on `.stat-card` itself, not its children

### Round 3: Skeleton ok, post-render overflow
- Initial page load shows skeleton → looks fine
- After `render()` fills real text (e.g. "¥94 · 剩余 ¥901≈ $13.71 / $132.") → overflow appears
- CSS must handle the post-render state, not just the skeleton

## All Fixes Applied

### 1. Search box width (639px only)
```css
.search-box.open, .search-box:focus-within { max-width: 100px; }
/* Was: max-width: 200px */
```
Web端 base rule stays `260px` — only the 639px override changed.

### 2. Search placeholder & padding (639px)
```html
placeholder="搜索"  <!-- Was: "搜索节点…" -->
aria-label="搜索"
```
```css
.search-box.open input, .search-box:focus-within input { padding-left: 10px; }
/* Without this, text is flush against left edge in row-reverse layout */
```

### 3. Container overflow safety (639px + 480px)
```css
.container { overflow-x: hidden; }
.page { overflow-x: hidden; }
```

### 4. CSS Grid item overflow fix — KEY INSIGHT
**Correct (grid item itself):**
```css
.stat-card { min-width: 0; overflow: hidden; }
```
**Wrong (grid item's children — doesn't work):**
```css
.stat-card > * { min-width: 0; overflow: hidden; }
/* ❌ Grid's min-width: auto intercepts at the item level */
```

### 5. Flex child overflow fix (639px + 480px)
```css
.node-card, .node-name, .card-metric { min-width: 0; }
.node-card { word-break: break-word; }  /* 480px */
```

### 6. Stat-card text overflow prevention (639px + 480px)
```css
.stat-card .value { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.stat-card .label { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.stat-card svg { flex-shrink: 0; }
```

### 7. Container padding tightened at 480px
```css
@media (max-width: 480px) {
  :root { --container-pad: 0.75rem; }
}
```

## CSS Grid vs Flexbox: Where `min-width: 0` goes

| Layout | Where to apply `min-width: 0` | Reason |
|--------|-------------------------------|--------|
| **CSS Grid** | On the grid item itself (`.stat-card`) | Grid items default `min-width: auto` — can't be overridden by children |
| **Flexbox** | On the flex child (`.node-card > child`) | Flex items also default `min-width: auto`, but overflow control can propagate up |

## Verification
- Hard refresh `stat.357561.xyz` on mobile viewport (480px / 639px)
- Wait for all API data to load and `render()` to execute
- Check: no horizontal scroll, stat cards don't overflow, search expands to ~100px with padding
