---
name: galaxy-glass-table-redesign
description: GalaxyGlass 表格视图三阶段演变 — v1 单行9列 → v2 每行2列(perf+bill) → v3 #table-body 2列网格紧凑卡片(当前)
---

# GalaxyGlass 表格视图重设计（2026-05-10）

> **版本演变**：v1 → 9列固定宽度（用户：太细了）→ v2 每行2列(perf+bill)（用户：还不错）→ **v3 ✅ 当前：`#table-body` 2列网格，紧凑卡片**

## 当前布局（v3 — 2列表格网格，紧凑卡片）

```
┌───────────────────────────────────────┐  ┌───────────────────────────────────────┐
│ 🟢 🐧 Acck | 东京 🇯🇵                 │  │ 🟢 🐧 Acck | 香港 🇭🇰                 │
│ CPU █████████████████████░  5.0%     │  │ CPU ██████████████████░░░░  3.9%       │
│ 内存 ████████████████████████████░ 25.5%│  │ 内存 ████████████████████████░░ 49.2% │
│ 磁盘 ████████████████████░░░░░░  17.1% │  │ 磁盘 ███████████████████░░░░░░  20.1% │
│ ↓5.3K/s · ↑0B/s · 15天 · ¥148/年 · 70G/500G · 285天 │  │ ↓... · ↑... · ...             │
└───────────────────────────────────────┘  └───────────────────────────────────────┘
                  554px                                    554px
```

**结构**：`#table-body { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }`
每行 554px（1124px容器/2 - gap）。

**每行内部**（flex column）：
```
.table-row (flex column, gap 6px, padding 12px 14px)
  ├── .row-title: 🟢 🐧 名称 🇯🇵（flex row, gap 6px）
  ├── .row-meters: 3个 .meter-row（CPU / 内存 / 磁盘）
  │     └── .meter-label(24px) + .meter-bar(flex:1) + .meter-value(36px)
  └── .row-footer: ↓speed · ↑speed · uptime · price · traffic · days
        （flex wrap, gap 6px, 圆点分隔 .sep）
```

## CSS

```css
#table-body { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }

.table-row {
  display: flex; flex-direction: column;
  padding: 12px 14px; border-radius: 14px;
  background: rgba(0,0,0,0.22); backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.08); gap: 6px;
  cursor: pointer; transition: all 0.3s;
}
.table-row:hover { transform: translateY(-6px) scale(1.02); box-shadow: 0 20px 40px rgba(0,0,0,0.3); border-color: rgba(255,255,255,0.15); }

/* Title */
.row-title { display: flex; align-items: center; gap: 6px; }
.row-title .node-status { width: 7px; height: 7px; flex-shrink: 0; }
.row-title .node-os-icon { width: 16px; height: 16px; border-radius: 2px; flex-shrink: 0; }
.name-text { font-size: 13px; font-weight: 600; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; }
.table-flag { width: 22px; height: 16px; object-fit: cover; border-radius: 2px; flex-shrink: 0; }

/* Meters */
.row-meters { display: flex; flex-direction: column; gap: 3px; }
.meter-row { display: flex; align-items: center; gap: 6px; }
.meter-label { font-size: 10px; font-weight: 600; width: 24px; color: rgba(255,255,255,0.45); flex-shrink: 0; text-align: right; }
.meter-bar { flex: 1; height: 4px; background: rgba(255,255,255,0.08); border-radius: 9999px; overflow: hidden; }
.meter-fill { height: 100%; border-radius: 9999px; transition: width 0.3s; }
.meter-fill.ok { background: #10b981; }
.meter-fill.warn { background: #f59e0b; }
.meter-fill.danger { background: #ef4444; }
.meter-value { font-size: 12px; font-weight: 600; font-family: var(--font-mono); color: #fff; width: 36px; text-align: right; flex-shrink: 0; }

/* Footer */
.row-footer {
  display: flex; align-items: center; gap: 6px;
  font-size: 11px; font-family: var(--font-mono); color: rgba(255,255,255,0.35);
  flex-wrap: wrap; padding-top: 6px;
  border-top: 1px solid rgba(255,255,255,0.06);
}
.row-footer .sep { width: 2px; height: 2px; border-radius: 50%; background: rgba(255,255,255,0.15); flex-shrink: 0; }
.footer-price { font-weight: 600; color: #10b981; background: rgba(16,185,129,0.1); padding: 0 6px; border-radius: 9999px; font-size: 11px; }
```

## JS（renderRow 函数，v3 简化版）

```javascript
function renderRow(n) {
  const cpu = n.cpu_usage || 0, mem = n.memory_usage || 0, disk = n.disk_usage || 0;
  // ... 颜色计算（cpuClass, memClass, diskClass, trafficClass, daysClass）
  const osIcon = getOSIcon(n.os);
  const priceStr = n.price ? `${n.currency||'¥'}${n.price}/${周期}` : '-';
  const trafficStr = n.traffic_limit ? `${bytes(used)}/${bytes(limit)}` : bytes(used);
  const daysStr = expiredAt ? r.toFixed(0)+'天' : '-';
  return `
    <div class="table-row${n.online ? '' : ' offline'}" data-uuid="${n.uuid}">
      <div class="row-title">
        <span class="node-status ${n.online ? 'online' : 'offline'}"></span>
        ${osIcon ? `<img src="${osIcon}" class="node-os-icon">` : ''}
        <span class="name-text">${n.name || n.uuid}</span>
        ${n.region ? `<img src="https://flagcdn.com/${flagEmoji(n.region)}.svg" class="table-flag">` : ''}
      </div>
      <div class="row-meters">
        <div class="meter-row">CPU 行...</div>
        <div class="meter-row">内存行...</div>
        <div class="meter-row">磁盘行...</div>
      </div>
      <div class="row-footer">
        <span>↓ ${bytes(n.network_in||0)}/s</span>
        <span class="sep"></span>
        <span>↑ ${bytes(n.network_out||0)}/s</span>
        <span class="sep"></span>
        <span>${uptime(n.uptime||0)}</span>
        <span class="sep"></span>
        <span class="footer-price">${priceStr}</span>
        <span class="sep"></span>
        <span class="${trafficClass}">${trafficStr}</span>
        <span class="sep"></span>
        <span class="${daysClass}">${daysStr}</span>
      </div>
    </div>
  `;
}
```

## 三版本对比

| 维度 | v1（起始） | v2（6月10日午） | v3 ✅（6月10日晚，当前） |
|------|-----------|----------------|------------------------|
| 表格容器 | flex column | flex column | **grid 1fr 1fr** |
| 内部列数 | `repeat(10, 1fr)` | 2列 `1fr 1fr` | **flex column（紧凑卡片）** |
| 列宽 | ~106px | ~443px | 整张卡 **554px** |
| 行布局 | 水平9列 | col-perf + col-bill | **title + meters + footer**（垂直） |
| 用户评价 | "太细了" | "还不错" | ✅ |
| 国旗 | 无 | 🇯🇵 22×16 | 🇯🇵 22×16 |
| 价格 | 白字 | 绿色 badge | 绿色 badge |
| footer分隔 | 无 | 无 | **圆点 ·** 分隔 |
| CSS 行数 | ~117行 | ~56行 | **~53行** |

## JS 调试：`const` 重复声明导致整段脚本不执行

GalaxyGlass 的所有 JS 逻辑都在 index.html 的一个 `<script>` 标签内（内联 ~48KB）。如果 JS 里有语法错误（如同一函数内 `const` 声明两次同名变量），**整个脚本不会执行**，`init()` 不被定义，页面永远显示"连接后端中…"。

**症状：**
- 页面空白，显示 loading spinner + "连接后端中…"
- `typeof init === 'undefined'`
- API 全部正常（`curl http://127.0.0.1:25774/api/nodes` 返回 200）
- 浏览器无可见错误（无 404，无 CORS 错误）
- 实际上是 JS 解析错误，在浏览器 console 里显示为无名 exception

**排查方法：**
```bash
# 把服务器的 index.html 拉到本地
scp root@server:/data/theme/GalaxyGlass/dist/index.html /tmp/check.html

# 用 Node.js 检查内联脚本语法
node -e "
const fs = require('fs');
const html = fs.readFileSync('/tmp/check.html', 'utf8');
const match = html.match(/<script>([\s\S]*?)<\/script>/);
if (match) {
  const js = match[1];
  try {
    new Function(js);
    console.log('SYNTAX OK');
  } catch(e) {
    console.log('SYNTAX ERROR:', e.message);
  }
}
"
```

**历史案例（2026-05-10）**：`renderDetailSysinfo` 函数内 `trafficLimit` 用 `const` 声明了两次（L1944 和 L1999），导致整段内联脚本解析失败。修复：删掉 L1999 的 `const`（已有同名变量）。

## Deployment 路径坑

**问题：** komari 读主题文件不是从 `/data/theme/`，而是从 `/root/data/theme/`。

**原因：**
- komari 二进制硬编码了 `./data/theme/`、`./data/secret.key` 等相对路径
- `supervise-daemon` 启动 komari 时没有设 `--chdir`，进程 cwd 是 `/root/`
- 所以 `./data/theme/` → `/root/data/theme/`

**修复：** `ln -s /root/data/theme /data/theme`（两个路径一致）

**部署确认方法：** 登录服务器后 `wc -c` 对比本地文件大小：
```bash
# 服务器上
wc -c /root/data/theme/GalaxyGlass/dist/index.html   # komari 实际读的
wc -c /data/theme/GalaxyGlass/dist/index.html          # 软链指向同一个
curl -s http://127.0.0.1:25774/ | wc -c               # komari 返回的
```
如果 `curl` 结果跟文件大小不一致 → komari 读的不是你改的文件。

## 关键坑

1. **`.table-view` 不要写 padding** — 外层 `.container` 已有 `padding: 0 1.5rem`
2. **meter-bar 不要 max-width**（v2 的 80px 限制不宜在 v3 紧凑卡片中使用）→ 让进度条填满整行
3. **row-footer 用 `.sep` 圆点分隔**（2×2px 圆形），不用文字分隔符
4. **hover 效果**：必须与 `.node-card:hover` 完全一致（`translateY(-6px) scale(1.02)` + `box-shadow: 0 20px 40px rgba(0,0,0,0.3)`）。用户明确纠正过差异。**⚠️ 不要用更轻微的 hover**（之前用过 -3px 不缩放但用户要求统一）。
5. **13 个节点**在 2 列网格中排列为 7 行（6+6+1），最后一行单卡
