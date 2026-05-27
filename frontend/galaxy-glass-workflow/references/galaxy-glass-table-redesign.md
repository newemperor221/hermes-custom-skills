# GalaxyGlass 表格视图重设计（历史记录）

> **版本演变**：v1 → 9列固定宽度（用户：太细了）→ v2 每行2列(perf+bill)（用户：还不错）→ **v3 ✅ 当前：`#table-body` 2列网格，紧凑卡片**

## 当前布局（v3 — 2列表格网格，紧凑卡片）

略。当前线上为卡片视图（node-card grid），表格视图已弃用。

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