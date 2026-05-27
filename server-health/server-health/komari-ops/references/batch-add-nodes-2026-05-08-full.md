# 批量添加节点完整记录（2026-05-08）

## 12台服务器全部在线

| 节点 | IP | SSH端口 | 用户 | 密码 | Token | 系统 |
|------|-----|---------|------|------|-------|------|
| 56idc-la | <洛杉矶2_IP> | 42185 | root | Y@BU1%wmP#xFs8bK | 56idc-la-token | Alpine/LXC |
| 将军鸡 | 2001:470:e2db:100:: | 27589 | root | qr2j%tgez2ys | 207c22bb50597a5b27e72e57c66f3cd9 | Debian |
| Dedirock | <旧Master_IP> | 58193 | root | Y@BU1%wmP#xFs8bK | dedirock-token | Debian |
| acck-东京 | <东京_IP> | 47283 | root | 4561834 | acck-tokyo-token | Debian |
| acck-香港 | <acck香港_IP> | 47632 | root | 4561834 | acck-hk-token | Debian |
| akile-东京 | <akile东京_IP> | 62174 | root | 4561834 | akile-tokyo-token | Debian |
| racknerd-纽约 | <纽约_IP> | 27391 | root | 4561834 | racknerd-ny-token | Debian |
| ccs-洛杉矶1 | <洛杉矶1_IP> | 47283 | root | 4561834 | ccs-la1-token | Debian |
| ccs-洛杉矶2 | <运维本机_IP> | 43827 | woioeow | 4561834 | ccs-la2-token | Debian |
| hostvds-堪萨斯 | <KS_IP> | 63841 | root | 4561834 | hostvds-ks-token | Debian |
| yecaoyun-香港 | <香港_IP> | 62839 | root | 4561834 | yecaoyun-hk-token | Debian |
| racknerd-亚特兰大 | <亚特兰大_IP> | 53621 | woioeow | 4561834 | racknerd-atlanta-token | Debian |

## 安装命令模板（token 必须用下方正确值，不要用旧值）

### Token 正确值（2026-05-08 实测确认）

> ⚠️ **install.sh 每次运行生成随机 token**，必须从 komari server 日志抓实际值，不能用旧 token！
> 抓取方法：`grep 401 /var/log/komari.log | grep token= | head -3`

| 节点 | Token | 备注 |
|------|-------|------|
| 56idc-la | 56idc-la-token | ✅ 正确 |
| 将军鸡 | 207c22bb50597a5b27e72e57c66f3cd9 | ✅ 正确 |
| Dedirock | dedirock-token | ✅ 旧 token，2026-05-08 时 DediRock 用 c7fa2255... |
| acck-东京 | f76747abb0eb321dda3202e2bb302276 | ⚠️ install.sh 生成，不是 acck-tokyo-token |
| acck-香港 | dd391a8c13eec8176a2d4f618da935dd | ⚠️ 不是 acck-hk-token |
| akile-东京 | 6ec1efc6b7d042a854f62228155c8ad7 | ⚠️ 不是 akile-tokyo-token |
| racknerd-纽约 | 5a7dbf648caed570b8883cfef38e7560 | ⚠️ 不是 racknerd-ny-token |
| ccs-洛杉矶1 | 0a54dfb2387411751f31468179348e79 | ⚠️ 不是 ccs-la1-token |
| ccs-洛杉矶2 | ccs-la2-token | ✅ 正确 |
| hostvds-堪萨斯 | 9ba1af474e16313a6b6c00b43435aca6 | ⚠️ 不是 hostvds-ks-token |
| yecaoyun-香港 | 1d2fc8439594e38832931b7d5977d993 | ⚠️ 不是 yecaoyun-hk-token |
| racknerd-亚特兰大 | 460b8cc7d35e3b6db150443ceb95f719 | ⚠️ 不是 racknerd-atlanta-token |

## 验证
```bash
# 查看重连记录
grep 'reconnect success' /var/log/komari.log | tail -20

# 查看节点数据
sqlite3 /opt/komari/data/komari.db "select name, ipv4, ipv6, region, updated_at from clients order by name;"
```
