# 回到顶部按钮定位 — 迭代记录

> 2026-05-10 会话，持续约 1 小时，经 8+ 次修正后定案。
> 2026-05-12: 用户尝试固定右下角 (bottom:20px; right:20px) 后要求回退到动态方案。
> 2026-05-12（同日）: 最终方案——水平参照网格容器右边缘（gridRect.right），非最后卡片。

## 最终方案（2026-05-12 定案）

```css
.back-to-top {
  position: fixed;
  z-index: 20;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  visibility: hidden;
  transition: opacity 0.3s, visibility 0.3s;  /* 不含位置属性 */
}
```

### 垂直定位

按钮底部与**最后一张节点卡片的底部边缘**对齐。计算基于**绝对页面坐标**：

### 水平定位

按钮右边缘距离视口右边缘 = `(网格容器右边缘到视口右边缘的 gap + 16px) / 3`。

**为何不用最后卡片**：`auto-fill` 网格的最后一行可能不满（如 13 卡 3 列 → 最后行 1 卡）。用最后卡片的 `lastRect.right` 计算会导致按钮跟着偏左。改用 `gridRect.right`（网格容器右边缘）后位置稳定。

```js
function positionBackToTop() {
  var grid = document.getElementById('grid-view');
  var btn = document.getElementById('back-to-top');
  if (!grid || !btn || grid.classList.contains('hidden')) return;
  var cards = grid.querySelectorAll('.node-card');
  if (cards.length === 0) return;
  var last = cards[cards.length - 1];
  var lastRect = last.getBoundingClientRect();
  var gridRect = grid.getBoundingClientRect();
  var cardBottomPageY = lastRect.bottom + window.scrollY;
  var distToPageBottom = document.documentElement.scrollHeight - cardBottomPageY;
  btn.style.bottom = Math.max(4, distToPageBottom) + 'px';
  btn.style.top = 'auto';
  // 水平参照网格容器右边缘（防最后行不满偏移）
  btn.style.right = Math.max(4, (window.innerWidth - gridRect.right + 16) / 3) + 'px';
}
```

**触发时机**：仅在 `render()` 末尾（`positionBackToTop()` 调用一次）。不绑定 resize/scroll。

### 迭代过程

1. 最初：`right: 1.5rem`（贴在最右边）
2. → `right: gap + 16px`（贴在卡片右侧，但用户觉得太靠左）
3. → `right: (gap + 16px) / 2`（往右移一半）
4. → **初版最终**: `right: (gap + 16px) / 3`（再往右移三分之一）
5. → **2026-05-12** 改为 `gridRect.right` 而非 `lastRect.right`

## 被否决的方案

| 方案 | 原因 |
|------|------|
| 动态跟随滚动（scroll 监听实时算 bottom） | 位置跳动，体验差 |
| `top: 50%; transform: translateY(-50%)` | 居中于视口，不是卡片区域的右侧中间 |
| `transition: all 0.3s` | bottom 被 JS 改变时产生弹出动画 |
| 基于 getBoundingClientRect().bottom 简单计算 | 只在初始 scroll 位置正确，滚动后偏移 |
| 用 alignBackToTop 函数绑定 resize | 多余事件监听，不需要 |
| **固定 bottom:20px; right:20px**（2026-05-12 尝试） | 用户要求退回动态 — 固定位置不符合其视觉预期 |
| **水平对齐最后卡片（lastRect.right）**（2026-05-12 尝试后修复） | 最后一行不满时按钮偏左 → 改为参照网格容器 gridRect.right |

## 关键教训

1. **`transition: all` 是万恶之源** — 当 JS 动态改变位置属性时会产生弹出动画。必须只保留 `opacity, visibility` 过渡。
2. **`position: fixed` 的定位是一次性设定** — 不要用 scroll 事件实时更新。固定位置意味着选中一个页面 Y 坐标后永久停留。
3. **用户习惯**：用户通过"再往右移一半""再往右移三分之一"这种短指令微调位置，不需要讨论方案。前几次都会偏，需要预留迭代空间。
4. **差值法**：用 `distToPageBottom = scrollHeight - cardBottomPageY` 代替视口相对计算，保证当页面完全滚动时两者的 vertical position 精确匹配。
5. **不要提议改成固定右下角** — 用户试过后主动退回动态方案，这是明确选择，非未尝试的备选。
6. **最后一行不满陷阱**（关键）：`auto-fill` 网格的最后一行卡片数量可能少于列数，用 `lastRect.right` 计算水平位置会导致按钮偏左。必须用网格容器的 `getBoundingClientRect()` 代替。
