# Alpine LXC Agent Recovery (2026-05-25)

## Summary

Two Alpine LXC nodes (Taiwan GCP + Singapore isvoro) had Komari agent processes stopped. Both were recovered via SSH password auth and manual agent restart. Singapore required ARM64 binary.

## Taiwan (无聊云测试 | 台湾)

- **IP**: <台湾_IP>
- **SSH**: port 43590, root/password
- **Arch**: x86_64
- **OS**: Alpine Linux 3.17 LXC
- **Issue**: Agent binary existed at `/opt/komari/agent` but process not running
- **Recovery**:
  1. `nohup /opt/komari/agent -e https://stat.357561.xyz -t gcp-us-agent > /opt/komari/agent.log 2>&1 &`
  2. Verified: logs showed `Basic info uploaded successfully` and `WebSocket connected`
  3. Set auto-start: wrote command to `/etc/local.d/komari.start`, `chmod +x`, `rc-update add local default`
  4. Actual token from panel: `gcp-us-agent`

## Singapore (isvoro | 新加坡)

- **IP**: <新加坡_IP>
- **SSH**: port **10425** (non-standard), root/password (jZmogE2tU94HJibt)
- **Arch**: **ARM64 (aarch64)**
- **OS**: Alpine Linux 3.17 LXC
- **Issue**: Fresh reinstall, no agent binary
- **Recovery**:
  1. Downloaded ARM64 binary: `wget -qO /tmp/agent https://github.com/komari-monitor/komari-agent/releases/latest/download/komari-agent-linux-arm64`
  2. Moved to `/opt/komari/agent`, `chmod +x`
  3. Started: `nohup /opt/komari/agent -e https://stat.357561.xyz -t uJbWkMELxRA7TdawxjV6bi > /opt/komari/agent.log 2>&1 &`
  4. Verified: same log checks as Taiwan
  5. Set auto-start: same OpenRC local.d method

## Authentication Notes

- Panel login: admin / ybr52tlztwfr6b at stat.357561.xyz
- To get agent token: Server → search node → click Install command button
- The token is different for each node (not the same as display name)
