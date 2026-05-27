# Komari 1.2.0 主题系统部署实录

日期：2026-05-19
场景：将 GalaxyGlass 静态版部署到线上 <监控面板域名>

## 核心发现

### 架构

```
用户浏览器 → <监控面板域名> (Cloudflare CDN)
  ↓
cloudflared tunnel (从 ccs-la2 SSH 到波兰 Master 执行)
  ↓
Poland Master (<荷兰_IP>) → komari server :25774
  ↓
/opt/komari/data/theme/GalaxyGlass/dist/index.html ← 自定义首页！
```

**关键：** cloudflared tunnel 是指向 `http://127.0.0.1:25774`（Komari server），不是 proxy。

### 主题文件读取路径

Komari 1.2.0 的主题系统读取路径：
```
/opt/komari/data/theme/
  └── GalaxyGlass/                ← 主题名必须匹配 API 返回的 "theme" 字段
      ├── komari-theme.json       ← 必选（JSON 清单）
      └── dist/                   ← 实际静态文件所在目录
          ├── index.html          ← ✅ 替换此文件即可更新首页
          ├── detail.html (...)
          └── _astro/ (...)
```

**文件结构必须严格遵循。** 直接把文件扔到 `/opt/komari/data/theme/` 根目录无效——Komari 只读子目录。

### komari-theme.json 格式

```json
{
  "name": "GalaxyGlass",
  "short": "GalaxyGlass",
  "description": "A modern server monitor with deep space glass design.",
  "version": "2.7.0",
  "author": "newemperor221"
}
```

### 热更新

Komari 1.2.0 **不需要重启**即可读取新文件。替换 `index.html` 后立即生效。验证：

```bash
# 部署前
curl -s http://127.0.0.1:25774/ | wc -c
# 10903 ← 旧版（Astro / 内置 UI）

# 部署后
curl -s http://127.0.0.1:25774/ | wc -c
# 97606 ← 新版（静态版全内联）
```

## 部署流程

### 使用 deploy.sh（推荐）

```bash
cd ~/galaxy-glass
bash deploy.sh
```

deploy.sh 实际操作：
1. `scp index.html root@<荷兰_IP>:/tmp/index-static.html`
2. `ssh` 到波兰，执行：
   - `rm -rf /opt/komari/data/theme/GalaxyGlass/dist/`（清理旧文件）
   - `cp /tmp/index-static.html /opt/komari/data/theme/GalaxyGlass/dist/index.html`

### 手动

```bash
scp -P 46748 -i ~/.ssh/hermes_admin \
  ~/galaxy-glass/index.html \
  root@<荷兰_IP>:/opt/komari/data/theme/GalaxyGlass/dist/index.html

# 验证
ssh -p 46748 -i ~/.ssh/hermes_admin root@<荷兰_IP> \
  "curl -s http://127.0.0.1:25774/ | wc -c"
```

## 各端口的用途

| 服务器 | 端口 | 进程 | 用途 |
|--------|------|------|------|
| Poland Master | 25774 | komari server | Web UI + API 后端，cloudflared 指向此 |
| Poland Master | 45774 | socat | 端口转发（25774 → 45774），agent 连接 |
| Poland Master | 46748 | sshd | SSH 登录端口 |
| Poland Master | 22 | sshd | LXC 默认 SSH |
| ccs-la2 | 25774 | galaxy-proxy.py | 开发代理，serve 本地 theme 目录 |
| ccs-la2 | 26080 | komari-old | 旧版 komari server（已弃用） |
| ccs-la2 | 9113 | ? | 未识别 |

## 新旧架构对比

### 旧架构（deprecated）

```
cloudflared → galaxy-proxy.py (:25774) → 读 /opt/komari/data/theme/index.html
                                      → 代理 API 到 komari (:25776)
```

### 当前架构（2026-05-19）

```
cloudflared → komari server 1.2.0 (:25774) → 内置 UI + 自定义主题
                                            → 主题从 GalaxyGlass/dist/ 读取
                                            → /admin 由内置 UI 处理
                                            → / 由 index.html 覆盖
```

**变化原因：** galaxy-proxy.py 是开发/中转方案，Komari 1.2.0 自身支持主题系统后无需额外代理。

## 踩坑记录

1. **部署到根目录无效：** `scp ... :/opt/komari/data/theme/index.html` → curl 还是返回旧页面。必须部署到 `GalaxyGlass/dist/`。
2. **Cloudflare 缓存：** 修改后如果 CF 缓存旧版，需要强制刷新（?v=1 参数）或清除 CF 缓存。
3. **dist/ 目录需手动清理：** 从 Astro 切回静态版时，`dist/` 下残留的 `_astro/` 子目录和 `detail.html` **不碍事**——Komari 只读 `index.html`。但 deploy.sh 还是清理了保持整洁。
4. **SSH 密钥：** 当前仅接受 `~/.ssh/hermes_admin` 密钥登录（密码认证已禁用）。
