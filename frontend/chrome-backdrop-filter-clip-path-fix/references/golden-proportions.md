# GalaxyGlass 卡片黄金比例速查表

## 8px 网格基准

所有间距、padding、radius 用 8px 倍数：`8, 16, 24, 32, 40, 48...`

**半径标尺：**
```
xs: 4px   (标签内圆角, 极小元素)
sm: 8px   (筛选按钮chip, 小标签)
md: 12px  (小型容器, 输入框)
lg: 16px  ✅ 标准卡片圆角
xl: 24px   (大卡片, modal)
xxl: 32px  (面板)
full: ∞   (药丸形)
```

**间距标尺：**
```
xs: 8px   (内部元素间隙)
sm: 16px  (小卡片padding)
md: 24px  ✅ 标准卡片padding
lg: 32px  (大卡片padding, section间)
xl: 48px  (页面段落间距)
xxl: 64px (页面边缘margin)
```

---

## 各卡片比例表

### 1️⃣ NodeCard（主网格服务器卡片）

| 属性 | 推荐值 | 依据 |
|------|--------|------|
| cornerRadius | **16px** (lg) | 8px网格标准圆角 |
| padding | **24px** (3×8) | 8px网格，24 > 16 ✅ 黄金公式安全 |
| gap (sections之间) | **8px** (1×8) | 统一8px |
| 内部元素间距 (metrics) | **8px** | 统一8px |
| 内元素圆角 | **0** (16-24=-8 取0) | 黄金公式，padding>radius不需要 |
| 节点名大小 | **14px** | body文字层级 |
| 指标文字 | label **10px** uppercase, value **11px** monospace tabular-nums | 对比清晰 |

**视觉流程：**
```
[●] 节点名                🇯🇵          ← gap: 8
Debian · kvm                           ← gap: 8
[标签1] [标签2]                        ← gap: 8
CPU ██████████░░ 54.1%                  ← gap: 8
MEM ██████░░░░░░ 2.3%                   ← gap: 8
DSK ████████████░ 9.7%                
▲ 416B/s  ▼ 720B/s                     ← gap: 8
──────────────────── 渐隐线 ──────────
🕐 49天13时                ¥10/年      ← gap: 8
```

### 2️⃣ StatCard（顶栏统计）

| 属性 | 推荐值 |
|------|--------|
| cornerRadius | **16px** (lg) |
| padding | **16px** (2×8) 均匀 |
| 图标大小 | **20px** (lucide) |
| 文字层级 | label **11px** + value **16px** font-mono |

**高度统一：** 用 `minHeight: 70px` 确保4张卡片等高。

### 3️⃣ MetricCard（详情页指标卡）

| 属性 | 推荐值 |
|------|--------|
| cornerRadius | **16px** (lg) |
| padding | **16px** (2×8) |
| 文字层级 | label **11px** uppercase / value **20px** font-mono bold |
| label:value 比值 | 11 × 1.618≈18 — 接近黄金比例 |

### 4️⃣ Sysinfo / Chart 卡（详情页）

| 属性 | 推荐值 |
|------|--------|
| cornerRadius | **16px** (lg) |
| padding | **24px** (3×8) |
| 内部行间距 | **8px** (1×8) |
| 分隔线 | 渐隐渐变，15%-85% 区间 |

### 5️⃣ FilterChip（筛选按钮）

| 属性 | 推荐值 |
|------|--------|
| cornerRadius | **9999px** (full / 药丸形) |
| padding-h | **12px** |
| 高度 | **30px** |

---

## 圆角曲率选择

| cornerRadius | squircle vs border-radius 差异 |
|-------------|-------------------------------|
| ≤ 12px | **肉眼不可辨** — 直接用 border-radius |
| 14-16px | 极微 — 可以用 `corner-shape: squircle` 渐进增强 |
| 20-24px | 轻微可辨 — 建议用 squircle |
| ≥ 32px | 明显差异 — 必须用 squircle |

**结论：14-16px 区间直接用 CSS border-radius，加一行渐进增强就够了。**

---

## 不同卡片的差异化设计

| 卡片 | 个性化 | 目的 |
|------|--------|------|
| NodeCard | Tags用**紫色调**分隔，hover 上移-5px + 边框发光 | 和内容区分层次 |
| StatCard | 图标 **self-start mt-[2px]** 顶部对齐 | 避免字数不同不对齐 |
| MetricCard | label **10px uppercase** 极简风格 | 突出大数字值 |
| SysinfoCard | 内联 `load-badge` 用不同颜色区分负载等级 | 快速视觉扫描 |
| ChartCard | 底部图表区域用 D3/SVG，零依赖 | 精确控制 |

---

## 通用 UI 规则

1. **渐隐分隔线代替 border**: separator 用 `linear-gradient(90deg, transparent, rgba(...,0.08) 15%, rgba(...,0.08) 85%, transparent)`
2. **状态指示点**: 10×10 wrapper + `animate-pulse`（不要 `animate-ping`，会被圆角切）
3. **离线卡片**: `opacity-60 grayscale-[0.25]` 保持可见但不突出
4. **hover效果**: `translateY(-4px/-5px)` + 边框发光 `box-shadow: 0 0 28px rgba(16,185,129,0.06)`
5. **阴影**: 放在 Squircle 外部的独立 `<div>`，避免被 clip 掉
6. **顶部渐变光晕**: `linear-gradient(180deg, rgba(255,255,255,0.03) → transparent)` 增加立体感
