# 导航栏：登录 → 在线人数胶囊替换

## 背景

2026-05-16 用户要求移除导航栏右上角的登录按钮，替换为"在线 1 人"绿色胶囊，同时删除 Live badge。

## 改动清单

### index.html

1. **登录按钮**（`#login-btn`）→ 删除，替换为在线胶囊：
```html
<!-- 旧：a.sort-btn → 删除 -->
<a class="sort-btn" id="login-btn" href="/admin">...</a>

<!-- 新：span.online-pill -->
<span class="sort-btn online-pill">
  <svg viewBox="0 0 24 24" fill="currentColor" width="13" height="13">
    <path fill-rule="evenodd" d="M12 2.25c-5.385 0-9.75 4.365-9.75 9.75s4.365 9.75 9.75 9.75 9.75-4.365 9.75-9.75S17.385 2.25 12 2.25Zm-2.625 6c-.54 0-.828.419-.936.634a1.96 1.96 0 0 0-.189.866c0 .298.059.605.189.866.108.215.395.634.936.634.54 0 .828-.419.936-.634.13-.26.189-.568.189-.866 0-.298-.059-.605-.189-.866-.108-.215-.395-.634-.936-.634Zm4.314 0c-.54 0-.828.419-.936.634a1.96 1.96 0 0 0-.189.866c0 .298.059.605.189.866.108.215.395.634.936.634.54 0 .828-.419.936-.634.13-.26.189-.568.189-.866 0-.298-.059-.605-.189-.866-.108-.215-.395-.634-.936-.634ZM12 13.5a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z" clip-rule="evenodd"/>
  </svg>
  在线 1 人
</span>
```

2. **Live badge**（`.live-badge`）→ 整行删除

### CSS (`components.css`)

```css
/* 新增 */
.online-pill { color: var(--accent); border-color: rgba(16,185,129,0.25); background: rgba(16,185,129,0.08); gap: 5px; }
.online-pill svg { color: var(--accent); width: 13px; height: 13px; flex-shrink: 0; }
```

### JS

删除 `updateLiveBadge()` 函数定义（render.js）和 `updateLiveBadge()` 调用（events.js）。

### 清扫验证

```bash
grep -r 'live-badge\|live-dot\|live-pulse\|login-btn\|updateLiveBadge' src/
# 应返回空
```

## 设计说明

- 使用 Heroicons Solid 的人形图标（`fill="currentColor"`）
- 绿色调（`var(--accent)` = `#10b981`），半透明绿色背景
- 目前静态显示"在线 1 人"（个人面板，仅 admin 使用）

## ⚠️ 后续变更：中性风格统一 (2026-05-16 同一 session)

用户随后要求在线胶囊与排序按钮**样式统一**（"看你你觉得绿色好就绿色白色好就白色"）。最终决定：在线胶囊**继承 `.sort-btn` 全部样式**（中性灰色、毛玻璃底），不保留绿色 override。改动：

```diff
- .online-pill { color: var(--accent); border-color: rgba(16,185,129,0.25); background: rgba(16,185,129,0.08); gap: 5px; }
+ .online-pill { gap: 5px; }  /* 继承 sort-btn 的 text-secondary 颜色和 glass-bg 背景 */
```

**理由：** 导航栏三个元素（搜索、排序、在线）用同一视觉层级，绿色 accent 留给统计卡片和 hover 状态等强调位置。
