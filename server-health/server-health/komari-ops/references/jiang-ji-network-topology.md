# 将军鸡与56idc-la 网络架构（2026-05-08 更新）

## 当前架构（2026-05-08 重建后）

**56idc-la（komari server 所在）**：
- SSH：`sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP>`
- 系统：**Debian**（重装后不再是 Alpine），LXC 容器
- komari server：`/opt/komari/komari server -l :25774`，监听 `tcp6 :::25774`
- IPv4：<洛杉矶2_IP>（NAT 映射端口 58461 → 容器 25774）
- IPv6：2001:470:d:7a4:1::a1（公网可路由，从 DediRock 可 ping 通）
- cloudflared：已安装，服务模式，监听 localhost:20241，token 指向 stat.357561.xyz
- 面板：stat.357561.xyz（cloudflared 隧道 → localhost:20241 → komari 25774）
- 两个节点均已上线：将军鸡（将军鸡，KP）+ 56idc-la（56idc-la，US）

**将军鸡（komari agent）**：
- SSH：`sshpass -p 'qr2j%tgez2ys' ssh -p 27589 root@2001:470:e2db:100:0:5459:389:6b27`
  - 本机无法直连，通过 Dedirock 跳转
- 系统：Debian，HE IPv6 隧道 `2001:470:e2db:100:0:5459:389:6b27`
- komari agent：token `207c22bb50597a5b27e72e57c66f3cd9`，连 `https://stat.357561.xyz`
- agent init：`/etc/init.d/komari-agent`，参数 `-e https://stat.357561.xyz -t 207c22bb50597a5b27e72e57c66f3cd9 --disable-web-ssh`

## 关键发现

- **将军鸡连 stat.357561.xyz 可通**：将军鸡 curl https://stat.357561.xyz 返回 HTML（CF JS 挑战页面），HTTPS 层面可达，agent 用 HTTPS WebSocket 绕过 CF JS 挑战 → 成功上报 BasicInfo ✅
- **56idc-la 有公网 IPv6**：`2001:470:d:7a4:1::a1`，从 DediRock 可 ping 通（124ms，0% 丢包）
- **不需要 IPv6 跳板代理**：将军鸡 agent 直接连 `https://stat.357561.xyz` 即可

## 坑（历史）

- **56idc-la 误判为 Alpine**：重装后实际是 Debian，但 init 系统仍是 OpenRC（容器级）
- **cloudflared 端口映射**：宿主机 NAT 58461 → 容器内 komari 25774，stat.357561.xyz 通过此端口访问
- **将军鸡 GeoIP 误标**：HE 隧道地址 2001:470::/32 在 ipinfo.io 显示 KP（朝鲜），实际出口在美国
