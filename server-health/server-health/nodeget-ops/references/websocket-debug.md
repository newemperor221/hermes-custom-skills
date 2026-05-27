# NodeGet WebSocket 调试指南

## 调试顺序

### 1. 确认 HTTP API 正常
```bash
curl -s https://statapi.yourdomain.com/
# 应返回 HTML 页面（NodeGet Server 欢迎页）
```

### 2. 确认 JSON-RPC API 正常（用 WebSocket，HTTP POST 不适用）
NodeGet 的 JSON-RPC 走 WebSocket，curl HTTP POST 无法测试（会返回 Method not found）。

**浏览器 Console 测试（WS 直连 Server）：**
```js
const ws = new WebSocket('wss://statapi.yourdomain.com');
ws.onopen = () => {
  ws.send(JSON.stringify({
    jsonrpc: '2.0',
    method: 'nodeget-server\\_list\\_all\\_agent\\_uuid',
    params: { token: 'YOUR_TOKEN' },
    id: '1'
  }));
};
ws.onmessage = (e) => {
  const r = JSON.parse(e.data);
  console.log('result:', JSON.stringify(r));
  ws.close();
};
```

### 3. 浏览器原生 WebSocket 测试
在目标页面的 Console 执行：
```js
const ws = new WebSocket('wss://statapi.yourdomain.com');
ws.onopen = () => { console.log('WS OPENED'); ws.close(); };
ws.onerror = (e) => console.log('WS ERROR:', e.type);
ws.onclose = (e) => console.log('WS CLOSED:', e.code, e.reason);
```

### 4. rpc-websockets 库测试（CLI）
```bash
node -e "
const { Client } = require('rpc-websockets');
const c = new Client('wss://statapi.yourdomain.com', {autoconnect: true, reconnect: false});
c.socket.on('open', () => {
  c.call('nodeget-server_list_all_agent_uuid', {token: 'YOUR_TOKEN'})
    .then(r => { console.log('OK:', JSON.stringify(r)); c.close(); process.exit(0); })
    .catch(e => { console.log('CALL ERR:', e.message); c.close(); process.exit(1); });
});
c.socket.on('error', e => { console.log('WS ERR:', e.message); process.exit(1); });
setTimeout(() => { console.log('TIMEOUT'); process.exit(1); }, 10000);
"
```

### 5. 检查 config.json
```bash
curl -s https://stat.yourdomain.com/config.json | python3 -m json.tool
# 确认 backend_url 和 token 正确
```

## 常见误判

### ❌ "Cloudflare Bot Fight Mode 拦截 WebSocket"
- curl 对 WebSocket 端点返回 200 是**正常的**，因为 NodeGet Server 对普通 HTTP GET 也返回 200（HTML 页面）
- 真正的 WebSocket 握手需要浏览器客户端发起，带 Upgrade 头
- 不要轻易归因于 CF Bot 验证

### ✅ "连接后端中…"最常见的原因
- **没有 Agent 连接到 Server** — `uuids` 为空，前端没数据可显示
- 先装 Agent，再看状态页

## NodeGet Server 支持的 JSON-RPC 方法（StatusShow 用到的）
- `nodeget-server_list_all_agent_uuid` — 列出所有 Agent UUID
- `agent_static_data_multi_last_query` — 批量查询静态数据
- `agent_dynamic_summary_multi_last_query` — 批量查询动态摘要
- `kv_get_multi_value` — 批量查询 KV 存储
