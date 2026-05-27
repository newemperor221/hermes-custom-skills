# galaxy-proxy 恢复流程（服务器重建后丢失时）

## 背景

galaxy-proxy.py 是一个 Python 反向代理，位于 Cloudflare tunnel 和 Komari server 之间：

```
cloudflared → galaxy-proxy.py(:25774) → komari(:25776)
```

它负责两件事：
1. 拦截 `/themes/Glass/*` 请求，从 `/opt/komari/data/theme/` 读取自定义主题文件（komari-theme.json、icon.svg、preview.webp）
2. 其余请求代理到 komari server

**没有 proxy 时：** `/themes/Glass/komari-theme.json` 返回 komari 内置默认主题的 JSON，所有面板配置（壁纸 URL 设置等）消失。

## 恢复步骤

### 1. SCP proxy 脚本到服务器

```bash
scp -o StrictHostKeyChecking=no -i $HOME/.ssh/user_key -P 10425 \
  ~/glass/galaxy-proxy.py \
  root@140.245.97.144:/opt/komari/data/theme/
```

### 2. 停 komari server 并改端口

```bash
ssh -o StrictHostKeyChecking=no -i $HOME/.ssh/user_key -p 10425 root@140.245.97.144 \
  'pkill -f "komari server"'
```

### 3. 启动 komari 在 25776

```bash
ssh -o StrictHostKeyChecking=no -i $HOME/.ssh/user_key -p 10425 root@140.245.97.144 \
  'cd /opt/komari && nohup ./komari server -l :25776 -d /opt/komari/data/komari.db > /tmp/komari.log 2>&1 &'
```

### 4. 启动 proxy 在 25774

```bash
ssh -o StrictHostKeyChecking=no -i $HOME/.ssh/user_key -p 10425 root@140.245.97.144 \
  'cd /opt/komari/data/theme && nohup python3 galaxy-proxy.py > /tmp/proxy.log 2>&1 &'
```

### 5. 验证

```bash
# 检查端口
ssh -o StrictHostKeyChecking=no -i $HOME/.ssh/user_key -p 10425 root@140.245.97.144 \
  "ss -tlnp | grep -E '2577[46]'"
# 应看到: 25774 → python3 (proxy), 25776 → komari

# 验证主题 JSON
curl -s "https://stat.357561.xyz/themes/Glass/komari-theme.json" | grep wallpaper
# 应返回 静态壁纸 URL / 动态壁纸 URL 字段
```

## 关键路由规则

| 路径 | 代理行为 |
|------|---------|
| `/` | 从 `/opt/komari/data/theme/index.html` 返回 Glass 主题 |
| `/instance/*` | 同上（SPA 路由） |
| `/themes/Glass/*` | 从 `/opt/komari/data/theme/` 返回对应文件 |
| `/admin/*` | **必须代理到 komari** — 管理员后台 SPA 由 komari 内置 |
| `/api/*` | 代理到 komari |
| `/assets/*` | 代理到 komari（admin SPA 资源） |

**⚠️ 常见错误：** 把 `/admin/*` 路由到 Glass 的 `index.html`，导致 admin 页面显示的是探针首页而非后台管理页面。

## 为何会丢失

galaxy-proxy.py 在以下情况下丢失：
- 服务器重装（LXC 重建）
- 手动清理 `/opt/komari/data/theme/`

**当前服务器：** 新加坡主控 `140.245.97.144:10425`，proxy 文件在本地 `~/glass/galaxy-proxy.py`。
