# GalaxyGlass 主题布局文档

> 来源：2026-05-04/05 session，GitHub 同步更新（仓库已改名 nodeget-galaxy-glass）

## 文件结构

```
nodeget-komari-theme/
├── LAYOUT.md          # 本文档
└── dist/
    ├── index.html    # 主页（节点列表）
    └── detail.html   # 详情页（单节点图表）
```

## 主页布局（index.html）

### 视觉层级（z-index）

| 层级 | 元素 | 用途 |
|------|------|------|
| -1 | `.bg-layer` | 背景视频/图片，fixed 铺满 |
| 10 | `.page` | 主容器，relative |
| 10 | `.navbar` | 导航栏，sticky top |
| 20 | `.back-to-top` | 回到顶部按钮，fixed |

### 页面结构

```
<body>
├── .bg-layer          # 背景视频/图片（始终 fixed）
│   ├── #poster         # 图片（移动端 fallback）
│   └── #bg-video       # 视频（桌面端）
│
├── .page
│   ├── nav.navbar     # 导航栏 sticky
│   │   ├── .navbar-brand → ./（链接回主页）
│   │   └── .navbar-actions
│   │       ├── #profile-dropdown  # 右上角用户图标下拉菜单
│   │       ├── .search-box        # 搜索框
│   │       ├── .view-toggle       # 卡片/表格切换
│   │       └── #sort-dropdown     # 排序下拉
│   │
│   └── main.container.main
│       ├── .stats-grid           # 4 张统计卡
│       ├── #region-filters       # 区域筛选按钮
│       ├── .nodes-grid           # 卡片网格
│       ├── .table-view          # 表格视图
│       └── .empty               # 空状态
│
├── footer.footer      # 页脚（非 sticky）
└── button.back-to-top  # 回到顶部
```

## detail.html 与 index.html 的差异

| 项目 | index.html | detail.html |
|------|-----------|-------------|
| 导航栏 | `.navbar` + 搜索/视图/排序 | `.detail-nav` + 返回+标题 |
| 节点区域 | 网格/表格列表 | 单节点详情 |
| 统计卡 | 有 | 无 |
| 区域筛选 | 有 | 无 |
| 图表 | 无 | CPU/内存/网络 3个 |
| 概览信息 | 无 | 14 个 info-card |

## CSS 关键约束

```css
.container    { max-width: 1124px; margin: 0 auto; padding: 0 1.5rem; width: 100%; }
.nodes-grid   { min-height: calc(100vh - 380px); align-content: start; }
.node-card    { min-height: 160px; }
.table-view   { max-width: 1124px; margin: 0 auto; padding: 0 1.5rem; width: 100%; }
.table-header, .table-row { grid-template-columns: 48px 1fr 70px 65px 65px 65px 100px 65px 85px 80px; }
```

改导航栏高度后需同步更新 `nodes-grid` 的 min-height 偏移值。

## 统计卡数据来源

| 字段 | 计算方式 |
|------|----------|
| 在线服务器 | `nodesList.filter(n => n.online).length` |
| 流量/速率 | Σ`network_out`，Σ`network_total_received` |
| 剩余价值/总价值 | `Σ price_CNY × 剩余天数/周期天数`，汇率实时获取 |

## API 数据流向

```
/api/public          → fetchSiteInfo() → 站点名称
/api/nodes           → fetchNodes() → 节点静态信息
/api/recent/{uuid}   → fetchRecentData(uuid) → 节点动态数据
↓
mergeNodeData(node, recent) → 合并静态+动态 → nodesList[]
↓
getFiltered() → renderCard() / renderRow()
```

## 表格列（10列）

`48px 1fr 70px 65px 65px 65px 100px 65px 85px 80px`
= 状态 / 名称 / 系统 / CPU% / 内存% / 磁盘% / 流量% / 下载% / 价格 / 到期

## 部署路径

| 位置 | 路径 |
|------|------|
| 服务器 | `root@<洛杉矶2_IP>:/opt/komari/data/theme/GalaxyGlass/dist/` |
| GitHub | `https://github.com/newemperor221/nodeget-galaxy-glass` |
| 访问地址 | `http://<监控面板域名>` |
