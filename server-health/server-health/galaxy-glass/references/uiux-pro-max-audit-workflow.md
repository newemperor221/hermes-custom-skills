# UI/UX Pro Max 设计审查工作流

## 概述

使用 UI/UX Pro Max skill（161 条行业规则 / 67 种 UI 风格 / 161 配色方案）对 GalaxyGlass 主题进行系统化设计审查。

## 审查流程

### 1. 加载技能

当用户要求审查/改进 GalaxyGlass 主题的 UI/UX 时，先加载 `ui-ux-pro-max` 技能。

### 2. 多维度搜索查询

```bash
SKILL_DIR="/home/woioeow/.hermes/skills/creative/ui-ux-pro-max"

# 产品类型匹配 — 确定目标受众推荐的设计方向
python3 "$SKILL_DIR/scripts/search.py" "monitoring dashboard" --domain product -n 5

# 风格匹配 — 评估当前风格 vs 推荐风格
python3 "$SKILL_DIR/scripts/search.py" "dark glass monitoring" --domain style -n 5

# UX 准则 — 检查常见 UX 问题
python3 "$SKILL_DIR/scripts/search.py" "dashboard monitoring data visualization" --domain ux -n 5

# 配色方案 — 验证颜色体系
python3 "$SKILL_DIR/scripts/search.py" "dark dashboard monitoring" --domain color -n 3

# 图表推荐 — 检查图表实现
python3 "$SKILL_DIR/scripts/search.py" "real-time monitoring charts" --domain chart -n 3

# 字体搭配 — 检查排版
python3 "$SKILL_DIR/scripts/search.py" "dashboard monospace data" --domain typography -n 3
```

### 3. 对比分析维度

| 维度 | 搜索域 | 审查目标 |
|------|--------|---------|
| 风格匹配度 | product + style | 当前风格是否匹配行业推荐 |
| 配色合规 | color | 主色/accent/状态色是否合理 |
| 字体架构 | typography | 数据/标签字体是否规范 |
| 动画交互 | ux | 过渡、脉冲、视频播放是否尊重用户偏好 |
| 图表实现 | chart | Canvas/实时数据/无障碍 |
| 无障碍 | ux | 对比度、aria-label、prefers-reduced-motion |

### 4. 优先级分级

| 等级 | 含义 | 行动 |
|------|------|------|
| 🔴 P0 | 可用性问题 / 耗电 / 无障碍违规 | 必须修 |
| 🟡 P1 | 交互细节 / 视觉效果优化 | 建议修 |
| 🟢 P2 | 代码可维护性 / 补充完善 | 可修可不修 |

### 5. 输出格式

审查报告应包括每个发现项的：
- **规则依据** — UI UX Pro Max 的规则编号或引用
- **现状** — GalaxyGlass 当前的实现
- **差距** — 与推荐的偏差
- **修法** — 具体的 CSS/JS 改动

## v2.3.0 审查结果摘要

| 规则 | 发现 | 优先级 | 措施 |
|------|------|--------|------|
| 22(Auto-Play Video) | 视频自动播放耗电 | 🔴 P0 | IntersectionObserver + prefers-reduced-motion |
| WCAG AA 对比度 | muted text 38% 透明度过低 | 🔴 P0 | 提升至 48%，glass-border 6%→10% |
| 实时监控状态指示 | 无在线/离线视觉区分 | 🟡 P1 | 加 status-dot 脉冲指示器 |
| 过渡统一 | 多个不同 easing 混杂 | 🟡 P1 | 定义 --ease-out 统一使用 |
| Canvas 无障碍 | 图表无 aria-label | 🟢 P2 | 加 role="img" + aria-label |
| 设计变量体系 | 缺状态色/脉冲变量 | 🟢 P2 | 补 --online/--offline/--pulse-duration |
