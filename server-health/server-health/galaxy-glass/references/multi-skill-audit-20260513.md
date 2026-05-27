# GalaxyGlass Multi-Skill Audit — 2026-05-13

## Skills Used
- **ui-ux-pro-max** — 6-domain sweep (product/style/color/ux/chart/typography)
- **taste-skill** — Anti-slop design rules
- **impeccable** — Design audit/lint
- **css-glassmorphism-backdrop-filter** — Glassmorphism implementation pitfalls
- **ui-skills** — WCAG accessibility
- **status-page-customization** — Theme customization patterns

## Audit Findings & Fixes

| Priority | Source | Issue | Fix |
|----------|--------|-------|-----|
| P1 | UI UX Pro Max / Style | bg-deepest too light (#081830 vs recommended #020203) | → #020203 (OLED pure black) |
| P1 | UI UX Pro Max / Typography | System font stack, no Google Fonts | → Fira Code + Fira Sans with `<link>` |
| P1 | UI UX Pro Max / Chart | Streaming charts need pause/resume | → `.chart-pause-btn` + `_chartPaused` override |
| P1 | UI UX Pro Max / UX | No connection status indicator | → `.conn-toast` + fetchJSON override |
| P1 | UI UX Pro Max / Style | No auto-refresh "Live" indicator | → `.live-badge` with pulsing dot |
| P2 | css-glassmorphism | Wallpaper too bright, glass not transparent enough | → `filter: brightness(0.8)` on bg-layer media |
| P2 | ui-skills / WCAG | No keyboard focus styles | → `:focus-visible` global rule |

## Priority System

- **P1 (功能/对比度/交互):** 直接影响用户看数据的能力
- **P2 (无障碍/一致性):** 锦上添花，不影响核心功能

## Execution Order

1. CSS variables (bg colors, fonts, brightness, focus-visible) — fastest, no risk
2. HTML elements (live badge, conn toast, pause buttons) — add markup
3. JS logic (chart pause, connection monitor, live badge) — add to script section

Deploy via: `cat index.html | sshpass ... ssh ... "cat > /opt/komari/data/theme/index.html"`
