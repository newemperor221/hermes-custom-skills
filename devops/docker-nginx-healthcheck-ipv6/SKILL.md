---
name: docker-nginx-healthcheck-ipv6
description: Docker Compose 部署 nginx 时健康检查 localhost 连接被拒绝的修复 — localhost 在容器内解析为 IPv6 ::1，但 nginx 只监听 IPv4
---

# Docker nginx 健康检查 IPv6 问题

## 触发场景
Docker Compose 部署 nginx，健康检查配置使用 `localhost`：
```yaml
healthcheck:
  test: ["CMD", "wget", "-q", "--spider", "http://localhost/"]
```

容器日志报错：`wget: can't connect to remote host (::1): Connection refused`

## 根因
Docker 容器内 `localhost` 默认解析为 IPv6 `::1`，而 nginx 容器只监听 IPv4 `0.0.0.0:80`，导致连接被拒绝。健康检查持续失败，容器始终处于 `unhealthy` 状态。

## 修复
健康检查改用 `127.0.0.1` 而非 `localhost`：
```yaml
healthcheck:
  test: ["CMD", "wget", "-q", "--spider", "http://127.0.0.1/"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 10s
```

## 验证
```bash
docker compose up -d --force-recreate nginx
docker ps  # 等待 Status 变为 "(healthy)"
```

## 预防
Docker 健康检查、容器内 curl/wget 目标地址一律使用 `127.0.0.1`，不要用 `localhost`。容器内 `localhost` 行为依赖宿主机的 `/etc/hosts` 配置，Docker 默认会添加 `::1 localhost` 条目。

## 适用版本
- Docker Engine 所有版本
- 任何使用 Dockerfile HEALTHCHECK 或 docker-compose healthcheck 的镜像
