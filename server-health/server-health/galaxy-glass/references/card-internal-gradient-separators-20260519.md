# Next.js 版卡片内部渐隐分隔线 + 间距适配（2026-05-19）

## 背景

之前静态版（vanilla JS index.html）已实现的卡片内部渐隐分隔线（replacing hard `border-top`/`border-bottom` with `::before` gradient-fading lines），在 2026-05-19 session 中移植到 Next.js 版。

同时发现 Next.js 版 NodeCard 中 Tags 放在 Footer **下方**（逻辑错误），一并修正。

## 改动清单

### 1. NodeCard.tsx — 底部分隔线 + 间距 + Tags 位置

**分隔线替换：**
```tsx
// ❌ 旧：硬直角线
<div className="flex items-center gap-2 pt-[7px] font-mono text-[12px] text-text-muted border-t border-glass-border/10">

// ✅ 新：渐隐线
<div className="relative flex items-center gap-2 pt-[10px] font-mono text-[12px] text-text-muted">
  <div className="absolute top-0 left-0 right-0 h-px pointer-events-none"
    style={{
      background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.10) 12%, rgba(255,255,255,0.10) 88%, transparent)",
    }}
  />
```

**Tags 位置修复：** Tags 从 Footer **下方**移动到 Metrics（CPU/MEM/DSK）**上方**，OS info 行下方。

**Padding 增大（适配 squircle radius=22）：** `p-[14px_16px]` → `p-[16px_18px]`

**移除 per-card shimmer keyframes：** 原来每张卡片内联 `<style>{`@keyframes shimmer {...}`}</style>` → 移到 `globals.css` 全局定义一次。Shimmer 动画通过 `animation: "shimmer 3s ease-in-out infinite"` 在 `style` prop 中引用。

### 2. DetailContent.tsx — sysinfo 行分隔线

```tsx
// ❌ 旧：硬直角线（border-b）
<div key={i} className="flex justify-between items-center py-1.5 border-b border-white/5 last:border-b-0">

// ✅ 新：渐隐线
<div key={i} className="flex justify-between items-center py-1.5 relative">
  {i < rows.length - 1 && (
    <div className="absolute bottom-0 left-0 right-0 h-px pointer-events-none"
      style={{
        background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.05) 10%, rgba(255,255,255,0.05) 90%, transparent)",
      }}
    />
  )}
```

### 3. globals.css — 全局 keyframes

添加 `@keyframes shimmer` 和 `@keyframes live-pulse` 全局动画定义。

## 渐变分隔线的 Tailwind 实现模式

由于 Tailwind 不直接支持 `linear-gradient` on borders，改用**条件渲染的绝对定位 `<div>`** 伪元素：

```tsx
// 模式：条件渲染的 h-px div 替代 ::before
<div className="relative">
  {condition && (
    <div className="absolute top-0 left-0 right-0 h-px pointer-events-none"
      style={{
        background: "linear-gradient(90deg, transparent, <color> 12%, <color> 88%, transparent)",
      }}
    />
  )}
  {/* content */}
</div>
```

关键：
- `absolute top-0 left-0 right-0` — 拉伸到父容器宽度
- `h-px` — 1px 高
- `pointer-events-none` — 不拦截点击
- `<color>` 用 `rgba(255,255,255,0.10)`（白色10%）或 `rgba(255,255,255,0.05)`（白色5%）依使用场景
- 12% 起止是经验值，~300px 宽的卡片上 fade 自然
- `.node-footer` 最后不需要隐藏伪元素（只有一个分隔线）
- `.sysinfo-row` 最后一条用 `i < rows.length - 1` 条件跳过

## 后续同步建议

- 将 NodeCard 的 shimmer `<style>` 注入完全移除（已移入 globals.css）
- 如果将来 Squircle 半径变化（22px→其他值），同步调整卡片内 padding
