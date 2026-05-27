# Online Count Tab Heartbeat Implementation (2026-05-16)

## Background
The original online count used `SELECT COUNT(*) FROM sessions WHERE latest_online > datetime('now', '-30 minutes')`. This counted unique login sessions — opening multiple tabs in the same browser didn't increase the count (same session cookie).

The user expected: open more tabs → count increases.

## Failed Attempt: WebSocket Connection Counter

Changed `_handle_online_count` to return `len(proxy._ws_connections)` — a counter incremented/decremented in the `_ws()` method on WS connect/disconnect.

**Result: Disaster.** Showed 10→12 "people" when only 1 user opened 1 tablet. Why? GalaxyGlass frontend uses 100% HTTP fetch() — NO WebSocket. The proxy's WS connections are all Komari Agent connections (probe data reporting), not human viewers.

## Final Solution: Tab UUID Heartbeat

### Server Side (galaxy-proxy.py)

Global tab tracker with TTL:
```python
import time, threading

TAB_TTL = 90
_tabs = {}
_tabs_lock = threading.Lock()

def tab_heartbeat(tab_id):
    with _tabs_lock:
        _tabs[tab_id] = time.monotonic()

def tab_purge():
    now = time.monotonic()
    cutoff = now - TAB_TTL
    with _tabs_lock:
        dead = [tid for tid, ts in _tabs.items() if ts < cutoff]
        for tid in dead:
            del _tabs[tid]
        return len(_tabs)
```

`do_GET` routing parses `?t=` query param:
```python
if clean_path == "/api/proxy/online-count":
    qs = parse_qs(parsed.query)
    tab_id = qs.get("t", [None])[0]
    return self._handle_online_count(tab_id)
```

### Frontend (scripts/data.js)

Per-tab UUID in sessionStorage:
```js
var _tabId = sessionStorage.getItem('gg-tab') || crypto.randomUUID();
sessionStorage.setItem('gg-tab', _tabId);

async function refreshOnline() {
  var oc = await fetchJSON('/api/proxy/online-count?t=' + _tabId);
  ...
}
```

`sessionStorage` is per-tab — same tab on refresh keeps the UUID; new tab generates a new one.

### Lifecycle
1. Open tab → UUID generated → stored in sessionStorage → heartbeated to server → `{"online": N+1}`
2. Refresh tab → same sessionStorage → same UUID → count unchanged
3. Close tab → 90s TTL expires → auto-purge → count -1
4. New tab → new UUID → count +1

### TTL Design
- Frontend polls every 60s (`setInterval(refreshOnline, 60000)`)
- Server TTL = 90s (allows 1 missed heartbeat)
- If tab closes between polls, it takes at most 90s to decrement

### Key Lesson: Know Your Protocol!
- GalaxyGlass: **HTTP fetch() only** — no WebSocket, no EventSource
- Komari Agent connections: **WebSocket** (for real-time data push)
- NEVER mix agent WS connections with human viewer counting
- Before implementing any "connection count" feature, audit the frontend's actual transport: `grep -E 'WebSocket|EventSource|new WebSocket'` on all JS files
