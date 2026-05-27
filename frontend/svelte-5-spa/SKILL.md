---
name: svelte-5-spa
description: Build SPAs with Svelte 5, SvelteKit static adapter, Skeleton UI v4, Tailwind CSS v4, and Chart.js — covering runes export restrictions, the object-pattern workaround for module state, component-derived values, and deployment behind a proxy.
category: frontend
triggers: ["svelte", "sveltekit", "svelte 5", "runes", "spa", "skeleton ui", "chart.js svelte", "svelte static adapter"]
---

# Svelte 5 SPA Architecture

## Critical: Module-Level State Export Restrictions

Svelte 5 **forbids** exporting reassignable `$state` or `$derived` from `.svelte.ts` module files. You also cannot `bind:` to an imported state variable. The compiler rejects:

```ts
// ❌ DOES NOT COMPILE
export let count = $state(0);         // "Cannot export state from a module if it is reassigned"
export let doubled = $derived(count * 2); // "Cannot export derived state from a module"
```

```svelte
<!-- ❌ DOES NOT COMPILE -->
<input bind:value={importedSearchQuery} />  <!-- "Cannot bind to import" -->
```

### ✅ Solution: Object Pattern

Put all reassignable state into a single exported object. Access via `state.property`:

```ts
// state.svelte.ts
export const state = $state({
    nodes: [] as NodeType[],
    loading: true,
    searchQuery: '',
    sortMode: 'default' as SortMode,
    filterRegion: null as string | null,
    viewMode: 'grid' as 'grid' | 'table'
});
```

In components, read/mutate via `state.` prefix:

```svelte
<script lang="ts">
    import { state } from '$lib/state.svelte';
</script>

{state.loading}
<button onclick={() => state.filterRegion = 'us'}>Filter</button>
<input bind:value={state.searchQuery} />
```

### ✅ Derived Values in Components, Not Modules

Since `$derived` cannot be exported from modules, compute them in each consuming component:

```svelte
<script lang="ts">
    import { state } from '$lib/state.svelte';
    import type { MergedNode } from '$lib/types';

    let filteredNodes = $derived.by((): MergedNode[] => {
        let list = [...state.nodes];
        if (state.filterRegion) list = list.filter(n => n.region === state.filterRegion);
        if (state.searchQuery) list = list.filter(n => n.name.toLowerCase().includes(state.searchQuery));
        return list;
    });

    let onlineCount = $derived(state.nodes.filter(n => n.online).length);
</script>
```

### ⚠️ What CAN Be Exported from `.svelte.ts`

- **Action functions** that mutate the state object — these compile fine:
```ts
// state.svelte.ts
export function setFilter(region: string | null) { state.filterRegion = region; }
```

- **Pure helper functions** (formatting, math, etc.) — put in a separate `.ts` file (NOT `.svelte.ts`):
```ts
// helpers.ts (plain .ts, no runes)
export function bytes(v: number): string { ... }
export function formatPrice(usd: number): string { ... }
```

## Layout: `@render children()` Replaces `<slot />`

Svelte 5 deprecates `<slot />`. Use the snippet pattern:

```svelte
<!-- +layout.svelte -->
<nav>...</nav>
<main>
    {@render children()}
</main>
<footer>...</footer>
```

## SPA Configuration with SvelteKit

```js
// svelte.config.js
import adapter from '@sveltejs/adapter-static';

const config = {
    compilerOptions: {
        runes: ({ filename }) => (filename.includes('node_modules') ? undefined : true)
    },
    kit: {
        adapter: adapter({
            pages: 'build',
            assets: 'build',
            fallback: 'index.html',   // enables client-side routing
            precompress: false,
            strict: true
        })
    }
};
```

For pages using browser-only APIs (Canvas, fetch, `window`):

```svelte
<script lang="ts">
    export const ssr = false;
</script>
```

## Skeleton UI v4 + Tailwind CSS v4 Setup

```bash
npm create svelte@latest my-app
cd my-app
npm install
npm install -D @skeletonlabs/skeleton @skeletonlabs/skeleton-svelte @skeletonlabs/tw-plugin tailwindcss @tailwindcss/vite chart.js lucide-svelte
```

```css
/* src/routes/+layout.css */
@import 'tailwindcss';
@import '@skeletonlabs/skeleton';
@import '@skeletonlabs/skeleton-svelte';
@import '@skeletonlabs/skeleton/themes/cerberus';
/* or: @import '../my-custom-theme'; */
```

```html
<!-- src/app.html -->
<html data-theme="cerberus">
```

### Custom Glass Presets (add to layout.css)

```css
.preset-glass-bg {
    background: rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(48px) saturate(120%);
    -webkit-backdrop-filter: blur(48px) saturate(120%);
}
.preset-glass-nav {
    background: rgba(255, 255, 255, 0.06);
    backdrop-filter: blur(16px);
}
.card-glow {
    border: 1px solid rgba(16, 185, 129, 0.08);
    box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.04), inset 0 1px 0 rgba(255, 255, 255, 0.03);
    transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1), box-shadow 0.35s ease, border-color 0.3s;
}
.card-glow:hover {
    transform: translateY(-3px);
    box-shadow: 0 24px 64px rgba(0,0,0,0.5), 0 0 0 1px rgba(16,185,129,0.18), 0 0 28px rgba(16,185,129,0.08);
    border-color: rgba(16,185,129,0.22);
}
```

## Chart.js with Svelte 5

Use `$effect` for lifecycle management:

```svelte
<script lang="ts">
    import { Chart, registerables } from 'chart.js';
    Chart.register(...registerables);

    let canvas: HTMLCanvasElement;
    let chart: Chart | null = null;
    let chartData = $state<number[]>([]);

    $effect(() => {
        if (!canvas || chartData.length === 0) return;
        chart?.destroy();
        chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: chartData.map((_, i) => `#${i}`),
                datasets: [{ data: chartData, borderColor: '#10b981', fill: true }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
        return () => chart?.destroy();
    });
</script>
<canvas bind:this={canvas} style="height: 130px;"></canvas>
```

## Deployment: Static Assets Behind a Proxy

When deploying a SvelteKit SPA behind a Python proxy (e.g., galaxy-proxy.py):

1. **The `_app/` directory** must be served as static files with correct MIME types
2. **Add the path** to the proxy's file-serving logic:

```python
# In do_GET handler — ADD `_app/` to static file serving:
if clean_path.startswith("/styles/") or clean_path.startswith("/scripts/") or clean_path.startswith("/_app/"):
    rel = clean_path.lstrip("/")
    return self._serve_static(rel)
```

3. **Fallback for client-side routing**: All non-file, non-API paths should serve `index.html`

## Custom Theme File Structure

```css
/* galaxy-glass-theme.css */
[data-theme='galaxy-glass'] {
    --color-primary-500: #10b981;
    --color-secondary-500: #818cf8;
    --color-surface-500: #080b18;
    --color-surface-950: #010103;
    --body-background-color: #080b18;
    --body-background-color-dark: #020203;
    --radius-base: 6px;
    --radius-container: 16px;
}
```

## Pitfalls

- **`export const state = $state(...)` MUST use `const`** — `let` with reassignment won't work for exports
- **Do NOT destructure `state` in components** — `const { nodes, loading } = state` breaks reactivity. Always use `state.nodes`, `state.loading`
- **`bind:value` on imported state works** when it's a property of the exported object (e.g., `bind:value={state.searchQuery}`)
- **Chart.js canvas bindings**: Use `let canvas: HTMLCanvasElement | undefined = $state()` for `bind:this` to work correctly
- **`ssr = false` pages**: Set this on any page using browser globals or Canvas to prevent SSR errors
- **Skeleton v4 uses Tailwind v4** — no `tailwind.config.js`. All theme is CSS-based via `@import` and `@theme` directive
