# Komari 面板 + IP Sentinel 迁移实录 — 56idc-la → 荷兰机

**日期：** 2026-05-12
**源：** 56idc-la (<洛杉矶2_IP>) — Alpine 3.22 LXC
**目标：** 荷兰机 (<荷兰_IP>) — Alpine 3.22 LXC（波兰机房，AS214481 Wojciech Czapkowicz）
**SSH：** root/OX8w$nE9A%tfqb6v :46748
**耗时：** ~15分钟

## 迁移内容

| 组件 | 大小 | 说明 |
|------|------|------|
| komari panel 二进制 | 43MB | server 端 |
| komari.db | 5MB | SQLite 数据库（含所有节点配置/token） |
| ip_sentinel 配置+脚本 | ~140KB | webhook.py + config.conf |
| ip_sentinel_master | ~60KB | tg_master.sh + master.conf + sentinel.db |

## 传输方式

56idc-la →（scp via sshpass）→ **本机（ccs-la2）** →（scp via sshpass）→ 荷兰机

## 关键命令记录

### 打包（在 56idc-la 上）
```bash
tar czf /tmp/komari-migrate.tar.gz -C /opt/komari komari data/komari.db
tar czf /tmp/ip-sentinel-migrate.tar.gz -C /opt ip_sentinel ip_sentinel_master
```

### 解压（在荷兰机上）
```bash
mkdir -p /opt/komari/data /opt/komari/theme
cd /opt/komari && tar xzf /tmp/komari-migrate.tar.gz
# ⚠️ 必须先 mkdir 再 cd 进去解压，因为 tar 包只有 komari（文件）和 data/komari.db
# 直接 tar -C /opt 会报 "Not a directory"

tar xzf /tmp/ip-sentinel-migrate.tar.gz -C /opt/
```

### 更新 IP Sentinel 配置
关键改动：PUBLIC_IP、REGION_CODE/REGION_NAME、NODE_NAME/NODE_ALIAS

### 更新所有 Agent endpoint（共 9 台）
旧: `https://<监控面板域名>`
新: `http://<荷兰_IP>:45774`

对所有 server 执行:
```bash
# systemd:
sed -i "s|https://<监控面板域名>|http://<荷兰_IP>:45774|g" /etc/systemd/system/komari-agent.service
systemctl daemon-reload && systemctl restart komari-agent

# openrc:
sed -i "s|https://<监控面板域名>|http://<荷兰_IP>:45774|g" /etc/init.d/komari-agent
rc-service komari-agent restart
```

### 验证
```bash
sqlite3 /opt/komari/data/komari.db "SELECT name, last_active FROM clients;"
```

## 踩坑记录

1. **Alpine 无 /bin/bash**：tg_master.sh 依赖 bash，必须 `apk add bash`
2. **tar 路径陷阱**：komari tarball 内路径是 `komari`（文件）和 `data/komari.db`，不是 `/opt/komari/...`
3. **supervise-daemon 拒绝停止**：`rc-service komari stop` 说 no matching processes found，但 ps 显示还在。需 `pkill -9` 并指定进程
4. **clients 表叫 clients 不是 nodes**：SQLite 查节点用 `SELECT * FROM clients;`
5. **无 cloudflared 时用 http:// 不是 https://**：agent 的 -e 参数必须匹配面板实际协议
6. **IPv6-only 探针不能走 NAT 端口**：将军鸡（IPv6-only，2001:470:e2db:100:0:5459:389:6b27）连接荷兰面板时必须用 `http://[2a0f:85c1:840:2ce:1::8c]:25774`（实际服务端口，非 NAT 45774）。curl -6 先验证可达性再改 agent 配置

## 迁移后结果

**荷兰机：** Komari 面板 http://<荷兰_IP>:45774 + ip_sentinel webhook :42186 + tg_master
**56idc-la：** 仅剩 komari-agent，内存从 45MB → 16MB
**面板节点数：** 12 台已接入
