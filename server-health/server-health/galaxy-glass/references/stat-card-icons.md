# 统计卡大图标 SVG 路径

统计卡 4 张卡片的 SVG 大图标（2rem，20px/20px viewBox）。

## ① 时钟（时间卡）
```html
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:2rem;height:2rem;color:var(--accent,#29a944)">
  <circle cx="12" cy="12" r="10"/>
  <polyline points="12 6 12 12 16 14"/>
</svg>
```

## ② 显示器（服务器在线卡）
```html
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:2rem;height:2rem;color:var(--accent2,#3b82f6)">
  <rect x="2" y="3" width="20" height="14" rx="2" ry="2"/>
  <line x1="8" y1="21" x2="16" y2="21"/>
  <line x1="12" y1="17" x2="12" y2="21"/>
</svg>
```

## ③ 数据传输（流量概览卡）
```html
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:2rem;height:2rem;color:var(--accent3,#f59e0b)">
  <circle cx="12" cy="12" r="10"/>
  <circle cx="12" cy="12" r="3"/>
  <line x1="12" y1="2" x2="12" y2="6"/>
  <line x1="12" y1="18" x2="12" y2="22"/>
  <line x1="2" y1="12" x2="6" y2="12"/>
  <line x1="18" y1="12" x2="22" y2="12"/>
</svg>
```
（环形网络图标 — 3 圆点相连的网络符号）

## ④ 货币/账单（月度开销卡）
```html
<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="width:2rem;height:2rem;color:var(--accent4,#10b981)">
  <line x1="12" y1="1" x2="12" y2="23"/>
  <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
</svg>
```
（$ 货币符号图标）

## 小图标（第③卡内部 4 行）

| 行 | 图标 | SVG path |
|----|------|----------|
| 上传总量 | ☁️↑ | `用户提供的云朵+向上箭头 SVG` |
| 下载总量 | ☁️↓ | `用户提供的云朵+向下箭头 SVG` |
| 上行速率 | ⚡ | `M13 2L3 14h9l-1 8 10-12h-9l1-8z`（闪电） |
| 下行速率 | ⚡ | 同上，颜色不同（上行橙 #f59e0b，下行绿 #10b981） |

云朵 SVG path（用户提供，上传）:
```html
<path d="M5.25589 16C3.8899 15.0291 3 13.4422 3 11.6493C3 9.20008 4.8 6.9375 7.5 6.5C8.34694 4.48637 10.3514 3 12.6893 3C15.684 3 18.1317 5.32251 18.3 8.25C19.8893 8.94488 21 10.6503 21 12.4969C21 14.8148 19.25 16.7236 17 16.9725M12 21V11M12 11L9 14M12 11L15 14"/>
```

云朵 SVG path（用户提供，下载）:
```html
<path d="M5.25589 16C3.8899 15.0291 3 13.4422 3 11.6493C3 9.20008 4.8 6.9375 7.5 6.5C8.34694 4.48637 10.3514 3 12.6893 3C15.684 3 18.1317 5.32251 18.3 8.25C19.8893 8.94488 21 10.6503 21 12.4969C21 14.0582 20.206 15.4339 19 16.2417M12 21V11M12 21L9 18M12 21L15 18"/>
```

时钟 SVG path（流量概览卡之前用过的替代方案）:
```html
<path d="M6.34315 17.6569C5.22433 16.538 4.4624 15.1126 4.15372 13.5607C3.84504 12.0089 4.00346 10.4003 4.60896 8.93853C5.21446 7.47672 6.23984 6.22729 7.55544 5.34824C8.87103 4.46919 10.4177 4 12 4C13.5823 4 15.129 4.46919 16.4446 5.34824C17.7602 6.22729 18.7855 7.47672 19.391 8.93853C19.9965 10.4003 20.155 12.0089 19.8463 13.5607C19.5376 15.1126 18.7757 16.538 17.6569 17.6569M12 12L16 10"/>
```

### 简化云朵图标
最终采用精简版云朵+箭头（~109 chars 替代原来 ~250 chars）:
```html
<path d="M17 8h1a4 4 0 0 1 0 8H7a5 5 0 0 1-5-5 5 5 0 0 1 5-5h.5A5.5 5.5 0 0 1 17 8z"/>
<!-- 上传箭头 -->
<path d="M12 16V9m0 0l-3 3m3-3l3 3"/>
<!-- 下载箭头 -->
<path d="M12 9v7m0 0l-3-3m3 3l3-3"/>
```
