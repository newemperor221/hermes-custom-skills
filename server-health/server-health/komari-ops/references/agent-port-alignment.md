# Komari Agent-to-Server Port Alignment

## Problem

Agent reports "Online" in panel but shows zero data (CPU 0%, mem_total 0 B). Logs may show 500 errors on `/api/clients/uploadBasicInfo`.

## Root Cause

Agent's `-e` endpoint points to a port where no komari server is listening (old port after migration, or wrong default).

## Quick Diagnostic

```bash
# On komari server: find actual listening port
ssh -p 52137 -i ~/.ssh/id_ed25519 -o StrictHostKeyChecking=no root@<server> \
  "cat /proc/net/tcp | awk '{print $2}' | grep -v '^ 0' | while read h p; do printf '%d\n' 0x$p; done | sort -u"

# On node: check agent endpoint config
# Alpine:
grep command_args /etc/init.d/komari-agent
# Debian:
grep ExecStart /etc/systemd/system/komari-agent.service
```

## Known Default Ports

| Install type | Default port |
|---|---|---|
| Alpine komari install.sh | 25774 |
| Debian komari install.sh | 45774 |
| Old Debian (manual) | 47926 |

## Fix

```bash
# Alpine: sed + restart
sed -i 's|http://[^:]*:[0-9]*|http://127.0.0.1:<CORRECT_PORT>|' /etc/init.d/komari-agent
rc-service komari-agent restart

# Debian
sed -i 's|ExecStart=/opt/komari/agent.*|ExecStart=/opt/komari/agent -e http://127.0.0.1:<PORT> -t <TOKEN>|' \
  /etc/systemd/system/komari-agent.service
systemctl daemon-reload && systemctl restart komari-agent
```

## Verify

```bash
# Check logs for successful BasicInfo upload
grep "uploadBasicInfo" /var/log/komari.log | tail -3
# Should show: 200 POST ...  (not 500)
```

After fix, panel should show `mem_total > 0` for the node.
