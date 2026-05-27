# Hermes Custom Skills

用 Hermes Agent 过程中手工制作的 skill 集合，覆盖 VPS 运维、代理部署、监控面板、前端开发、备份恢复等场景。

## Skill 清单

### DevOps
| Skill | 说明 |
|-------|------|
| `cloudflare-r2-ops` | Cloudflare R2 存储桶管理 |
| `cloudflare-tunnel-ops` | Cloudflare Tunnel 全栈运维 |
| `docker-compose-patterns` | Docker Compose 生产级编排 |
| `docker-nginx-healthcheck-ipv6` | Nginx 健康检查 IPv6 修复 |
| `github-actions-self-hosted-runner` | 自有服务器部署 GH Actions Runner |
| `kanban-orchestrator` | Kanban 主流程编排 |
| `kanban-worker` | Kanban Worker 踩坑指南 |
| `multi-server-backup` | 多 VPS 自动化备份 |
| `nginx-production-config` | Nginx 生产配置 |
| `openhuman-core-deployment` | OpenHuman 头部应用部署 |
| `pre-deploy-verification` | 部署前语法/内容校验 |
| `prometheus-grafana-stack` | Prometheus + Grafana 监控栈 |
| `vps-finance` | VPS 财务资产管理 |
| `vps-init` | 新 VPS 全生命周期初始化 |
| `webhook-subscriptions` | Webhook 事件驱动 |

### Frontend / Glass 主题
| Skill | 说明 |
|-------|------|
| `glass-workflow` | Glass Komari 面板工程化工作流 |
| `galaxyglass-design-references` | Glass 主题设计参考 |
| `chrome-backdrop-filter-clip-path-fix` | Chrome 毛玻璃兼容修复 |
| `css-glassmorphism-backdrop-filter` | CSS 毛玻璃实现 |
| `frontend-css-resources` | CSS 前端工具箱 |
| `frontend-workflows` | 现代前端工作流 |
| `npm-package-to-browser` | npm 包转浏览器脚本 |
| `svelte-5-spa` | Svelte 5 SPA 构建 |
| `tab-heartbeat-online-count` | 真实在线人数追踪 |
| `web-perf-optimization` | 前端性能优化 |

### Sysadmin
| Skill | 说明 |
|-------|------|
| `image-batch-convert` | 批量图片格式转换 |
| `ip-sentinel-ops` | IP-Sentinel 资产养护系统 |
| `iptables-firewall` | iptables 防火墙全栈 |
| `linux-perf-toolkit` | Linux 性能分析工具箱 |
| `lxc-alpine-maintenance` | Alpine LXC 容器维护 |
| `lxc-probe-deploy` | LXC 探针部署 |
| `network-recon` | 网络侦察与排障 |
| `sing-box-ops` | sing-box 全生命周期运维 |
| `system-hardening` | 服务器安全加固 |
| `wireguard-vps-mesh` | WireGuard VPS 组网 |

### Server Health / 监控
| Skill | 说明 |
|-------|------|
| `server-health` | 一键巡检服务器健康 |
| `nodeget-ops` | NodeGet 探针面板运维 |
| `komari-server-ops` | Komari 监控面板运维 |
| `log-search` | 跨服务器日志搜索 |
| `sysadmin-toolkit` | 常用运维操作工具集 |

## 安装

```bash
git clone https://github.com/newemperor221/hermes-custom-skills.git ~/hermes-custom-skills
# 将需要的 skill 目录复制到 ~/.hermes/skills/ 对应分类下
cp -r ~/hermes-custom-skills/devops/* ~/.hermes/skills/devops/
# 其他分类同理
```

或者直接在 Hermes 配置中将此仓库添加为 external_dir。
