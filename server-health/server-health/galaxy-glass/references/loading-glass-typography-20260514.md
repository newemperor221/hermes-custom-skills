# 加载闪白/毛玻璃/排版优化 (2026-05-14)

## 加载状态闪白修复

**症状**：从列表页切换到详情页时，数据加载期间页面出现白色闪烁（白色背景短暂可见）。

**根因**：
- `.loading-state` 和 `.detail-loading` 没有设置 `background`，继承了 `--bg-surface`（深蓝）或透明
- 在 SPA 切换过程中，CSS `display: none !important` 被移除的瞬间，元素还没有任何内容，浏览器在渲染间隙显示白色背景
- canvas 图表 `ctx.clearRect(0,0,w,h)` 之前如果 canvas 尺寸尚未被 `getCtx` 正确设置，可能显示为透明（透出白色底层）

**修复**：给所有加载/过渡状态容器加上深色背景：

```css
.loading-state, .empty-state, .error-state {
  background: var(--bg-deep);
}

.detail-loading, .detail-error {
  background: var(--bg-deep);
}
```

**原理**：`var(--bg-deep)` 是深空蓝黑 `#0c1f3f`，与页面背景一致。加载状态显示时不会出现白色闪烁。使用 CSS 变量而非硬编码色值，确保主题切换时自动跟随。

**原则**：任何涉及 `display: none ↔ block/flex` 切换的容器都应有明确的 background。特别是：
- 加载/空/错误状态（`.loading-state`, `.empty-state`, `.error-state`）
- 详情页加载覆盖层（`.detail-loading`）
- 骨架屏（`.skeleton-card` — 已有 `background: var(--bg-glass)` ✅）
- SPA 视图切换时的过渡元素

## 毛玻璃透明度优化

**目标**：使玻璃效果「看得见但不过度」。

**原始值**（v2.7.0 早期）：
- `--bg-glass: rgba(255,255,255,0.025)` — 卡片背景
- `--glass-bg: rgba(255,255,255,0.03)` — UI 控件背景

**问题**：0.025 意味着 97.5% 的背景透过卡片，玻璃几乎不可见。卡片看起来只是普通半透明，没有「玻璃」质感。

**优化后**（2026-05-14 用户 approval）：
- `--bg-glass: rgba(255,255,255,0.06)` — 从 0.025 提升到 0.06 (2.4x)
- `--glass-bg: rgba(255,255,255,0.06)` — 从 0.03 提升到 0.06 (2.0x)

**效果**：
- 6% 白色叠加在深蓝背景上产生可见的毛玻璃感
- 配合 `backdrop-filter: blur(40px)` 形成真实的玻璃质感
- 信息可读性不受影响（文字色 `#f0fdf4` 在 6% 白底上对比度足够）

**注意事项**：
- `--bg-glass` 用于大面积极卡片背景（skeleton-card, node-card），透明度过高会丧失玻璃感
- `--glass-bg` 用于小控件（search-box, sort-btn, filters, stat-card, chart-card），透明度需要和 `backdrop-filter` 的 blur 值配合
- 如果是明亮壁纸（白天场景），6% 白色可能略重，可适度降至 4-5%
- 如果是暗色壁纸（夜景场景），6% 正好

## 图表排版字号优化

**原始值**：
- `.chart-title`（"CPU 占用率"、"内存占用率"、"网络速率"）：12px
- `.chart-badge`（"66.3%"、"↑ 366B/s · ↓ 218B/s"）：12px

**提升后**：
- `.chart-title`：12px → 13px
- `.chart-badge`：12px → 13px

**理由**：
- 14px 基础字体的页面中，12px 偏小。13px 是「最小可读字号」和「紧凑排版」之间的平衡点
- 图表标题和 badge 是详情页右侧的核心信息入口，需要与左侧 `metric-card .metric-sub`（11px）拉开视觉层级
- 不需要调整 `--font-mono` 字族，13px 在 monospace 字体下可读性已足够
