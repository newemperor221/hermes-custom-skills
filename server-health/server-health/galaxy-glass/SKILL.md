---
name: flag-emoji-mapping
description: 国旗emoji → flagcdn.com SVG代码的映射表。
---

# flagEmoji 映射表（静态版）

定义在 `index.html` 的 JS 块中，约第 617 行：

```javascript
function flagEmoji(r) {
  var m = {
    '🇺🇸': 'us', '🇯🇵': 'jp', '🇭🇰': 'hk', '🇳🇱': 'nl',
    '🇰🇵': 'kp', '🇩🇪': 'de', '🇸🇬': 'sg', '🇬🇧': 'gb',
    '🇰🇷': 'kr', '🇹🇼': 'tw', '🇨🇳': 'cn', '🇷🇺': 'ru',
    '🇨🇦': 'ca', '🇦🇺': 'au'
  };
  return m[r] || '';
}
```

对应 flagcdn.com 代码：`https://flagcdn.com/{code}.svg`

## 当前线上节点覆盖的地区

（截至 2026-05-19，共 6 个活跃地区）

| 标识 | flagcdn 代码 | 显示文本 | 节点数 |
|------|-------------|---------|--------|
| 🇺🇸 | us | US | 7 |
| 🇯🇵 | jp | JP | 2 |
| 🇭🇰 | hk | HK | 2 |
| 🇳🇱 | nl | NL | 1 |
| 🇹🇼 | tw | TW | 1 |
| 🇰🇵 | kp | KP | 1 |

## 添加新地区步骤

1. 在 `flagEmoji()` 对象中添加映射：`'新emoji': 'flagcdn-code'`
2. 确认 `flagcdn.com/{code}.svg` 存在（如 `flagcdn.com/tw.svg`）
3. 无需修改其他代码——`buildRegionFilters()` 函数在渲染时动态读取节点数据中的 `region` 字段生成筛选按钮
