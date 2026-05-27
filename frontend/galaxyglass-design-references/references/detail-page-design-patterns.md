# 探针详情页设计模式（Detail Page）

> stat.357561.xyz 服务器详情页的视觉设计模式
> 来源: 2026 暗色仪表盘趋势研究 (Muzli, Dribbble, Dark Glassmorphism)
> 最后更新: 2026-05-20（确立chart-header column布局 + 无坐标轴原则）

## 布局

```
┌──────────────────────────────────────────┐
│ [←]  服务器名  🇺🇸 · lxc · Alpine         │ ← 导航栏
├──────────────────┬───────────────────────┤
│  左侧信息面板     │    右侧图表区          │
│  1fr             │    1.2fr              │
│                  │                       │
│  💻 硬件         │  ┌─ 渐变绿条 ─┐       │
│  CPU 型号        │  │ CPU 占用率 42.6%  │ ← 文字全在顶部
│  核心数           │  │  ▂▃▅█▇▆▅         │ ← 图表满宽，无坐标轴
│  ...             │  └───────────┘       │
│                  │  ┌─ 渐变紫条 ─┐       │
│                  │  │ 内存占用率  2.0%    │
│                  │  │  ▁▃▄▆▇█▇          │
│                  │  └───────────┘       │
│  📡 网络         │  ┌─ 渐变橙条 ─┐       │
│  流量限额 1000GB  │  │ 网络速率          │
│                  │  │ ↑上行 ↓下行        │
│  ⚡ 状态         │  │  ↑▂▃▄▅▆▇         │
│  进程数 17       │  └───────────┘       │
│  更新 1分钟前     │                       │
├──────────────────┴───────────────────────┤
│  tags-card (标签 · 连接)                  │
└──────────────────────────────────────────┘
```

## 关键视觉模式

### 0. ⭐ 核心原则：所有文字在卡片顶部，图表满宽无坐标轴

**这条原则是用户经过4轮发火后确立的。** 不要试图加Y轴/X轴。

```
❌ 错误：有Y轴 → 数据被挤到左边
┌──────────────────┐
│ 网络速率          │
│ 6K┤╱╲    ╱╲     │ ← Y轴占空间
│ 4K┤╱  ╲  ╱  ╲    │
│ 2K┤╱    ╲╱    ╲   │
└──────────────────┘

✅ 正确：无坐标轴，文字在上，图表满宽
┌──────────────────┐
│ 网络速率  ↑3KB/s  │ ← 标题+数据 第一行
│ ↑ 上行  ↓ 下行    │ ← 图例 第二行
│                   │
│  ╱╲    ╱╲        │ ← 图表满宽，无轴
│ ╱  ╲  ╱  ╲       │
└──────────────────┘
```

### chart-header column 布局（核心实现）

```css
/* 必须用 column 纵排，不能 space-between 横排 */
.chart-header { 
  display: flex; 
  flex-direction: column;   /* ← column 不是 row */
  gap: 2px; 
}
.chart-header-left { 
  display: flex; 
  align-items: center; 
  gap: 6px; 
}
.chart-legend { 
  display: flex; 
  gap: 8px; 
  font-size: 11px; 
  color: var(--text-muted); 
}
```

HTML结构（网络速率卡片为例）：
```html
<div class="chart-card">
  <div class="chart-header">            <!-- column -->
    <div class="chart-header-left">      <!-- row: title + badge -->
      <div class="chart-title">网络速率</div>
      <div class="chart-badge" id="badge-net">—</div>
    </div>
    <div class="chart-legend">           <!-- row: up/down labels -->
      <span class="legend-up">↑ 上行</span>
      <span class="legend-down">↓ 下行</span>
    </div>
  </div>
  <div class="chart-canvas net-chart">
    <canvas id="chart-net"></canvas>
  </div>
</div>
```

渲染效果：
```
┌──────────────────────────────┐
│ 网络速率    ↑3KB/s · ↓2KB/s  │ ← title+badge 第一行
│ ↑ 上行    ↓ 下行             │ ← legend 第二行
│                              │
│    ╱╲    ╱╲                 │ ← chart 满宽
│   ╱  ╲  ╱  ╲                │
└──────────────────────────────┘
```

### 1. 颜色编码体系
| 指标 | 颜色 | CSS变量 |
|------|------|---------|
| CPU 使用率 | 翠绿 #10b981 | `--accent` |
| 内存使用率 | 靛紫 #818cf8 | `--accent-2` |
| 网络上行 | 橙色 #f59e0b | `--accent-orange` |
| 网络下行 | 翠绿 #10b981 | `--accent` |

### 2. 组标题风格
- 11px 小字 + emoji 前缀：`💻 硬件` `📡 网络` `⚡ 状态`
- letter-spacing 0.05em，全大写感（实际中文）
- 上方有 8px padding 分隔不同信息块

### 3. 图表卡片顶部分隔条
```css
.chart-card { position: relative; }
.chart-card::before {
  content: ''; position: absolute; top: 0; left: 14px; right: 14px;
  height: 2px; border-radius: 0 0 2px 2px;
}
.chart-card:nth-child(1)::before { background: linear-gradient(90deg, #10b981, rgba(16,185,129,0.2)); }
.chart-card:nth-child(2)::before { background: linear-gradient(90deg, #818cf8, rgba(129,140,248,0.2)); }
.chart-card:nth-child(3)::before { background: linear-gradient(90deg, #f59e0b, rgba(245,158,11,0.2)); }
```

### 4. 图表卡片高度差异化
- CPU/内存：130px（`.chart-canvas`）
- 网络速率（上行+下行双折线）：200px（`.chart-canvas.net-chart`）

CSS：
```css
.chart-canvas { width: 100%; height: 130px; }
.chart-canvas canvas { width: 100% !important; height: 130px !important; }
.chart-canvas.net-chart { height: 200px; }
.chart-canvas.net-chart canvas { height: 200px !important; }
```

### 5. Chart.js 无坐标轴配置（当前方案，替代 ECharts）
```js
// 基础配置 — 无显示坐标轴
{
  backgroundColor: 'transparent',    // 融入毛玻璃
  grid: {left: 4, right: 4, top: 4, bottom: 4},  // 满宽
  xAxis: {type: 'category', data: lbs, show: false},  // 不显示
  yAxis: {type: 'value', show: false, min: 0},        // 不显示
  animationDuration: 300
}
```

关键参数：

| 参数 | 值 | 说明 |
|------|-----|------|
| init theme | 无 | `echarts.init(dom)` 不要传 'dark'，用户拒绝 |
| backgroundColor | 'transparent' | 透明以契合毛玻璃卡片 |
| grid | 4px all | 图表满宽 |
| xAxis.show | false | 时间轴隐藏 |
| yAxis.show | false | 数值轴隐藏 |
| smooth | true | 贝塞尔曲线平滑 |
| symbol | 'none' | 不显示数据点 |
| lineStyle.width | 2 | 线条粗细 |

## 设计原则（探针面板专用）

1. **数据密度优先** — 每一行都有意义，不要装饰性留白
2. **颜色即含义** — 不要为好看而用色，每种颜色对应一种指标
3. **左文字右数值** — 标签左对齐，数值右对齐，符合扫视路径
4. **分组可见** — 信息分 3-4 组，组标题让用户跳读
5. **图表与数据联动** — 图表当前值 = 图表区唯一来源，左侧信息面板不要重复展示已用图表展示的使用率数据
6. **布局平衡** — 左侧信息卡片的高度应尽量与右侧图表区等高，避免底部大片空白；可通过拆分sysinfo为多张卡片（硬件/网络&状态/标签）来填充纵向空间
7. **⭐ 所有文字在卡片顶部，图表无坐标轴满宽** — 不要放Y轴/X轴在左侧占空间

## 设计迭代流程（用户工作流）

> 用户对设计敏感且反馈高效。整个过程是：**我改 → 你看 → 你指正 → 我再改**

### Phase 1: 研究
用户说"有点单调"或"学学设计"时：搜索 Dribbble/Muzli/Dark Dashboard UI，收集 3-5 个具体可落地的视觉模式。

### Phase 2: 实施
1. 改 CSS → 改 JS → build → deploy → GitHub push
2. 用 browser 工具截图验证

### Phase 3: 修正反馈
常见指正模式及正确响应：
- "我认为左边没必要加上XXX" → 立即移除，右侧已有
- "左下角空了很多" → 拆分卡片填满左侧
- "有点单调了" → 重新研究
- "没有坐标系" → 不要加坐标轴！用户要的是数据可读性
- "都挤到左边去了" → 移除Y轴，文字放卡片顶部

## 代码实现要点

### 返回按钮纯图标
```html
<button class="back-btn" aria-label="返回">
  <svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
    <path fill-rule="evenodd" d="M7.72 12.53a.75.75 0 0 1 0-1.06l7.5-7.5a.75.75 0 1 1 1.06 1.06L9.31 12l6.97 6.97a.75.75 0 1 1-1.06 1.06l-7.5-7.5Z" clip-rule="evenodd"/>
  </svg>
</button>
```
```css
.back-btn { padding: 6px; min-height: 32px; min-width: 32px; justify-content: center; }
```

### 左侧信息卡片拆分（填充纵向空间）
```html
<div class="detail-left">
  <div class="sysinfo-card" id="detail-hw"></div>
  <div class="sysinfo-card" id="detail-status"></div>
  <div class="tags-card" id="detail-tags"></div>
</div>
```
```js
$('detail-hw').innerHTML = '<div class="sysinfo-single">' + leftRows.map(rr).join('') + '</div>';
$('detail-status').innerHTML = '<div class="sysinfo-single">' + rightRows.map(rr).join('') + '</div><div class="sysinfo-bill">...</div>';
```
