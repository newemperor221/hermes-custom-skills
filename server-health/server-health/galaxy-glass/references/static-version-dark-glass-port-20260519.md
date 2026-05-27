# 静态版暗色玻璃风格移植（2026-05-19）

## 背景

用户要求将静态版 `index.html` + `detail.html` 的视觉风格移植到 Next.js 版。

## 改动的核心：玻璃背景色

静态版 detail.html 使用 `rgba(0,0,0,0.35)` + `blur(20px) saturate(160%)`，比 Next.js 版之前用的 `rgba(255,255,255,0.06)` + `blur(80px)` 暗得多、密实得多。

## 逐文件改动

### `src/app/globals.css`

- `--color-glass-bg`: `rgba(0,0,0,0.35)`（原 `rgba(255,255,255,0.06)`）
- `--glass-bg`: 同上
- `--text-muted`: `rgba(240,253,244,0.48)`（原 `0.55`）
- `--blur-card`: `20px`（原 `40px`）
- `--blur-glass`: `20px`（原 `60px`）
- `--blur-surface`: `12px`（原 `24px`）
- `--space-5`: `20px`（新增，原被占用）

### `src/app/page.tsx`

- **StatCard** → `padding: 14px 16px`, `border-radius: 12px`，`rgba(0,0,0,0.35)` + `blur(12px)`
- **FilterChip** → `border-radius: 8px`（非9999px），选中态 `rgba(16,185,129,0.1)` 背景 + 绿边框
- **排序/搜索/登录** → 统一 `rgba(0,0,0,0.35)` + `blur(12px)` 玻璃背景
- **下拉菜单** → `rgba(0,0,0,0.35)` + `blur(20px) saturate(160%)`, `border-radius: 12px`
- **表格行** → 同上玻璃，`border-radius: 12px`
- **回到顶部按钮** → 同上玻璃，`blur(20px)`
- 去掉所有 `saturate-150` 等 Tailwind 类，改用 inline style

### `src/app/detail/DetailContent.tsx`

- **MetricCard** → `padding: 14px 16px`, `border-radius: 14px`，`rgba(0,0,0,0.35)` + `blur(20px) saturate(160%)`
- Metric label → `text-[10px]` uppercase `tracking-[0.07em]`（原11px）
- Metric bar → `h-[3px]`（原 `h-0.5` = 2px），`rounded-[2px]`
- **Sysinfo 卡** → `padding: 16px 18px`（原24px）
- Sysinfo 行 → `py-[7px] px-[14px]`（原 `py-1.5`）
- **Chart 卡** → `padding: 18px 20px`（原24px）
- Chart title → `text-[12px]` uppercase `tracking-[0.06em]`（原 `text-xs`）
- 所有卡统一用 inline `box-shadow` 替代 Tailwind 类

### `src/components/NodeCard.tsx`

- Padding → `16px 18px`（原 `p-[24px]` 24px均匀）
- 指标行高度 → `minHeight: 20`（原18）
- 进度条高度 → `h-[6px]`（原5px）
- label 宽度 → `w-[26px]`（原28px）
- label 大小 → `text-[10px]`（保持，已匹配）
- hover 上移 → `-3px`（原-5px）
- 卡片入场动画 → `opacity:0 y:10 scale:0.98`（原 0 12 0.97），duration 0.35s（原0.4s）
- 离线点大小 → `w-[9px]`（原10px）
- OFFLINE badge → 位置 `top-[18px] right-[18px]`（随 padding 调整）

## 验证结果

浏览器截图确认：
- MetricCard radius 约 14px ✅
- MetricCard padding 约 14px 16px ✅
- Metric label 约 10px ✅
- Sysinfo padding 约 16px 18px ✅
- Chart padding 约 18px 20px ✅
- 整体暗色玻璃质感匹配静态版 ✅
