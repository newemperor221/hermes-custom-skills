# Theme Settings Sub-Object Bug

## Summary
Komari 1.2.0 `/api/public` returns theme settings nested inside `theme_settings` sub-object, but GalaxyGlass theme JS was reading directly from the top-level `siteInfo` object. This meant **admin panel changes never took effect**.

## API Response Format
```json
{
  "status": "success",
  "data": {
    "sitename": "GG 探针",
    "theme": "GalaxyGlass",
    "theme_settings": {           ← settings are HERE, not at top level
      "blurValue": 20,
      "buildTime": "2026-05-01",
      "posterUrl": "https://...",
      "videoUrl": "https://..."
    }
  }
}
```

## The Bug (lines 1698-1711 in index.html)
```javascript
// ❌ WRONG — reads from top level
const siteInfo = await fetchSiteInfo();
poster.src = siteInfo.posterUrl || 'hardcoded-fallback';   // undefined → always fallback
const blur = siteInfo.blurValue || 20;                      // undefined → always 20

// ✅ CORRECT — reads from theme_settings sub-object
const ts = siteInfo.theme_settings || {};
poster.src = ts.posterUrl || 'hardcoded-fallback';
const blur = ts.blurValue || 20;
```

## SITE_START was also hardcoded
```javascript
// ❌ WRONG — const, never read from API, couldn't be changed
const SITE_START = new Date('2026-05-01T21:34:00+08:00').getTime();

// ✅ CORRECT — let, updated from API in init()
let SITE_START = new Date('2026-05-01T21:34:00+08:00').getTime();
// In init():
if (ts.buildTime) {
  const parsed = new Date(ts.buildTime);
  if (!isNaN(parsed.getTime())) SITE_START = parsed.getTime();
}
```

## Lesson
When theme config changes in admin panel don't take effect, ALWAYS check:
1. API response format: `curl -s http://localhost:25774/api/public | python3 -m json.tool`
2. JS reading path: is the code reading from the right nesting level?
3. Hardcoded fallback: do they override API values?
