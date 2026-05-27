# OpenHuman Core — Troubleshooting Reference

## DNS Propagation Check

```bash
dig +short core.yourdomain.com @1.1.1.1
```

Always verify DNS resolves to the correct IP **before** reloading Caddy. Caddy's TLS-ALPN-01 challenge needs the domain to resolve to the server's public IP. Cloudflare-proxied (orange cloud) records break this — use DNS-only (grey cloud) for Let's Encrypt challenges.

## Check Core Process Environment

Verify that the running core has the correct environment variables:

```bash
# Find the core PID
pgrep -x openhuman-core

# Inspect its environment
cat /proc/$PID/environ | tr '\0' '\n' | grep -iE 'BACKEND|OPENHUMAN|CORE_TOKEN|APP_ENV'
```

Critical vars to check:
- `BACKEND_URL=https://api.tinyhumans.ai` — required for GitHub OAuth
- `OPENHUMAN_CORE_TOKEN=<token>` — must match what the desktop client uses
- `OPENHUMAN_APP_ENV=production` (default if unset)

## Verify TLS Certificate

```bash
# Check the certificate chain
curl -s https://core.yourdomain.com:8443/health
echo | openssl s_client -connect core.yourdomain.com:8443 -servername core.yourdomain.com 2>/dev/null | openssl x509 -noout -issuer -subject -dates
```

Expected issuer: `CN = E8` or similar Let's Encrypt CA.  
If issuer shows self-signed, the Caddy config has a manual `tls` directive that should be removed — Caddy auto-provisions Let's Encrypt certs.

## Core Health Check

```bash
# Direct (behind Caddy)
curl -s https://core.yourdomain.com:8443/health
# → {"ok":true}

# Direct (core internal port, from server)
curl -s http://localhost:7788/health
# → {"ok":true}
```

If health returns `{"ok":true}` but the desktop app can't connect, the issue is **client-side configuration**, not the core.

## Desktop App Still Shows "Connecting..."

If the user reports the desktop app is stuck on "connecting" after GitHub login:

1. **The login-screen RPC URL field was missed.** On the login surface, look for a small text input, gear icon, or "Use custom core" / "Advanced" toggle. Enter the RPC URL and token **before** clicking login. The app tries to connect to the configured core URL immediately after GitHub OAuth succeeds, and if the URL was never set (defaulting to `http://127.0.0.1:7788/rpc`), it hangs forever.

2. **If already past the login screen** and stuck in "connecting", close the app, find config that persisted the session, and restart fresh. On Windows, check `%APPDATA%/openhuman/` or `app/.env.local` for persisted RPC URL config.

3. **Token mismatch.** Regenerating `OPENHUMAN_CORE_TOKEN` invalidates every connected client. Update the desktop app's RPC URL config.

## "Switch Mode" Button

Every result screen in `BootCheckGate` has a **Switch Mode** button. It calls:
```typescript
handleSelectRuntime() → resetCoreMode() → clears stored RPC URL, token, cache → returns to picker
```
If the user is stuck on any result screen, tell them to click **Switch Mode** and re-enter Cloud config.

## OAuth Deep Link Redirect Broken (Known Issue)

### Symptoms
- User clicks "Login with GitHub" on the Welcome screen
- Browser opens, GitHub authorization succeeds
- Browser redirects back but the app stays on the Welcome screen showing "Signing you in..." or stuck on "Connecting..."
- Core health is OK, RPC URL+token were correctly configured and tested

### Root Cause
The OAuth flow uses deep links: after GitHub authorization, `api.tinyhumans.ai` redirects to `openhuman://oauth/success?token=<jwt>`. On Windows, this deep link handler is unreliable and the JWT token never reaches the app.

### GitHub Issues Tracking This
- **#1049** — "Re-enable welcome screen OAuth buttons after auth fixes land" (OAuth buttons were previously disabled because of permanent "Connecting..." state)
- **#1985** — "504 Gateway Timeout on api.tinyhumans.ai during OAuth login" (backend timeout)
- **#2020** — "Critical Security and Architecture Concerns Regarding OAuth" (mentions "Redirect to tinyhuman isnt working!")

All three are **open issues** — this is not a configuration error.

### Workarounds
1. Click **Switch Mode** → re-enter Cloud config → re-test → try login again
2. Clear app data via the **error panel button** on the Welcome screen (clears localStorage persisted config)
3. Restart the desktop app and try again
4. **Server-side session injection** — see "Session JWT Recovery Workaround" in the main SKILL.md

### Callback Page Detection

When the user reports the deep link bug, you can curl the `openhuman://` deep link page from the server to confirm, but you need a **fresh** OAuth code — expired state returns `Invalid%20or%20expired%20OAuth%20state`.

```bash
# On the VPS, after user sends the callback URL:
curl -sL "https://api.tinyhumans.ai/auth/github/callback?code=...&state=..."
# Look for: openhuman://#auth/github/success?token=eyJ...
```

The HTML page always contains an `<a>` tag with the deep link target. The token is the `token` query parameter — a JWT (starts with `eyJ`).

#### What to do when the user sends a callback URL

When the user pastes an `api.tinyhumans.ai/auth/github/callback?code=...&state=...` URL from their browser address bar:

1. **The state has already expired.** Do NOT curl this URL expecting a JWT — it will return `Invalid or expired OAuth state`.
2. **Tell the user:** "That's from the address bar, and it's expired. Start a fresh login, authorize, and this time look at the **page content** (not the address bar). There's a **Copy Link** button — click it and paste what it copies."
3. **Use for diagnosis only:** Curling the callback URL from the server shows the page structure, which helps you explain the Copy Link button to the user.
4. **The Copy Link button copies the `openhuman://auth?token=...&key=auth` format** — this is what you need for server-side session injection. The address bar never shows this format.

## Diagnosing by Checking GitHub Issues First

When the user reports a non-obvious problem with the OpenHuman desktop app or core:

1. **Search GitHub issues** before trying any server-side changes:
   ```
   site:github.com/tinyhumansai/openhuman/issues "search terms"
   ```
   OpenHuman is actively developed with frequent releases — many UX/packaging bugs are documented.

2. **Check the source code** of relevant components:
   - `BootCheckGate.tsx` — first-launch flow
   - `Welcome.tsx` — OAuth login screen
   - `configPersistence.ts` — how RPC URL/token are stored
   - GitHub OAuth flow in `src/openhuman/` Rust code

3. **Verify the issue is NOT a known bug** before proposing server-side fixes. The OAuth deep link bug (#1049/#1985/#2020) is the most common false alarm — the core and Caddy are fine, the desktop app's own flow is broken.

## OAuth Account Binding Flows

### If using `BACKEND_URL=https://api.tinyhumans.ai` (default):
GitHub OAuth is handled entirely by the OpenHuman cloud backend. The core **does not need** `GITHUB_CLIENT_ID` or `GITHUB_CLIENT_SECRET`. The login flow goes:

```
Desktop app → Browser → api.tinyhumans.ai → GitHub OAuth → api.tinyhumans.ai issues session JWT → Desktop app stores it
```

### If NOT using cloud backend (self-hosted auth):
Set these env vars on the core:
```
GITHUB_CLIENT_ID=Ov23xxxx
GITHUB_CLIENT_SECRET=<40-char-hex>
```
And configure the GitHub OAuth App callback URL to `http://localhost:7788/oauth/callback` (or `https://core.yourdomain.com:8443/oauth/callback`).
