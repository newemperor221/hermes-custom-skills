---
name: css-glassmorphism-backdrop-filter
description: "CSS frosted glass / glassmorphism via backdrop-filter — pitfalls with Tailwind, stacking contexts, video backgrounds, and strong blur effects. Trigger: 'frosted glass', 'glassmorphism', 'backdrop-filter', 'blur card', '毛玻璃'."
triggers:
  - frosted glass
  - glassmorphism
  - backdrop-filter
  - blur card
  - 毛玻璃
  - liquid glass
  - 磨砂玻璃
---

# CSS Glassmorphism / backdrop-filter

## Critical Pitfall: Tailwind/PostCSS Strips Standard `backdrop-filter`

**Tailwind's PostCSS pipeline strips the standard `backdrop-filter` property**, keeping only the `-webkit-` prefixed version. This causes the blur to **silently fail** in modern browsers.

**Fix:** Put `-webkit-backdrop-filter` BEFORE `backdrop-filter` in source CSS:

```css
/* ✅ CORRECT — both preserved in build output */
.glass-card {
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
}

/* ❌ WRONG — standard version stripped by PostCSS */
.glass-card {
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}
```

**Verification:** After build, grep the output CSS:
```bash
grep -o '\.glass-card{[^}]*}' dist/assets/*.css
# Must contain BOTH: -webkit-backdrop-filter AND backdrop-filter
```

**Debugging:** Check computed styles in browser console:
```js
const cs = window.getComputedStyle(document.querySelector('.glass-card'));
console.log('backdropFilter:', cs.backdropFilter); // Must NOT be "none"
```

## Stacking Context Rules

`backdrop-filter` only blurs content **within the same stacking context**. Key implications:

- Video at `z-index: -10` → cards at normal flow → **blur does NOT work**
- Video at `z-index: 0` + cards in `position: relative; z-index: 10` wrapper → **blur works**
- `backdrop-filter` itself creates a new stacking context

**Rule of thumb:** Background element and blurred element must share a parent stacking context, or the background must be at a higher z-index than the blur target.

## Nezha-Style Frosted Glass (Reference Implementation)

From inspecting nezha.probes.cc:
```css
/* Background layer */
.bg-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
  background-image: url(...);
  filter: brightness(0.75);
}

/* Card */
.card {
  position: relative;
  background: rgba(0, 0, 0, 0.22);
  -webkit-backdrop-filter: blur(6px);
  backdrop-filter: blur(6px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  overflow: hidden;
}
```

- Background is `z-index: 0` (NOT negative)
- Body has solid dark background as fallback
- Cards use dark semi-transparent overlay + small blur
- The magic is in the **background image + brightness filter**, not in extreme blur values

## Blur Value Guidelines

| Effect | blur() | background | Notes |
|--------|--------|------------|-------|
| Subtle glass | blur(4-6px) | rgba(0,0,0,0.2) | Nezha style, needs good bg image |
| Medium glass | blur(12-20px) | rgba(0,0,0,0.3-0.4) | General use |
| Strong glass | blur(40-80px) | rgba(0,0,0,0.5-0.7) | Heavy frosted effect |
| Light wallpaper glass | blur(60-80px) | rgba(255,255,255,0.03-0.05) | Near-invisible base, wallpaper clearly visible |
| Dark wallpaper glass | blur(60-80px) | rgba(255,255,255,0.08-0.12) | Dark wallpaper absorbs white tint — 3-5% looks like solid black, need 8-12% for visible glass |

**暗壁纸关键：** 4% 白底在 luma ~23 的壁纸上看起来是纯黑实心，视觉上像没有毛玻璃。至少需要 **8-10%** 才能在暗色背景上显出玻璃效果。

**Key insight:** Higher blur + lighter background ≠ better frosted glass. The nezha dashboard uses only `blur(6px)` with a dark background and it looks amazing because the background image is well-chosen.

## Video Background + Glassmorphism

```tsx
// Background.tsx — video must be at z-index 0 or higher, NOT -10
<video
  autoPlay loop muted playsInline
  src="/wallpaper.mp4"
  className="fixed inset-0 w-full h-full object-cover"
  style={{ zIndex: 0, filter: 'brightness(0.75)' }}
/>

// App wrapper must be above the video
<div style={{ position: 'relative', zIndex: 10 }}>
  {/* cards go here */}
</div>
```

## Transparent Navbar / Footer

```tsx
// Remove sticky, remove background
<header className="relative z-10">  {/* NOT sticky top-0 */}
  ...
</header>

// Footer — no border, no background
<footer style={{ background: 'transparent' }}>
```

## Glass Button Hover — No Solid Color

User preference: glass buttons should NOT show a solid/dark background on hover. Use subtle glow instead:

```css
/* ✅ Subtle glow, no solid fill */
.glass-btn:hover {
  background: rgba(255, 255, 255, 0.12);
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 0 12px rgba(255, 255, 255, 0.1);
  transform: none; /* no translateY bounce */
}

/* ❌ Too dark / solid on hover */
.glass-btn:hover {
  background: rgba(255, 255, 255, 0.14);
  transform: translateY(-1px);
}
```

## Glass Input Hover

```css
.glass-input {
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  transition: all 0.3s;
}

.glass-input:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.15);
}
```

## Expandable Search Box Pattern

Icon button → expanded input with smooth width transition. The button ITSELF becomes the search box (not a separate element).

**CRITICAL**: CSS classes like `glass-input` have `border-radius: 12px` which **overrides inline styles** in some build setups. For true capsule shape, use **pure inline styles** — do NOT mix with CSS classes on the same element.

```tsx
// ✅ CORRECT — pure inline styles, no CSS class on wrapper
<div
  ref={wrapperRef}
  style={{
    display: 'inline-flex',
    alignItems: 'center',
    height: '2.25rem',
    width: searchOpen ? '14rem' : '2.25rem',
    borderRadius: '9999px',  // ALWAYS 9999px, not 50%
    background: 'rgba(255, 255, 255, 0.06)',
    backdropFilter: 'blur(20px)',
    WebkitBackdropFilter: 'blur(20px)',
    border: '1px solid rgba(255, 255, 255, 0.1)',
    cursor: 'pointer',
    overflow: 'hidden',
    flexShrink: 0,
    transition: 'width 0.3s cubic-bezier(0.4, 0, 0.2, 1), background 0.3s, border-color 0.3s',
  }}
  onClick={() => { if (!searchOpen) setSearchOpen(true) }}
>
  <SearchIcon style={{ width: '1rem', height: '1rem', color: 'rgba(255,255,255,0.5)' }} />
  <input
    ref={inputRef}
    type="search"
    placeholder="搜索节点…"
    value={query}
    onChange={e => onQuery(e.target.value)}
    style={{
      flex: 1, minWidth: 0,
      opacity: searchOpen ? 1 : 0,
      background: 'transparent', border: 'none', outline: 'none',
      color: '#fff', fontSize: '0.875rem',
      transition: 'opacity 0.15s ease 0.15s',
    }}
  />
</div>

// ❌ WRONG — glass-input class overrides border-radius
<div className="glass-input inline-flex h-9 items-center" style={{ borderRadius: '9999px' }}>
```

Key: click outside to close, focus after animation ends (`setTimeout 300ms`), clear query on close.

## Circular Glass Elements

For pill/capsule shape on non-square elements: `borderRadius: '9999px'` (NOT `'50%'` — `50%` on non-square creates ellipse, not capsule).

For perfect circles on square elements: `borderRadius: '50%'` works fine.

**Always use pure inline styles** for capsule/circular glass elements. CSS classes like `glass-input` have `border-radius: 12px` that silently overrides inline styles in some build toolchains.

```tsx
// ✅ Capsule container — inline styles only
<div style={{
  borderRadius: '9999px',
  background: 'rgba(255, 255, 255, 0.06)',
  backdropFilter: 'blur(20px)',
  WebkitBackdropFilter: 'blur(20px)',
  border: '1px solid rgba(255, 255, 255, 0.1)',
}}>
  {/* circular inner buttons */}
  <button style={{ borderRadius: '50%', width: '2rem', height: '2rem' }}>...</button>
</div>
```

## Footer Z-Index with Fixed Video

Footer needs explicit z-index when video is `fixed inset-0 z-index: 0`:
```tsx
<footer style={{ background: 'transparent', position: 'relative', zIndex: 10 }}>
```

## Nezha-Style Table Layout (哪吒探针)

For server monitoring table views — each row is a flex container, NOT an HTML `<table>`:

```
[StatusDot] [Flag] [Name+Virt]  |  [系统] [运行时间] [CPU] [内存] [存储] [上传] [下载]
     ~180px fixed left           |  divider   ~9 columns via CSS Grid
```

Key specs:
- Left: `minWidth: 180px, maxWidth: 220px` — status dot, flag, name (12px bold), virt (10px)
- Divider: `width: 1px, background: rgba(255,255,255,0.1)`
- Right: `display: grid; grid-template-columns: repeat(9, 1fr); gap: 8px`
- Each cell: label (10px, gray) on top, value (11px, white monospace) below
- **No progress bars** in table view — pure text for compactness
- Card: `padding: 10px 14px; borderRadius: 16px; background: rgba(0,0,0,0.22); boxShadow: 0 4px 12px rgba(0,0,0,0.24)`
- Row gap: `10px`
- Labels: tags (9px, colored backgrounds for bandwidth/traffic/IP types)

## View Switching Animation

For sliding between card/table views with translateX:

```tsx
// Container must be position: relative, overflow: hidden
<div style={{ position: 'relative', overflow: 'hidden' }}>
  {/* Cards: slide left when inactive */}
  <div style={{
    transition: 'transform 0.35s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.35s',
    transform: view === 'cards' ? 'translateX(0)' : 'translateX(-100%)',
    opacity: view === 'cards' ? 1 : 0,
    position: view === 'cards' ? 'relative' : 'absolute',
    width: '100%',
    pointerEvents: view === 'cards' ? 'auto' : 'none',
  }}>...</div>
  {/* Table: slide right when inactive */}
  <div style={{
    transform: view === 'table' ? 'translateX(0)' : 'translateX(100%)',
    // ...same pattern
  }}>...</div>
</div>
```

Inactive view must be `position: absolute` so it doesn't take space.

## Apple Squircle / 超椭圆圆角

CSS `border-radius` 生成的是**圆弧**（G1 连续），Figma 的 corner smoothing 和 iOS app icon 用的是**超椭圆曲线**（G2 连续）。视觉上超椭圆更平滑自然。

### Chrome 原生方案（推荐）

Chrome 139+ (2025-08) 支持 CSS 原生 `corner-shape: squircle`：

```css
.card {
  border-radius: 16px;
  corner-shape: squircle;  /* Chrome 139+ */
}
```

作为渐进增强使用：
```css
@supports (corner-shape: squircle) {
  .sq-card { corner-shape: squircle; }
}
```

### 各尺寸下 border-radius vs squircle 差异

| cornerRadius | 差异 | 建议 |
|-------------|------|------|
| ≤ 14px | 肉眼不可辨 | 直接用 border-radius |
| 16-24px | 极微 | border-radius + 渐进增强 |
| ≥ 32px | 明显 | 用 squircle |

### 已知问题：SVG clip-path squircle + backdrop-filter 冲突

见 `chrome-backdrop-filter-clip-path-fix` skill 的决策矩阵和完整修复方案。

### 各卡片黄金比例速查

见 `chrome-backdrop-filter-clip-path-fix` skill 的 `references/golden-proportions.md`。

### Squircle Legacy Approach (JS-based, deprecated)

以前用 `@squircle-js/react` 或手动 SVG clip-path 实现 squircle，但现在 CSS 原生支持了。仅在 cornerRadius ≥ 24px **且** 无 strong backdrop-filter 的场景下保留 JS 方案。

## Common Mistakes

1. **`backdrop-filter: none` in computed style** → Tailwind stripped it. Fix ordering.
2. **Blur not visible with Squircle/Clip** → Chrome drops `backdrop-filter` when on the same element as `clip-path`. Fix: separate the glass layer into a child `absolute inset-0` div. See `chrome-backdrop-filter-clip-path-fix` skill for full fix with glass-layer separation, willChange rule, and SquircleClip component code.
3. **Hover effect not working on glass** → After fixing #2 (glass on child div), `group-hover/card:bg-*` on the parent won't reach the child. Use `transition-opacity opacity` with `group-hover:opacity-80` on the glass div instead.
3. **Blur not visible (video z-index)** → Video at wrong z-index. Move to 0.
3. **Dark cards instead of frosted** → `background: rgba(0,0,0,0.6)` too opaque. Use 0.22 like nezha.
4. **Blur on everything** → Put blur only on specific elements, not body/wrapper.
5. **Solid hover on glass buttons** → Use subtle glow, no solid fill.
6. **Footer hidden behind video** → Add `position: relative; zIndex: 10` to footer.
7. **Search box animation janky** → Use `width` transition with `cubic-bezier(0.4, 0, 0.2, 1)`, focus after 300ms delay.
9. **Squircle clip-path + strong backdrop-filter (blur≥40px) edge artifacts** → SVG clip-path clips backdrop-filter's pixel sampling at corners. Even with the "glass layer on child div" fix, very strong blur (80px) shows visible artifacts. **Fix: abandon Squircle clip-path, use CSS `border-radius` + `overflow: hidden` instead.** See `chrome-backdrop-filter-clip-path-fix` skill for full details and the decision matrix.
9. **Table row spacing not working** → If `.table-view` gap doesn't apply, add `display: flex; flex-direction: column; gap: Xpx` to `.table-body` container.
10. **Capsule shape not working** → Use `borderRadius: '9999px'` (NOT `'50%'`) for non-square elements. Always use pure inline styles for capsule glass elements.

## User Preferences

- **Dark glassmorphism**: Prefer `rgba(0,0,0,0.35)` for dark glass, not light themes
- **Nezha-style blur**: `blur(6px)` + `rgba(0,0,0,0.22)` works better than high blur values
- **Video z-index**: Video must be at `z-index: 0` or higher, NOT negative
- **Capsule shapes**: `borderRadius: '9999px'` for non-square, `borderRadius: '50%'` for squares
- **Pure inline styles**: For capsule/circular glass elements, use pure inline styles, no CSS classes
