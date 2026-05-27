# GalaxyGlass Code Audit Checklist

Generated 2026-05-19 from full code review of Astro 5 + React Islands v3.

## Critical (P0 — breaks functionality)

| Check | Look for | Fix |
|-------|----------|-----|
| `QueryClientProvider` stability | `new QueryClient(...)` in JSX | Use `useState(() => new QueryClient(...))` |
| Link paths for Astro output | `/detail?uuid=xxx` | Must be `/detail/?uuid=xxx` (trailing slash) |
| NodeCard link href | `href="/detail?...` | Should be `href="/detail/?uuid=..."` |
| DetailContent node fetch | `fetchNodes().find(...)` | O(n) — fetches ALL nodes for one UUID |

## Important (P1 — visual/code quality)

| Check | Look for | Fix |
|-------|----------|-----|
| Unused imports | `Gauge`, unused Lucide icons | Remove them |
| Unused variables | `c()` helper, `siteInfo` in DetailContent | Remove or use |
| Sysinfo row padding | `px-[2px]` | Change to `px-[14px]` for breathing room |
| CSS double load | Open Props via both `@import` and CDN `<link>` | Remove CDN link |
| DOM access fragility | `getElementById("detail-poster")` | Replace with `useRef` |
| ViewMode toggle | `viewMode` state has setter but no UI | Add grid/table switch or remove state |
| CSS variable vs hardcode | `--glass-saturate` defined but `saturate(180%)` hardcoded everywhere | Use the variable |

## Nice-to-have (P2 — enhancement)

| Check | Look for | Fix |
|-------|----------|-----|
| Skeleton loading | Only spinner, no content skeleton | Add skeleton cards matching real card shape |
| Error boundaries | No React ErrorBoundary wrapper | Wrap each island with error boundary |
| Entry animations | Only stat cards have `animate-fade-in` | Apply to grid/table too |
| Time labels unused | `timeStart`/`timeEnd` passed but UPlotChart ignores | Remove from props or implement |
| Tailwind + inline style mix | Both patterns in same component | Pick one (prefer Tailwind classes) |
| 404/500 states | No degraded state for server errors | Add structured error UI with retry |

## Deployment checks

| Check | Verify |
|-------|--------|
| Build succeeds | `pnpm astro build` exits 0 |
| `/detail/?uuid=xxx` works | Browser navigate and verify content renders |
| No Open Props CDN request | Network tab should NOT show `open-props/normalize.min.css` |
| Bundle size | DashboardContent < 10KB gzip, DetailContent < 30KB gzip |
| All links work | Click NodeCard → detail page, back button → home |
