---
name: frontend-workflows
description: Modern frontend development workflows — Svelte 5 SPAs, npm-to-browser conversion, and Glass Komari theme engineering. Use this umbrella skill when you need to build, deploy, or maintain any frontend project covered by its subsections.
triggers: ["svelte", "sveltekit", "runes", "npm package to browser", "glass theme", "komari theme", "frontend build", "spa deployment", "galaxy-glass"]
---

# Frontend Workflows

This umbrella skill covers three distinct frontend engineering patterns. Each subsection links to a reference file with full details.

## 1. Svelte 5 SPAs with SvelteKit Static Adapter

See `references/svelte-5-spa.md` for complete guide on:
- Module-level state export restrictions and the object pattern workaround
- `@render children()` replacing `<slot />`
- Skeleton UI v4 + Tailwind CSS v4 setup
- Chart.js integration with `$effect`
- Deployment behind a Python proxy (adding `_app/` to static routes)

**Quick start:**
```bash
npm create svelte@latest my-app
cd my-app
npm install -D @skeletonlabs/skeleton @skeletonlabs/skeleton-svelte @skeletonlabs/tw-plugin tailwindcss @tailwindcss/vite chart.js lucide-svelte
```

## 2. npm Package to Browser Script

See `references/npm-package-to-browser.md` for extracting core logic from CJS/ESM npm packages and adapting it as a standalone browser script. Covers IIFE wrapping, tagged template literal pitfalls, and integration with SVG clipPath + backdrop-filter.

## 3. Glass Komari Theme Engineering

See `references/glass-workflow.md` for the complete Glass (formerly GalaxyGlass) theme workflow:
- Source structure (`src/`, ITCSS layers, fonts/, video/)
- Build script (`build.sh`), deploy script (`deploy.sh`), release script (`release.sh`)
- Komari official theme packaging specs (`komari-theme.json`, `dist/index.html`)
- Critical pitfalls: zip nesting, `_next/` asset path conflict, font self-hosting, video wallpapers (WebM only), Cloudflare cache bypass
- Managed configuration via `theme_settings` (page title, footer uptime template)
- Deployment on two VPS (CCS LA + Poland) with galaxy-proxy.py

**Quick build:**
```bash
./build.sh          # compile to single index.html
./deploy.sh         # build + deploy to both servers
./release.sh v1.x.x # build + package + GitHub release
```

## Decision Tree

| What you need | Go to subsection |
|---------------|------------------|
| Build a Svelte 5 SPA with Skeleton UI and Chart.js | Section 1 |
| Convert an npm package to a standalone browser script | Section 2 |
| Develop or deploy the Glass Komari monitoring theme | Section 3 |

## Cross-cutting Concerns

### Deployment Behind a Proxy
All three workflows may need to serve static assets behind a Python reverse proxy (e.g., galaxy-proxy.py). For any frontend that generates an `_app/`, `_astro/`, or `_next/` directory, you must add that path to the proxy's static file routing. See `references/static-asset-proxy.md` for a generic proxy configuration template.

### Video Assets
Glass theme uses self-hosted WebM wallpapers. See Section 3 for MIME type configuration and proxy routing.

## Migration Note

This umbrella skill consolidates three previously separate skills:
- `svelte-5-spa` (archived)
- `npm-package-to-browser` (archived)
- `glass-workflow` (archived)

Their original reference files are now stored in `references/` under this skill directory. The full content has been preserved exactly.
