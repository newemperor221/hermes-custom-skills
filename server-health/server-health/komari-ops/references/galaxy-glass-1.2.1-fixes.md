# GalaxyGlass v1.2.1 Bug Fixes (2026-05-10)

## Fix 1: Theme Settings Read from Wrong Path

**Bug**: `/api/public` returns theme settings nested in `theme_settings` sub-object, but JS read from top-level `siteInfo`. Result: admin panel changes to videoUrl/posterUrl/blurValue never took effect.

**Fix**: Read `siteInfo.theme_settings.*` instead of `siteInfo.*`.

See `references/theme-settings-subobject-bug.md` for API response format and code diff.

## Fix 2: Mobile Search Toggle Non-Functional

**Bug**: `#mobile-search` input was `hidden` by default with no button to toggle it. The click handler was attached to the hidden element itself — user couldn't trigger it.

**Fix**: Added a `#mobile-search-btn` (round icon button) visible only on mobile (<640px). Clicking it toggles the full-width search input. Clicking again closes and clears search. Also hid the old desktop `.search-box` on mobile to avoid two redundant search icons.

```css
@media (max-width: 639px) {
  #mobile-search-btn { display: inline-flex !important; }
  .search-box { display: none !important; }
}
```

## Fix 3: Scroll Detection via setInterval Polling

**Bug**: `setupScroll()` used `setInterval(..., 100)` to poll `window.scrollY` every 100ms. Wasteful CPU. Also conflicted with separate `scroll` event listener in `setupRouter()`.

**Fix**: Replaced with passive scroll event + requestAnimationFrame throttling:

```javascript
window.addEventListener('scroll', () => {
  if (!scrollTicking) {
    window.requestAnimationFrame(() => {
      // update navbar scrolled class + back-to-top visibility
      scrollTicking = false;
    });
    scrollTicking = true;
  }
}, { passive: true });
```

## Fix 4: Footer Uptime Updated Every Second

**Bug**: `setInterval(updateFooterUptime, 1000)` — ran date math + DOM update every second for a footer display nobody reads precisely.

**Fix**: Changed to 60-second interval:

```javascript
setInterval(updateFooterUptime, 60000);
```

## Fix 5: Detail View Fetched All Nodes on Every Open

**Bug**: `loadDetailData()` called `fetch('/api/nodes')` + `fetch('/api/recent/' + uuid)` every time a card was clicked. N+1 API calls per detail view open.

**Fix**: Try `nodesList` cache first. If node found in cache, only fetch `/api/recent/{uuid}`. Fall back to full fetch if not cached. Reduces detail view API calls from 16 to 1 (for 15-node setup).

## Fix 6: BuildTime Hardcoded as const, Never Read from API

**Bug**: `const SITE_START = new Date('2026-05-01T21:34:00+08:00').getTime();` — hardcoded at module level, never updated from `/api/public`'s `theme_settings.buildTime`.

**Fix**: Changed `const` to `let`, updated in `init()` from `siteInfo.theme_settings?.buildTime`. See `references/theme-settings-subobject-bug.md`.

## Fix 7: Asset Calculation Overhaul (月度开销/剩余折旧)

**Bug**: `totalValue = Σ(price)` — summed raw prices regardless of billing cycle. `billing_cycle=0` (永久) parsed as `parseInt(0) || 30` = 30 days. Monthly servers without `expired_at` never depreciated.

**Fix**: `monthlyPrice()` and `remainingPrice()` functions. Exchange rate default 6.84→7.24. Labels: 总资产/剩余资产 → 月度开销/剩余折旧.

## Fix 8: Cloudflare HTML Caching

**Bug**: After deploying new `index.html` via scp, Cloudflare continued serving old cached version for minutes/hours.

**Fix**: Three-layer approach:
1. Version comment in HTML: `<!-- GalaxyGlass v1.2.1-cfN -->` (change N each deploy)
2. Cache-Control meta tags in `<head>`
3. User hard-refresh: `Ctrl+Shift+R`
