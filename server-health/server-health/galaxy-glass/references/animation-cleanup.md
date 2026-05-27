# GalaxyGlass 动画清理（2026-05-13）

## 背景

用户主动要求审查主题的「不必要的动画」。逐一分析了 CSS 中的所有 transition/animation/@keyframes。

## 已移除的动画

### 1. 在线绿点脉冲动画

```css
/* 已删除 */
.node-status.online { animation: pulse-dot 2.5s ease-in-out infinite; }
@keyframes pulse-dot { 0%,100% { opacity:1; box-shadow:0 0 6px rgba(45,158,107,0.5); } 50% { opacity:0.6; box-shadow:0 0 3px rgba(45,158,107,0.15); } }
```

**理由**：10+ 个节点同时呼吸闪烁 = 视觉噪音。绿色已经表示在线。改为静态阴影 `box-shadow: 0 0 4px rgba(45,158,107,0.3)`。

### 2. 骨架屏 shimmer

```css
/* 已删除 */
.skeleton-line { animation: shimmer 1.5s ease-in-out infinite; background: linear-gradient(90deg, ...); background-size: 200% 100%; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
```

**理由**：数据加载通常在 0.5-1s 完成，shimmer 1.5s 循环跑不完就被替换掉了。改为静态底色 `background: rgba(255,255,255,0.05)`。

### 3. 卡片 hover scale

```css
/* 已删除 scale 部分，保留 translateY */
/* 旧 */ transform: translateY(-3px) scale(1.012);
/* 新 */ transform: translateY(-3px);
```

**理由**：1.2% 缩放肉眼不可见。`translateY(-3px)` 才是有效的 hover 反馈。

## 已加速的过渡

### 搜索框展开/收回

```css
/* 旧 */ transition: max-width 0.5s cubic-bezier(0.25, 0.46, 0.45, 0.94), ...;
/* 新 */ transition: max-width 0.25s cubic-bezier(0.25, 0.46, 0.45, 0.94), ...;
```

**理由**：一个简单的展开/收回搞半秒太拖沓。0.25s 足矣。

## 新增的 backdrop-filter 平滑修复

### 导航栏 scroll-up 闪白

```css
/* 旧：无 backdrop-filter 基础值 */
.navbar { background: transparent; transition: backdrop-filter 0.35s; }

/* 新：blur(0px) 提供过渡起点 */
.navbar { background: transparent; backdrop-filter: blur(0px); transition: backdrop-filter 0.35s; }
```

**理由**：`none` → `blur(24px)` 在不同浏览器上插值行为不一致，取消 `.scrolled` 时闪白。`blur(0px)` → `blur(24px)` 有明确定义的插值路径。

**同样修复**：`.detail-nav` 也加了 `backdrop-filter: blur(0px)` 基础值。

## 保留的动画

| 动画 | 类型 | 保留理由 |
|------|------|---------|
| 卡片入场 cascade | `@keyframes cardIn` | 错峰入场增强层次感 |
| 进度条填充 | `transition: transform 0.4s` | 数据加载反馈 |
| 滚动变毛玻璃 | `transition` | 滚动状态指示 |
| 下拉菜单出现 | `@keyframes fadeIn` | 交互反馈 |
| 卡片 hover 上移 | `transition: transform` | 有效的交互反馈 |
| 颜色过渡 | `transition: color/background` | 交互反馈 |

## 用户偏好

- 对 `infinite` 循环动画容忍度极低——尤其是多个元素同时循环（如 10+ 绿点脉冲）
- 交互反馈动画（hover、点击、展开）可以保留但时长不宜超过 0.3s
- 装饰性动画必须有明确视觉价值，否则删
