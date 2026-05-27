# Card Design Enhancements (2026-05-19)

Session: user asked to review NodeCard and provide UI improvements, then implement in Next.js.

## Changes made to `/home/woioeow/galaxy-glass/nextjs/src/components/NodeCard.tsx`

### 1. Top Accent Gradient Bar (Shimmer)
- 2px gradient line at top of each online card: `linear-gradient(90deg, #10b981, #818cf8, #10b981)`
- `background-size: 200% 100%` + CSS `@keyframes shimmer` for animated gradient sweep
- Only shows on online cards (offline cards skip it)
- Injected as `<style>` element inside the component (keyframe scoped to component)

```tsx
{!offline && (
  <div className="absolute top-0 left-0 right-0 z-10 h-[2px]"
    style={{
      background: "linear-gradient(90deg, #10b981, #818cf8, #10b981)",
      backgroundSize: "200% 100%",
      animation: "shimmer 3s ease-in-out infinite",
    }}
  />
)}
```

### 2. Offline Card Treatment
- `opacity-55 grayscale-[0.3]` — reduced opacity + partial grayscale filter
- Red "OFFLINE" badge in top-right corner
  - `rgba(239,68,68,0.15)` background + `rgba(239,68,68,0.25)` border
  - `color: var(--color-danger)`
- Offline status dot gets red glow: `shadow-[0_0_6px_rgba(239,68,68,0.3)]`

### 3. Enhanced Glass Shadow
Online cards use:
```
shadow-[0_0_0_1px_rgba(45,158,107,0.06),_inset_0_1px_0_rgba(255,255,255,0.06),_0_8px_32px_rgba(0,0,0,0.25)]
```
- Outer glow: `0 0 0 1px rgba(45,158,107,0.06)` (subtle green border)
- Inner highlight: `inset 0 1px 0 rgba(255,255,255,0.06)` (top light edge)
- Deep shadow: `0 8px 32px rgba(0,0,0,0.25)` (bottom lift)

### 4. Staggered Metric Bar Animation
- Each CPU/MEM/DSK bar has a `delay` prop
- Formula: `0.35 + index * 0.04 + i * 0.06` where `i = 0,1,2` for CPU/MEM/DSK
- This creates a cascading fill effect per card + per metric

```tsx
const metricDelay = (i: number) => 0.35 + index * 0.04 + i * 0.06;
// ...
<MetricRow label="MEM" ... delay={metricDelay(1)} />
```

### 5. Price Tag Enhancement
Replaced the solid gradient background with a translucent glass-style badge:
```tsx
background: "linear-gradient(135deg, rgba(16,185,129,0.15), rgba(129,140,248,0.15))",
border: "1px solid rgba(16,185,129,0.2)",
boxShadow: "0 0 12px rgba(16,185,129,0.08)",
```
- Semi-transparent green-to-purple gradient bg
- Green border with subtle glow effect
- Text color remains `text-text-primary` for contrast

### 6. Tags with Accent Prefix Dot
Each tag pill gained a small green dot prefix:
```tsx
<span className="w-[3px] h-[3px] rounded-full" style={{background:"var(--accent)"}} />
```
- Tag background: `rgba(16,185,129,0.06)`
- Tag border: `1px solid rgba(16,185,129,0.12)`
- Tags gap increased to `gap-1.5` (from `gap-1`)

### 7. Last-Update Time Orange Highlight
When last update is > 2 minutes ago, the timestamp text turns orange:
```tsx
style={{
  color: node.last_update && Date.now() - new Date(node.last_update).getTime() > 120000
    ? "var(--color-accent-orange)" : undefined
}}
```

### 8. Net Row Arrow Enhancement
Network up/down arrows now have `opacity-60` spans rather than raw Unicode characters:
```tsx
<span className="opacity-60">↑</span>
```

### 9. Card Hover Lift
Increased from `y: -3` to `y: -4` for a slightly more pronounced hover effect.

## Files Changed
- `nextjs/src/components/NodeCard.tsx` — all visual changes

## Verification
- `curl -sI https://<监控面板域名>/` returns `HTTP/2 200`
- All `/_next/static/chunks/` assets return 200
- Detail page `/detail` renders correctly
