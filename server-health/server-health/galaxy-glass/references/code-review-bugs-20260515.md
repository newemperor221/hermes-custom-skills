# 2026-05-15 第二次综合代码审查 — 8 个 bug 及修复

## 背景
用户要求「检查整个项目源码，有没有bug」。审查范围：GalaxyGlass 主题 `index.html` + `galaxy-proxy.py`。

## 项目文件
- `/opt/komari/data/theme/index.html` — 前端单文件 (672行, 82KB, HTML/CSS/JS)
- `/opt/komari/galaxy-proxy.py` — Python 反向代理 (92行)

## 发现的 bug

### 🔴 严重

| # | 问题 | 位置 | 修复 |
|---|------|------|------|
| CSS-1 | `.detail-body` 内嵌套 `.page { }` 和 `#list-view { }` 选择器（CSS 不支持嵌套），导致 `display: grid` 被丢弃 | L356-361 | 去掉嵌套，修正为 `display: grid; grid-template-columns: 1.2fr 0.8fr` |
| JS-1 | `//` 注释换掉了 `if(ts.buildTime){...}` → 单行 JS 中 `//` 吞掉同行后续代码（包括 `if(siteData.sitename){...}}` 闭括号），整个 IIFE 语法错误 | L563 | 直接用空字符串删除，不要用注释替换 |
| JS-2 | 美元汇率 API key `4eb672eb...` 硬编码在前端代码中 | L566 | 移到后端 proxy（`/api/proxy/exchange-rate`），前端调本地端点 |

### 🟡 中等

| # | 问题 | 位置 | 修复 |
|---|------|------|------|
| JS-3 | `showListView()` 不调用 `render()` → 返回列表时过滤/搜索状态丢失 | L600 | 在 `showListView` 开头加 `render()` |
| CSS-2 | `.page` 和 `#list-view` 被重复声明（在 detail-body 内嵌套后又在外层有同名规则） | L46-47, 357-358 | 随 CSS-1 一并移除 |

### 🟢 轻微

| # | 问题 | 位置 | 修复 |
|---|------|------|------|
| JS-4 | `var _i` 循环变量泄漏到 IIFE 作用域 | L621 | `var _i` → `let _i` |
| JS-5 | 搜索框 focus 延迟 200ms 感知卡顿 | L649 | 200ms → 50ms |
| CSS-3 | back-to-top hover 用了金色 `rgba(201,169,78,0.3)` 与整体风格不搭 | L433 | 改为 accent-2 靛蓝 `rgba(129,140,248,0.3)` |

## 修复过程踩坑

### `//` 注释吞代码（JS-1）

用 sed 替换 `if(ts.buildTime){...}` 为 `// siteStart is set from first user creation date, not buildTime` 后，整个页面 JS 不执行（SyntaxError）。整个页面只有静态 HTML，所有交互失效。

第一次修复时不理解症状，以为是 browser cache，尝试 `navigate()` 刷新、加 `?t=1` cache bust、console 调试。直到 `eval(document.querySelector('script').textContent)` 返回 `SyntaxError: Unexpected token ')'` 才确认是语法错误。

**教训**：单行 JS 中 `//` 注释会吃掉整行剩余代码。直接删除目标代码即可，不要用注释替换。

### Proxy 重启方法

由于 LXC 容器无 systemd，proxy 由用户手动 `nohup python3 ... &` 启动。
```
sshpass -p 'OX8w$nE9A%tfqb6v' ssh -p 46748 root@<荷兰_IP> "kill PID; sleep 1"
# 然后用 Hermes 的 background=true 启动新进程
```

### 验证方法

```bash
# 验证 JS 语法
node --check /opt/komari/data/theme/index.html  # ❌ 会报错因为是 HTML 含 script

# 正确：从 HTML 提取 script
python3 -c "import re; m=re.search(r'<script>(.*?)</script>',open('/opt/komari/data/theme/index.html').read(),re.DOTALL); open('/tmp/v.js','w').write(m.group(1))"
node --check /tmp/v.js

# 或浏览器 eval
try { new Function(document.querySelector('script').textContent) } catch(e) { e.toString() }
```

## 相关 PR/commit
(none — 直接修改远程服务器文件)
