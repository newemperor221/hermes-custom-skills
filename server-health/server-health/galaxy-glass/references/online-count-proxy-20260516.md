# Real-time Online Count via Proxy + SQLite

**⚠️ SUPERSEDED — This approach was replaced by Tab UUID Heartbeat (see SKILL.md §实时在线人数).**
The DB session approach counted unique browser sessions (cookies), not open tabs. Opening 5 tabs in Chrome still showed 1. The Tab UUID approach correctly counts each tab independently.

## Context (historical)
2026-05-16: User wanted a real "在线 N 人" pill instead of fake static "在线 1 人". Komari backend stores sessions in SQLite but has no public API for online count.

## Solution (historical)
Add a new endpoint `/api/proxy/online-count` to the Python proxy (`galaxy-proxy.py`), which:
1. Reads the Komari SQLite database (`/opt/komari/data/komari.db`)
2. Counts sessions with `latest_online > datetime('now', '-30 minutes')`
3. Returns `{"online": N}`

## Key Decisions
- **30-minute window** — balances freshness vs stale-session filtering. Komari sessions expire in 30 days so we filter by `latest_online`.
- **Proxy-level endpoint** — no need to modify the Go backend. The proxy already has a pattern for `/api/proxy/exchange-rate`.
- **Inline sqlite3 import** — standard library, no extra deps. Imported at top of proxy.py.
- **Fallback to 1** — if the DB read fails, return `{"online": 1}` so the frontend always shows something.

## Gotchas
- The `_handle_online_count` method must be INSIDE the `PH` class (not at module level) — it's called via `self._handle_online_count()` from `do_GET`. An earlier edit put it outside the class, which caused AttributeError and a silent crash on every request.
- When restarting the proxy, `pkill -f galaxy-proxy` then start a new one. If the old process holds the port, the new one silently exits without printing an error (unless you pipe stderr).
- The frontend JS (`data.js`) calls `fetchJSON()` which silently returns `null` on network error — the pill just won't update, no user-visible error.
