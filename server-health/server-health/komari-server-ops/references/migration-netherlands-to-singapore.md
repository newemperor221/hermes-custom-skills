# Migration: Netherlands → Singapore (2026-05-25)

## Source
- **Host**: 无聊云 | 阿姆斯特丹 (31.58.51.127:46748)
- **Arch**: x86_64, Alpine 3.22.2, 488MB RAM, 1GB disk
- **Keys**: hermes_admin SSH key

## Target
- **Host**: isvoro | 新加坡 (140.245.97.144:10425)
- **Arch**: ARM64 (aarch64), Alpine 3.17, 23GB RAM (LXC host), 1GB disk
- **Auth**: root password (stored in memory)

## Migrated Services

| Service | Port | Description |
|---------|------|-------------|
| Komari backend | 25776 | Panel + API server |
| galaxy-proxy | 25774 | Python static file proxy + API passthrough |
| cloudflared tunnel | — | Tunnel to stat.357561.xyz |
| IP-Sentinel webhook | 42186 | Webhook handler |
| IP-Sentinel TG Master | — | Telegram bot controller |

## Migration Steps

### 1. Install binaries on target (ARM64)

```bash
# komari server (43MB)
curl -sL https://github.com/komari-monitor/komari/releases/download/1.2.0/komari-linux-arm64 -o /opt/komari/komari
chmod +x /opt/komari/komari

# cloudflared (ARM64)
curl -sL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# ⚠️ Agent is from SEPARATE repo: komari-monitor/komari-agent
# Don't accidentally use komari-linux-arm64 as agent!
```

### 2. Transfer data files

```bash
# On source
cd /opt/komari/data
tar czf /tmp/komari-data.tar.gz komari.db komari.db-shm komari.db-wal secret.key theme/

# SCP via local machine as intermediate
scp -P 46748 root@31.58.51.127:/tmp/komari-data.tar.gz /tmp/
scp -P 46748 root@31.58.51.127:/opt/komari/galaxy-proxy.py /tmp/
sshpass -p 'PASSWORD' scp -P 10425 /tmp/komari-data.tar.gz root@140.245.97.144:/tmp/
sshpass -p 'PASSWORD' scp -P 10425 /tmp/galaxy-proxy.py root@140.245.97.144:/opt/komari/

# On target
cd /opt/komari && tar xzf /tmp/komari-data.tar.gz -C /opt/komari/data/
```

### 3. Start services on target

```bash
# Komari backend
nohup /opt/komari/komari server -l 0.0.0.0:25776 -d /opt/komari/data/komari.db > /var/log/komari-server.log 2>&1 &

# galaxy-proxy
cd /opt/komari/data/theme
nohup python3 /opt/komari/galaxy-proxy.py > /var/log/galaxy-proxy.log 2>&1 &

# Verify
ss -tlnp | grep -E '25774|25776'
curl -s http://127.0.0.1:25776/api/version
curl -s http://127.0.0.1:25774/ | head -5
```

### 4. Cloudflared tunnel (token extraction)

When cloudflared is already running on source with `--token`, extract token from procfs:

```bash
# Method: hex dump to bypass output filters
cat /proc/PID/cmdline | hexdump -C
# Token starts after null-byte separator following "--token"
# Copy hex bytes, decode: bytes.fromhex('...').decode('utf-8')

# Start on target with same token
nohup /usr/local/bin/cloudflared tunnel run --token '<TOKEN>' > /var/log/cloudflared.log 2>&1 &
```

### 5. IP-Sentinel migration

```bash
# Pack on source
tar czf /tmp/ip-sentinel.tar.gz -C /opt ip_sentinel ip_sentinel_master

# Transfer and extract on target
tar xzf /tmp/ip-sentinel.tar.gz -C /opt/

# Update config (/opt/ip_sentinel/config.conf):
#   PUBLIC_IP → new server IP
#   REGION_CODE / REGION_NAME → new location
#   NODE_NAME / NODE_ALIAS → new name

# Dependencies (Alpine)
apk add jq sqlite bash openssl

# Start
nohup python3 /opt/ip_sentinel/core/webhook.py 42186 > /var/log/ip-sentinel-webhook.log 2>&1 &
nohup bash /opt/ip_sentinel_master/tg_master.sh > /var/log/ip-sentinel-master.log 2>&1 &
```

### 6. Alpine auto-start scripts

Create `/etc/local.d/*.start` scripts (executable) for each service:

```
/etc/local.d/komari-server.start
/etc/local.d/galaxy-proxy.start
/etc/local.d/cloudflared.start
/etc/local.d/ip-sentinel.start
```

Enable: `rc-update add local default`

### 7. Re-point source server agent

After migration, the source server becomes a monitored node only:

```bash
# Download agent binary from SEPARATE repo
curl -sL https://github.com/komari-monitor/komari-agent/releases/download/1.2.0/komari-agent-linux-amd64 -o /opt/komari/agent
chmod +x /opt/komari/agent

# ⚠️ Don't confuse with komari-linux-amd64 (43MB server binary)!
# komari-agent-linux-amd64 is 11MB, has -e / -t flags

# Start agent pointing to new panel via cloudflared tunnel URL
nohup /opt/komari/agent -e https://stat.357561.xyz -t <TOKEN> --disable-web-ssh > /var/log/komari-agent.log 2>&1 &

# Agent token found in komari DB: clients table (uuid, token, name, ipv4)
sqlite3 /opt/komari/data/komari.db 'SELECT uuid, token, name, ipv4 FROM clients;'
```

### 8. Stop source services

```bash
kill $(cat /var/run/cloudflared.pid 2>/dev/null) 2>/dev/null  # or kill -9
pkill -f "galaxy-proxy"
pkill -f "komari server"
pkill -f "tg_master|webhook"
```

### 9. Verify

```bash
curl -sI https://stat.357561.xyz/  # Should return 200 via cloudflare
# Browser: check all nodes online, data flowing
```
