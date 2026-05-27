---
name: galaxyglass-design-references
description: Glass 主题设计参考 — 品牌设计系统 DESIGN.md、CSS 纯前端资源、毛玻璃示例、暗色仪表盘模式。加载时自动提示可用资源。
tags: [galaxyglass, design, css, dark-theme, dashboard, glassmorphism]
---

# Glass 设计参考

> stat.357561.xyz 深色毛玻璃探针面板的设计弹药库

## 本地已获取的设计系统 DESIGN.md

存放在 `~/glass/design-references/`

| 品牌 | 文件名 | 适用场景 |
|------|--------|---------|
| **Linear** | `linear.app.md` | 暗色后台标杆 — #010102 深底、灰白文字、淡紫蓝 accent #5e6ad2 |
| **Supabase** | `supabase.md` | 翠绿开发者品牌 — 暗色配绿 accent，跟 Glass 配色接近 |
| **Cursor** | `cursor.md` | AI 原生 IDE 暗色主题 — 暖黑色 #26251e、橙色单一 accent |
| **Stripe** | `stripe.md` | 深海军蓝 #1c1e54、电感蓝 primary — dashboard 数据展示参考 |
| **Vercel** | `vercel.md` | 黑白极简 + mesh 渐变 — 41KB 完整设计令牌 |

### 使用方式

```bash
# 加载某个品牌的设计系统做 UI
skill_view(name='galaxyglass-design-references')
# 然后读对应的 DESIGN.md 文件
# 用 "按 Linear 风格改 GalaxyGlass 卡片" 等指令
```

## 在线资源

### CSS 设计系统（纯 CSS / 无框架）

| 项目 | 说明 | 链接 |
|------|------|------|
| **vanilla-css-design-system** | 轻量模块化纯 CSS 设计系统 | github.com/pattespatte/vanilla-css-design-system |
| **Vanilla Framework (Ubuntu)** | 开源可组合 CSS 框架（Sass） | github.com/canonical/vanilla-framework |
| **awesome-css-only** | 纯 CSS 项目合集 | github.com/refusado/awesome-css-only |
| **awesome-css-frameworks** | CSS 框架合集（Troxler） | github.com/troxler/awesome-css-frameworks |
| **awesome-css-resources** | CSS 资源合集 | github.com/MarketingPipeline/Awesome-CSS-Resources |

### 毛玻璃（Glassmorphism）

| 资源 | 说明 | 链接 |
|------|------|------|
| **65 CSS Glassmorphism Examples** | 65 个毛玻璃示例（卡片、表单、导航） | freefrontend.com/css-glassmorphism/ |
| **CSS Glassmorphism Button Hover** | 毛玻璃按钮悬停效果 | freefrontend.com |
| **Dark Theme Glassmorphism (Dribbble)** | 暗色毛玻璃设计灵感 | dribbble.com/search/dark-theme-glassmorphism |

### CSS 动画

| 库 | 说明 | 类型 |
|----|------|------|
| **Animate.css** | 即插即用 CSS 动画 | CSS keyframes |
| **Animista** | CSS 动画生成器（在线配置） | 工具 |
| **AnimXYZ** | 可组合 CSS 动画（支持 React/Vue） | CSS + JS |
| **Whirl** | 加载动画合集 | 纯 CSS |
| **Magic UI** | 动画 UI 组件库 | React + Tailwind |
| **Hover.dev** | 交互式动画组件 | React + Framer Motion |

### 暗色仪表盘模式参考

| 品牌 | 特色 | 暗色方案 |
|------|------|---------|
| Linear | 极简任务管理 | #010102 深底，#5e6ad2 accent |
| Vercel | 部署面板 | #000 黑底，白字，mesh 渐变 |
| Stripe | 金融仪表盘 | #1c1e54 深海军蓝 |
| Cursor | IDE 编辑器 | #26251e 暖黑，#f54e00 orange |
| Sentry | 错误监控 | 暗色 + 红色 accent |
| PostHog | 产品分析 | 暗色 + 粉色 accent |

## Glass 配色 & 令牌参考

```css
:root {
  /* 品牌 */
  --accent:        #10b981;  /* 翠绿 */
  --accent-2:      #818cf8;  /* 靛蓝 */
  --accent-gradient: linear-gradient(135deg, #10b981, #818cf8);

  /* 背景 — Linear 风格极深近黑 */
  --bg-deepest:    #020203;  /* 最深 */
  --bg-deep:       #050510;  /* 深 */
  --bg-surface:    #080b18;  /* 表面（带蓝调） */

  /* 玻璃层级系统（6 层） */
  --glass-subtle:   rgba(255,255,255,0.04);
  --glass-bg:       rgba(255,255,255,0.06);
  --glass-raised:   rgba(255,255,255,0.08);
  --glass-hover:    rgba(255,255,255,0.10);
  --glass-strong:   rgba(255,255,255,0.14);
  --glass-border:       rgba(255,255,255,0.10);
  --glass-border-hover: rgba(255,255,255,0.16);

  /* 文字层级 — 清晰的三级阶梯 */
  --text-primary:   #f0fdf4;  /* 近白微绿 */
  --text-secondary: rgba(240, 253, 244, 0.70);
  --text-muted:     rgba(240, 253, 244, 0.45);

  /* 阴影体系 */
  --shadow-sm:  0 1px 3px rgba(0,0,0,0.3);
  --shadow-md:  0 4px 12px rgba(0,0,0,0.4);
  --shadow-lg:  0 12px 40px rgba(0,0,0,0.5);
  --shadow-xl:  0 24px 64px rgba(0,0,0,0.6);
  --shadow-accent:  0 0 28px rgba(16,185,129,0.08);

  /* 弹性曲线 */
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);

  /* Z-index 映射 */
  --z-nav:     100;
  --z-dropdown:200;
  --z-toast:   9999;
}
```

> **设计来源：** Linear（极深底 #010102、炭灰表面、发丝边框）、Supabase（翠绿 accent）

## 参考文件

- `references/css-redesign-approach.md` — 系统性 CSS 重构方法论：令牌系统模板、导航毛玻璃、卡片悬浮发光、导航堆叠层级、壁纸滤镜陷阱、emoji→SVG 替换模式、部署流程、post-deploy 验证清单、在线人数 tab heartbeat 机制
- `references/glassmorphism-best-practices.md` — 暗色毛玻璃设计规范：blur 值范围（4-15px 最佳）、深色背景上 backdrop-filter 不可见的陷阱、Fallback 兼容方案、性能注意事项、Glass 各组件 blur 值审计
- `references/d3-svg-chart-nextjs.md` — D3.js + SVG 实时折线图模式（CPU/内存/网络，60数据点，CSS动画，SVG filters辉光，端点圆点脉冲）
- `references/figma-squircle.md` — Apple 连续曲线圆角实现：figma-squircle 算法移植、Squircle React 组件、各卡片圆角值对应表
- `references/detail-page-design-patterns.md` — 探针详情页设计模式：布局、颜色编码体系、迷你进度条、图表卡片渐变色装饰条、Y轴标注、设计原则与流程

## 用户设计偏好（重要）

当用户说"有点单调了" → **先去网上学当前设计趋势，再改代码**。上线前要用 browser 截图验证视觉效果。流程：
1. 搜索 Dribbble/Muzli/Dark Dashboard UI 同类参考
2. 收集 3-5 个可落地的视觉模式（颜色编码、进度条、卡装饰线、图标标题等）
3. 逐一实施，每次改完等用户反馈，不要一口气全改完

用户设计反馈模式：
- "单调" → 重新研究视觉模式
- "左边没必要加上XXX" → 右侧已有同类信息，立刻移除
- "左下角空了很多" → 拆分信息卡片填充纵向空间，让左右等高
- 说"你决定"/"看你" → 按优先级自底向上逐个实施
- 直接截图提问 → 在截图位置有具体问题，用 vision_analyze 看细节再回应
- "你去网上学设计行吗？学学怎么设计" → 停止改代码，先去搜索调研

**关键偏好：一个数据只有一个展示位置。** 图表区展示实时使用率，左面板只展示静态规格和文本状态。不要做冗余展示。

### 字体统一（2026-05-20 确立）

- **全站禁用等宽字体** — 所有 `--font-mono` 引用已删除，统一使用 `--font-sans`（Fira Sans）
- 包括：stats 数字、卡片指标值、系统信息值、计费芯片、流量行、chart badge、页脚运行时间
- 页脚三行字号统一为 **12px**，logo 不加粗

### Tab 标题

- `<title>` 标签使用网站名称（`GG 探针` 或 API 注入的 `siteData.sitename`），不保留硬编码的 "Komari Monitor"

### 主题命名原则

- 名称反映**实际视觉特征**（深色 + 玻璃质感），不要用抽象概念（星、银河、宇宙）
- 例：GalaxyGlass → Glass（因为就是纯深色毛玻璃，不是星空主题）

### 探针面板详情页设计要点（2026-05-20 更新：无标题行、无重复数据、共享 stats-bar）

- **颜色即含义** — CPU 绿、MEM 紫、NET 橙/绿，贯穿整个页面（左侧进度条 + 右侧图表 + 卡片装饰条）
- **无分类标题行** — `💻 硬件` `📡 网络` `⚡ 状态` 已被用户要求移除，直接展示数据行。`sysinfo-header` CSS 定义保留但不再使用。
- **一个数据只有一个展示位置**（核心原则）：
  - 流量限额 → 只在 bill-chip `📊 已用/限额` 中展示，不在上方 sysinfo-row 重复
  - TCP/UDP 连接数 → 只在 tags-card 的 conn-row 展示，不在右侧状态区重复
  - CPU/MEM/DSK 使用率 → 只在右侧图表展示，不在左侧 sysinfo 重复
  - 分类标题行已被移除（2026-05-20 用户要求）
- **迷你进度条** — 4px 高，50px 宽，渐变填充，放在数值右侧
- **图表卡片顶部装饰条** — `::before` 2px 渐变线，颜色对应指标
- **左侧1fr : 右侧1.2fr** — 图表区更宽，给折线图更多横向空间
- **详情页导航栏** — navbar 保留可见（`navbar-actions` 隐藏搜索/排序/登录），`detail-nav` 在 navbar 下方独立 sticky 显示返回按钮和节点名
- **左侧两卡片 + tags 垂直布局**（2026-05-20 确立）：
  - 💻 硬件（sysinfo-card#detail-hw）：CPU型号/核心数/架构/虚拟化/OS/内存/Swap/磁盘/GPU — 静态规格，不展示实时使用率
  - 📡 网络 + ⚡ 状态（sysinfo-card#detail-status）：进程数/负载/更新/到期 + 账单 chips（价格/流量/剩余天数）
  - 🏷️ 标签·连接（tags-card#detail-tags）：节点标签 + TCP/UDP 连接数
- **图表卡片高度差异化** — 网络速率图（上行+下行双折线）需要更高空间（200px vs 130px），加 `.net-chart` 类实现
- **Chart.js 4.4.7 当前方案**（2026-05-20）：`tension: 0.4` 平滑曲线，`CanvasGradient` 渐变填充（通过 `backgroundColor: function(c){...}` 动态获取 chartArea），Y 轴 `display: false`，X 轴极淡时间标签

## 相关技能

- `awesome-design-md` — 71 个品牌 DESIGN.md，按需获取
- `taste-skill` — 前端反"屎山"设计框架，9 个子技能
- `impeccable` — AI 前端设计品味，反模式检测
- `ui-skills` — UI 基线验证，可访问性，动效审计
- `css-glassmorphism-backdrop-filter` — 毛玻璃 CSS 实现细节

## Komari 主题打包格式

参考官方主题（komari-next）的 Release 结构：

```
Glass-v1.0.0.zip
├── komari-theme.json      ← 元数据（根目录）
└── dist/
    └── index.html         ← 主题主页（静态文件目录）
```

- `komari-theme.json` 在 zip 根目录，包含名称/版本/描述
- `dist/` 目录是 Komari 的静态文件服务根目录
- 上传方式：Komari 后台 → 设置 → 主题管理 → 上传主题 → 选择 zip
- 一键打包发布：`./release.sh vX.Y.Z`（自动 build → 打包 → tag → GitHub Release）
