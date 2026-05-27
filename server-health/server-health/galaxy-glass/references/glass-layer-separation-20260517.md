# SquircleClip 玻璃层分离 + borderBoxSize 修复

**日期：** 2026-05-17  
**问题：** GalaxyGlass Next.js 版 Chrome 上下所有卡片的毛玻璃消失  
**影响范围：** NodeCard（80px 模糊）、StatsBar（60px 模糊）

## 问题 1：clip-path + backdrop-filter 同一元素 → blur 丢弃

### 根因
Chrome 已知 bug：当 `clip-path` + `backdrop-filter` 在同一元素上时，Chrome 丢弃 backdrop-filter（多年未修）。

### 初始尝试
`willChange: 'transform'` 条件性设置（仅 ResizeObserver 测量后）——但首次 paint 发生在测量之前，Chrome 已做出丢弃决策。

### 修复
将玻璃层拆到独立的 `absolute inset-0` 子元素上，与 `clip-path` 容器分离：

```tsx
<SquircleClip radius={20} smoothing={0.6}
  className="relative border ..."
>
  {/* 玻璃层 — 单独承担 backdrop-filter */}
  <div className="absolute inset-0 pointer-events-none
    bg-[rgba(255,255,255,0.08)]
    backdrop-blur-[80px] saturate-[1.2]"
  />
  {/* 内容层 — z-index 高于玻璃层 */}
  <div className="relative z-[1] ...">
    {children}
  </div>
</SquircleClip>
```

### 配套修改
- `SquircleClip.tsx`：`willChange: "transform"` 改为始终设置（不依赖 dims 条件）
- `NodeCard.tsx`：移除 SquircleClip className 中的 `bg-[...] backdrop-blur-[...]` 及 hover background 过渡
- `StatsBar.tsx`：相同的玻璃层分离模式，提取为 `GlassCard` 辅助组件

## 问题 2：contentRect 排除 padding → clipPath 裁切内容

### 根因
`SquircleClip.tsx` 中使用 `entry.contentRect` 测量尺寸。`contentRect` 返回的是**内容区**尺寸（excludes padding + border）。当卡片有 20px padding 时，clip-path 只覆盖内容区（249.5x157px），padding 范围（20px 各边）超出 clip-path → 数值、边框、玻璃层被裁切。

### 修复
改用 `entry.borderBoxSize[0]`（含 padding）：

```tsx
const box = entry.borderBoxSize?.[0];
const w = box ? box.inlineSize : entry.contentRect.width;
const h = box ? box.blockSize : entry.contentRect.height;
```

- `borderBoxSize.inlineSize` = 宽度（含 padding + border）
- `borderBoxSize.blockSize` = 高度（含 padding + border）
- `box?.[0]` 回退到 `contentRect` 兼容旧浏览器

### 验证
```js
// 浏览器 console
const card = document.querySelector('[style*="clip"]');
const s = getComputedStyle(card);
console.log('padding:', s.padding); // 应为 "20px"
// 确认最后一条文本在卡片范围内
const content = card.querySelector('[class*="z-[1]"]');
const last = content.lastElementChild;
console.log('last text bottom:', last.getBoundingClientRect().bottom);
console.log('card bottom:', card.getBoundingClientRect().bottom);
// 应满足: lastBottom (+ margin) < cardBottom
```

## 部署后的浏览器缓存问题

Next.js Turbopack 构建时 JS 文件名哈希可能不变（`Uta72SnjosHJgLLDCbEE5` 由项目结构决定），导致浏览器从本地 HTTP 缓存加载旧 JS。

**此时：** `curl` 从 Cloudflare 拉的 JS 已含新值，但 `getComputedStyle()` 仍返回旧值。

**解决方案：**
1. 部署后告知用户 Ctrl+F5 / Cmd+Shift+R 硬刷新
2. 如果不行，修改 `next.config.ts` 触发新哈希
3. 下次构建自然会产生新哈希（如添加新组件）
