# 壁纸驱动配色方法论

> 壁纸不变，主题颜色去匹配壁纸，不是换壁纸迁就主题。

## 核心理念

当用户有一张喜欢的壁纸（图片/视频），页面主题色应从壁纸中提取，而不是用固定色板。这样壁纸和 UI 才是一体的。

## 提取流程

### 1. 视觉分析壁纸色彩分区

用 vision_analyze 描述壁纸内容 + 颜色分布。至少识别出：

| 分区 | 示例 | 通常映射到 |
|------|------|-----------|
| ☁️ 天空/背景主导色 | 深蓝、浅蓝、灰 | `--bg` 系列变量 |
| 🌿 地面/次要大面积色 | 绿、棕 | `--accent` |
| 🎨 点缀色/小面积高饱和 | 黄、橙、紫 | `--accent-2` |
| ☀️ 高光/暖色点缀 | 金黄、奶油 | `--accent-orange` |

### 2. 量化验证（可选）

用 Python 从壁纸文件提取 top N 色值：

```python
from PIL import Image
import collections
img = Image.open('wallpaper.png').convert('RGB')
small = img.resize((200, 113))
pixels = list(small.getdata())
quantized = [(r//32*32, g//32*32, b//32*32) for r,g,b in pixels]
counter = collections.Counter(quantized)
for (r,g,b), count in counter.most_common(20):
    print(f'#{r:02x}{g:02x}{b:02x}')
```

### 3. 色值映射策略

| 壁纸颜色 | 页面角色 | 变暗/变亮规则 |
|----------|---------|-------------|
| 天空蓝 `#3a6ea5` | `--bg-surface` | 加深 60-70% 用于深色主题；直接用亮度用于浅色 |
| 草地绿 `#4a7c59` | `--accent` | 稍微提亮 + 提高饱和度（变成发光 accent） |
| 巴士黄 `#d4a843` | `--accent-2` | 保持原色或略提高饱和度 |
| 暖色点缀 | `--accent-orange` | 保持原色 |

### 4. 应用注意事项

- **CSS 变量只需改一处**，但 `--accent-gradient` 和 `--chart-mem` 是硬编码色值，必须额外处理
- **rgba 变体**（阴影、边框、背景、hover 效果）必须全局替换 RGB 值
  - `rgba(旧R,旧G,旧B,` → `rgba(新R,新G,新B,`
  - 不需要改透明度系数，只改 RGB
- **JS 图表色**：`drawLineChart`、`drawNetChart` 中的硬编码 hex 也需要替换
- **替换后验证**：`node --check /tmp/script.js` 确保无语法错误

## 实际案例：GalaxyGlass + 动漫巴士壁纸

壁纸内容：动漫风女孩 + VW 巴士 + 蓝天 + 草地 + 橙色云朵

### 提取结果

| 壁纸元素 | 原色 | 深色主题映射 |
|----------|------|-------------|
| 天空 | `#3a6ea5` | `--bg-surface: #12284a`（暗化 60%） |
| 草地 | `#34c759`→`#10b981`→`#2d9e6b` | `--accent: #2d9e6b`（自然绿） |
| 巴士 | `#e6c870`→`#c9a94e` | `--accent-2: #c9a94e`（暖黄） |
| 暖色云 | `#f59e0b`（保留） | `--accent-orange: #f59e0b` |

### 背景色关键原则

- **不要用跟壁纸无关的深色** — `#0e152e`（纯深蓝黑）在明亮蓝天壁纸下显得突兀
- **背景应从壁纸天空色暗化** — `#12284a`（天空蓝的深色版）让壁纸和背景属于同一色调
- **不同深度层级**：`--bg-deepest` < `--bg-deep` < `--bg-surface` 逐步提亮，形成从壁纸天空渐变过渡到 UI 背景的效果

### 踩坑

- 壁纸为 **RGBA PNG** 时，透明区域透出页面 `--bg-deep` 色。透明区域大时背景色的影响范围也大
- vision_analyze 给出的色值不够精确，最好用 PIL 或 ffmpeg 精确提取，或凭视觉经验逼近
- 用户对突兀的反馈很敏感（"不觉得很突兀吗"），背景色是第一个要检查的
