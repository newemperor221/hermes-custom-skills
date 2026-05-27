---
name: prometheus-grafana-stack
description: "Prometheus + Grafana + Alertmanager 监控全栈 — 指标采集、告警规则、仪表盘、节点探测。触发：\"Prometheus\"、\"Grafana\"、\"监控\"、\"告警\"、\"metrics\"、\"node_exporter\"。"
tags: [prometheus, grafana, monitoring, alerting, node-exporter, alertmanager]
---

# Prometheus + Grafana + Alertmanager 监控全栈

## 架构
```
node_exporter → Prometheus → Grafana (可视化)
                     ↓
              Alertmanager → Telegram/Slack/Email
```

## Docker Compose 部署
```yaml
version: "3.8"

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "127.0.0.1:9090:9090"
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - ./prometheus/rules:/etc/prometheus/rules:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.retention.time=30d'
      - '--storage.tsdb.retention.size=10GB'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "127.0.0.1:3000:3000"
    environment:
      GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD}
      GF_SERVER_ROOT_URL: https://grafana.example.com
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    depends_on:
      - prometheus
    networks:
      - monitoring

  alertmanager:
    image: prom/alertmanager:latest
    container_name: alertmanager
    restart: unless-stopped
    ports:
      - "127.0.0.1:9093:9093"
    volumes:
      - ./alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml:ro
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
    networks:
      - monitoring

  node-exporter:
    image: prom/node-exporter:latest
    container_name: node-exporter
    restart: unless-stopped
    ports:
      - "127.0.0.1:9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--path.rootfs=/rootfs'
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
```

## Prometheus 配置 (`prometheus/prometheus.yml`)
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - /etc/prometheus/rules/*.yml

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
        labels:
          instance: 'main-server'

  # 远程节点
  - job_name: 'remote-nodes'
    static_configs:
      - targets: ['10.0.1.5:9100', '10.0.1.6:9100']
        labels:
          env: 'production'

  # Nginx（需开启 stub_status）
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']

  # 应用自定义指标
  - job_name: 'myapp'
    metrics_path: /metrics
    static_configs:
      - targets: ['api:8000']
```

## 告警规则 (`prometheus/rules/node-alerts.yml`)
```yaml
groups:
  - name: node-alerts
    rules:
      - alert: HighCPU
        expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 80
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "CPU 使用率超过 80% ({{ $value }}%)"
          description: "实例 {{ $labels.instance }} CPU 持续高负载"

      - alert: HighMemory
        expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100 > 85
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "内存使用率超过 85% ({{ $value }}%)"

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 < 15
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "磁盘剩余空间不足 15%"

      - alert: InstanceDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "实例 {{ $labels.instance }} 宕机"

      - alert: HighLoadAverage
        expr: node_load1 / count(node_cpu_seconds_total{mode="idle"}) by (instance) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "负载均值超过 CPU 核心数 2 倍"
```

## Alertmanager 配置 (`alertmanager/alertmanager.yml`)
```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'instance']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'telegram'

  routes:
    - match:
        severity: critical
      receiver: 'telegram-critical'
      repeat_interval: 1h

receivers:
  - name: 'telegram'
    telegram_configs:
      - bot_token: '${TELEGRAM_BOT_TOKEN}'
        chat_id: ${TELEGRAM_CHAT_ID}
        parse_mode: 'HTML'

  - name: 'telegram-critical'
    telegram_configs:
      - bot_token: '${TELEGRAM_BOT_TOKEN}'
        chat_id: ${TELEGRAM_CHAT_ID}
        parse_mode: 'HTML'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

## 常用 PromQL 查询
```promql
# CPU 使用率
100 - (avg by(instance)(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)

# 内存使用率
(1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) * 100

# 磁盘使用率
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100

# 网络流量 (MB/s)
rate(node_network_receive_bytes_total{device="eth0"}[5m]) / 1024 / 1024

# HTTP 请求速率
rate(http_requests_total[5m])

# 错误率
rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100

# P95 延迟
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

## Grafana 导入仪表盘
- **Node Exporter Full**: ID 1860
- **Docker**: ID 893
- **Nginx**: ID 12708
- **PostgreSQL**: ID 9628

```bash
# API 导入
curl -X POST http://admin:pass@localhost:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d '{"dashboard": {"id": 1860}, "overwrite": true}'
```

## 排错
```bash
# Prometheus 配置检查
docker exec prometheus promtool check config /etc/prometheus/prometheus.yml

# 告警规则检查
docker exec prometheus promtool check rules /etc/prometheus/rules/*.yml

# 查看活跃告警
curl -s http://localhost:9090/api/v1/alerts | jq .

# Alertmanager 状态
curl -s http://localhost:9093/api/v2/status | jq .

# 测试告警路由
amtool config routes test --config.file=alertmanager.yml alertname=HighCPU severity=warning
```
