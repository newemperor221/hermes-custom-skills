# GalaxyGlass 部署架构与操作实录 — 已过时 ⚠️

**2026-05-19：本文件描述的架构已过时。** 当前架构见 `references/komari-theme-deploy-20260519.md`。

## 主要变化

| 旧（本文件） | 新（当前） |
|------|------|
| galaxy-proxy.py 作为中间代理 | Komari 1.2.0 原生主题系统 |
| `/opt/komari/data/theme/` 根目录 | `GalaxyGlass/dist/` 子目录 |
| proxy 转发 API 到 komari :25776 | Komari server 同时 serve 前端 + API |

以下为历史记录，仅供参考，**不要按此操作**。
