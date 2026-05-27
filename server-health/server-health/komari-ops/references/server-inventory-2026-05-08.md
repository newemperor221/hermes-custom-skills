# 服务器列表（2026-05-08 更新）

## komari 相关服务器

| 节点 | 地址 | SSH端口 | 用户 | 密码/密钥 | 系统 | komari端口 | 备注 |
|------|------|---------|------|----------|------|-----------|------|
| 56idc-la | <洛杉矶2_IP> | 42185 | root | Y@BU1%wmP#xFs8bK | Alpine 3.22 LXC | 25774 | komari server + cloudflared + agent |
| 将军鸡 | 2001:470:e2db:100:: | 27589 | root | qr2j%tgez2ys | Debian | - | IPv6 only，网络不通 |
| Dedirock | <旧Master_IP> | 58193 | root | (key) | Debian | - | 可跳将军鸡 |
| ccs-la2 | <运维本机_IP> | 43827 | woioeow | 4561834 | Debian | 25774 | komari server 旧版已撤 |
| racknerd-atlanta | <亚特兰大_IP> | 53621 | woioeow | 4561834 | Debian | - | sudo |
| nosla-hk | <nosla香港_IP> | 27691 | root | (key) | Debian | - | |
| acck-东京 | <东京_IP> | 47283 | root | (key) | Debian | - | |
| acck-香港 | <acck香港_IP> | 47632 | root | (key) | Debian | - | |
| akile-东京 | <akile东京_IP> | 62174 | root | (key) | Debian | - | |
| racknerd-ny | <纽约_IP> | 27391 | root | (key) | Debian | - | |
| ccs-la1 | <洛杉矶1_IP> | 47283 | root | (key) | Debian | - | |
| hostvds-ks | <KS_IP> | 63841 | root | (key) | Debian | - | |
| yecaoyun-hk | <香港_IP> | 62839 | root | (key) | Debian | - | |

## komari token 列表

| 节点 | Token |
|------|-------|
| 56idc-la | 56idc-la-token |
| 将军鸡 | 207c22bb50597a5b27e72e57c66f3cd9 |
| Dedirock | c7fa2255ec9338154563e4e0ae18ffa4 |
| acck-东京 | f76747abb0eb321dda3202e2bb302276 |
| acck-香港 | dd391a8c13eec8176a2d4f618da935dd |
| akile-东京 | 6ec1efc6b7d042a854f62228155c8ad7 |
| racknerd-纽约 | 5a7dbf648caed570b8883cfef38e7560 |
| ccs-洛杉矶1 | 0a54dfb2387411751f31468179348e79 |
| ccs-洛杉矶2 | ae30645a65f6017cfeb71eadf3d13938 |
| hostvds-堪萨斯 | 9ba1af474e16313a6b6c00b43435aca6 |
| yecaoyun-香港 | 1d2fc8439594e38832931b7d5977d993 |
| racknerd-亚特兰大 | 460b8cc7d35e3b6db150443ceb95f719 |
| nosla-香港 | 0615eea8dd66147add4d3a8d9c22c334 |

## 关键路径

- komari server: 56idc-la:25774
- <监控面板域名> → cloudflared tunnel → 56idc-la:25774
- cloudflared token: eyJhIjoiYzFkMTgwNGNiNTA3NGM2YTYwNGU1NDc0YjZjNTA4MTYiLCJ0IjoiYmE0ZThlYTctZThlMS00MTE1LTg0MGItNjRiODdlMTUyYjg1IiwicyI6IllqRmtOR1l6TW1VdE16WmlOUzAwWXpNNUxUZzBZakV0TldReU1qTTROakk1WWpFMSJ9
- komari 面板: https://<监控面板域名>
- admin 账号: admin / Komari@2026

## komari 版本状态

| 版本 | 大小 | 路径 | Alpine 可用 |
|------|------|------|-----------|
| 1.1.9 | 31MB | /opt/komari/komari (working) | ✅ |
| 1.2.0 | 43MB | /opt/komari/komari_new (SIGSEGV) | ❌ |
