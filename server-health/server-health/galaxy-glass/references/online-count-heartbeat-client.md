# 客户端在线人数心跳（localStorage + BroadcastChannel）

## 背景
2026-05-19：登录按钮替换为在线人数显示。不使用后端 API，纯前端方案。

## 实现

### HTML
```html
<span class="online-badge" id="online-count">● <span id="online-num">1</span> 在线</span>
```

### CSS
```css
.online-badge {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 11px; color: var(--text-muted);
  white-space: nowrap; flex-shrink: 0;
}
.online-badge #online-num {
  font-variant-numeric: tabular-nums;
  min-width: 1em; text-align: center;
}
```

### JS
```javascript
function startHeartbeat(){
  // 每个 tab 生成唯一 ID，存 sessionStorage（tab 关闭自动清除）
  var tid = sessionStorage.getItem('gg_tab_id')
    || 't_' + (Date.now() + '_' + Math.random().toString(36).slice(2, 8));
  sessionStorage.setItem('gg_tab_id', tid);

  var key = 'gg_tabs';
  function sync() {
    try {
      var m = JSON.parse(localStorage.getItem(key) || '{}');
      m[tid] = Date.now();
      // 清除 90 秒无心跳的 tab
      var keys = Object.keys(m), now = Date.now();
      keys.forEach(function(k){ if (now - m[k] > 90000) delete m[k]; });
      localStorage.setItem(key, JSON.stringify(m));
      var n = Object.keys(m).length;
      document.getElementById('online-num').textContent = n || 1;
    } catch(e) {}
  }
  sync();

  // 每 30 秒心跳
  setInterval(sync, 30000);

  // tab 关闭前清理
  window.addEventListener('beforeunload', function(){
    try {
      var m = JSON.parse(localStorage.getItem(key) || '{}');
      delete m[tid];
      localStorage.setItem(key, JSON.stringify(m));
    } catch(e) {}
  });

  // BroadcastChannel 同源跨 tab 实时同步
  try {
    var bc = new BroadcastChannel('gg_tabs');
    bc.onmessage = function(){ sync(); };
    setInterval(function(){ bc.postMessage('ping'); }, 30000);
  } catch(e) {
    // BroadcastChannel 不支持时仅靠轮询 localStorage
  }
}
```

## 限制
- 仅统计**同浏览器**的标签页（localStorage 域隔离）
- 不同浏览器/不同设备无法互知
- 如有跨设备需求，需在后端/代理层面加 tab heartbeat API 端点
