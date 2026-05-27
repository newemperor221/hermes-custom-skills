# 详情页重设计

> 从 History API SPA 路由到布局迭代的全过程。

## 演进历史

### v1 — 基础抽离
- 从 komari 官方主题 `detail.html` 抽离，首次嵌入 index.html
- 简单导航 + 6 指标卡 + 系统信息 1 列 + 3 Canvas 图表

### v2 — 布局优化
- 系统信息改 2 列网格（`360px width` 容器）
- 添加账单卡片（price · traffic · days）
- 图表加端点圆点 + 当前值标注
- Metrics 值 14px → 22px，加绝对值副标题

### v3 — 溢出修复 + 账单入 grid
- 修复 CSS Grid 文字/ badge 溢出（需 `min-width: 0; overflow: hidden;`）
- 账单从 grid 外移入内部作为第三行（`grid-column: 1 / -1`），铺满底部消除左列空区域

### v4 — 新增标签卡
- sysinfo-card 下方新增 tags-card
- 显示节点标签 chips（4 色循环）+ TCP/UDP 连接数
- 无内容时自动隐藏不占位

### v5 — 流量卡 + 语义分组

（内容同上）

### v6 — Metrics 卡重排序 + 合并（当前）

- 用户要求"把在线时长放在上行前面，让上行和下行处于一行"
- 改动：
  1. **上移"在线时长"**：从第 6 位提前到第 4 位（CPU→内存→磁盘→**在线时长**）
  2. **合并上行+下行**：两张卡合并为一张"网络速率"卡，显示 `↑ xxx/s  ↓ xxx/s` 在一个值字符串中
  3. **补位"流量用量"**：合并后 6 卡变 5 卡，3×2 网格会空一格。必须补一张新卡（流量用量：`已用 xxx / yyy`）填回，维持视觉整齐
- **教训**：合并 metric 卡时必须补位，用户明确说"你合并两个，那还空一个"
- 新增第三张左列卡 `#detail-traffic`（流量统计）：
  - 累计上传/下载总量 + 流量使用进度条（颜色分级：<60% 绿，60-80% 黄，>80% 红）
  - 使用 `latest.network.totalUp/Down` 计算流量（`node.network_total_*` 在详情页上下文不存在，会导致显示 0）
- sysinfo 行改为**显式语义分组**（不用 `slice(mid)` 机械切分）：
  - 左列硬件（CPU型号/核心数/架构/Virt/OS/GPU/内存/Swap/磁盘）
  - 右列运行时（流量限额/进程/TCP/更新/在线/负载/到期）
- 左列高度平衡策略：3 张卡（sysinfo + tags + traffic）填满约 622px，与右侧 3 个图表卡（~739px）差距 ~117px

## CSS 溢出修复细节

**问题**：`grid-template-columns: 1fr 1fr` 在 324px 内容区（360px card - 36px padding）中，每列 154px。但：
- 超长 CPU 型号无视列宽溢出
- 负载均值 3 个 flex badge 合计 > 154px
- `.val` 的 `max-width: 60%` 不够用

**修复**：
```css
/* 父容器 */
.sysinfo-grid { min-width: 0; }
.sysinfo-grid > div { min-width: 0; overflow: hidden; }

/* 值容器 */
.sysinfo-row .val { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* badge 组 */
.sysinfo-row .load-badge { font-size: 9px; padding: 1px 6px; }
.load-row { flex-wrap: wrap; gap: 4px; min-width: 0; }
```

## 标签卡数据流

```
komari SQLite (clients.tags)
  → /api/nodes → node.tags (逗号分隔字符串, 如 "副力,东京,9929")
  → JS 拆分: String(node.tags).split(',').filter(t => t.trim())
  → 4 色循环: .tag-chip(''), -alt, -warm, (repeat)

TCP/UDP 连接:
  → /api/recent/{uuid} → latest.connections.tcp / .udp
  → 无连接数据时不显示 conn-row
```
