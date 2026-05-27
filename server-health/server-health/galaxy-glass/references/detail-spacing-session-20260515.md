# 2026-05-15 详情页调优 — 间距 + sysinfo-grid + 网络箭头

## 详情页导航栏与内容的间距

用户反馈「返回按钮那行和内容离得有点远」。

**迭代**：
1. `detail-content-wrap { padding-top: 0 }` + `detail-body { margin-top: 8px }` → 用户说「第二个改回去」（回退 CPU 型号修改） + 「继续调」
2. `detail-body { margin-top: 0 }` + `#detail-view .container.main { padding-top: 0.5rem }` → 「可以了」

**最终总间距**：~9px（nav padding-bottom）+ ~7px（.container.main padding-top）= **~16px**

## sysinfo-grid 两列间距

用户反馈「第三行左边那个卡片，第一列的值和第二列的标题都挤在一起了」。

**根因**：`.sysinfo-grid { gap: 0 }` 导致两列之间没有水平间距。左列值右对齐、右列标签左对齐，刚好在网格边界处相遇。

**修复**：`.sysinfo-grid { gap: 0 16px }`（只加水平 gap，垂直 gap 由行 border-bottom 提供）

## 尝试过但被回退的修改

给 `.sysinfo-row` 的 label 加 `min-width: 48px`、value 加 `max-width: 65%` — 用户说「第二个改回去」。回退到原始样式。

## 网络卡片箭头间距

用户说「网络那个卡片箭头和数据之间缺少间隔」。

**根因**：详情页 metrics 卡片中 network 值的 JS 拼写不带空格：
- stat 栏：`'↑ '+bytes(ttUp)` ✅
- detail chart badge：`'↑ '+bytes(nu)+'/s · ↓ '+bytes(nd)+'/s'` ✅
- detail metric 卡片：`'↑'+bytes(nu)+'/s ↓'+bytes(nd)+'/s'` ❌

**修复**：在 ↑/↓ 后加空格，与 stat 栏一致。
