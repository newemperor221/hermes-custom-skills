# komari 1.2.0 SPA Detail View — Vanilla JS 实现方案

**日期**：2026-05-10  
**问题**：komari 1.2.0 是纯 SPA，`detail.html` 静态文件返回 HTTP 404，详情页必须嵌入 `index.html`

---

## 架构要点

```
komari 1.2.0 路由（History API）
├── / → index.html（节点列表）
└── /instance/:uuid → index.html 内的隐藏 view（详情页）
```

- **不是**独立 `.html` 文件，是 `index.html` 里的一个隐藏 `<div>`
- 用 `history.pushState()` + `popstate` 事件控制显示/隐藏
- 浏览器前进/后退按钮天然支持

---

## 实现结构

### HTML（在 `</div> <!-- page -->之后，`back-to-top` 按钮之前）

```html
<div class="detail-view hidden" id="detail-view">
  <div class="detail-nav" id="detail-nav">
    <div class="container detail-nav-inner">
      <button class="back-btn" id="detail-back" type="button">
        <svg>...</svg> 返回
      </button>
      <div style="flex:1;min-width:0;">
        <div class="detail-title" id="detail-name"></div>
        <div class="detail-subtitle" id="detail-meta"></div>
      </div>
    </div>
  </div>
  <main class="container main">
    <div class="loading" id="detail-loading">...</div>
    <div class="error-state hidden" id="detail-error"></div>
    <div class="hidden" id="detail-content">
      <div class="metrics-grid" id="detail-metrics"></div>
      <div class="detail-body">
        <div class="detail-left">
          <div class="sysinfo-card" id="detail-sysinfo"></div>
        </div>
        <div class="detail-right">
          <!-- chart-card × 3 (CPU/内存/网络) -->
        </div>
      </div>
    </div>
  </main>
</div>
```

### 核心 JS 逻辑

```javascript
// 1. 点击卡片 → pushState 路由
if (uuid) history.pushState({ uuid }, '', '/instance/' + encodeURIComponent(uuid));

// 2. 显示详情视图
function showDetailView(nodeUuid) {
  document.getElementById('detail-view').classList.remove('hidden');
  document.getElementById('list-view').classList.add('hidden');
  loadDetailData(nodeUuid);
}

// 3. 返回列表
function showListView() {
  window.removeEventListener('resize', drawDetailCharts);
  document.getElementById('detail-view').classList.add('hidden');
  document.getElementById('list-view').classList.remove('hidden');
}

// 4. popstate 处理浏览器前进/后退
window.addEventListener('popstate', (e) => {
  const match = location.pathname.match(/^\/instance\/(.+)$/);
  match ? showDetailView(decodeURIComponent(match[1])) : showListView();
});

// 5. 初始化时检查 URL
if (location.pathname.match(/^\/instance\/(.+)$/)) {
  showDetailView(decodeURIComponent(match[1]));
}
```

### CSS 要点

```css
.detail-view.hidden { display: none; }
.detail-nav { position: sticky; top: 0; z-index: 20; }
/* 滚动后加毛玻璃 */
.detail-nav.scrolled {
  background: rgba(0,0,0,0.4);
  backdrop-filter: blur(20px);
}
.detail-body { display: grid; grid-template-columns: 360px 1fr; gap: 16px; }
/* Canvas 宽度由 JS 计算（DPR 适配），CSS 只设 height */
canvas { width: 100% !important; display: block; }
```

### 数据获取

```javascript
async function loadDetailData(uuid) {
  const [nodesData, recentData] = await Promise.all([
    fetch('/api/nodes').then(r => r.json()),
    fetch('/api/recent/' + uuid).then(r => r.json())
  ]);
  const node = nodesData.data.find(n => n.uuid === uuid);
  const recent = recentData.data || [];
  // ... 渲染指标卡 + sysinfo + 图表
}
```

### komari 1.2.0 新字段（详情页需要）

| 字段 | 来源 | 用途 |
|------|------|------|
| `cpu_cores` | `/api/nodes` → node | 核心数 badge |
| `swap_total` | `/api/nodes` → node | Swap 总量（0="无"） |
| `load1/load5/load15` | `/api/recent/{uuid}` → latest | 负载均值 badge |
| `traffic_limit` | `/api/nodes` → node | 流量限额（0="无"） |
| `process` | `/api/recent/{uuid}` → latest | 进程数 |
| `connections.tcp` | `/api/recent/{uuid}` → latest | TCP 连接数 |

---

## 已知坑

1. **resize 监听器泄漏**：切换到列表页时必须 `removeEventListener('resize', drawDetailCharts)`，否则每次进入详情页都叠加一个新监听器
2. **双 `requestAnimationFrame`**：canvas 的 `offsetWidth` 在首次 layout 时为 0，需要两个 RAF 才能正确拿到宽高
3. **nginx fallback**：如果 komari 部署在 nginx 反代后面，`/instance/xxx` 路径需要在 nginx 规则里 fallback 到 `index.html`（History API 需要服务器配置支持）

## nginx fallback 规则（如果需要）

```nginx
location /instance {
  rewrite ^/instance/(.*)$ /index.html last;
}
```
