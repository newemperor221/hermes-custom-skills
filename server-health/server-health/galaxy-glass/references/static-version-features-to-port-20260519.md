# 静态版设计特征值得移植清单（2026-05-19）

会话中对比了静态版（vanilla JS `src/`）和 Next.js 版的代码，以下静态版的设计值得考虑移植：

## 🥇 高价值，好移植

| 特征 | 静态版实现 | Next.js 现状 | 移植成本 |
|------|-----------|-------------|---------|
| **骨架屏加载** | 8张 skeleton 骨架卡片占位，数据加载完才替换 | 一个大 spinner → 突变成卡片 | 低（写个 SkeletonCard 组件） |
| **筛选条滑动指示器** | `filter-slider` 跟着激活 chip 滑动，spring 过渡 | 只变色，无滑块动效 | 低（framer-motion 自带 AnimatePresence） |
| **NET 行标签** | CPU/MEM/DSK 第四行标 "NET" | 网络行没有标签，裸数据 | 极低（改 NodeCard render） |
| **Footer 站点运行时间** | "GG探针 · 已稳定运行 0日0时0分" 实时计时 | 固定文字"🛰️ 本站在线运行中 🌌" | 低（加个 useEffect 计时器） |
| **连接状态 Toast** | 断连/重连时底部闪烁提示（绿/红色） | 没有 | 中（写个 Toast 组件 + 拦截 fetch） |
| **默认排序含权重** | 默认按 `weight` 字段二次排序，重要节点排前面 | 默认只按 online + 名称字母序 | 极低（sort 函数加一行） |
| **Stat 卡片 hover 效果** | 悬停时边框变绿 + 阴影加深 + 图标变色 purple | 没有 hover 效果 | 极低（加 tailwind hover:） |

## 🥈 设计细节

| 特征 | 静态版做法 | Next.js 现状 |
|------|-----------|-------------|
| **Figma squircle 圆角** | 动态 `clipPath` 用 figma-squircle 算法实时计算（node=22px, stat=16px） | 只有 `rounded-[16px]` 静态圆角 |
| **CSS Unicode OS 图标** | `::before` 用 ⛰/◆/☮/● + 品牌色 | Devicon CDN 外部图片，3 次 HTTP 请求 |
| **脉动点 `prefers-reduced-motion`** | `@media (prefers-reduced-motion: reduce)` 禁用动画 | 直接用 `animate-ping`，无 motion 检测 |
| **宽屏 1600px+ 放大卡片** | `minmax(340px, 1fr)` 替代默认 280px | 只有默认 `minmax(280px, 1fr)` |
| **图表端点圆点** | Canvas 绘制端点圆点 + 发光圈 | 只有线和渐变填充 |

## 🥉 大工程（后续评估）

| 特征 | 说明 |
|------|------|
| **detail 页 Canvas 图表** | charts.js 含完整 Canvas 绘制（DPR、端点圆点、渐变），Next.js 版 DetailContent.tsx 已有类似实现 |
| **Skeleton 加载状态** | 8张骨架卡片占位，配合 CSS keyframe shimmer |
| **侧栏操作按钮图标（Heroicons Solid）** | Heoricons Solid 比 Lucide 在暗色背景更醒目 |

## 静态版关键代码位置

- **卡片渲染模板**: `src/scripts/render.js`（`renderCard()` 函数）
- **推荐算法**: `src/scripts/squircle.js`（figma-squircle 浏览器端口 + applySquircles）
- **图表绘制**: `src/scripts/charts.js`（Canvas 原生绘制，含端点圆点）
- **连接状态**: `src/scripts/data.js`（fetchJSON 覆写，连接失败显示 toast）
- **滑动筛选**: `src/scripts/render.js`（filter-slider 跟随）
