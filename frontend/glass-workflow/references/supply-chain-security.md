# 供应链安全 — node-ipc 投毒事件

> 2026-05-14 记录。适用环境：Hermes Agent、Glass 主题开发、Komari 探针面板服务器。

## 事件概要

| 项目 | 内容 |
|------|------|
| 时间 | 2026-05-14 ~14:25 UTC |
| 包名 | `node-ipc`（npm，350万+ 月下载量） |
| 恶意版本 | `9.1.6`, `9.2.3`, `12.0.1` |
| 攻击方式 | 维护者账号被黑，恶意代码写入 CommonJS 入口 `node-ipc.cjs` |
| 载荷行为 | 收集环境变量、SSH 密钥、云凭证、K8s 配置、AI API Key，通过 DNS TXT 查询外泄 |
| 外泄目标 | `sh.azurestaticprovider.net:443`，编码后缀 `bt.node.js` |
| 相关恶意软件 | Mini-Shai Hulud worm（自复制蠕虫） |

## Hermes Agent 受影响范围

Hermes Agent **不直接依赖** node-ipc（纯 Python 项目）。以下组件使用 Node.js：
- **TUI（Ink 终端）** — `ui-tui/` 目录，但不装 node_modules，无运行时依赖
- **Web/Website** — 同样不装 node_modules

**风险来源**：如果开发机器上其他项目（非 Hermes）安装了恶意版本的 node-ipc，或 CI 环境中执行了 `npm install`。

## 检查是否为受影响版本

```bash
npm ls node-ipc 2>/dev/null
# 如果输出 ✅ (empty) 或版本号 12.0.0 / 9.2.2 / 9.1.5 以下 → 安全
# 如果输出 9.1.6 / 9.2.3 / 12.0.1 → 已中招
```

## 修复

```bash
# 降级到安全版本
npm install node-ipc@12.0.0   # 或 9.2.2 / 9.1.5

# 全局搜索恶意版本
npm ls -g node-ipc 2>/dev/null

# 扫描是否已被感染
# nisten/shaiscan — https://github.com/nisten/shaiscan
```

## 系统级防护

### 最低包龄限制（阻止新发布恶意包）

设置 npm 的 `max-age`（安装时拒绝 <24h 的包）：

```bash
# npm 自身不带此功能，用第三方工具
npm install -g npm-package-age
npm config set package-age-minimum 86400000  # 24 小时
```

### PyPI 对应防护（pip）

```bash
# 安装时检查包龄
pip install pip-age-check
```

### 通用防护

- **沙箱运行**：Hermes/Agent 跑在 Docker 或 VM 中
- **专用 API Key**：每个 agent/机器独立 API Key，存在密码管理器（1Password/Bitwarden）
- **最小权限**：agent 只给需要的 key，不给整个 `.env` 文件

## 扫描工具

- [nisten/shaiscan](https://github.com/nisten/shaiscan) — Mini-Shai Hulud 蠕虫专杀
- [tiamat.live/scan](https://tiamat.live/scan) — 免费 npm/PyPI 供应链扫描
- `ghcr.io/nisten/shaisan` — Docker 镜像版
