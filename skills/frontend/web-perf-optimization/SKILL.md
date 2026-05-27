---
name: web-perf-optimization
description: 前端性能优化实战 — Lighthouse 自动化审核、Core Web Vitals 优化、缓存策略、图片懒加载、字体优化、CDN 预热。覆盖 <监控面板域名> 等自托管站点。触发："性能优化"、"Lighthouse"、"页面慢"、"优化网站"、"Core Web Vitals"、"缓存"、"preload"、"懒加载"。
---

# Web 性能优化

## 适用场景

- 自托管静态站点（<监控面板域名>、GalaxyGlass 等）速度优化
- Lighthouse / PageSpeed Insights 评分提升
- Core Web Vitals（LCP、FID、INP、CLS）优化
- 减少首屏加载时间
- 优化缓存策略减少回源

## 核心指标

| 指标 | 全称 | 含义 | 好 |
|------|------|------|------|
| **LCP** | Largest Contentful Paint | 最大内容渲染 | <2.5s |
| **INP** | Interaction to Next Paint | 交互响应延迟 | <200ms |
| **CLS** | Cumulative Layout Shift | 布局偏移 | <0.1 |
| **FCP** | First Contentful Paint | 首次内容渲染 | <1.8s |
| **TBT** | Total Blocking Time | 总阻塞时间 | <200ms |

## 分析工具

```bash
# CLI Lighthouse（需要 Node.js）
npx lighthouse https://<监控面板域名> --view --chrome-flags="--headless"

# 输出 JSON 报告
npx lighthouse https://<监控面板域名> --output json --output-path ./lighthouse-report.json

# 在线
# - https://pagespeed.web.dev/
# - 浏览器 DevTools → Lighthouse 标签
```

## 优化策略（按重要性排序）

### 1. 图片优化（最高 ROI）

```html
<!-- WebP 优先，fallback 到原格式 -->
<picture>
  <source srcset="image.webp" type="image/webp">
  <img src="image.png" alt="" loading="lazy" width="800" height="600">
</picture>

<!-- 或为不支持 WebP 的古老浏览器准备 -->
<img src="image.webp" alt="" onerror="this.src=this.src.replace('.webp','.png')">

<!-- 给关键图片加 fetchpriority="high"（首屏可见的 hero 图） -->
<img src="hero.webp" alt="" fetchpriority="high" width="1200" height="600">
```

关键属性：
- `loading="lazy"` — 滚动到视口才加载，节省流量
- `fetchpriority="high"` — LCP 图片必须加，提示浏览器优先下载
- `width` + `height` — 防止 CLS 布局抖动
- `decoding="async"` — 异步解码，不阻塞渲染

### 2. 字体优化

自托管字体（用户偏好）且禁止等宽字体：

```html
<!-- 在 <head> 中 preload 关键字体 -->
<link rel="preload" href="/fonts/inter-var.woff2" as="font" type="font/woff2" crossorigin>

<!-- 使用 font-display: swap 避免 FOIT（隐藏文字） -->
<style>
@font-face {
  font-family: 'Inter';
  src: url('/fonts/inter-var.woff2') format('woff2');
  font-display: swap;
  /* subset: 如果只用了拉丁字符，可以只加载 latin subset 减少体积 */
  unicode-range: U+0000-00FF, U+0131, U+0152-0153, U+02BB-02BC, U+02C6, U+02DA, U+02DC, U+2000-206F, U+2074, U+20AC, U+2122, U+2191, U+2193, U+2212, U+2215;
}
</style>
```

优化要点：
- **只加载 woff2**（压缩率最高，浏览器支持 >96%）
- **font-display: swap** — 先用 fallback 字体显示文字，Web 字体加载完后替换，避免空白文本（FOIT）
- **unicode-range** — 只加载你用到的字符
- **preload** — 提前下载关键字体

### 3. 关键 CSS 内联

```html
<head>
  <!-- 首屏关键 CSS 直接内联 -->
  <style>
    /* 只包含首屏渲染需要的样式 */
    body { margin: 0; font-family: system-ui, sans-serif; }
    .hero { ... }
    /* 限 15KB 以内 */
  </style>

  <!-- 非关键 CSS 异步加载 -->
  <link rel="preload" href="/styles/main.css" as="style" onload="this.rel='stylesheet'">
  <noscript><link rel="stylesheet" href="/styles/main.css"></noscript>
</head>
```

### 4. 缓存策略（nginx）

nginx 配置：

```nginx
# 静态资源强缓存
location /fonts/ {
    expires 365d;
    add_header Cache-Control "public, immutable";
}

location /images/ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location ~* \.(webp|png|jpg|jpeg|gif|ico)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}

location ~* \.(css|js)$ {
    expires 7d;
    add_header Cache-Control "public, immutable";
}

# HTML 不缓存（确保更新）
location / {
    expires -1;
    add_header Cache-Control "no-cache";
}

# 如果通过 Cloudflare，添加浏览器缓存指令
location / {
    add_header Cache-Control "public, max-age=0, s-maxage=86400";
}
```

### 5. 预加载关键资源

```html
<!-- 预加载 LCP 图片 -->
<link rel="preload" href="/images/hero.webp" as="image">

<!-- 预连接第三方源 -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="dns-prefetch" href="https://img.<用户域名>">
```

## 针对 <监控面板域名>（nginx + 静态站）的优化清单

1. ✅ WebP 替代 PNG
2. ✅ 图片加 `loading="lazy"` + `width/height`
3. ✅ LCP 图片加 `fetchpriority="high"`
4. ✅ Inter 字体预加载 + `font-display: swap`
5. ✅ 关键 CSS 内联
6. ✅ nginx 设置强缓存
7. ✅ Cloudflare 开启 Brotli 压缩（Dashboard → Speed → Optimization）
8. ✅ 启用 gzip（nginx）：`gzip on; gzip_types text/css application/javascript image/svg+xml;`
9. ✅ 从 Cloudflare 移除/精简 HTML/CSS/JS
10. ✅ 确保无外部依赖（用你自己偏好）

## 踩坑记录

1. **preload 不代表优先级最高** — 同时 preload 太多资源会互相竞争。只 preload 最重要的 1-2 个
2. **font-display: swap 的副作用** — 会导致 FOUT（字体闪烁），但比 FOIT（空白文本）体验好得多。可以加 `@font-face { size-adjust: 100%; }` 缓解
3. **loading="lazy" 对首屏图片无效** — 首屏可见的图片不要加 lazy，会延迟加载
4. **immutable 缓存陷阱** — 只有文件名带 hash（如 `main.a1b2c3.css`）的文件才能用 immutable。否则用户永远拿不到更新
5. **preconnect vs dns-prefetch** — preconnect 开销更大（建立 TCP+TLS），只用于关键域名；次要域名用 dns-prefetch 即可

## 验证步骤

```bash
# 1. 运行 Lighthouse
npx lighthouse https://<监控面板域名> --output json 2>/dev/null | jq '.categories.performance.score'

# 2. 检查缓存头
curl -sI https://<监控面板域名>/images/test.webp | grep -i "cache-control"

# 3. 检查是否启用 Brotli
curl -sI -H "Accept-Encoding: br" https://<监控面板域名> | grep -i "content-encoding"

# 4. 检查 LCP 元素（浏览器控制台）
# 在页面中运行：
# new PerformanceObserver((list) => {
#   list.getEntries().forEach(e => console.log('LCP:', e.element, e.startTime));
# }).observe({type: 'largest-contentful-paint', buffered: true});
```
