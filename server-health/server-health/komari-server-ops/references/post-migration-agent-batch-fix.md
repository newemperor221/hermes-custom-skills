# Post-Migration Batch Agent Fix (2026-05-25)

## Scenario

After migrating Komari backend from Netherlands (<荷兰_IP>) to Singapore (<新加坡_IP>), agents on 8+ nodes were still pointing to the OLD backend URL (`http://<荷兰_IP>:45774`), causing them to show 0% data on the panel.

## Diagnosis

Check each node's agent process args to see the endpoint:

```bash
ssh -p PORT -i ~/.ssh/id_ed25519 root@IP "ps aux | grep komari | grep -v grep"
```

## Fix Pattern

```bash
# 1. Kill old agent process
kill $(pgrep -f 'agent.*31.58') 2>/dev/null

# 2. If agent binary doesn't exist or is wrong version, download from SEPARATE repo:
# komari-monitor/komari-agent (NOT komari-monitor/komari which is 43MB server)
curl -sL https://github.com/komari-monitor/komari-agent/releases/download/1.2.0/komari-agent-linux-amd64 -o /opt/komari/agent
chmod +x /opt/komari/agent

# 3. Start with correct endpoint
nohup /opt/komari/agent -e https://<监控面板域名> -t <TOKEN> --disable-web-ssh > /opt/komari/agent.log 2>&1 &
```

## Avoiding nohup/& Blocks

When the terminal tool blocks nohup/setsid/& in local foreground mode:

- Put the command inside an SSH string: `ssh user@host "nohup ... &"`
- Or use `setsid` instead of `nohup`

## Pitfalls

- Wrong binary: agent = 11MB from `komari-agent` repo, server = 43MB from `komari` repo
- Systemd auto-restart: stop service first before killing process, or old config respawns
- Skip re-download if agent.log shows "Current version is latest: 1.2.0" — binary is fine, just endpoint wrong
