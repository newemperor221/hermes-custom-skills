---
name: npm-package-to-browser
title: Porting npm packages to vanilla browser scripts
description: >-
  Extract core logic from CJS/ESM npm packages and adapt it as a standalone
  browser script for vanilla HTML/JS projects. Covers IIFE wrapping, tagged
  template literal pitfalls, and integration with SVG clipPath + backdrop-filter.
category: frontend
---

# Porting npm packages to the browser

When you need an npm package's algorithm but can't use a bundler (vanilla HTML/JS), port the core logic to a standalone script.

## General approach

1. **Download the package**:
   ```bash
   npm pack <package>
   tar xzf <package>.tgz
   ```

2. **Read the entry point** (from `package.json`'s `"main"` field). CJS dist files are generally straightforward.

3. **Wrap in an IIFE** that attaches the API to `window`:
   ```js
   (function(global) {
     // ... original code ...
     global.exportedFunction = exportedFunction;
   })(window);
   ```

4. **Watch for `export` statements** — CJS uses `module.exports` or `export { ... }`. Replace with `global.xxx = xxx`.

5. **Watch for tagged template literals** (see pitfall below).

## Pitfall: `rounded` tagged template (figma-squircle)

The `figma-squircle` library uses a `rounded` tagged template literal to format SVG path numbers with `.toFixed(4)`. **Do NOT replace it with array-based function calls** — the tagged template's `strings.length === values.length + 1` invariant is easy to break. Instead:

**Safe replacement (direct string concatenation)**:
```js
function f4(x) { return x.toFixed(4); }

function drawCorner(params, corner) {
  if (!params.cornerRadius) return 'l ' + params.p.toFixed(4) + ' 0';
  var a = params.a, b = params.b, c = params.c, d = params.d;
  var cr = params.cornerRadius, arc = params.arcSectionLength;
  var a4 = f4, ab = a + b, abc = a + b + c, bc = b + c;
  switch (corner) {
    case 'topRight':
      return 'c ' + a4(a) + ' 0 ' + a4(ab) + ' 0 ' + a4(abc) + ' ' + a4(d) +
        ' a ' + a4(cr) + ' ' + a4(cr) + ' 0 0 1 ' + a4(arc) + ' ' + a4(arc) +
        ' c ' + a4(d) + ' ' + a4(c) + ' ' + a4(d) + ' ' + a4(bc) + ' ' + a4(d) + ' ' + a4(abc);
    // ... other corners follow the same pattern with signs flipped ...
  }
}
```

**TL;DR**: Just use string concatenation with a helper. Don't try to reimplement the tagged template combinatorics — the string alignment is too error-prone.

## Using figma-squircle in vanilla JS

After porting, integrate on your page:

```js
function applySquircles() {
  var cards = document.querySelectorAll('.node-card, .stat-card, .metric-card, .chart-card');
  if (!cards.length) return;

  var defs = document.querySelector('svg#sq-defs defs') || (function(){
    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.id = 'sq-defs';
    svg.style.cssText = 'position:absolute;width:0;height:0';
    svg.setAttribute('aria-hidden', 'true');
    var d = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
    svg.appendChild(d);
    document.body.prepend(svg);
    return d;
  })();

  var existing = defs.querySelectorAll('[id^="sq-dyn-"]');
  for (var i = 0; i < existing.length; i++) defs.removeChild(existing[i]);

  cards.forEach(function(card, idx) {
    var w = card.offsetWidth, h = card.offsetHeight;
    if (!w || !h) return;
    var rad = card.classList.contains('node-card') || card.classList.contains('chart-card') ? 16 : 12;
    var path = getSvgPath({ width: w, height: h, cornerRadius: rad, cornerSmoothing: 1 });
    var id = 'sq-dyn-' + idx;
    var clip = document.createElementNS('http://www.w3.org/2000/svg', 'clipPath');
    clip.id = id;
    clip.setAttribute('clipPathUnits', 'userSpaceOnUse');
    var pathEl = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    pathEl.setAttribute('d', path);
    clip.appendChild(pathEl);
    defs.appendChild(clip);
    card.style.clipPath = 'url(#' + id + ')';
  });
}
```

**Key points:**
- `clipPathUnits="userSpaceOnUse"` — coordinates are relative to the referencing element (the card), not the SVG. So the path can use absolute pixel coordinates from the card's `offsetWidth`/`offsetHeight`.
- Call with a small delay after render (50-60ms) to ensure layout is complete.
- Debounce resize handler to regenerate on window resize.
- `backdrop-filter` works inside `clip-path: url(#...)` in modern Chrome.

## Calling after dynamic render

In a page where cards are rendered via `innerHTML`:

```js
setTimeout(applySquircles, 50);
```

For detail views that render separately, add a parallel call after that render completes.

## Caching note

If the page is behind Cloudflare/cloudflared, the old HTML (without the script tag) may be cached. Append `?_cb=N` to bust cache, or update the proxy to set `Cache-Control: no-cache`.
