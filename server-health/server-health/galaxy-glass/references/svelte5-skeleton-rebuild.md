# GalaxyGlass v3: Svelte 5 + Skeleton UI Rebuild

## Stack
- **Svelte 5** (runes mode: $state, $derived, $effect)
- **SvelteKit** + `@sveltejs/adapter-static` (fallback: index.html)
- **Skeleton UI v4** (`@skeletonlabs/skeleton` + `@skeletonlabs/skeleton-svelte` + `@skeletonlabs/tw-plugin`)
- **Tailwind CSS v4** (`@tailwindcss/vite`)
- **Chart.js** + `registerables` for real-time line charts
- **Lucide Svelte** for SVG icons

## Svelte 5 Runes Module Pattern (Critical)

Svelte 5 forbids exporting reassignable `$state` or `$derived` from `.svelte.ts` modules directly.

### DO: Object pattern
```ts
// state.svelte.ts
export const state = $state({
    nodes: [] as MergedNode[],
    loading: true,
    searchQuery: '',
    viewMode: 'grid' as 'grid' | 'table'
});
```

### DON'T: Individual exports
```ts
// ❌ Cannot export reassignable $state
export let nodes = $state([]);
export let loading = $state(true);
```

### Derived values go in components, NOT modules
```ts
// +page.svelte — $derived works fine here
let filteredNodes = $derived.by(() => {
    let list = [...state.nodes];
    // filter/sort logic...
});
```

### State mutation in components: use `state.property = value`
```svelte
<button onclick={() => state.filterRegion = null}>
<input bind:value={state.searchQuery}>
```

## Cloudflare Cache Pitfalls (galaxy-proxy.py)

The `galaxy-proxy.py` Python proxy serves static files from `/opt/komari/data/theme/`.

### 1. Proxy must handle `/_app/` static paths
The default proxy only catches `/styles/` and `/scripts/`. Add:
```python
if clean_path.startswith("/styles/") or clean_path.startswith("/scripts/") or clean_path.startswith("/_app/"):
    rel = clean_path.lstrip("/")
    return self._serve_static(rel)
```

### 2. Cloudflare caches wrong Content-Type
- When proxy returns wrong Content-Type for JS (text/html instead of text/javascript), Cloudflare caches it
- Subsequent requests get cached wrong MIME → `import()` fails with "Failed to fetch dynamically imported module"
- `fetch()` works but `import()` doesn't — because `import()` checks MIME strictly

### 3. Relative imports don't carry query strings
- `?v=3` on `start.js` doesn't propagate to `../chunks/foo.js` imports
- Cache-busting via query params on `<script>` tags is useless for ES module chains

### 4. Fix: rename `_app` to `_app2` for full cache bust
- Server: `mv _app _app2` 
- All HTML refs: `/ _app/` → `/_app2/`
- Proxy: add route for `/_app2/` → strip prefix, serve from `_app/` on disk
```python
if clean_path.startswith("/_app2/"):
    rel = "_app/" + clean_path[7:]  # rewrite _app2 -> _app
    return self._serve_static(rel)
```

### 5. MIME headers to set in proxy
```python
ct_map = {
    ".css": "text/css",
    ".js": "application/javascript",
    ".html": "text/html",
    ".json": "application/json",
    ".svg": "image/svg+xml",
    ".png": "image/png"
}
# Also set these:
self.send_header("X-Content-Type-Options", "nosniff")
self.send_header("Content-Type", ct + "; charset=utf-8")
```

## Deployment Flow
1. `npm run build` → outputs to `build/`
2. Tar `build/` → scp to server → extract to `/opt/komari/data/theme/`
3. Kill old `galaxy-proxy.py` → start new one
4. If Cloudflare has stale cache: rename `_app` → `_app2` (step 4 in the fix above)
5. Verify: open in browser, check console for no errors

## Component Architecture
```
+layout.svelte          # Wallpaper, navbar, footer, back-to-top
+page.svelte            # Dashboard: stats grid + filters + card/table grid
detail/[uuid]/+page.svelte  # Detail: metrics cards + 3 Chart.js charts + sysinfo
```
All state lives in `$lib/state.svelte.ts`. Derived/filtered state is computed via `$derived` inside consuming components.
