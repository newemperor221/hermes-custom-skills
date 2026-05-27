# 布局呼吸感全局调整 (2026-05-16)

## 触发

用户看了全局布局后说"按你的想法做"，我做了一套系统性间距调整。

## 修改清单

| 区域 | 文件 | 改前 | 改后 |
|------|------|------|------|
| 节点卡片 padding | components.css | 14px 16px | 16px 18px |
| 节点卡片 gap | components.css | 10px | 12px |
| 指标行 gap (card-metrics) | components.css | var(--space-1)=4px | var(--space-2)=8px |
| 标签区 margin-top | components.css | 6px | 8px |
| 标签区 margin-bottom | components.css | 4px | 6px |
| 底部分割线 padding-top | components.css | 7px | 8px |
| 顶部 stat 卡片 padding | components.css | 14px | 16px |
| 导航栏 height | layout.css | 48px | 44px |
| 导航栏 padding | layout.css | 0.65rem | 0.5rem |
| 右侧组件 gap | layout.css | 0.35rem | 0.65rem |

## 间距语义层级

- **4px (--space-1)**：同一行内的元素间距（↑↔数值、箭头↔值）
- **8px (--space-2)**：不同指标行间隙（CPU↔MEM↔DSK）
- **12px (--space-3)**：卡片内不同段落（header↔tags↔metrics↔footer）
- **16px (--space-4)**：卡片边缘 padding、grid gap
- **24px (--space-5)**：页面区域间距（navbar↔内容区）

## 导航栏右侧组件间距

从 0.35rem（~5.6px）改为 0.65rem（~10.4px）。用户反馈 0.35rem 时三个组件（搜索框、排序按钮、在线人数）太挤，"单调"。
