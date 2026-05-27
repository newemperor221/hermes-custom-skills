# Code audit fixes (2026-05-15)

Applied after user confirmed layout was good on both web and mobile.

## Fixes

### P1 — Visual/Logic
1. **Missing `.metric-label` CSS** — Detail page metric cards used `.metric-label` in JS template but no CSS rule existed → label inherited body 14px. Added:
   ```css
   .metric-card .metric-label { font-size: 11px; color: var(--text-muted); letter-spacing: 0.02em; }
   ```

2. **`hasError` never resets** — `loadData()` failure sets `hasError=true`. After returning from detail view, `showListView()` calls `render()` which exits early via `if(hasError)return`. Fix: `hasError=false` at start of `showListView()`.

### P2 — CSS redundancy cleanup
3. **Duplicate `.node-card { min-width:0 }`** in 639px block (two copies from repeated script runs)
4. **Redundant `.stat-card svg { flex-shrink:0 }`** in 639px/480px (already in base CSS)
5. **`.stat-card svg { flex-shrink:0 }`** merged into width rule at 480px

### P3 — Small optimizations
6. **theme-color meta tag** — `#0c1f3f` for dark mobile browser chrome
7. **Favicon** — Properly URL-encoded SVG data URI with "GG" on green `#10b981` background
8. **`getCtx()` height** — Changed `parseInt(c.style.height)` to `c.offsetHeight || parseInt(c.style.height) || 130`

### P3 — Dropdown menu clipped by overflow
9. **Removed `overflow-x: hidden` from `.container` and `.page` at 639px/480px** — The absolutely positioned `.dropdown-menu` (sort button) was being clipped. Card overflow prevention now handled at component level only (`.stat-card { min-width:0; overflow:hidden }`).

### Favicon encoding lesson
Inline SVG data URIs MUST be URL-encoded:
```python
import urllib.parse
encoded = urllib.parse.quote(svg, safe='')
href = f'data:image/svg+xml,{encoded}'
```
Without encoding, `<` `>` `'` `#` characters break the URI and favicon disappears.
