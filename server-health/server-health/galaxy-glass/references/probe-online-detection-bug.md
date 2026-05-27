# 探针在线检测逻辑分析（2026-05-18）

## 发现：mergeNodeData() 无时间戳判在线

**位置：** `~/galaxy-glass/nextjs/src/lib/api.ts` `mergeNodeData()`

```typescript
export function mergeNodeData(node: NodeData, recent: RecentDataPoint[]): MergedNode {
  if (!recent || recent.length === 0) {
    return { ...node, online: false, ... }   // 没数据 → 离线 ✅
  }
  const latest = recent[0];
  return {
    ...node,
    online: true,   // ← 有数据就标在线 ❌ BUG
    ...
  };
}
```

**症状：** 只要 Komari 后端 `/api/recent/{uuid}` 返回了至少一条历史数据（无论多旧），前端就标记为在线。

## 修复（2026-05-18，已部署到源码）

**修复位置：** `~/galaxy-glass/nextjs/src/lib/api.ts` `mergeNodeData()`

**变更：**
```typescript
const ONLINE_THRESHOLD_MS = 150_000; // 150s safety margin (agents push every 60s)

export function mergeNodeData(node: NodeData, recent: RecentDataPoint[]): MergedNode {
  if (!recent || recent.length === 0) {
    return { ...node, online: false, ... };
  }
  const latest = recent[0];
  let online = false;
  if (latest.updated_at) {
    const elapsed = Date.now() - new Date(latest.updated_at).getTime();
    online = elapsed < ONLINE_THRESHOLD_MS;
  }
  return {
    ...node,
    online,
    ...
  };
}
```

**设计选择：**
- `ONLINE_THRESHOLD_MS = 150_000`（2.5× agents 的 60s 上报间隔），允许一次漏报不误判离线
- 如果 `updated_at` 为 null → `online = false`（安全降级）
- 无需后端修改，纯前端修复

## 验证方法（部署后测试）

```bash
# 检查某节点最近一次上报时间
sqlite3 /opt/komari/data/komari.db \
  "SELECT client, MAX(time) as last_time, \
   ROUND((julianday('now') - julianday(MAX(time))) * 86400) as seconds_ago \
   FROM records GROUP BY client ORDER BY seconds_ago"
```

## 实际验证结果（2026-05-18 部署后）

探测 5 个节点的最近上报时间，全部在 150s 阈值内：

| 节点 | 最近上报 | 距当前 | 状态 |
|------|---------|:------:|:----:|
| ccs-la2 | 18:35:55 | 19s | ✅ ONLINE |
| racknerd-ny | 18:35:55 | 19s | ✅ ONLINE |
| dedirock | 18:35:54 | 20s | ✅ ONLINE |
| 56idc-la | 18:35:07 | 67s | ✅ ONLINE |
| jiangjunji | 18:35:18 | 56s | ✅ ONLINE |

**注意：如果某节点 `seconds_ago > 120` 但在面板上仍显示绿色"在线"，说明修复仍有问题。**

**浏览器端验证：**
1. 打开 stat.357561.xyz
2. F12 → Console → `nodesList.filter(n => n.online).length / nodesList.filter(n => !n.online).length`
3. 手动构造旧数据测试：在 Console 中 `mergeNodeData({uuid:'test'}, [{updated_at: new Date(Date.now()-180_000).toISOString()}]).online` 应返回 false

| 概念 | 实现位置 | 状态 |
|------|---------|------|
| **探针在线** (Probe/Agent) | `mergeNodeData()` 前端逻辑 | ✅ 已修复 — 150s 时间戳阈值 |
| **浏览器在线人数** (Tab heartbeat) | `galaxy-proxy.py` `/api/proxy/online-count` | ✅ 正确 — 90s TTL + UUID |

**注意：** 不要混淆这两个概念。浏览器在线人数（右上角"N人在线"胶囊）用的是 Tab UUID 心跳机制，计算是正确的。有 bug 的是探针列表里每个节点的在线状态标记。

## 数据管道

```
Agent → WebSocket → Komari server(:25776) → SQLite records表
  → Next.js 前端 /api/nodes 拉节点列表
  → /api/recent/{uuid} 拉最新数据
  → mergeNodeData() 判断在线（bug在这里）
```

## 验证方法

```bash
# 检查某节点最近一次上报时间
sqlite3 /opt/komari/data/komari.db \
  "SELECT client, MAX(time) as last_time, \
   ROUND((julianday('now') - julianday(MAX(time))) * 86400) as seconds_ago \
   FROM records GROUP BY client ORDER BY seconds_ago"
```

如果某节点 `seconds_ago > 120` 但在面板上仍显示绿色"在线"，就是此 bug。
