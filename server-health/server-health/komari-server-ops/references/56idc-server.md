# 56idc-la Komari 面板服务器

## 基本信息
- **IP/端口**：<洛杉矶2_IP>:42185
- **SSH 用户**：root
- **SSH 密码**：Y@BU1%wmP#xFs8bK
- **系统**：Alpine Linux 3.22.2（LXC 容器）
- **服务管理**：OpenRC (`rc-service`)
- **宿主机**：ColoCrossing 洛杉矶

## Komari 面板
- **二进制路径**：`/opt/komari/komari`（43MB server 版本）
- **Agent 路径**：`/opt/komari/agent`（11MB agent 版本）
- **数据库**：`/opt/komari/data/komari.db`（SQLite）
- **监听端口**：25774
- **admin 密码**：ybr52tlztwfr6b（2FA 已关闭）
- **服务管理**：`rc-service komari restart`

## Cloudflared 隧道
- 运行方式：Quick Tunnel（token 认证）
- 命令：`/usr/local/bin/cloudflared tunnel run --token <token>`
- 旧域名 `mon.357561.xyz`（指向 DediRock）已废弃

## 密码重置命令
```bash
/opt/komari/komari chpasswd -p '新密码' -d /opt/komari/data/komari.db
/opt/komari/komari disable-2fa -d /opt/komari/data/komari.db
rc-service komari restart
```

## 旧记录（已过期）
- Token 文件中记录端口 52137 / 密码 4561834 — 均不再有效
- SSH key 认证（id_ed25519）已不再支持
