---
name: nginx-production-config
description: "Nginx 生产级配置 — 反向代理、SSL/TLS、负载均衡、限流、安全头、缓存。触发：\"nginx\"、\"反向代理\"、\"SSL配置\"、\"负载均衡\"、\"限流\"、\"443\"。"
tags: [nginx, reverse-proxy, ssl, load-balancing, rate-limit, security-headers]
---

# Nginx 生产级配置

## 反向代理 + SSL（最常用）

```nginx
# /etc/nginx/sites-available/myapp.conf

# HTTP → HTTPS 重定向
server {
    listen 80;
    listen [::]:80;
    server_name example.com;
    return 301 https://$host$request_uri;
}

# HTTPS 主配置
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name example.com;

    # SSL 证书
    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    # SSL 安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;

    # OCSP Stapling
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 8.8.8.8 8.8.4.4 valid=300s;

    # 安全头
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;

    # 静态文件
    location /static/ {
        alias /var/www/myapp/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
        access_log off;
    }

    # API 反向代理
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";

        # 超时
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # 缓冲
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
    }

    # 健康检查端点
    location /health {
        proxy_pass http://127.0.0.1:8000/health;
        access_log off;
    }

    # 禁止访问隐藏文件
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

## 限流配置

```nginx
# 在 http 块中定义
http {
    # 按 IP 限流
    limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

    # 按 IP 连接数限制
    limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

    server {
        # API 限流：每秒 10 请求，突发 20
        location /api/ {
            limit_req zone=api_limit burst=20 nodelay;
            limit_conn conn_limit 10;
            limit_req_status 429;

            # 自定义 429 页面
            error_page 429 = @rate_limit_exceeded;
        }

        location @rate_limit_exceeded {
            return 429 '{"error": "Rate limit exceeded"}';
            add_header Content-Type application/json;
        }
    }
}
```

## 负载均衡

```nginx
http {
    upstream backend {
        least_conn;  # 最少连接算法
        # 或: ip_hash;  # IP 哈希（会话保持）
        # 或: random two least_conn;  # 随机两个选最少连接

        server 10.0.1.1:8000 weight=3 max_fails=3 fail_timeout=30s;
        server 10.0.1.2:8000 weight=2 max_fails=3 fail_timeout=30s;
        server 10.0.1.3:8000 backup;  # 备用节点

        keepalive 32;  # 保持连接池
    }

    server {
        location / {
            proxy_pass http://backend;
            proxy_next_upstream error timeout http_502 http_503;
            proxy_next_upstream_tries 2;
        }
    }
}
```

## Gzip 压缩

```nginx
http {
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 4;
    gzip_min_length 256;
    gzip_types
        text/plain
        text/css
        text/javascript
        application/json
        application/javascript
        application/xml
        application/rss+xml
        image/svg+xml;
}
```

## 日志配置

```nginx
http {
    # JSON 格式日志（便于 ELK 解析）
    log_format json_combined escape=json
        '{'
            '"time":"$time_iso8601",'
            '"remote_addr":"$remote_addr",'
            '"method":"$request_method",'
            '"uri":"$request_uri",'
            '"status":$status,'
            '"body_bytes_sent":$body_bytes_sent,'
            '"request_time":$request_time,'
            '"upstream_response_time":"$upstream_response_time",'
            '"http_user_agent":"$http_user_agent",'
            '"http_x_forwarded_for":"$http_x_forwarded_for"'
        '}';

    access_log /var/log/nginx/access.log json_combined;
    error_log /var/log/nginx/error.log warn;
}
```

## 常用运维命令
```bash
# 测试配置
nginx -t

# 重载（不断线）
nginx -s reload

# 查看连接数
ss -s | grep estab
curl -s http://localhost/nginx_status  # 需要 stub_status

# 日志分析
# Top 10 IP
awk '{print $1}' /var/log/nginx/access.log | sort | uniq -c | sort -rn | head -10

# Top 10 慢请求
awk '{print $NF, $7}' /var/log/nginx/access.log | sort -rn | head -10

# 错误统计
awk '$9 >= 400' /var/log/nginx/access.log | awk '{print $9}' | sort | uniq -c | sort -rn
```

## 常见坑
1. **proxy_pass 尾部斜杠** → `proxy_pass http://backend/` 会吃掉 location 前缀
2. **502 Bad Gateway** → 上游服务未启动或端口错误
3. **SSL 证书路径错误** → 必须用 fullchain.pem 而非 cert.pem
4. **配置不生效** → 检查 sites-enabled 软链接
5. **413 Request Entity Too Large** → 调大 `client_max_body_size`
