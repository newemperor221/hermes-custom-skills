# 2026-05-17 — Backdrop-filter + Squircle + Chinese Fonts 修复

## Chrome clip-path + backdrop-filter 冲突（终版修复）

### 问题
`@squircle-js/react` 的 SVG clip-path 在 Chrome 中会**裁剪掉 backdrop-filter**，导致服务器卡片没有强模糊（统计卡片和标签栏不受影响，因为它们不用 clip-path）。

### 终版方案：两层结构

外层：`borderRadius: 22, overflow: "hidden"` — 控制视觉边缘
- 第一内层（absolute inset-0）：backdrop-filter，全尺寸，**不受 clip-path 影响**
- 第二内层（absolute inset-0）：inset box-shadow 模拟边框
- 第三内层（Squircle 组件 relative z-10）：只裁剪内容形状

```tsx
<motion.a style={{ borderRadius: 22, overflow: "hidden", boxShadow: "var(--shadow-card)" }}>
  {/* ✅ backdrop-filter 在外层，无 clip-path */}
  <div className="absolute inset-0" style={{
    background: "var(--glass-bg)",
    backdropFilter: "blur(var(--blur-glass)) saturate(120%)",
  }} />
  {/* 边框 */}
  <div className="absolute inset-0 pointer-events-none"
    style={{ boxShadow: "inset 0 0 0 1px rgba(45,158,107,0.12)", borderRadius: 22 }} />
  {/* Squircle 仅裁剪内容 */}
  <Squircle cornerRadius={22} cornerSmoothing={0.6} className="relative z-10">
    <div className="p-4 flex flex-col gap-3">{/* content */}</div>
  </Squircle>
</motion.a>
```

**关键：backdrop-filter 元素不能是 Squircle 组件的孩子，必须是与 Squircle 同级的兄弟或外层包裹。**

## 中文字体策略（2026-05-17 修正）

### 问题
Google Fonts（Fira Sans / Inter）**不支持中文**，且在中国经常被墙。中文字会回退到系统 PingFang/Noto Sans，与英文字体产生视觉不匹配。

### 修复
去掉 Google Fonts，使用纯系统字体栈：
```css
--font-sans: -apple-system, BlinkMacSystemFont,
  "SF Pro Display", "PingFang SC", "Noto Sans SC", "Microsoft YaHei",
  system-ui, "Segoe UI", Roboto, Helvetica, sans-serif;
--font-mono: "SF Mono", "JetBrains Mono", "Fira Code",
  ui-monospace, Menlo, Consolas, "Noto Sans Mono", monospace;
```

也去掉了 layout.tsx 中的 `<link href="...fonts.googleapis.com...">`，零外部依赖。

## 背景色微调

从 `#020203`/`#050510`（极黑）改为 `#0a0a0f`/`#0d0d14`（柔和深灰）：
- Google Material Design dark theme 建议使用 `#121212` 而非纯黑
- 纯黑 (`#000`) 在 dark UI 中对比度过高，容易导致眼睛疲劳
- 文字也从 `#f0fdf4` 改为 `#e8f5e9`（更温和的亮白绿）

## Design 工作流（从用户反馈提炼）

用户明确要求的迭代方式：
1. **不要猜** — 不确定的设计实现先上网找教程/案例
2. **短指令迭代** — 用户给"继续加""宽一些"这类简短反馈，改完看结果
3. **一次指出全部问题** — 用户会列出所有问题，期望批量一次性修完
4. **别自作主张替换设计系统** — 不要擅自更换配色/字体/风格

## Komari API 端点

正确的 API 端点（从原始备份 data.js 确认）：
- `/api/public` — 站点信息
- `/api/nodes` — 节点列表
- `/api/recent/{uuid}` — 节点近期数据
- `/api/proxy/exchange-rate` — 汇率
- `/api/proxy/online-count?t={tabId}` — 在线人数
