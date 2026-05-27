# 2026-05-14 CSS Reorganization & Mobile Polish Session

## What was done

### CSS reorganization (attempted and reverted)
- Tried to move all `@media (max-width)` rules to a single `/* ── Responsive Overrides ── */` block at end of `<style>`
- Used `re.sub` regex → **broke the CSS** (24 extra closing braces from nested `{}`)
- Lesson: **NEVER use regex on CSS with nested braces**. CSS `@media` queries contain rules with their own `{}`, and simple regex patterns like `[^}]*[^}]*` can't handle arbitrary nesting depth.

### Fixes applied this session

1. **JS syntax error from previous sesson** — drawNetChart line 650 had dots `.` instead of quotes `"` around strings. Fixed by sed replacement.

2. **Chart legend: Canvas → HTML** — Removed Canvas-drawn legend from `drawNetChart()`, added HTML `.chart-legend` with `.legend-up` / `.legend-down` spans. Layout: right-aligned, column. CSS: `.chart-header { display:flex; justify-content:space-between; align-items:flex-start; }` with `.chart-header-left { flex:1; }` and `.chart-legend { flex-direction:column; align-items:flex-end; }`.

3. **CPU badge missing** — `$('badge-cpu').textContent=cpu.toFixed(1)+'%'` was never in the code. Added before `$('badge-mem').textContent=mp.toFixed(1)+'%'`.

4. **Empty-state background removed** — `.empty-state` had `background: var(--bg-deep)` which showed as dark blue rectangle when search returned no results. Removed (user wants NO background boxes on transient/empty elements).

5. **Fade-out animation removed** — `render()` used `grid.classList.add('fade-out')` + CSS `transition: opacity 0.25s` causing background flash during search. Removed both CSS and JS references.

6. **Search box mobile** — Changed from `display:none` to `flex-direction:row-reverse` + `max-width:36px` expanding to `200px` on focus, so the input extends to the LEFT from its position.

7. **Footer brand font** — Removed gradient `background-clip: text` from `.footer-brand`, set plain `color: var(--text-muted)` to match other footer text.

8. **Stat cards background** — User initially said "no background boxes" → removed `background: var(--glass-bg)` from `.stat-card`. Then user said "我要的啊" → restored it. Pattern: glass backgrounds on stat cards are desired; backgrounds on transient/empty-state elements are not.

9. **Mobile responsive CSS** added for: chart-legend (smaller margin/font), chart-badge (smaller font), stat-card (tighter padding on 480px), footer (centered on 639px).

## CSS structure after session

Style block is 14 sections (order preserved, no media query movement):
:root → Global reset → Navbar → Search → Sort Button → Main → Stats → Filters → Grid → Skeleton → Card → States → Detail View → Footer → Back to Top → (then the 4 @media blocks)

## Current mobile breakpoints summary

| Width | Effect |
|-------|--------|
| 800px | Detail body → single column |
| 680px | Nodes grid → 1fr column |
| 639px | Search compact, stats 2-col, footer centered, filters full-width+scroll |
| 480px | Stats tighter, chart elements smaller, metric/chart cards tighter padding |

## Remaining issues (user-reported at session end)

1. Filter capsules bar has issues on web (desktop)
2. Detail page has issues on web (desktop)  

Both need investigation — possible CSS artifact from the failed reorg.
