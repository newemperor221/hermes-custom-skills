# Proxy + SvelteKit Module Import 调试记录

## 背景
2026-05-16 SvelteKit 构建的 GalaxyGlass 部署到 <监控面板域名>，通过 galaxy-proxy.py 代理 `_app/` 静态文件。浏览器白屏，SvelteKit 未初始化。

## 症状
- 页面加载后空白，`<div style="display:contents">` 中只有原始 `<script>` 标签
- `import("/_app/immutable/entry/start.xxx.js")` 报 `TypeError: Failed to fetch dynamically imported module`
- 但 `fetch()` 同一 URL 正常（200 OK, 正确的 Content-Type, 正确的 body）

## 排查步骤

### 1. 确认响应头正确
```js
fetch('/_app/immutable/entry/start.xxx.js').then(r => {
  console.log(r.status, r.headers.get('content-type'), r.headers.get('x-content-type-options'));
})
```
结果：`200 application/javascript; charset=utf-8 nosniff` ✅

### 2. 排除 CORS/缓存
- 同源（<监控面板域名>），无 CSP 限制
- `Cache-Control: no-cache, no-store, must-revalidate` → 浏览器不缓存
- Cloudflare `cf-cache-status: BYPASS`

### 3. 确认文件可访问
- Performance API 显示所有 chunk 已成功下载（transferSize > 0）
- GET 响应 body 82 bytes，是有效的 ES module

### 4. 排除浏览器兼容问题
- `import('data:text/javascript,export default 42')` 成功 ✅
- `import(window.location.origin + '/_app/...')` 也失败 ❌
- 移除 `<link rel="modulepreload">` 后重试 → 仍然失败

## 最可疑元凶

**Cloudflare zstd 压缩（`content-encoding: zstd`）与模块加载器交互异常。**

- 所有通过 Cloudflare 代理的 GET 响应被自动 zstd 压缩
- `fetch()` 的 Fetch API 能正常解压 zstd
- 但浏览器的 ES module 加载器（`import()` 内部）在处理 zstd 压缩模块时可能有问题
- 这是一个 **Headless Chrome 148** 测试环境，真实浏览器可能无此问题

## 验证方法（下一轮排查）

1. **真实浏览器测试**：用户用自己的 Chrome/Firefox 打开 `<监控面板域名>` 看是否正常
2. **禁用 Cloudflare 压缩**：在 Cloudflare Dashboard → Speed → Optimization → Brotli 关闭，或添加 `Accept-Encoding: identity` 策略
3. **改用 `<script type="module" src="...">`**：测试非动态 import 方式
4. **改用 text/javascript**：测试旧 MIME 类型兼容性

## 已知正确的配置

galaxy-proxy.py 的 `_serve_static()` 正确设置了：
```python
self.send_header("Content-Type", "application/javascript")
self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
self.send_header("Pragma", "no-cache")
self.send_header("Expires", "0")
```

`do_HEAD` 未覆盖会导致 HEAD 请求绕过自定义路由（见 skill pitfall 1b）。
