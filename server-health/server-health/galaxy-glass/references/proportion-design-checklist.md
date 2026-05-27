# 比例核查清单

当在 GalaxyGlass 中新增或调整 UI 元素时，在确定尺寸前执行以下检查，避免用户反馈「太大了」「不合尺寸」「随意弄的」。

## 第一步：找参考系

修改哪个元素，就先找出页面上和它**同层级或兄弟级**的元素，记录它们的尺寸作为基准。

| 参考元素 | 高度/尺寸 | 出现场景 |
|---------|----------|---------|
| card-metric 行 | 20px | 卡片内每行指标 |
| cm-label 文字 | 11px font | 卡片指标标签 |
| cm-value 文字 | 12px font | 卡片指标数值 |
| card-metric gap | 3px | 卡片内行间距 |
| progress bar | 6px | 卡片进度条 |
| node-name | 14px font | 卡片标题 |
| stat-card padding | 14px 16px | 顶部统计卡 |
| 进度条值文字（高饱和度） | 12px | 卡片指标数值 |

## 第二步：问三个问题

1. **新元素应该比参考元素大还是小？** — 如果是次要交互（筛选、排序、标签），通常 ≤ 周边主要内容元素（card-metric 的 20px）
2. **圆角匹配哪个层级？** — 容器用 `--radius-md`(12px) 或自定义 14px，别直接上 `--radius-full`(9999px) 除非设计就是药丸
3. **字体应该排在第几级？** — 按之前确定的字号层级（11px label、12px value、13px chip、14px name）

## 第三步：在浏览器 console 验证

```js
// 测量目标元素和目标对比元素
var el = document.querySelector('.your-new-element');
var ref = document.querySelector('.node-card .card-metric'); // 或其他对比基准
if (el && ref) {
  console.table({
    target: { height: el.getBoundingClientRect().height, font: getComputedStyle(el).fontSize },
    reference: { height: ref.getBoundingClientRect().height, font: getComputedStyle(ref).fontSize },
    ratio: (el.getBoundingClientRect().height / ref.getBoundingClientRect().height).toFixed(2)
  });
}
```

## 第四步：头脑中渲染「缩小版」

问自己：如果我把这个元素缩小 20-30%，它还能正常工作吗？如果答案是「可以」，说明当前尺寸大了。

## 历史教训

- 2026-05-14 筛选 chip 首次实施：33px 容器 + 13px font + full-pill 圆角 → 用户反馈「太大了」。修正到 26px + 12px font + 14px 圆角后通过。
- 修正思路：对比卡片 metric row 的 20px，意识到筛选栏应该是 <30px 的细元素，不是独立的交互块。
