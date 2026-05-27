## Debugging in SPA Mode

As of 2026-05-18, <监控面板域名> loads a Vite Svelte SPA (`entry-index-CN3NDSn4.js`) alongside legacy scripts. In this mode, `flagEmoji` is NOT on `window` scope:

```js
typeof window.flagEmoji  // → 'undefined' (function exists but not in global scope)
eval('typeof flagEmoji') // → error: not defined
```

**Workarounds for inspecting flagEmoji at runtime:**

1. **Fetch the source:**
   ```js
   fetch('/scripts/config.js?v=4').then(r=>r.text()).then(t=>{
     let s = t.indexOf('flagEmoji');
     let e = t.indexOf('\n}\n', s);
     console.log(t.substring(s, e+4));
   })
   ```

2. **Override via script injection** (admin API `custom_head`):
   Put the corrected version in a `<script>` tag that runs on every page load.

3. **Check filter button HTML directly:**
   ```js
   [...document.querySelectorAll('.chip')].map(c => c.innerHTML.substring(0,120))
   ```
   This doesn't need flagEmoji access — just reads the rendered DOM.
