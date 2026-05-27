# 卡片紧凑度 + 指标颜色 + Chip 密度 (2026-05-13 调整)

## 测量脚本

在浏览器 console 执行以精确测量卡片内容占比：

```js
(function() {
  var card = document.querySelector('.node-card');
  var h = card.querySelector('.node-card-header');
  var m = card.querySelector('.card-metrics');
  var f = card.querySelector('.node-footer');
  var hr = h.getBoundingClientRect();
  var mr = m.getBoundingClientRect();
  var fr = f.getBoundingClientRect();
  var cs = getComputedStyle(card);
  return {
    cardHeight: card.getBoundingClientRect().height,
    padding: cs.padding,
    contentPct: ((hr.height + mr.height + fr.height) / card.getBoundingClientRect().height * 100).toFixed(1) + '%',
    header: hr.height,
    metrics: mr.height,
    footer: fr.height,
    gapTotal: (fr.top - hr.bottom) + 'px',
    bottomGap: card.getBoundingClientRect().bottom - fr.bottom + 'px',
  };
})();
```

## 卡片紧凑化（v2.7+ 用户 feedback 驱动）

| 属性 | 旧值 | 新值 | 省空间 |
|------|------|------|--------|
| `.node-card` padding | `1rem`(14px) | `10px 14px` | 8px |
| `.node-card` gap | `10px` | `7px` | 6px |
| `.card-metric` height | `22px` | `20px` | 8px |
| `.card-metrics` gap | `5px` | `3px` | 6px |
| **卡高** | **206px** | **~183px** | **23px** |
| **内容占比** | **76%** | **89%** | **+13pp** |

## 指标颜色区分（2026-05-13）

CPU/MEM/DSK 三条进度条不再统一用绿色渐变，用不同颜色区分指标类型：

| 指标 | CSS 类 | 低占用填充色 |
|------|--------|-------------|
| CPU | `.card-metric.cpu` | `var(--accent-gradient)` (绿色) |
| MEM | `.card-metric.mem` | `linear-gradient(90deg, #7c3aed, #a78bfa)` (紫色) |
| DSK | `.card-metric.dsk` | `linear-gradient(90deg, #d97706, #f59e0b)` (琥珀) |

**实现方式**：
1. JS renderCard 中为各 metric div 添加类：`cpu`/`mem`/`dsk`
2. CSS 覆盖 `.low` 填充色：
```css
.card-metric.cpu .cm-fill.low { background: var(--accent-gradient); }
.card-metric.mem .cm-fill.low { background: linear-gradient(90deg, #7c3aed, #a78bfa); }
.card-metric.dsk .cm-fill.low { background: linear-gradient(90deg, #d97706, #f59e0b); }
```
3. medium/high 状态保持共享的 `var(--accent-orange)` / `var(--danger)`

**设计原则**：低占用时颜色区分指标类型，中/高占用时颜色反映负载等级。用户可以通过进度条颜色快速定位是哪个指标高。

## NET 空进度条删除（2026-05-13）

NET 行原本有 `<div class="cm-bar"></div>` 但内部无 `.cm-fill`，导致 CPU/MEM/DSK 三行有填充条、NET 只有空的灰色条纹，视觉上像缺口。

**修复**：
1. JS renderCard 中 NET 行去掉 `<div class="cm-bar"></div>`
2. 新增 CSS：`.card-metric.net-row { height: 18px; }`（比标准 20px 矮，因为只有 label + 文字，无进度条）

**当前 NET 行结构**：
```html
<div class="card-metric net-row">
  <span class="cm-label">NET</span>
  <span class="cm-value">
    <span class="up">↑X/s</span>
    <span class="down">↓X/s</span>
  </span>
</div>
```

## 在线状态点 7px→9px（2026-05-13）

```css
.node-status {
  width: 9px; height: 9px;  /* 旧: 7px */
  border-radius: 50%; flex-shrink: 0;
}
```

7px 与 14px 字体放在一起比例失衡，像"点"不像"指示器"。9px 更适合与卡片头部 14px 文字搭配。

## 筛选 Chip 紧凑化（2026-05-13）

| 属性 | 旧值 | 新值 |
|------|------|------|
| `.chip` padding | `7px 14px` | `5px 10px` |
| `.chip` gap | `6px` | `5px` |
| `.chip` min-height | `36px` | **移除** |

**效果**：移除 `min-height: 36px` 后，chip 高度由内容自然决定（flag 17px + padding 5px×2 = 27px），不再"大药丸包小字"。
