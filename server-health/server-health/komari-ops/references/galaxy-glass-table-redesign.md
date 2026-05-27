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

## 三版本对比

| 维度 | v1（起始） | v2（每行2列perf+bill） | v3 ✅（当前，2列网格紧凑卡片） |
|------|-----------|----------------|------------------------|
| 表格容器 | flex column | flex column | **grid 1fr 1fr** |
| 内部列数 | `repeat(10, 1fr)` | 2列 `1fr 1fr` | **flex column（紧凑卡片）** |
| 列宽 | ~106px | ~443px | 整张卡 **554px** |
| 行布局 | 水平9列 | col-perf + col-bill | **title + meters + footer**（垂直） |
| 用户评价 | "太细了" | "还不错" | ✅ 当前 |
| 国旗 | 无 | 🇯🇵 22×16 | 🇯🇵 22×16 |
| 价格 | 白字 | 绿色 badge | 绿色 badge |
| footer分隔 | 无 | 无 | **圆点 ·** 分隔 |
| CSS 行数 | ~117行 | ~56行 | **~53行** |

## 关键坑

1. **列宽不够时用户反馈"太细了"** → 不要强行塞9列或窄列。改用grid 2列紧凑卡片方案。
2. **`.table-view` 不要写 padding** — 外层 `.container` 已有 `padding: 0 1.5rem`
3. **meter-bar 不要 max-width** — 让进度条填满整行
4. **row-footer 用 `.sep` 圆点分隔**（2×2px 圆形），不用文字分隔符
5. **hover 效果**：上移 -3px，不缩放（比 card hover 的 -6px scale(1.02) 更文雅）
6. **13 个节点**在 2 列网格中排列为 7 行（6+6+1），最后一行单卡
7. **`const` 重复声明 = 整段内联 JS 不执行** → 见 `references/const-duplicate-crash.md`
8. **Cloudflare 缓存旧版 HTML** → 部署后可能需加版本标记或强制刷新 cache
9. **部署路径** → scp 到 `/root/data/theme/GalaxyGlass/dist/index.html`（不是 `/data/theme/`，已建软链）
