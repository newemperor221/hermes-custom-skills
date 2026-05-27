# Galaxy Proxy 静态文件路由陷阱

日期：2026-05-19
场景：部署 Astro 5 静态输出到 `galaxy-proxy.py` 后端

## 问题

Astro 构建产物放在 `/opt/komari/data/theme/` 后，页面显示导航栏和背景，但 React 组件（DashboardContent）不渲染，数据区域空白。控制台无 JS 错误。

## 根因

`galaxy-proxy.py` 的 `do_GET()` 方法使用白名单路由策略：

```python
# 只对以下路径调用 _serve_static()
if clean_path.startswith("/styles/") or clean_path.startswith("/scripts/") \
   or clean_path.startswith("/_app/") or clean_path.startswith("/_next/"):
    rel = clean_path.lstrip("/")
    return self._serve_static(rel)
```

Astro 的 JS/CSS 文件在 `/_astro/` 目录下，不在白名单中。请求 `/_astro/DashboardContent.B-QvomF5.js` 时：

1. 不匹配任何静态文件前缀 → 跳过
2. fallback 到通用 handler → 找不到 `_astro/DashboardContent.B-QvomF5.js.html` 或 `_astro/DashboardContent.B-QvomF5.js/index.html`
3. 最终 `self.path = "/index.html"` → 返回 `index.html`（`Content-Type: text/html`）
4. 浏览器收到 HTML 内容但期望 JS → `<script>` 标签静默失败，模块不执行

## 诊断方法

```bash
# 检查 content-type 是否正常
curl -s -o /dev/null -w "HTTP %{http_code} content-type: %{content_type}\n" \
  http://localhost:25774/_astro/DashboardContent.B-QvomF5.js
# ❌ 错误：HTTP 200 content-type: text/html
# ✅ 正确：HTTP 200 content-type: application/javascript

# 也检查 size
curl -s -o /dev/null -w "size: %{size_download}\n" \
  http://localhost:25774/_astro/DashboardContent.B-QvomF5.js
# ❌ 错误：size: 10903（index.html 的大小）
# ✅ 正确：size: 21840（实际 JS 大小）
```

浏览器端探测：
```js
fetch('/_astro/Some.file.js', {method: 'HEAD'})
  .then(r => console.log(r.status, r.headers.get('content-type')))
```

## 修复

在 `do_GET()` 的静态文件白名单中添加 `/_astro/`：

```python
if clean_path.startswith("/styles/") or clean_path.startswith("/scripts/") \
   or clean_path.startswith("/_app/") or clean_path.startswith("/_next/") \
   or clean_path.startswith("/_astro/"):   # ← 添加这行
    rel = clean_path.lstrip("/")
    return self._serve_static(rel)
```

## 通用模式

每次更换前端框架后，新框架的静态资产目录必须加入此白名单：

| 框架 | 资产目录 | 是否已加 |
|------|---------|---------|
| Next.js | `/_next/` | ✅ |
| Astro | `/_astro/` | ✅ (2026-05-19 新增) |
| SvelteKit | `/_app/` | ✅ |
| Vite/React SPA | `/assets/` | ❌ 需要时加 |
| 静态版 | 无（全内联） | ✅ 不需要 |
