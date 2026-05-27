# Static Version → Astro Style Port (2026-05-19)

## What was ported

The static HTML version (`~/galaxy-glass/index.html`) had a well-developed CSS design system with glass blur, pill shapes, gradient accents, and smooth animations. This was ported to the Astro React architecture.

## Key style tokens from static version

```css
--accent:        #10b981
--accent-2:      #818cf8
--accent-gradient: linear-gradient(135deg, #10b981, #818cf8)
--bg-glass:      rgba(255,255,255,0.06)
--glass-strong:  rgba(255,255,255,0.12)
--blur-card:     40px
--blur-surface:  24px
--blur-glass:    60px
--blur-chip:     12px
--glass-border:  rgba(255,255,255,0.10)
```

## Navbar style

- `background: transparent` (not `var(--bg-surface)`)
- All buttons/inputs: `border-radius: var(--radius-full)` (pill shape)
- Glass effect: `background: var(--bg-glass)`, `backdrop-filter: blur(12px)`
- Site title: gradient text via `background: var(--accent-gradient)`, `-webkit-background-clip: text`

## Card/row styling

**NodeCard (grid):** `className="glass-card"` uses CSS class: `backdrop-filter: blur(var(--blur-glass)) saturate(120%)`, with cardIn entrance animation.

**NodeRow (table):** Inline glass style `background:"var(--bg-glass)"`, `backdropFilter:"blur(var(--blur-glass)) saturate(120%)"`, `borderRadius:"var(--radius-md)"`.

**Stat card wrapper:** Same glass blur(12px) style, `borderRadius:"var(--radius-md)"`.

## Filter chips

Pill-shaped container: `borderRadius:"var(--radius-full)"`, glass blur(12px).  
Individual chips: `borderRadius: 8`, active state `rgba(45,158,107,0.10)` background.

## Footer

Gradient site name (`var(--accent-gradient)` + `background-clip: text`), "🛰️ 运行中 🌌" emoji, "Powered by Komari" link.

## Back-to-top button

Circle (`borderRadius:"50%"`), `background:"var(--glass-strong)"`, `backdropFilter:"blur(20px)"`.

## Bars

`height: 6px`, `borderRadius:"var(--radius-full)"`, `transition: transform 0.4s ease` (was `width` before).

## Deployment fix

See main SKILL.md — komari requires subdirectory-based theme deployment.
