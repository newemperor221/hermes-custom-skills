---
name: docker-compose-patterns
description: "Docker Compose 生产级编排 — 多服务编排、健康检查、日志收集、资源限制、网络隔离。触发：\"docker-compose\"、\"容器编排\"、\"多服务部署\"、\"compose\"。"
tags: [docker, compose, orchestration, containers, production]
---

# Docker Compose 生产级编排

## 标准模板 (`docker-compose.yml`)
```yaml
version: "3.8"

services:
  # === 应用层 ===
  api:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    container_name: myapp-api
    restart: unless-stopped
    ports:
      - "127.0.0.1:8000:8000"  # 只监听 localhost
    environment:
      - DATABASE_URL=postgresql://app:${DB_PASSWORD}@postgres:5432/mydb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 5s
      retries: 3
      start_period: 10s
    deploy:
      resources:
        limits:
          cpus: "2.0"
          memory: 1G
        reservations:
          cpus: "0.5"
          memory: 256M
    networks:
      - frontend
      - backend
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
    labels:
      - "com.myapp.service=api"
      - "com.myapp.env=production"

  # === 数据库 ===
  postgres:
    image: postgres:16-alpine
    container_name: myapp-postgres
    restart: unless-stopped
    environment:
      POSTGRES_DB: mydb
      POSTGRES_USER: app
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d mydb"]
      interval: 10s
      timeout: 5s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 512M
    networks:
      - backend

  # === 缓存 ===
  redis:
    image: redis:7-alpine
    container_name: myapp-redis
    restart: unless-stopped
    command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3
    networks:
      - backend

  # === 反向代理 ===
  nginx:
    image: nginx:alpine
    container_name: myapp-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - certbot_data:/var/www/certbot:ro
    depends_on:
      - api
    networks:
      - frontend

  # === SSL 证书 ===
  certbot:
    image: certbot/certbot
    container_name: myapp-certbot
    volumes:
      - certbot_data:/var/www/certbot
      - ./nginx/ssl:/etc/letsencrypt
    entrypoint: "/bin/sh -c 'trap exit TERM; while :; do certbot renew; sleep 12h & wait $${!}; done'"

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local
  certbot_data:
    driver: local

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true  # 不暴露到外部
```

## 关键模式

### 1. 健康检查 + 依赖
```yaml
# 服务必须健康后才启动依赖它的服务
depends_on:
  db:
    condition: service_healthy  # 不是 service_started
```

### 2. 网络隔离
```yaml
networks:
  frontend:    # 外部可访问（nginx、api）
    driver: bridge
  backend:     # 内部专用（api、db、redis）
    driver: bridge
    internal: true  # 无法访问外网
```

### 3. 资源限制
```yaml
deploy:
  resources:
    limits:
      cpus: "2.0"
      memory: 1G
    reservations:
      memory: 256M
```

### 4. 日志管理
```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"   # 单文件最大 10MB
    max-file: "3"     # 最多 3 个文件
```

### 5. 环境变量管理
```bash
# .env 文件（不提交到 git）
DB_PASSWORD=supersecret
API_KEY=xxx

# docker-compose.yml 引用
environment:
  - DB_PASSWORD=${DB_PASSWORD}
```

## 运维命令
```bash
# 启动（后台）
docker compose up -d

# 查看状态
docker compose ps
docker compose logs -f api --tail 100

# 重建（代码变更后）
docker compose build --no-cache api
docker compose up -d api

# 进入容器
docker compose exec api bash
docker compose exec postgres psql -U app mydb

# 清理
docker compose down              # 停止并删除容器
docker compose down -v           # 同时删除 volumes
docker system prune -af          # 清理所有未使用资源

# 扩展
docker compose up -d --scale api=3  # 水平扩展
```

## 常见坑
1. **depends_on 不等健康** → 必须用 `condition: service_healthy`
2. **环境变量泄露** → `.env` 加入 `.gitignore`
3. **volume 权限** → 容器内用户 UID 和宿主机不匹配
4. **日志撑爆磁盘** → 必须配置 `max-size` 和 `max-file`
5. **网络不通** → 检查 `internal: true` 是否阻止了出站
6. **端口冲突** → 用 `127.0.0.1:8000:8000` 只监听本地
