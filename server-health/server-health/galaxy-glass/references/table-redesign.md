# 表格视图重设计（三阶段演变）

## v1 — 9列水平（太细了 ❌）
```
🟢 Acck | 东京 │ CPU 5% │ 内存 25% │ 磁盘 17% │ ↓3K │ ↑256B │ 15天 │ ¥148/年 │ 70G/500 │ 285天
```
- 9 列固定宽度 `58 72 72 62 62 68 76 84 62`，合计仅 ~616px
- 行宽 1124px，右边空了 283px 空白
- 每列太细（94px），用户反馈"太细了"

## v2 — 每行2列 perf+bill（还不错）
```
┌──────────────────────────────┐  ┌──────────────────────────────┐
│ 🟢🐧 Acck|东京 🇯🇵           │  │ 🟢 ¥148.88/年               │
│ CPU ████████████  5.1%      │  │ 流量 70G/500G               │
│ 内存 █████████████████  25.5%│  │ 剩余 285天                 │
│ 磁盘 ██████████  17.1%      │  │                              │
│ ↓3.9K/s  ↑0B/s  15天20时    │  │                              │
└──────────────────────────────┘  └──────────────────────────────┘
col-perf (443px)                  col-bill (443px)
```
- 每列 ~443px，内容松散
- perf 列左侧有很多空白
- 用户反馈"还不错"但仍然不是最终方案

## v3 ✅ — 2列网格紧凑卡片（当前）
```
┌──────────────────────────────────────┐  ┌──────────────────────────────────────┐
│ 🟢 🐧 Acck | 东京 🇯🇵                │  │ 🟢 🐧 Acck | 香港 🇭🇰                │
│ CPU ████████████████████████  5.0%   │  │ CPU ████████████████████  3.9%       │
│ 内存 ██████████████████████████████ 25.5%│  │ 内存 ██████████████████████████ 49.2% │
│ 磁盘 ████████████████████████████  17.1%│  │ 磁盘 ████████████████████████  20.1% │
│ ↓5.3K/s · ↑0B/s · 15天 · ¥148/年 · 70G/500G · 285天│  │ ↓... · ↑... · ...             │
└──────────────────────────────────────┘  └──────────────────────────────────────┘
                 554px                                     554px
```

### CSS
```css
#table-body { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.table-row {
  display: flex; flex-direction: column; gap: 8px;
  padding: 12px 14px; border-radius: 12px;
  background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05);
  cursor: pointer; transition: transform 0.2s, box-shadow 0.2s;
}
.table-row:hover { transform: translateY(-3px); box-shadow: 0 8px 32px rgba(0,0,0,0.3); }
.row-title { display: flex; align-items: center; gap: 6px; font-size: 13px; }
.row-meters { display: flex; flex-direction: column; gap: 4px; }
.meter-row { display: flex; align-items: center; gap: 6px; }
.meter-label { width: 36px; font-size: 11px; color: rgba(255,255,255,0.5); }
.meter-bar { flex: 1; height: 8px; background: rgba(255,255,255,0.08); border-radius: 4px; overflow: hidden; }
.meter-fill { height: 100%; border-radius: 4px; transition: width 0.5s; }
.meter-fill.ok { background: #29a944; }
.meter-fill.warn { background: #e6a817; }
.meter-fill.danger { background: #dc3545; }
.meter-value { width: 42px; text-align: right; font-size: 13px; font-weight: 600; }
.row-footer { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; font-size: 11px; color: rgba(255,255,255,0.5); }
.sep { display: inline-block; width: 3px; height: 3px; border-radius: 50%; background: rgba(255,255,255,0.2); }
```

### 渲染函数
```js
function renderRow(n) {
  const cpu = n.cpu_usage || 0, mem = n.memory_usage || 0, disk = n.disk_usage || 0;
  const trafficUsed = (n.network_total_transmitted||0) + (n.network_total_received||0);
  const trafficLimit = n.traffic_limit || 0;
  const trafficPct = trafficLimit > 0 ? (trafficUsed / trafficLimit) * 100 : 0;
  const expiredAt = n.expired_at;
  const daysLeft = expiredAt ? Math.max(0, (new Date(expiredAt).getTime() - Date.now()) / 86400000) : null;
  // ...render template with status, osIcon, flag, meters, footer
}
```

### 对比

| 维度 | v1（9列） | v2（perf+bill） | v3 ✅（2列卡片） |
|------|-----------|----------------|----------------|
| 容器 | flex column | flex column | **grid 1fr 1fr** |
| 行内容 | 水平9列 | 2列 flex | flex column（紧凑卡片） |
| 列宽 | ~94px | ~443px | **整张 554px** |
| 国旗 | ❌ | 🇯🇵 22×16 | 🇯🇵 22×16 |
| 价格 | 白字 | green badge | green badge |
| footer分隔 | 无 | 无 | 圆点 · 分隔 |
| hover | -6px scale(1.02) | -6px scale(1.02) | **-6px scale(1.02)（与卡片一致）** |
| CSS 行数 | ~117行 | ~56行 | ~53行 |
