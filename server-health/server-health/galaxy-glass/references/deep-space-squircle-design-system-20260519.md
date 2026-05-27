# Deep Space Squircle — GalaxyGlass 设计系统 (2026-05-19)

用户给予完全创作自由：「两个要求 — 强模糊 + Squircle曲线，任何都交给你来做，你也可以上网学习搜寻案例」。

## 设计方向

**"Deep Space Squircle"** — 深空宇宙配色 + 强玻璃质感 + Squircle 超椭圆曲线。

## 色彩体系

| 层级 | 色值 | 用途 |
|------|------|------|
| 最深空 | `#020306` | 页面背景基底 |
| 深空 | `#040814` | body 背景 |
| 表面 | `#070C1A` | 备用表面色 |
| 卡片玻璃 | `rgba(6, 12, 26, 0.75)` | 所有卡片背景基色 |
| 玻璃 hover | `rgba(6, 12, 26, 0.88)` | 卡片悬浮/聚焦态 |

### 强调色
| 色值 | 用途 |
|------|------|
| `#10b981`（翠绿） | 主 accent — 在线、CPU、下行、成功 |
| `#6366f1`（靛蓝） | 次要 accent — 内存、下行图标、hover 态 |
| `#f59e0b`（琥珀） | 警告色 — 70-90% 阈值 |
| `#f43f5e`（玫瑰红） | 危险色 — 90%+ 阈值、离线状态 |

### 文字不透明度层级（严格四阶，不混用）

| 层级 | 透明度 | 用途 |
|------|--------|------|
| primary | `rgba(255,255,255,0.92)` | 核心数值、标题 |
| secondary | `rgba(255,255,255,0.60)` | 次要信息、描述 |
| muted | `rgba(255,255,255,0.38)` | 标签、副标签、footer |
| faint | `rgba(255,255,255,0.18)` | 极淡装饰线、占位符 |

### 边框系统

| 色值 | 用途 |
|------|------|
| `rgba(255,255,255,0.06)` | 卡片外边框（细线） |
| `rgba(255,255,255,0.08)` | 按钮/交互元素边框 |
| `rgba(255,255,255,0.04)` | 极淡分割线 |

## 玻璃公式（核心）

```css
/* 所有卡片通用玻璃底 */
background: rgba(6, 12, 26, 0.75);
backdrop-filter: blur(24px) saturate(180%);
-webkit-backdrop-filter: blur(24px) saturate(180%);

/* 双重阴影 — 外影深度 + 内顶部发光 */
box-shadow: 
  0 4px 24px rgba(0, 0, 0, 0.25),       /* 外影：深度 */
  inset 0 1px 0 rgba(255,255,255,0.03);  /* 内顶光：模拟光源 */
```

### 为什么是 rgba(6,12,26,0.75) + blur(24px)

通过多轮实验比较：

| 公式 | 效果 | 适用 |
|------|------|------|
| `rgba(0,0,0,0.35)` + `blur(20px)` | 用户指定的静态版暗色玻璃 | 之前的静态版风格 |
| `rgba(6,12,26,0.75)` + `blur(24px)` + `saturate(180%)` | 更深邃、更高饱和、壁纸透出冷色调 | ✅ **当前 Deep Space 风格** |
| `rgba(255,255,255,0.03-0.06)` + `blur(60-100px)` | 明亮毛玻璃 | 明亮壁纸方案 |

关键差异：新公式的玻璃底色更深（0.75 vs 0.35 opacity），但用了**深蓝黑**（hue=220）而非纯黑（hue=0），和翠绿 accent 形成冷绿反差。saturate(180%) 让壁纸色彩更鲜明透出。

## Squircle 曲线应用

```css
/* globals.css — 渐进增强 */
@supports (corner-shape: squircle) {
  .sq-card { corner-shape: squircle; }
  .sq-sm  { corner-shape: squircle; }
  .sq-chip { corner-shape: squircle; }
}
```

Chrome 139+ 原生渲染，不支持时降级为 border-radius。

### 各元素半径

| 元素 | CSS class | radius | 说明 |
|------|-----------|--------|------|
| NodeCard（VPS卡片） | `.sq-card` | 16px | 最突出的大卡片 |
| StatCard（统计栏） | `.sq-card` | 16px | 与 NodeCard 统一 |
| MetricCard（详情指标） | `.sq-card` | 14px | 略小于主卡片，区分层级 |
| Sysinfo/Chart 卡 | `.sq-card` | 16px | 统一主卡片半径 |
| 搜索/排序/登录按钮 | `.sq-sm` | 12px | 操作入口 |
| FilterChip（筛选标签） | `.sq-chip` | 8px | 小标签 |
| 返回按钮 | `.sq-sm` | 10px | 导航操作 |
| Back-to-top | `.sq-sm` | 12px | 浮窗 |

### 黄金公式（来自 Squircle 设计原则）

**`padding >= cornerRadius`** — Squircle 的超椭圆曲线比普通圆角更「吃」空间，padding 必须大于等于 radius 否则内容被曲率裁切。

遵循情况：NodeCard(16px radius, 20px padding ✅), MetricCard(14px radius, 16px padding ✅), Sysinfo(16px radius, 18px padding ✅), Chart(16px radius, 22px padding ✅)

## 卡片布局规范

### 间距系统（4px 网格）

| Token | 值 | 使用场景 |
|-------|-----|---------|
| `gap-1` | 4px | 箭头↔数值、图标↔文字 |
| `gap-2` | 8px | 指标行之间、标签之间 |
| `gap-3` | 12px | 不同段落之间 |
| `gap-4` | 16px | 网格间距、卡片间距 |
| `gap-5` | 20px | 图表之间的间距 |
| `gap-6` | 24px | 大区块间距 |

### 各组件精确间距

| 组件 | Padding | 内部 Gap |
|------|---------|----------|
| NodeCard | `20px` 均匀 | `10px` |
| StatCard | `16px 18px` | `12px`（flex gap-3）|
| MetricCard | `16px 18px` | `10px` |
| Sysinfo 卡 | `18px 20px` | row: `8px` |
| Chart 卡 | `22px 24px` | header: `16px` |
| FilterChip | `h-[30px]` + `px-3` | `6px` gap |

### 渐变分隔线

所有卡片内部的分隔线用绝对定位 `<div>` + `linear-gradient` 实现，左右淡出：

```tsx
<div 
  className="absolute bottom-0 left-0 right-0 h-px pointer-events-none"
  style={{
    background: "linear-gradient(90deg, transparent 4%, rgba(255,255,255,0.04) 10%, rgba(255,255,255,0.04) 90%, transparent 96%)",
  }}
/>
```

参数经验：小卡片（NodeCard ~300px）用 `12%→88%`，大卡片（sysinfo ~360px）用 `4%→96%`。

## 进度条系统（Metric Bars）

| 属性 | 值 | 说明 |
|------|-----|------|
| 高度 | `4px` | 细但可见 |
| 圆角 | `9999px` | 胶囊形 |
| 背景 | `rgba(255,255,255,0.04)` | 极淡灰底 |
| 低阈值（<70%） | 类型色（绿/紫/黄）渐变 | CPU=#10b981→#34d399, MEM=#6366f1→#818cf8, DSK=#f59e0b→#fbbf24 |
| 中阈值（70-90%） | `#f59e0b` 纯色 | 警告 |
| 高阈值（90%+） | `#f43f5e` 纯色 | 危险 |
| 动画 | `scaleX` from 0 | 0.6s ease-out staggered |
| Shine效果 | `linear-gradient` 覆盖层 opacity 0.2 | 模拟光泽 |

```tsx
// 进度条外层
<div style={{ borderRadius: 9999, background: "rgba(255,255,255,0.04)" }}>
  <motion.div
    initial={{ scaleX: 0 }}
    animate={{ scaleX: Math.min(1, pct / 100) }}
    style={{ transformOrigin: "left", background: grad }}
  >
    {/* Shine 光泽 */}
    <div className="absolute inset-0 opacity-20"
      style={{ background: "linear-gradient(90deg, transparent 20%, rgba(255,255,255,0.4) 50%, transparent 80%)" }}
    />
  </motion.div>
</div>
```

## 状态指示器

### 在线脉冲动画

```css
@keyframes live-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.4; transform: scale(0.85); }
}
```

- 使用 `transform: scale()` 而非 `opacity` 单独变化
- 2.5s 周期，比默认 pulse 更柔和
- 用 `animate-ping` → 改用自定义 `live-pulse`（ping 会超出容器被 overflow 截断）

### 离线状态
- 整个 NodeCard 降低 opacity 至 0.50
- 右上角 `OFFLINE` 玫瑰红标签 `rgba(244,63,94,0.12)` 背景
- 进度条和图标半透明

## 交互细节

| 行为 | 实现 | 参数 |
|------|------|------|
| 卡片 hover 上移 | `whileHover={{ y: -4, scale: 1.005 }}` | 4px + 微小放大 |
| 卡片入场动画 | `initial={{ opacity:0, y:12, scale:0.96 }}` → 0.45s ease-out | staggered 0.04s |
| 图标 hover 变绿 | `group-hover:text-[#10b981]` | StatCard 图标 |
| 卡片边框 hover 发光 | 第二层 `box-shadow` + `opacity 0→1` transition 500ms | 翠绿晕 28px |
| Back-to-top hover | `hover:scale-105` | 5% 放大 |
| 排序 dropdown | backdrop-blur(32px) 更厚玻璃 | 用 spring 缓动 |

## 导航栏

- 自身也做玻璃：`rgba(4,8,20,0.6)` + `blur(24px)` + 底部细边框
- 品牌 G 图标：`26x26` squircle 渐变块 + 渐变文字
- 搜索/排序/登录：统一 `12px` squircle，`rgba(6,12,26,0.75)` 玻璃

## 渐变色应用

| 位置 | 渐变 | 说明 |
|------|------|------|
| 标题文字 | `linear-gradient(135deg, #10b981, #6366f1)` | 翠绿→靛蓝对角 |
| 品牌 G 图标 | 同上 | 26x26 方块的 background |
| Footer 文字 | 同上 | 品牌名 |
| 价格徽章背景 | `linear-gradient(135deg, rgba(16,185,129,0.10), rgba(99,102,241,0.10))` | 极淡渐变底 |
| 顶部内发光 | `linear-gradient(180deg, rgba(255,255,255,0.025), transparent)` | 卡片顶部模拟光 |

## 字体系统

```css
--font-sans: 'Fira Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI',
  'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', system-ui, sans-serif;
--font-mono: 'Fira Code', ui-monospace, 'SF Mono', 'JetBrains Mono',
  Menlo, Consolas, monospace;
```

| 层级 | 字号/字重 | 使用 |
|------|-----------|------|
| 品牌 | 17px/700 | 导航栏站点名 |
| Metric value | 22px/700 mono | 详情页指标值 |
| Stat value | 16px/700 mono | 统计栏数值 |
| Node name | 14px/600 | 卡片标题 |
| Label | 11px/500 medium `0.04em` | 统计标签、指标标签 |
| Caption | 12px mono | 子信息、流量数值 |
| Tiny | 10px mono | 图表badge、标签tag |

## 详情页特有设计

### MetricCard（指标卡）
- 14px squircle, 16px/18px padding
- Label: 11px uppercase `0.06em` letter-spacing, 30% opacity
- Value: 22px bold mono, 90% opacity
- Bar: 3px, 按阈值变色 + 同色发光 `box-shadow`

### Sysinfo 卡（系统信息）
- 16px squircle, 18px/20px padding
- Row: 8px vertical padding, 11px label / 12px mono value
- 渐变分隔线：`transparent 4% → 4% → 96% → transparent`
- Load badges: 带颜色背景的10px mono 标签

### Chart 卡（图表）
- 16px squircle, 22px/24px padding（最宽 padding 给呼吸感）
- Title: 12px uppercase `0.06em`, 40% opacity
- Badge: 10px mono, 8px squircle 标签

## 框架/库选择

| 类别 | 选择 | 版本 |
|------|------|------|
| 框架 | Next.js 16 | `output: 'export'` |
| CSS | Tailwind v4 + inline styles | 复杂动态值用 inline |
| 动画 | Framer Motion | 入场、hover、进度条 |
| 图标 | Lucide React | 所有 UI 图标 |
| 图表 | D3.js SVG | `curveMonotoneX` + SVG gradient |
| Squircle | CSS `corner-shape` 原生 | Chrome 139+ 渐进增强 |
| 构建 | Turbopack | 注意: 非内容哈希 → 浏览器缓存 |

## 当前未使用（但存在于静态版的功能）

这些静态版功能尚未移植到 Deep Space 设计：
- Skeleton 骨架屏（当前用 spinner）
- 滑动筛选条（Filter Slider）
- 连接状态 Toast
- 在线人数计数
- 实时秒更新 footer uptime
- 详情页详情视图切换

这些不是设计风格的一部分，是功能特性。用户没有要求移植，暂不处理。
