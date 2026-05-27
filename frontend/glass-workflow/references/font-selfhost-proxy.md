# 字体自托管：galaxy-proxy.py 修改全参考

## 架构

```
Cloudflare → cloudflared(:443) → galaxy-proxy.py(:25774) → Komari(:25776)
                                      ↓
                             静态文件 /opt/komari/data/theme/
```

galaxy-proxy.py 是 Flask-style 的 Python HTTP 反向代理（ThreadingMixIn + HTTPServer），运行在 Alpine Linux 上，由 OpenRC 管理。

## galaxy-proxy.py 需要修改的位置

### 1. MIME 类型映射（`_serve_static` 方法）

```python
ct_map = {".css": "text/css", ".js": "application/javascript",
           ".html": "text/html", ".json": "application/json",
           ".svg": "image/svg+xml", ".png": "image/png",
           ".ttf": "font/ttf", ".woff2": "font/woff2"}
```

**⚠️ 注意**：最后一项 `.woff2` 后面必须紧跟 `}` 闭合字典。用 sed 替换时容易吃掉花括号，导致 SyntaxError。

### 2. 路由注册（`do_GET` 方法）

在 `/styles/` / `/scripts/` 等静态路由之后、Try static file 之前添加：

```python
if clean_path.startswith("/fonts/"):
    rel = clean_path.lstrip("/")
    return self._serve_static(rel)
```

### 3. 静态文件目录

`THEME_DIR = "/opt/komari/data/theme"` 是所有静态文件的根目录。
所以 `/fonts/Inter-400.ttf` → 文件位于 `/opt/komari/data/theme/fonts/Inter-400.ttf`

## 服务管理（Alpine OpenRC）

```bash
rc-service galaxy-proxy restart     # 重启
rc-service galaxy-proxy status      # 检查状态（正常: "started"）
rc-update add galaxy-proxy default  # 开机自启
```

## 验证方法

```bash
# 本地直测
curl -v "http://127.0.0.1:25774/fonts/Inter-400.ttf" 2>&1 | grep -E "Content-Type|Content-Length|HTTP"
# 期望: Content-Type: font/ttf, Content-Length: 324820

# 通过 Cloudflare（加 ?v=N 防缓存）
curl -sI "https://stat.357561.xyz/fonts/Inter-400.ttf?v=1" -o /dev/null -w "CT: %{content_type}\n"
# 期望: CT: font/ttf
```

## 常见故障

| 现象 | 原因 | 解决 |
|---|---|---|
| 返回 `text/html` 空内容 | Cloudflare 缓存旧响应 | 加 `?v=N` query param 或等待缓存过期 |
| 返回 200 但 `Content-Type: application/octet-stream` | MIME 映射缺少 `.ttf` | 在 ct_map 添加 `".ttf": "font/ttf"` |
| 页面字体还是等宽 | 部署的 index.html 是旧版，@font-face 仍指向 fonts.gstatic.com | 重新 build + deploy |

## 字体文件来源

从 Google Fonts 下载 Inter TTF（现代浏览器 with `font-display:swap` 也不需要 woff2）：

```bash
curl -sL -o Inter-400.ttf \
  "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfMZg.ttf"
```

URL 中的 hash（`UcCO...MZg`）会随 Inter 版本更新变化，从以下地址获取最新：
`https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap`
