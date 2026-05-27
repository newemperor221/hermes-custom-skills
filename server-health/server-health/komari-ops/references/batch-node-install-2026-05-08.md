# 节点安装记录 2026-05-08

## 当前 komari server
- **Host**: 56idc-la (<洛杉矶2_IP>:42185, root, Alpine + OpenRC)
- **Panel**: https://stat.357561.xyz (cloudflared → localhost:20241 → komari :25774)
- **cloudflared token**: `eyJhIjoiYzFkMTgwNGNiNTA3NGM2YTYwNGU1NDc0YjZjNTA4MTYiLCJ0IjoiYmE0ZThlYTctZThlMS00MTE1LTg0MGItNjRiODdlMTUyYjg1IiwicyI6IllqRmtOR1l6TW1VdE16WmlOUzAwWXpNNUxUZzBZakV0TldReU1qTTROakk1WWpFMSJ9`

## 全部节点一览（2026-05-08 添加）

| 简称 | 地址 | SSH端口 | 用户 | 密码 | 系统 | Init | Agent token |
|------|------|---------|------|------|------|------|-------------|
| 56idc-la | <洛杉矶2_IP> | 42185 | root | Y@BU1%wmP#xFs8bK | Debian+Alpine | OpenRC | 56idc-la-token |
| 将军鸡 | 2001:470:e2db:100::5459:389:6b27 | 27589 | root | qr2j%tgez2ys | Debian | OpenRC | 207c22bb50597a5b27e72e57c66f3cd9 |
| dedirock-洛杉矶 | <旧Master_IP> | 58193 | root | Y@BU1%wmP#xFs8bK | Debian | systemd | dedirock-token |
| acck-东京 | <东京_IP> | 47283 | root | 4561834 | Debian | systemd | acck-tokyo-token |
| acck-香港 | <acck香港_IP> | 47632 | root | 4561834 | Debian | systemd | acck-hk-token |
| akile-东京 | <akile东京_IP> | 62174 | root | 4561834 | Debian | systemd | akile-tokyo-token |
| racknerd-纽约 | <纽约_IP> | 27391 | root | 4561834 | Debian | systemd | racknerd-ny-token |
| ccs-洛杉矶1 | <洛杉矶1_IP> | 47283 | root | 4561834 | Debian | systemd | ccs-la1-token |
| ccs-洛杉矶2 | <运维本机_IP> | 43827 | woioeow | 4561834 | Debian | systemd | ccs-la2-token |
| hostvds-堪萨斯 | <KS_IP> | 63841 | root | 4561834 | Debian | systemd | hostvds-ks-token |
| racknerd-亚特兰大 | <亚特兰大_IP> | 53621 | woioeow | 4561834 | Debian | systemd | racknerd-atlanta-token |
| yecaoyun-香港 | <香港_IP> | 62839 | root | 4561834 | Debian | systemd | yecaoyun-hk-token |

## 批量安装命令模板

### root 用户（systemd）
```bash
curl -fsSL https://raw.githubusercontent.com/komari-monitor/komari-agent/refs/heads/main/install.sh | bash -s -- \
  -e 'https://stat.357561.xyz' \
  -t '<TOKEN>' \
  --disable-web-ssh

systemctl enable komari-agent && systemctl restart komari-agent
```

### 非 root 用户（woioeow + sudo）
```bash
echo '4561834' | sudo -S bash -c 'curl -fsSL https://raw.githubusercontent.com/komari-monitor/komari-agent/refs/heads/main/install.sh | bash -s -- -e https://stat.357561.xyz -t <TOKEN> --disable-web-ssh'

sudo systemctl enable komari-agent && sudo systemctl restart komari-agent
```

### Alpine OpenRC（56idc-la / 将军鸡）
```bash
curl -fsSL https://raw.githubusercontent.com/komari-monitor/komari-agent/refs/heads/main/install.sh | sh -s -- \
  -e 'https://stat.357561.xyz' \
  -t '<TOKEN>' \
  --disable-web-ssh

rc-service komari-agent start
rc-update add komari-agent default
```

## 数据库批量注册
```bash
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP> "sqlite3 /opt/komari/data/komari.db \"
INSERT OR IGNORE INTO clients (uuid, token, name, os, created_at, updated_at) VALUES
('56idc-la', '56idc-la-token', '56idc-la', 'Linux', datetime('now'), datetime('now')),
('jiangjunji', '207c22bb50597a5b27e72e57c66f3cd9', '将军鸡', 'Linux', datetime('now'), datetime('now')),
('dedirock', 'dedirock-token', 'dedirock-洛杉矶', 'Linux', datetime('now'), datetime('now')),
('acck-tokyo', 'acck-tokyo-token', 'acck-东京', 'Linux', datetime('now'), datetime('now')),
('acck-hk', 'acck-hk-token', 'acck-香港', 'Linux', datetime('now'), datetime('now')),
('akile-tokyo', 'akile-tokyo-token', 'akile-东京', 'Linux', datetime('now'), datetime('now')),
('racknerd-ny', 'racknerd-ny-token', 'racknerd-纽约', 'Linux', datetime('now'), datetime('now')),
('ccs-la1', 'ccs-la1-token', 'ccs-洛杉矶1', 'Linux', datetime('now'), datetime('now')),
('ccs-la2', 'ccs-la2-token', 'ccs-洛杉矶2', 'Linux', datetime('now'), datetime('now')),
('hostvds-ks', 'hostvds-ks-token', 'hostvds-堪萨斯', 'Linux', datetime('now'), datetime('now')),
('racknerd-atlanta', 'racknerd-atlanta-token', 'racknerd-亚特兰大', 'Linux', datetime('now'), datetime('now')),
('yecaoyun-hk', 'yecaoyun-hk-token', 'yecaoyun-香港', 'Linux', datetime('now'), datetime('now'));
\""
```

## 验证命令
```bash
# 检查 komari 日志里的 200 OK 和 reconnect success
tail -50 /var/log/komari.log | grep -E '200|reconnect success|token'

# 检查数据库节点状态
sqlite3 /opt/komari/data/komari.db "select name, ipv4, ipv6, region, updated_at from clients order by name;"

# 检查面板 12/12 在线
curl -s https://stat.357561.xyz/api/v1/status | head -c 100
```

## 关键教训

1. **非 root + sudo 环境**：ccs-la2 和 racknerd-atlanta 是 woioeow 用户，sudo 需要 `-S` 从 stdin 读密码，或用 `ssh -t` 分配 pty
2. **install.sh 对 Debian/Alpine 的检测**：install.sh 会自动检测 systemd/OpenRC 并创建对应 init 脚本，参数 `-e` 和 `-t` 能正确传入
3. **所有节点统一用 HTTPS 域名 endpoint**：`https://stat.357561.xyz`，不要用 IP（将军鸡 IPv6 only 走不了 IPv4 NAT 端口映射）
4. **token 冲突**：每台机器必须独立 token，共用 token 会导致数据混淆
5. **批量生成 token 后必须同步写入远程数据库**：install.sh 每次运行生成新的随机 token，若数据库里存的是旧 token，agent 会 401 且不会自动恢复
6. **401 错误处理流程**：
   - 抓 agent 实际用的 token：从日志 `tail -100 /var/log/komari.log | grep 401` 取出 `token=xxx`
   - 对比数据库 token：`sqlite3 /opt/komari/data/komari.db 'SELECT name, token FROM clients;'`
   - 不一致则更新：`UPDATE clients SET token='<agent_token>' WHERE name='<node>';`
   - 重启 komari server 使改动生效（server 会缓存旧 token）
7. **komari server 重启前先 kill 旧进程**：确保新进程加载了更新后的数据库
