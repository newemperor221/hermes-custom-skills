# 从部署版 index.html 提取 src/ 源码

当需要将线上单文件 `index.html` 拆回 `src/` 结构时，按以下步骤操作。

## 提取 Python 脚本

```python
import re

with open('index.html') as f:
    html = f.read()

# 提取 CSS
css_m = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
css = css_m.group(1).strip()

# 提取 JS（第一个 <script> 块，排除 Cloudflare 等额外脚本）
js_m = re.search(r'<script>\n(.*?)</script>', html, re.DOTALL)
js = js_m.group(1).strip()

# 提取 HTML body（</style> 和 <script> 之间）
body_m = re.search(r'</style>(.*?)<script>', html, re.DOTALL)
body = body_m.group(1).strip()
body = re.sub(r'</head>\s*<body>', '', body)
```

## CSS 拆分（ITCSS 分层）

按注释头拆分 CSS 到 8 个文件：

| 文件 | ITCSS 层 | 内容 | 分割点 |
|------|----------|------|--------|
| `settings.css` | Settings | CSS 变量（:root） | 只取 `:root { ... }` 块 |
| `base.css` | Generic + Elements | Reset + 裸元素样式 | 从 `* { ... }` 到 `.page` 前 |
| `layout.css` | Objects | 页面骨架类选择器 | `.page`, `#list-view`, `.bg-layer`, `.container` + Navbar/Main/Grid/Footer/Back-to-Top 节 |
| `components.css` | Components | 可复用 UI 组件 | Search/Sort/Stats/Filters/Skeleton/Card/Detail/Toast/Pause/Live 节 |
| `states.css` | — | 状态类 | `/* ── States ── */` 节 |
| `utilities.css` | Utilities | 工具类 + 动画 | `::-webkit-scrollbar`, `.hidden`, `@keyframes` 从各处提取 |
| `web.css` | — | min-width 媒体查询 | 从 Responsive 节筛选 `@media (min-width: ...)` |
| `mobile.css` | — | max-width 媒体查询 | 从 Responsive 节筛选 `@media (max-width: ...)` |

```python
import re

with open('index.html') as f:
    html = f.read()

# 提取 CSS
css_m = re.search(r'<style>(.*?)</style>', html, re.DOTALL)
css = css_m.group(1).strip()

# ITCSS 拆分
# 1. settings.css: :root 块
settings_match = re.search(r':root\s*\{.*?\}', css, re.DOTALL)
settings_css = settings_match.group() if settings_match else ''

# 2. base.css: 元素选择器（* {} / :focus-visible / html / body / a / img）
# 3. layout.css: .page / #list-view / .bg-layer / .container + Navbar + Main + Grid + Footer + Back to Top 节
# 4. components.css: 剩余所有节
# 5. states.css: States 节
# 6. utilities.css: ::-webkit-scrollbar / .hidden / @keyframes
# 7. web.css: @media (min-width: ...) 块
# 8. mobile.css: @media (max-width: ...) 块

nav_idx = css.find('/* ── Navbar ── */')
ro_idx = css.find('/* ── Responsive Overrides ── */')
states_idx = css.find('/* ── States ── */')

# settings + base + layout 来自 css[:nav_idx]
# components 来自 css[nav_idx:ro_idx]
# 然后从 ro_idx 提取 @media 块分到 web/mobile
# 小部件追加到 components.css
```

## JS 拆分

JS 是单文件 `app.js`（原始代码是一个 IIFE `(function(){'use strict'; ...})()`，函数间通过 `var` 共享闭包作用域）。

**不要强行按文件名拆分**：过去的 6 文件拆分（config/data/render/charts/events/squircle）来自不同代码版本，混用会导致函数找不到变量而白页。

```python
# 移除 IIFE 包装
js = re.sub(r'^\(function\(\)\{\'use strict\'\;', '', js)
js = re.sub(r'\}\)\(\);?\s*$', '', js)

with open('src/scripts/app.js', 'w') as f:
    f.write(js + '\n')
```

## 写入文件

```python
with open('src/styles/tokens.css', 'w') as f:
    f.write(tokens_css + '\n')
with open('src/styles/components.css', 'w') as f:
    f.write(components_css + '\n')
with open('src/styles/web.css', 'w') as f:
    f.write(web_css + '\n')
with open('src/styles/mobile.css', 'w') as f:
    f.write(mobile_css + '\n')
with open('src/body.html', 'w') as f:
    f.write(body + '\n')
with open('src/scripts/app.js', 'w') as f:
    f.write(js + '\n')
```

## 验证

```bash
./build.sh
# 对比生成的 index.html 与原文件的 md5
# 确认功能正常：页面加载、数据渲染、交互
```
