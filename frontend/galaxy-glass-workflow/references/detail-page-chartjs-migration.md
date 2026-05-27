# GalaxyGlass Chart.js Migration (2026-05-20)

## Status

**Current online (2026-05-20)**: Chart.js 4.4.7 ✅
**Previous**: ECharts 5.6.0 (replaced by user request on 2026-05-20)
**Before that**: Chart.js 4.x (replaced by ECharts because user said "不够美")
**Original**: Hand-drawn Canvas (user said "潦草")

**Key lesson**: User's chart library preference is volatile. When they say "用 charts.js 绘制", switch immediately — don't debate, don't suggest alternatives.

## CDN

```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js"></script>
```

## Core Implementation (app.js)

### `renderDetailCharts()` — entry point

Called from `renderDetailView()` after data is ready (wrapped in double `requestAnimationFrame` for DOM layout timing):

```javascript
function renderDetailCharts(cpuPts, memPts, netPts) {
  // Destroy previous charts
  if(window._charts) {
    for(var k in window._charts) {
      if(window._charts[k]) window._charts[k].destroy();
    }
  }
  window._charts = {};

  // Gradient fill helper
  function gd(ctx, top, bottom, col) {
    var c = col.replace('rgba(','').replace(')','').split(',').map(Number);
    var g = ctx.createLinearGradient(0, top, 0, bottom);
    g.addColorStop(0, 'rgba('+c[0]+','+c[1]+','+c[2]+',0.18)');
    g.addColorStop(0.5, 'rgba('+c[0]+','+c[1]+','+c[2]+',0.04)');
    g.addColorStop(1, 'rgba(0,0,0,0)');
    return g;
  }

  // Byte formatter (shared with NET tooltip)
  function bl(v) {
    if(v >= 1073741824) return (v/1073741824).toFixed(1)+'GB/s';
    if(v >= 1048576) return (v/1048576).toFixed(1)+'MB/s';
    if(v >= 1024) return (v/1024).toFixed(1)+'KB/s';
    return v.toFixed(0)+'B/s';
  }

  // Chart factory
  function mk(id, labels, datasets, isNet) {
    var el = document.getElementById(id);
    if(!el) return;
    var ctx = el.getContext('2d');
    new Chart(ctx, {
      type: 'line',
      data: { labels: labels, datasets: datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: { duration: 500, easing: 'easeOutQuart' },
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(0,0,0,0.75)',
            titleFont: { size: 11, family: 'Inter,sans-serif' },
            bodyFont: { size: 12 },
            padding: { x: 8, y: 6 },
            borderColor: 'rgba(255,255,255,0.08)',
            borderWidth: 1,
            cornerRadius: 6,
            displayColors: isNet,
            boxPadding: { x: 4, y: 2 },
            callbacks: {
              title: function(its) { return its[0].label; },
              label: function(it) {
                if(isNet) return it.dataset.label + ': ' + bl(it.raw);
                return it.raw.toFixed(1) + '%';
              }
            }
          }
        },
        scales: {
          x: {
            display: true,
            grid: { display: false },
            ticks: {
              color: 'rgba(255,255,255,0.3)',
              font: { size: 10, family: 'Inter,sans-serif' },
              maxTicksLimit: 8
            }
          },
          y: { display: false, beginAtZero: true, min: 0 }
        },
        interaction: { mode: 'index', intersect: false }
      }
    });
  }

  // Create 3 charts
  var lbs = cpuPts.map(function(p) {
    return p.t.toLocaleTimeString('zh-CN', {hour:'2-digit', minute:'2-digit'});
  });

  mk('chart-cpu', lbs, [{
    label: 'CPU',
    data: cpuPts.map(function(p) { return p.r; }),
    borderColor: '#10b981',
    backgroundColor: function(c) {
      if(!c.chart.chartArea) return;
      return gd(c.chart.ctx, c.chart.chartArea.top, c.chart.chartArea.bottom, 'rgba(16,185,129,1)');
    },
    tension: 0.4, fill: true, pointRadius: 0, pointHoverRadius: 3, borderWidth: 2
  }], false);

  mk('chart-mem', lbs, [{
    label: 'MEM',
    data: memPts.map(function(p) { return p.r; }),
    borderColor: '#818cf8',
    backgroundColor: function(c) {
      if(!c.chart.chartArea) return;
      return gd(c.chart.ctx, c.chart.chartArea.top, c.chart.chartArea.bottom, 'rgba(129,140,248,1)');
    },
    tension: 0.4, fill: true, pointRadius: 0, pointHoverRadius: 3, borderWidth: 2
  }], false);

  var nlbs = netPts.map(function(p) {
    return p.t.toLocaleTimeString('zh-CN', {hour:'2-digit', minute:'2-digit'});
  });

  mk('chart-net', nlbs, [
    {
      label: '↑ 上行',
      data: netPts.map(function(p) { return p.u; }),
      borderColor: '#f59e0b',
      backgroundColor: function(c) {
        if(!c.chart.chartArea) return;
        return gd(c.chart.ctx, c.chart.chartArea.top, c.chart.chartArea.bottom, 'rgba(245,158,11,1)');
      },
      tension: 0.4, fill: true, pointRadius: 0, pointHoverRadius: 3, borderWidth: 2
    },
    {
      label: '↓ 下行',
      data: netPts.map(function(p) { return p.d; }),
      borderColor: '#10b981',
      backgroundColor: function(c) {
        if(!c.chart.chartArea) return;
        return gd(c.chart.ctx, c.chart.chartArea.top, c.chart.chartArea.bottom, 'rgba(16,185,129,1)');
      },
      tension: 0.4, fill: true, pointRadius: 0, pointHoverRadius: 3, borderWidth: 2
    }
  ], true);
}
```

## Key Differences from ECharts

| Aspect | ECharts 5.x | Chart.js 4.x |
|--------|-------------|--------------|
| Smoothness | `smooth: true` | `tension: 0.4` |
| Gradient | `echarts.graphic.LinearGradient(...)` | `ctx.createLinearGradient()` via `backgroundColor: function(ctx){...}` |
| Resize | Manual listener (`window.addEventListener('resize', ...)`) | Auto (`responsive: true, maintainAspectRatio: false`) |
| Destroy | `.dispose()` | `.destroy()` |
| Tooltip style | HTML formatter (string with `<style>`) | Canvas tooltip with font/color/padding config |
| Y-axis hide | `yAxis: { show: false }` | `scales: { y: { display: false } }` |
| End label | `endLabel: { show: true, ... }` | Not available — use top badge instead |
| Mark point | `markPoint: { ... }` | Not available |

## Critical Pitfalls

### 1. CanvasGradient needs chartArea (race condition)

Chart.js calls `backgroundColor` as a function. When it's first called DURING chart initialization, `chartArea` (top/bottom/left/right) is NOT yet populated. The function must guard against this:

```javascript
backgroundColor: function(c) {
  if(!c.chart.chartArea) return;  // ← CRITICAL guard
  return gd(c.chart.ctx, ...);
}
```

Without this guard, `ctx.createLinearGradient(0, undefined, 0, undefined)` produces an invisible gradient, and the fill area renders as black/transparent incorrectly.

### 2. No `new Chart` without assignment creates confusing traces (cosmetic)

`new Chart(ctx, {...})` as a bare expression statement is valid JS, but linters may flag it. If a linter gives a false positive, ignore it — Chart.js doesn't require storing the return value if you track instances via `window._charts`.

### 3. Multi-line object for Chart options (avoid brace mismatch)

Chart.js options object is deeply nested (plugins → tooltip → callbacks → label). Writing it as a single line is error-prone. Use multi-line formatting:

```javascript
// Do this — easy to count braces
new Chart(ctx, {
  type: 'line',
  options: {
    plugins: {
      tooltip: {
        ...
      }
    },
    scales: { ... }
  }
});

// Don't do this — hard to debug brace mismatch
new Chart(ctx,{type:'line',options:{plugins:{tooltip:{...callbacks:{title:...},...}},scales:{...}}})
```

### 4. Tooltip displayColors for single vs multi-series

For CPU/MEM (one series), set `displayColors: false` to avoid a colored square next to the percentage. For NET (two series — up/down), set `displayColors: true` so users can distinguish which line is which.

Pass as `isNet` flag through the `mk()` function:
```javascript
displayColors: isNet,
```

## HTML Structure

```html
<!-- CPU — single line -->
<div class="chart-card">
  <div style="display:flex;align-items:center;gap:6px">
    <div class="chart-title">CPU 占用率</div>
    <div class="chart-badge" id="badge-cpu">—</div>
  </div>
  <div class="chart-canvas">
    <canvas id="chart-cpu" role="img"></canvas>
  </div>
</div>

<!-- NET — dual line with legend -->
<div class="chart-card">
  <div class="chart-header">
    <div class="chart-header-row">
      <div class="chart-header-left">
        <div class="chart-title">网络速率</div>
        <div class="chart-badge" id="badge-net">—</div>
      </div>
      <div class="chart-legend">
        <span class="legend-up">↑ 上行</span>
        <span class="legend-down">↓ 下行</span>
      </div>
    </div>
  </div>
  <div class="chart-canvas net-chart">
    <canvas id="chart-net" role="img"></canvas>
  </div>
</div>
```

## Verification

```javascript
// Smoke test — 3 charts exist and visible
Object.keys(window._charts).length  // → 3

// Check canvas has actual pixels
document.getElementById('chart-cpu').width  // → > 0
document.getElementById('chart-cpu').height // → > 0

// CPU chart has 1 dataset
window._charts['chart-cpu'].data.datasets.length  // → 1

// NET chart has 2 datasets (up + down)
window._charts['chart-net'].data.datasets.length  // → 2
```
