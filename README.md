# Hermes Custom Skills

本人在用 Hermes Agent 过程中自制的 skill 集合，覆盖日常运维、性能优化、备份等场景。

## 安装

```bash
git clone https://github.com/newemperor221/hermes-custom-skills.git
# 将 skills/ 下的目录复制到 ~/.hermes/skills/ 对应分类下
```

## Skills

| 技能 | 分类 | 说明 |
|------|------|------|
| `cloudflare-r2-ops` | devops | Cloudflare R2 存储桶管理（rclone/AWS CLI） |
| `multi-server-backup` | devops | 多 VPS 自动化备份（rsync + Borg） |
| `image-batch-convert` | sysadmin | 批量图片格式转换（PNG→WebP, MP4→WebM） |
| `wireguard-vps-mesh` | sysadmin | WireGuard 多 VPS 组网 |
| `web-perf-optimization` | frontend | 前端性能优化（Lighthouse/缓存/字体） |

## License

MIT
