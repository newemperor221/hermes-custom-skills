# Debug: 美化版页面空白（无节点卡片）的排查与修复

## 背景

2026-05-13 将对 GalaxyGlass v2.7 做了全面字体放大 + 间距调整 + stats 差异化色调等美化改动后，部署上线发现页面仅显示顶部 4 个 stat 卡片骨架，下方服务器节点卡片完全空白。

## 症状

- ✅ 导航栏正常
- ✅ 顶部 stat 卡片布局正常（数据为空值）
- ✅ 背景壁纸能加载（poster/video URL 被赋值）
- ❌ 无节点卡片（`document.querySelectorAll('.node-card').length === 0`）
- ❌ 搜索结果筛选器未渲染
- ❌ 控制台无明显报错

## 特征性诊断

页面"能用但不完整"的原因是 **JS 语法错误导致整个 IIFE 不执行**。由于 GalaxyGlass 的主体代码全在一个 IIFE 内，任何语法错误都会让整个脚本静默失败，只留下 DOM 骨架和 HTML 内置的 stat 卡片结构。与 API 超时、网络错误的区别：

| 特征 | 语法错误 | API 超时 |
|------|---------|---------|
| stat 卡片 | 空值（骨架） | 空值（无数据） |
| 背景壁纸 | 加载成功 | 加载成功 |
| node-card count | `=== 0` | `=== 0` |
| console error | 无 | `fetch failed` 或 `TypeError` |

## 排查步骤

### 1. 确认后端正常

```bash
# 直连代理端口，确认 API 可访问
curl -s http://localhost:25774/api/nodes | python3 -m json.tool | head -20
# → 应返回 200 + 节点 JSON

curl -s -o /dev/null -w '%{http_code}' http://localhost:25774/
# → 应返回 200
```

如果 /api/nodes 返回 200 且 / 返回 200，说明后端和代理都正常，问题在前端 JS。

### 2. 提取 inline script 并用 node 验证

```bash
curl -s 'https://stat.357561.xyz/' -o /tmp/gg.html
python3 -c "
import re
html = open('/tmp/gg.html').read()
m = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if m:
    open('/tmp/gg_v.js','w').write(m.group(1))
"
node --check /tmp/gg_v.js
```

**注意**：通过 Cloudflare CDN 下载的页面可能含 CF Challenge injection（多个 `<script>` 标签），`re.search` 取第一个。GalaxyGlass 的主脚本始终是第一个且体积最大的 inline script。

### 3. 定位错误行

`node --check` 会明确报告语法错误位置和原因：

```
/tmp/gg_script.js:26
updateStats();buildRegionFilters();positionBackToTop();grid.classList.remove('fade-out')}
                                                                                        ^
SyntaxError: missing ) after argument list
```

错误指向 render 函数结尾缺少括号。

### 4. 修正方法

render 函数使用双层 `requestAnimationFrame` 嵌套实现渲染帧对齐。闭包展开对照：

```js
function render() {                            // {1 — render 函数体
  requestAnimationFrame(function() {           // (1, {2 — 外层 rAF
    requestAnimationFrame(function() {         // (2, {3 — 内层 rAF
      // filter/sort/swap DOM...
      updateStats(); buildRegionFilters(); 
      positionBackToTop(); 
      grid.classList.remove('fade-out')
    }                                           // }3 — 内层 rAF 回调结束
                                               // )2 — 内层 rAF 调用结束
                                               // }2 — 外层 rAF 回调结束
                                               // )1 — 外层 rAF 调用结束
  }                                             // }1 — render 函数体结束
}
```

写成一行时必须补全所有闭符号：
```js
grid.classList.remove('fade-out')});});}
```

完整闭符号映射：
| 符号 | 含义 |
|------|------|
| `}` | 闭合内层 rAF 回调函数体（{3） |
| `)` | 闭合 `rAF(function() { … }` 的调用括号（(2） |
| `}` | 闭合外层 rAF 回调函数体（{2） |
| `)` | 闭合外层 `rAF(function() { … }` 的调用括号（(1） |
| `}` | 闭合 render 函数体（{1） |

### 5. 验证修复

```bash
node --check /tmp/gg_fixed.js
# exit 0 = 通过
```

然后刷新页面，节点卡片应全部正常渲染。

## 根本原因

美化过程中对 render 函数做了内容调整（新增 `updateStats()` 等调用），在单行格式下人工调整时遗漏了双 rAF 嵌套所需的 3 个额外闭符号。这种错误在代码分散为多行时不易发生，但银河面板为了压缩体积会将大量代码写在一行内。

## 预防

- **每次提交前执行** `node --check` 验证 inline script 语法
- 如果修改了 render 函数的结尾部分，仔细检查 `}))};` 链是否完整
- 在 SKILL.md 坑点中已添加上述验证命令作为标准流程
