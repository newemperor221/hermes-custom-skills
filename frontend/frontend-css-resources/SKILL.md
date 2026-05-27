---
name: frontend-css-resources
description: 前端 CSS 纯前端工具箱 — 动画库、毛玻璃示例、暗色模式、CSS 框架、图标库。纯 CSS / 无框架优先。触发："找动画"、"毛玻璃例子"、"暗色模式"、"css 资源"、"前端工具箱"。
tags: [css, animation, glassmorphism, dark-mode, icons, frontend]
---

# 前端 CSS 工具箱

> 纯 CSS 优先 — 无框架依赖，跟 GalaxyGlass 技术栈一致

## CSS 动画库

| 库 | 类型 | 用法 | Stars |
|----|------|------|-------|
| **Animate.css** | CSS keyframes | 加 class 即用 | ~80k |
| **Animista** | CSS 生成器 | 在线配置→复制 CSS | 工具 |
| **AnimXYZ** | 可组合 CSS | 支持 React/Vue | ~1k |
| **Whirl** | 加载动画 | 纯 CSS spinner | ~2k |
| **CSS Wand** | 悬停/过渡 | 纯 CSS 效果 | ~1k |
| **Vov.css** | 滚动动画 | 纯 CSS | ~1k |
| **Animatopy** | 片段合集 | 复制即用 | ~1k |

**推荐：** Animate.css 最成熟，Animista 适合快速原型。

## 毛玻璃（Glassmorphism）

```css
/* GalaxyGlass v2.5.0 当前毛玻璃模式 */
.glass-card {
  background: var(--glass-bg);
  backdrop-filter: blur(var(--blur-surface));
  -webkit-backdrop-filter: blur(var(--blur-surface));
  border: 1px solid var(--glass-border);
  border-radius: 16px;
}
```

**GalaxyGlass 玻璃层级系统：**
- `--glass-subtle` (4%) — 环境填充
- `--glass-bg` (6%) — 默认卡片/按钮
- `--glass-raised` (8%) — hover 状态
- `--glass-hover` (10%) — 强交互反馈
- `--glass-strong` (14%) — 高亮元素
- `--glass-border` (10%) — 默认边框
- `--glass-border-hover` (16%) — 悬浮边框

**在线资源：**
- freefrontend.com/css-glassmorphism/ — 65 个完整示例
- dribbble.com/search/dark-theme-glassmorphism — Dribbble 暗色毛玻璃灵感
- CSS Glassmorphism Generator — 在线参数调节

**陷阱（详见 css-glassmorphism-backdrop-filter skill）：**
- `backdrop-filter` 在 stacking context 中易失效
- 视频背景上毛玻璃需要额外处理
- 强 blur 值（>40px）在移动端卡顿
- **导航栏玻璃在纯色深底上不可见** — `backdrop-filter: blur()` 在纯色背景上不产生视觉效果，必须：① 导航栏底色与页面底色有细微色差（如偏蓝）；② 加 `saturate(150%) brightness(1.15)` 增强；③ 不透明度 40% 而非 75%
- 导航栏毛玻璃在纯色深底上不可见（需 saturate+brightness+色差，见下方即用片段）
## 暗色仪表盘配色

| 风格 | 底色 | accent | 字体 | 出处 |
|------|------|--------|------|------|
| Linear 极简 | #010102 | #5e6ad2 | Inter | linear.app |
| Vercel 纯粹 | #000000 | mesh 渐变 | Geist | vercel.com |
| Stripe 金融 | #1c1e54 | #635bff | Söhne | stripe.com |
| Cursor IDE | #26251e | #f54e00 | 系统 | cursor.com |
| Supabase 翠绿 | #1a1a2e | #3ecf8e | 系统 | supabase.com |
| Sentry 监控 | #1a1a2e | #e74c3c | Inter | sentry.io |
| PostHog 分析 | #0d0d0d | #f54e00 | Inter | posthog.com |

## 纯 CSS 框架（无 JS 依赖）

| 框架 | 说明 | 大小 |
|------|------|------|
| **Pure.css** | Yahoo! 轻量模块化，~6KB | 6KB |
| **Picnic CSS** | 美观轻量，~10KB | 10KB |
| **Vanilla Framework** | Ubuntu 官方，可组合 Sass | 按需 |
| **Bulma** | 现代 Flexbox，纯 CSS | ~200KB |
| **vanilla-css-design-system** | 模块化纯 CSS 设计系统 | 轻量 |

## 图标库（纯 SVG，无 JS）

| 库 | 图标数 | 格式 |
|----|--------|------|
| **Lucide** | ~1500 | SVG 单文件 |
| **Heroicons** | ~500 | SVG 单文件 |
| **Tabler Icons** | ~5500 | SVG 单文件 |
| **Feather** | ~300 | SVG 单文件 |

> 已有 `better-icons` skill（20万+ 图标搜索），用 `"找图标"` 触发。

## 即用片段

### 毛玻璃导航栏（GalaxyGlass 模式 — 暗色背景兼容）
```css
/* 关键：深色背景下 backdrop-filter 纯 blur 不可见。
   需要 saturate+brightness 增强 + 底色与页面有微妙色差。 */
.navbar {
  background: rgba(10, 16, 34, 0.4);              /* 偏蓝 vs 页面深灰，色差让透明度可见 */
  backdrop-filter: blur(20px) saturate(150%) brightness(1.15);
  -webkit-backdrop-filter: blur(20px) saturate(150%) brightness(1.15);
  border-bottom: 1px solid rgba(255,255,255,0.10); /* glass-border */
  position: sticky;
  top: 0;
  z-index: 100;
}
```

### 毛玻璃导航栏（暗色背景兼容版）
```css
/* 关键：深色背景上 backdrop-filter 纯 blur 不可见。
   需要 saturate+brightness 增强 + 底色与页面有微妙色差。 */
.navbar {
  background: rgba(10, 16, 34, 0.4);              /* 偏蓝 vs 页面深灰，色差让透明度可见 */
  backdrop-filter: blur(20px) saturate(150%) brightness(1.15);
  -webkit-backdrop-filter: blur(20px) saturate(150%) brightness(1.15);
  border-bottom: 1px solid rgba(255,255,255,0.10);
  position: sticky;
  top: 0;
  z-index: 100;
}
```

### 详情页二级导航（透明从属栏）
```css
/* 页面中最多只有一个毛玻璃顶栏。二级导航透明融入内容区 */
.detail-nav {
  background: transparent;
  border-bottom: none;
}
```

### 卡片弹簧弹出悬浮效果
```css
.card {
  transition:
    transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),  /* 弹簧曲线 */
    box-shadow 0.35s ease,
    border-color 0.3s ease;
}
.card:hover {
  transform: translateY(-3px);
  box-shadow:
    0 24px 64px rgba(0,0,0,0.6),
    0 0 28px rgba(16,185,129,0.08),
    0 0 0 1px rgba(45,158,107,0.18);
}
```
> `cubic-bezier(0.34, 1.56, 0.64, 1)` 即 `--ease-spring`，弹性弹出效果

### 悬停上升动画（GalaxyGlass 模式 — 弹簧弹出）
```css
.card {
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1),
              box-shadow 0.35s ease,
              border-color 0.3s ease;
}
.card:hover {
  transform: translateY(-3px);
  box-shadow: 0 24px 64px rgba(0,0,0,0.6),
              0 0 28px rgba(16,185,129,0.08),
              0 0 0 1px rgba(45,158,107,0.18);
}
```
> `cubic-bezier(0.34, 1.56, 0.64, 1)` = `--ease-spring`，弹簧弹出效果

### 入场动画（淡入+上移）
```css
@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.card { animation: fadeInUp 0.4s ease both; }
.card:nth-child(2) { animation-delay: 0.05s; }
.card:nth-child(3) { animation-delay: 0.1s; }
/* 依次递增 */
```

### 文字渐变
```css
.gradient-text {
  background: linear-gradient(135deg, #10b981, #818cf8);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
```

### 骨架屏（加载占位）
```css
.skeleton {
  background: linear-gradient(90deg,
    rgba(255,255,255,0.04) 25%,
    rgba(255,255,255,0.08) 50%,
    rgba(255,255,255,0.04) 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 8px;
}
@keyframes shimmer {
  0%   { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
```
