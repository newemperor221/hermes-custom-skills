# 架构简化实录 — 2026-05-27

## 背景

新加坡 isvoro (<新加坡_IP>:10425) 面板之前是三层代理架构：

```
cloudflared → tcp-proxy:25774 → galaxy-proxy:25775 + komari:25776
```

2026-05-27 简化为两层：

```
cloudflared → komari:25774 (原生Glass主题)
```

## 触发原因

1. 所有节点离线（records 表为 0），发现 tcp-proxy 路由 bug (`"/"` 匹配所有路径)
2. 修路由时 kill tcp-proxy，cloudflared 连不上（Alpine localhost → IPv6 `::1`）
3. cloudflared token 丢失（仅存进程 cmdline，kill 后拿不到）
4. 用户提供新 token 后恢复

## 操作步骤

```bash
# 1. 设置 DB 主题为 Glass
sqlite3 /opt/komari/data/komari.db "UPDATE configs SET value='\"Glass\"' WHERE key='theme';"

# 2. 杀旧代理 + 旧 komari
kill 12402 234586 467 484 2>/dev/null
sleep 2

# 3. komari 直接监听 25774
cd /opt/komari
nohup ./komari server -l 0.0.0.0:25774 > /tmp/komari-server-2.log 2>&1 &

# 4. cloudflared 指向 127.0.0.1（显式 IPv4）
kill 12429 2>/dev/null
sleep 5
nohup cloudflared tunnel --no-autoupdate run --token 'TOKEN' --url http://127.0.0.1:25774 > /tmp/cf.log 2>&1 &

# 5. 验证
curl -s -o /dev/null -w '%{http_code}' https://<监控面板域名>/  # 200
curl -s -o /dev/null -w '%{http_code}' https://<监控面板域名>/admin/  # 200
```

## 效果

| 指标 | 三层 | 两层 | 省 |
|------|------|------|----|
| 进程 | tcp-proxy + galaxy-proxy + komari | komari 仅 1 个 | -2 |
| RSS | ~101MB | ~77MB | ~24MB |
| 故障点 | 3 个任一挂就崩 | 1 个 | 省心 |

## 注意事项

- Glass 主题必须存在于 `/opt/komari/data/theme/{short}/dist/index.html` 路径
- komari 修改主题文件后需重启才能生效
- cloudflared 永远用 `--url http://127.0.0.1:25774`，不用 `localhost`
- 简化后 `/admin` 面板由 komari 原生提供，不再需要 proxy 透传
