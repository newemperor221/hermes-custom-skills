# GalaxyGlass 原始设计系统（bak-v2，2026-05-17 恢复）

源自 `/opt/komari/data/theme-bak-1778947048/bak-v2/` — 用户确认可用的最后一次工作版本。

## CSS Tokens

```css
:root {
  /* Brand */
  --accent:        #10b981;
  --accent-2:      #818cf8;
  --accent-gradient: linear-gradient(135deg, #10b981, #818cf8);
  --accent-orange: #f59e0b;
  --warning:       #eab308;
  --danger:        #ef4444;
  --online:        #22c55e;
  --offline:       #6b7280;

  /* Background */
  --bg-deepest:    #020203;
  --bg-deep:       #050510;
  --bg-surface:    #0a0e1a;
  --bg-glass:      rgba(255,255,255,0.06);

  /* Chart */
  --chart-cpu:     #10b981;
  --chart-mem:     #818cf8;

  /* Text */
  --text-primary:   #f0fdf4;
  --text-secondary: rgba(240, 253, 244, 0.65);
  --text-muted:     rgba(240, 253, 244, 0.55);

  /* Glass */
  --glass-bg:       rgba(255,255,255,0.06);
  --glass-border:   rgba(255,255,255,0.10);
  --glass-hover:    rgba(255,255,255,0.10);
  --glass-strong:   rgba(255,255,255,0.12);

  /* Animation */
  --ease-out:       cubic-bezier(0.16, 1, 0.3, 1);
  --ease-in-out:    cubic-bezier(0.4, 0, 0.2, 1);
  --pulse-duration: 2s;

  /* Blur */
  --blur-card:      40px;
  --blur-surface:   24px;
  --blur-glass:     60px;

  /* Radius */
  --radius-sm:      8px;
  --radius-md:      12px;
  --radius-lg:      16px;
  --radius-full:    9999px;

  /* Spacing */
  --space-1:         4px;
  --space-2:         8px;
  --space-3:         12px;
  --space-4:         16px;
  --space-5:         24px;
  --space-6:         32px;
  --gap:             16px;
  --gap-sm:          12px;

  /* Layout */
  --container-max:   1280px;
  --container-pad:  1.75rem;

  /* Fonts */
  --font-sans: 'Fira Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI',
    'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  --font-mono: 'Fira Code', ui-monospace, 'SF Mono', 'JetBrains Mono',
    'Menlo', 'Consolas', monospace;
}

@media (max-width: 480px) {
  :root { --container-pad: 0.75rem; }
}
```

## 卡片布局参数

```css
/* Stats bar — 4列，gap 16px, radius 12px, blur 12px */
.stats-grid { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: var(--gap); }
.stat-card {
  display: flex; align-items: center; gap: var(--space-3);
  padding: 14px var(--space-4); border-radius: var(--radius-md);     /* 12px */
  background: var(--glass-bg); backdrop-filter: blur(12px);
  border: 1px solid var(--glass-border);
}
.stat-card .label { font-size: 11px; color: var(--text-muted); letter-spacing: 0.02em; }
.stat-card .value { font-size: 16px; font-weight: 700; font-family: var(--font-mono); }

/* Node cards — gap 10px, radius 16px, blur 60px */
.node-card {
  display: flex; flex-direction: column; gap: 10px;
  padding: 14px 16px; border-radius: var(--radius-lg);               /* 16px */
  background: var(--bg-glass); backdrop-filter: blur(var(--blur-glass)) saturate(120%);
  border: 1px solid rgba(45,158,107,0.08);
  box-shadow: 0 0 0 1px rgba(45,158,107,0.04), inset 0 1px 0 rgba(255,255,255,0.03);
  animation: cardIn 0.35s ease both;
}

/* Metrics inside card */
.card-metric { display: flex; align-items: center; gap: 6px; height: 20px; }
.card-metric .cm-label { font-size: 11px; font-weight: 700; width: 26px; text-align: right; }
.card-metric .cm-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.06); }
.card-metric .cm-value { width: 38px; text-align: right; font-size: 13px; font-weight: 600; }
```

## 常用尺寸总结

| 元素 | 值 | CSS 变量 |
|------|-----|---------|
| 容器最大宽度 | 1280px | `--container-max` |
| 容器 padding（桌面） | 1.75rem (28px) | `--container-pad` |
| 容器 padding（≤480px） | 0.75rem (12px) | `--container-pad` |
| 导航栏高度 | 44px | 固定 |
| 导航栏 title 字号 | 24px | 固定 |
| 导航栏 buttons | 36px 高, 13px 字号 | 固定 |
| 导航栏 gap | 0.65rem | 固定 |
| 统计卡 border-radius | 12px | `--radius-md` |
| 服务器卡 border-radius | 16px | `--radius-lg` |
| 统计卡 blur | 12px | 固定 |
| 服务器卡 blur | 60px | `--blur-glass` |
| 筛选胶囊 border-radius | 8px | `--radius-sm` |
| 卡片入场动画 | translateY(10px) scale(0.98), 0.35s ease | 固定 |
| 卡片 hover | translateY(-3px), 大阴影 | 固定 |

## 动画参数

```css
@keyframes cardIn {
  from { opacity: 0; transform: translateY(10px) scale(0.98); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}
.node-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 24px 48px rgba(0,0,0,0.35),
              0 0 0 1px rgba(45,158,107,0.18),
              0 0 28px rgba(45,158,107,0.06);
  border-color: rgba(45,158,107,0.22);
}
```
