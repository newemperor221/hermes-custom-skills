# Astro + TanStack Query: Blank Page Debug Session (2026-05-19)

## Problem
After deploying GalaxyGlass Astro build, the page showed a blank dark screen instead of the monitor dashboard. The browser's title bar showed "银河探针 — Komari Monitor" and navigation elements rendered, but the data area was empty.

## Root Cause (Two independent bugs)

### Bug 1: Wrong deployment path
- Komari's theme system reads from subdirectories, not the root of `/opt/komari/data/theme/`
- The running theme was `GalaxyGlass` (confirmed via API: `"theme":"GalaxyGlass"`)
- Files must go in `/opt/komari/data/theme/GalaxyGlass/dist/`
- deploy.sh was putting files in `/opt/komari/data/theme/` (root) → komari ignored them
- Result: curl to <监控面板域名> returned OLD HTML even though new files existed on disk

**Fix**: Updated deploy.sh to extract into `GalaxyGlass/dist/` subdirectory.

### Bug 2: QueryClientProvider context timing
- `useQuery` calls were in the component function body (top level)
- `<QueryClientProvider>` was in the JSX return
- React executes function body before resolving JSX → context not yet available
- TanStack Query v5 checks for QueryClient via `useContext(QueryClientContext)`
- Context Provider hasn't mounted yet → throws "No QueryClient set"

**Fix**: Split into outer shell (creates QueryClient + renders QueryClientProvider + renders inner component) and inner component (all useQuery hooks). Provider renders first, establishing context before inner component's hooks fire.

## Debugging Steps

### 1. Verify HTML is served correctly
```bash
curl -s https://<监控面板域名>/ | grep -o 'DashboardContent\.\w*'
# If hash is OLD, deployment path is wrong
```

### 2. Check Astro island hydration
```javascript
// In browser console:
document.querySelectorAll('astro-island').forEach(el => {
  console.log(el.getAttribute('uid'), {
    ssr: el.hasAttribute('ssr'),
    component: el.getAttribute('component-url'),
    children: el.children.length,
    html: el.innerHTML.length
  });
});
// ssr=false means hydration ran; children=0+innerHTML=0 means component rendered nothing
```

### 3. Catch silent JS exceptions
```javascript
window.addEventListener('error', function(e) {
  console.log('ERR:', e.message, e.filename, e.lineno);
}, true);
```

### 4. Verify module loading
```javascript
import('/_astro/DashboardContent.XXXX.js').then(m => {
  console.log('Module loaded, exports:', Object.keys(m));
}).catch(e => console.error('Import failed:', e));
```

### 5. Check nested hydration flow
- Outer `<astro-island client="load">` wraps inner `<astro-island client="only">`
- Outer hydrates first, then dispatches `astro:hydrate` event
- Inner needs the event or own `client:only` mechanism
- In headless browser, `customElements.get('astro-island')` should be defined

## Files Changed
- `astro/deploy.sh` — corrected deployment target path
- `astro/src/components/DashboardContent.tsx` — split into DashboardContent + DashboardInner
- `astro/src/components/DetailContent.tsx` — split into DetailContent + DetailInner
