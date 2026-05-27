# 表格视图删除决策（v2.2.0）

## 结论

删除了表格视图（`.table-view`、`renderRow()`、`view-toggle` 切换、`localStorage.viewMode`）。
导航栏不再有卡片/表格切换按钮。

## 原因

卡片（v2.1 瘦身后）和表格行信息趋同——都显示状态点+OS图标+名称+国旗+3条进度条+网络速率+uptime+价格。
卡片去掉硬件摘要行和底部流量后，表格唯一的"紧凑"优势就不存在了。两者还共用相同的 hover 效果、玻璃背景、入场动画。

## 删除内容

- `viewMode` / `localStorage.nodeViewMode` — 全部移除
- `.view-toggle`、`.view-toggle-slider`、`.view-toggle-btn`、`#view-cards`、`#view-table`
- `.table-view-wrap`、`#table-view`、`#table-body`
- `.table-row`、`.row-title`、`.row-meters`、`.row-title`、`.row-footer`
- `.meter-row`、`.meter-label`、`.meter-bar`、`.meter-fill`、`.meter-value`
- `renderRow()` 函数
- `updateViewToggle()` 函数
- `viewMode` 条件分支在 `render()`、`positionBackToTop()`、`setupEvents()` 中

## 导航栏变化

```
之前: GG探针 ── 🔍 ── [卡片|表格] [排序 ▾]
之后: GG探针 ── 🔍 ──── [排序 ▾]
```
