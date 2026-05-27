---
name: openhuman-core-deployment
category: devops
description: Deploy headless OpenHuman core (openhuman-core) on a VPS with Caddy reverse proxy, Let's Encrypt TLS, and desktop client configuration.
---

# OpenHuman Core Deployment

Deploy `openhuman-core` as a headless JSON-RPC server on a VPS, accessible from the OpenHuman desktop app.

## Prerequisites

- VPS with public IP and ports 80/443/8443 accessible (UFW: `sudo ufw allow 8443/tcp`)
- Domain name with A record pointing to the VPS IP (DNS-only, not Cloudflare proxied — TLS-ALPN-01 needs direct TCP)
- `openhuman-core` binary at `/usr/local/bin/openhuman-core`
- Caddy installed

## Steps

### 1. Set up environment

Create `/opt/openhuman/.env`:

```
BACKEND_URL=https://api.tinyhumans.ai
OPENHUMAN_CORE_TOKEN=<openssl rand -hex 32>
```

`BACKEND_URL` is **required** — without it the core can't authenticate via GitHub OAuth (the core calls api.tinyhumans.ai for session verification).

### 2. Start the core

```bash
mkdir -p /opt/openhuman/workspace
cd /opt/openhuman/workspace
export $(grep -v '^#' /opt/openhuman/.env | xargs)
openhuman-core run --host 0.0.0.0 --port 7788 --jsonrpc-only --verbose 2>&1 &
```

- `--jsonrpc-only`: serves JSON-RPC API only
- Internal port 7788 is not exposed directly to internet
- Logs go to stdout/stderr — capture to file if needed (`>> /var/log/openhuman-core.log 2>&1`)

### 3. Configure Caddy reverse proxy

`/etc/caddy/Caddyfile`:

```
core.yourdomain.com:8443 {
    reverse_proxy localhost:7788
}
```

Caddy auto-provisions a Let's Encrypt certificate via TLS-ALPN-01 challenge. No manual port 80 ACME redirect needed.

```bash
sudo caddy fmt --overwrite /etc/caddy/Caddyfile
sudo systemctl reload caddy
```

If DNS is behind Cloudflare, the A record for the subdomain must be **DNS-only** (grey cloud), not proxied. Proxied mode breaks TLS-ALPN-01.

### 4. Verify

```bash
curl -s https://core.yourdomain.com:8443/health
# → {"ok":true}

# Check cert issuer
echo | openssl s_client -connect core.yourdomain.com:8443 -servername core.yourdomain.com 2>/dev/null | openssl x509 -noout -issuer -dates
```

## Desktop client configuration — the critical ordering

This is the most commonly missed step. The OpenHuman desktop app defaults to connecting to a **local** core on `localhost:7788`. **Order matters — configure the RPC URL BEFORE logging in.**

### v0.54.0+ Onboarding Flow Changes

As of v0.54.0 (May 2026), the desktop app's first-launch flow changed to a multi-step wizard:

1. **Mode selection** → choose **"Run Custom"** (NOT "Simple" — Simple goes to OpenHuman cloud subscription)
2. **Inference (Text)** → choose **Configure** and enter an API key, OR choose **Default** (uses local Ollama on the core, which may not be available on a headless VPS)
3. **Voice** → **Continue** to skip (configurable later)
4. **Connections (OAuth)** → **Finish Setup**

⚠️ **Critical pitfalls:**

- **Choosing "Default" for Inference on a headless VPS**: The core's inference backend defaults to local Ollama with `gemma3:1b-it-qat`. If Ollama is not installed on the VPS, inference fails silently — the app loads but no chat works. The user must either install Ollama or configure a cloud API key afterward.
- **"Run Custom" is required for self-hosted cores**: "Simple" is the cloud subscription path. The user must explicitly pick "Run Custom".

### Configuring Cloud API Keys After Setup

If the user chose Default for Inference and can't chat (no Ollama on VPS):

```bash
# Check current inference config
openhuman-core inference status
# → active_backend: "ollama", state: "idle" means no model is running

# List available cloud providers
openhuman-core inference get_client_config
# → cloud_providers shows registered providers

# Configure a cloud API key (e.g. DeepSeek, OpenAI)
openhuman-core inference update_model_settings \
  --api_key "sk-xxx..." \
  --chat_provider "p_custom_xxxx" \
  --primary_cloud "p_custom_xxxx"
```

If only a custom provider is registered (like DeepSeekV4 with endpoint `https://api.deepseek.com` already in cloud_providers), just set the API key and provider. **Set all provider flags in one command** — the core expects each workload type to have a provider assigned:

```bash
openhuman-core inference update_model_settings \
  --api_key "sk-your-deepseek-key" \
  --primary_cloud "p_custom_xxxx" \
  --chat_provider "p_custom_xxxx" \
  --reasoning_provider "p_custom_xxxx" \
  --agentic_provider "p_custom_xxxx" \
  --coding_provider "p_custom_xxxx"
```

Find the provider ID from `get_client_config` output (`cloud_providers[].id`). If the provider slug is `"custom"`, the ID will be auto-generated (e.g. `"p_custom_e2b4h"`).

After configuring, verify:
```bash
openhuman-core inference get_client_config
# → api_key_set: true, primary_cloud: "p_custom_xxxx", chat_provider: "p_custom_xxxx"
```

Then restart the desktop app. The CLI `inference prompt` and `inference chat` commands may still say "local ai is disabled" — they only check the local Ollama backend, not the cloud provider. Cloud inference works through the RPC layer when the desktop app sends requests.

### BootCheckGate first-launch flow

The desktop app's pre-router component (`app/src/components/BootCheckGate/BootCheckGate.tsx`) runs before any other UI. Its phases:

1. **Picker phase** — user selects **Local** (desktop sidecar, default) or **Cloud** (remote RPC)
2. **Checking phase** — tests core reachability + version match
3. **Result screen** — shows `match` (success), `unreachable`, `auth` failure, or `outdated` — each has a **Switch Mode** button
4. **Login/Welcome screen** (`Welcome.tsx`) — GitHub/Google/Twitter OAuth buttons

**If the user accidentally chose "Local" on first launch:** Tell them to find the **"Switch Mode"** button on the result screen to go back to the mode picker and choose Cloud.
## Desktop client configuration — the critical ordering

This is the most commonly missed step. The OpenHuman desktop app defaults to connecting to a **local** core on `localhost:7788`.

### v0.54.0+ Onboarding Wizard (discovered May 2026)

As of v0.54.0 (May 19, 2026), the first-launch flow changed to a multi-step wizard:

1. **Mode selection** — choose **"Run Custom"** (NOT "Simple" — Simple goes to OpenHuman cloud subscription)
2. **Inference (Text)** — choose **Configure** and enter an API key, **OR choose "Default"** (⚠️ see pitfall below)
3. **Voice** — **Continue** to skip (configurable later)
4. **Connections (OAuth)** — **Finish Setup**

⚠️ **Critical pitfall — "Default" Inference on a headless VPS:**
Choosing "Default" sets the core's inference backend to local Ollama (`gemma3:1b-it-qat`). If Ollama is not installed on the VPS, inference fails **silently** — the desktop app loads fine but no chat works. The user must either:
- Install Ollama on the VPS and download the model
- **OR** reconfigure the inference provider with a cloud API key afterward (see "Configuring Cloud API Keys After Setup" below)

### Configuring Cloud API Keys After Setup

If the user chose "Default" for Inference and can't chat (no Ollama on VPS):

```bash
# Check what the core is doing
openhuman-core inference get_client_config
# → api_key_set: false, primary_cloud: null, chat_provider: null

# Find the cloud provider ID (e.g. "p_custom_e2b4h")
# → cloud_providers[].id

# Configure a cloud API key — set ALL provider flags in one command
openhuman-core inference update_model_settings \
  --api_key "sk-your-deepseek-key" \
  --primary_cloud "p_custom_xxxx" \
  --chat_provider "p_custom_xxxx" \
  --reasoning_provider "p_custom_xxxx" \
  --agentic_provider "p_custom_xxxx" \
  --coding_provider "p_custom_xxxx"

# Verify
openhuman-core inference get_client_config
# → api_key_set: true, primary_cloud: "p_custom_xxxx"

# Then restart the desktop app
```

> **Note:** `inference prompt` and `inference chat` CLI commands only check the local Ollama backend and will say "local ai is disabled" even when cloud providers are configured. Cloud inference works through the RPC layer when the desktop app sends requests.

### Legacy flow (pre-v0.54.0) — still relevant for BootCheckGate

If the user is on an older version or the wizard flow is somehow bypassed:

1. Open the OpenHuman desktop app
2. On the **login/Welcome screen**, find the RPC URL/token fields (may be collapsed behind a "Use custom core" / "Advanced" toggle)
3. Enter:
   - **RPC URL**: `https://core.yourdomain.com:8443/rpc`
   - **Core Token**: the value of `OPENHUMAN_CORE_TOKEN`
4. Click **Test connection** — should show `Connected ✓`
5. Now **log in with GitHub** to bind the cloud session to this core

> GitHub login authenticates against the OpenHuman cloud backend (`api.tinyhumans.ai`), not the core itself. The desktop app must first be configured to point at the remote core URL before GitHub login will work properly.

## Reference

See `references/troubleshooting.md` for:
- DNS propagation check
- Core process environment inspection
- TLS certificate verification
- Desktop app "stuck on connecting" diagnosis
- OAuth account binding details (cloud vs self-hosted auth)

## Pitfalls

- **Self-signed cert → Desktop app silently fails**: The desktop app won't connect to a self-signed certificate. Always use Let's Encrypt. Do NOT use `tls /path/to/self-signed.crt` in Caddyfile.
- **Missing `BACKEND_URL`**: Core runs, health endpoint returns `{"ok":true}`, but GitHub OAuth login never completes. Always set `BACKEND_URL=https://api.tinyhumans.ai`.
- **OAuth deep link redirect broken (known issue)**: GitHub login may succeed in the browser but the app stays on the Welcome screen because the `openhuman://oauth/success` deep link doesn't pass the session token back to the app. This is tracked as GitHub issues #1049, #1985, #2020 — the redirect flow is unreliable on Windows. If this happens:
  - Try "Switch Mode" → re-enter Cloud config → re-test → login again
  - Clear app data via the button on the Welcome screen error panel
  - The underlying bug is a desktop app issue, not a core/server misconfiguration
- **Desktop app stuck on "connecting" after GitHub login**: The app authenticated with the cloud backend but still can't reach the core. Go to Switch mode → paste RPC URL + token.
- **Token changed**: If you regenerate `OPENHUMAN_CORE_TOKEN`, every desktop client must update its config.
- **Core workspace permissions**: The core runs as the user who starts it. Its workspace (`~/.openhuman/`) holds SQLite databases and user state. Ensure the user owns the workspace directory.

## Diagnostic Approach

When a deployment or connection issue arises, **search the project's GitHub Issues first** before guessing at root causes. OpenHuman is actively developed with frequent releases — if the user reports a problem that sounds like a UX flow bug, OAuth hang, or configuration dead-end, there's likely an open issue tracking it. Search patterns:

```
site:github.com/tinyhumansai/openhuman/issues "connecting" OAuth
site:github.com/tinyhumansai/openhuman/issues "stuck" "remote core"
site:github.com/tinyhumansai/openhuman/issues "deep link" OR "oauth/success" redirect
```

Check the actual source code of the relevant component (`BootCheckGate.tsx`, `Welcome.tsx`, `configPersistence.ts`) to understand the expected flow before claiming a solution.

## Known Bug: OAuth Deep Link Redirect on Windows

### Symptom
GitHub login succeeds in browser, but desktop app stays on Welcome/Connecting screen. Core health is OK, RPC URL+token were correctly configured.

### Root Cause
The OAuth flow uses `openhuman://#auth/github/success?token=<jwt>` deep links to return the session JWT. On Windows this protocol handler is unreliable — the JWT never reaches the app. Tracked as GitHub issues #1049, #1985, #2020 (all open).

### Session JWT Recovery Workaround

When the user reports this, **do NOT keep trying desktop-side fixes. Switch to server-side session injection.**

#### ⚠️ CRITICAL PITFALL: Don't curl the callback URL from the server

When the user sends you the browser address bar URL (e.g. `https://api.tinyhumans.ai/auth/github/callback?code=...&state=...`), **do NOT expect to get the JWT by curling it from the server.** The `state` parameter in GitHub's OAuth flow is single-use with a short TTL (minutes). By the time the user copies the URL and sends it to you, the state has already been consumed and expired. Curling it will always return:

```html
<a href="openhuman://#auth/github/error?error=Invalid%20or%20expired%20OAuth%20state">Open OpenHuman</a>
```

**Correct approach:** Tell the user to start a **fresh login** and this time look at the **page CONTENT** (not the address bar) for the deep link token. The page that `api.tinyhumans.ai` renders after successful OAuth has a "Copy Link" button — that's what the user should click and paste.

The callback URL from the address bar is only useful as a **diagnostic tool** — curl it once from the server to confirm the page structure/format of the deep link, not to extract a live token.

1. **User starts a fresh OAuth flow** — click GitHub login on the desktop app (the `state` expires within minutes, so don't reuse old callback URLs)
2. **User inspects the browser page** that appears after GitHub authorization:
   - `api.tinyhumans.ai` shows an "Opening OpenHuman" or "Signing you in..." HTML page
   - The page has a **"Copy Link"** button — tell the user to click it and paste the full URL starting with `openhuman://auth?token=...`
   - The deep link format is: `openhuman://auth?token=<jwt>&key=auth`
   - If the user instead sends the browser address bar URL (e.g. `api.tinyhumans.ai/auth/github/callback?code=...&state=...`), **do not use the same URL to try again** — curl it from the server only as a DIAGNOSTIC to see what page the backend returned:
     ```bash
     curl -sL "https://api.tinyhumans.ai/auth/github/callback?code=...&state=..."
     ```
     If the response contains `error=Invalid%20or%20expired%20OAuth%20state`, the `state` parameter expired (it is single-use with a short TTL). Tell the user: **"The OAuth state expired. Start a fresh login from the desktop app, authorize on GitHub, and this time look at the PAGE CONTENT (not the address bar) for the 'Copy Link' button."**
3. **Extract the JWT** from the deep link: the `token` query param (starts with `eyJ`). Decode payload to verify:
   ```bash
   echo '<payload-segment>' | base64 -d 2>/dev/null | python3 -m json.tool
   ```
4. **Store session on the core** (from the VPS — may take up to 30s as core validates via GET /auth/me):
   ```bash
   timeout 45 openhuman-core auth store_session --token "<the-jwt>"
   ```
   Expected success logs:
   ```
   session JWT verified via GET /auth/me on https://api.tinyhumans.ai
   user directory activated for <userId>
   session stored
   subconscious engine bootstrapped
   login-gated services started
   ```
5. **Verify** on the server:
   ```bash
   openhuman-core auth get_state
   # → isAuthenticated: true, user: { ... }
   ```
6. **User restarts the desktop app** — it connects to the remote core and detects the authenticated session, skipping the login screen entirely

### Callback Page Structure (for reference)
When you curl the callback URL from the server:
```bash
curl -sL "https://api.tinyhumans.ai/auth/github/callback?code=...&state=..."
```

A successful response contains (deep link format verified May 2026):
```html
<title>Opening OpenHuman</title>
<a href="openhuman://auth?token=eyJ...&key=auth">Open OpenHuman</a>
<button class="copy-link">(Copy Link)</button>
<script>
  setTimeout(function(){window.location.href="openhuman://auth?token=eyJ...&key=auth";}, 1200);
</script>
```

An expired-state response:
```html
<a href="openhuman://#auth/github/error?error=Invalid%20or%20expired%20OAuth%20state">Open OpenHuman</a>
```

Key observations:
- The successful deep link format is `openhuman://auth?token=<jwt>&key=auth` (NOT `openhuman://#auth/github/success?...` as older documentation suggested)
- The failed/error format is `openhuman://#auth/github/error?error=...` (fragment-based, different from success)
- The page auto-redirects after 1200ms — if the protocol handler is not registered, the browser shows a blank page or error. Tell the user to look at the page CONTENT (not the address bar) for the Copy Link button before the redirect happens.
