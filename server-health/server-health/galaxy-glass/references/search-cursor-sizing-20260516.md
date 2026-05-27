# 搜索框光标大小调试 (2026-05-16)

## 问题

用户在 GalaxyGlass 面板（stat.357561.xyz）中认为搜索框展开后输入光标（caret）太小。

## 调试过程

| 尝试 | 修改 | 用户反馈 |
|------|------|----------|
| 1 | `caret-color: var(--accent)`（绿色光标） | "闪烁的那个太小了" |
| 2 | `font-size: 13px → 14px` | "没有变化" |
| 3 | 去掉绿色 border/focus/icon，font-size: 15px | "你不觉得这个光标样式有点怪吗" |
| 4 | 加 `caret-color: var(--text-primary)`，字号15px | "光标明显比字小，我要和字体一样大小" |
| 5 | `font-size: 20px; line-height: 34px; height: 34px` | 最终接受（开始时） |

## 结论（历史，不再适用）

**⚠️ 更新（2026-05-16 末）：** 上述 step 5 的 20px 方案已被后续更新覆盖。当前线上运行的是：
- **font-size: 15px; line-height: 20px; height: 20px**
- 这是用户多次确认正确的状态
- **不要再次修改搜索框的 font-size/line-height/height**，即使参考文件写的是 20px

光标在 15px 字号下看起来"够用"了，不需要更大。

## 搜索框样式教训

- 不要用 `caret-color: var(--accent)` 尝试改善（绿色光标在玻璃背景上显眼但用户嫌奇怪）
- 每次修改后告诉用户硬刷新（Ctrl+F5）加载最新 CSS
- 搜索框展开后不要有绿色 focus 效果（border/icon/caret），用户明确拒绝
