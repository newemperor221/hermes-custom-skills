# Frontend 渲染问题调试链（Proxy 架构下）

> 适用于任意 Python proxy（galaxy-proxy.py） + Komari 后端 + Cloudflare（可选） + 前端 JS 渲染的架构。

## 问题场景

用户报告的视觉问题（如节点名前多余单引号 `'`）涉及多个可能出问题的层：
1. 磁盘上的源文件
2. Python proxy 服务的静态文件
3. API 数据源
4. Cloudflare 缓存
5. 浏览器 JavaScript 运行时的渲染结果

**核心原则：逐个层验证，锁定根因再动手修复。**

## 架构先决条件：确认你在改哪台机器

**这是最常见的根因之一：修改了本地文件但实际公网服务走的是另一台机器。**

Komari 的双机部署架构：
- **本地机器**（开发机/维护机）— 文件修改后不自动生效
- **波兰主控**（<荷兰_IP>:46748）— 通过 cloudflared 隧道 → Cloudflare → <监控面板域名> 实际提供公网服务
- 请求链路：`浏览器 → Cloudflare → cloudflared tunnel → 波兰主控:25774 → Python proxy → /opt/komari/data/theme/index.html`

**验证方法：**
```bash
# 比较两台机器的文件大小即可快速判断是否一致
wc -c /opt/komari/data/theme/index.html
ssh -p 46748 -i ~/.ssh/hermes_admin root@<荷兰_IP> "wc -c /opt/komari/data/theme/index.html"

# 或直接对比关键行
ssh -p 46748 -i ~/.ssh/hermes_admin root@<荷兰_IP> \
  "grep -o 'node-name\">[^<]*<' /opt/komari/data/theme/index.html | head -3"
```

**同步方法：**
```bash
scp -P 46748 -i ~/.ssh/hermes_admin \
  /opt/komari/data/theme/index.html \
  root@<荷兰_IP>:/opt/komari/data/theme/index.html
```

⚠️ **但 SCP 同步可能仍然不够！** 如果远程机器跑的是 komari 直连（native 模式，无 galaxy-proxy），komari 使用的是内嵌主题，不读磁盘文件。必须切换架构：部署 galaxy-proxy.py 替代 komari 直接服务端口。详见 `komari-server-ops` 技能中「从 native 模式切换到 proxy 模式」。

**如果不一致则修改未生效。始终在做以下事情前先确认：**
1. <监控面板域名> 指向哪个服务器？（Cloudflare → cloudflared tunnel → ?）
2. 我改的机器是开发机还是实际服务机？
3. 需要同步到远程吗？
4. ⚠️ 远程机的端口是谁在监听？（komari → 内嵌主题; python3 → 读磁盘）

## 调试链（自上而下）

### 第1层：磁盘源文件

```bash
# 检查 JS 渲染函数（renderCard）
grep -o "renderCard.*" /opt/komari/data/theme/index.html | cut -c1-500

# 检查 server-rendered HTML（如果有的话）
grep -o 'node-name\">[^<]*<' /opt/komari/data/theme/index.html | head -5

# 验证关键行的具体内容
sed -n 'N,Np' /opt/komari/data/theme/index.html
```

📌 **确认点：** JS 代码中的字符串拼接是否正确。特别是 `\'` 转义、`''` 空字符串、`+` 拼接。

### 第2层：Python proxy 服务的文件

```bash
# 直接访问 proxy（绕开 Cloudflare）
curl -s http://localhost:25774/index.html | grep -o 'node-name\">[^<]*<' | head -5

# 如果 proxy 运行在远程，SSH 过去验证
ssh -p PORT user@HOST "curl -s http://127.0.0.1:25774/index.html | grep -o 'node-name\\\">[^<]*<' | head -5"
```

📌 **确认点：** proxy 是否真的在从磁盘读取文件（检查 `THEME_DIR` 路径）。`Cache-Control` 头是否为 `no-cache`。

### 第3层：API 数据源

```bash
# 确认 API 返回的数据不含脏数据
curl -s https://<监控面板域名>/api/nodes | python3 -c "
import json,sys
data = json.load(sys.stdin)
for n in data.get('data',[]) or []:
    name = n.get('name','')
    first = [ord(c) for c in name[:3]]
    print(f'{repr(name[:25]):30} bytes: {first}')
"
```

📌 **确认点：** 数据源名字无前导/后置脏字符。`repr()` 的 outer quotes 不是数据的一部分——用 `ord()` 验证每个字符的 unicode code point。

### 第4层：Cloudflare 缓存

```bash
# 通过 Cloudflare（正常域名）
curl -s 'https://<监控面板域名>/?_nocache=1' | grep -o 'node-name\">[^<]*<' | head -5

# 对比直连 origin（如果可用）
curl -s 'http://ORIGIN_IP:PORT/?_nocache=1' | grep -o 'node-name\">[^<]*<' | head -5
```

📌 **确认点：** Cloudflare 可能缓存旧版 HTML/JS。CF 缓存基于 URL + headers 组合，浏览器和 curl 可能命中不同缓存。

**清缓存方法：**
- URL 加 `?v=N` 参数
- Cloudflare Dashboard → Caching → Purge Everything
- 或 Purge Individual URLs（输入具体路径）

### 第5层：浏览器运行时

```bash
# 通过 browser_console 获取实际 DOM 内容
# 注意：需要等 JS 渲染完成（setTimeout 2-5s）
setTimeout(() => {
  const cards = document.querySelectorAll('.node-card .node-name, [class*="name"]');
  cards.forEach(el => {
    if (el.textContent && el.textContent.trim()) {
      console.log('"' + el.textContent.substring(0, 30) + '" [charCode 0: ' + el.textContent.charCodeAt(0) + ']');
    }
  });
}, 3000);
```

📌 **确认点：**
- JS 渲染后的 DOM 内容（可能和原始 HTML 不同）
- charCode(0) 是否为 39（单引号）或其他脏字符
- CSS 属性是否影响视觉（如 `::before` 伪元素内容）

### 层级对照决策树

```
用户报告问题
    ↓
确认你在改正确的机器（本地 vs 远程云服务机）──否→ SSH到远程或SCP同步
    ↓⚠️
确认远程机是 proxy 还是 native 模式（ss -tlnp | grep 25774）
    │ native (komari 直连)──→ 需先切换为 proxy 模式（部署 galaxy-proxy）
    ↓ proxy
磁盘源文件有脏数据？──是→ 修改源文件
    ↓否
Proxy 文件与磁盘一致？──否→ 检查 proxy 的文件读取路径/缓存
    ↓是
API 数据源干净？──否→ 修改数据库/上游
    ↓是
Cloudflare 缓存旧版？──是→ 清 CF 缓存 + ?v=N
    ↓否
浏览器运行时异常？──是→ JS 执行顺序 / DOM 操作 / 伪元素
    ↓否
推测：视觉工具误报 → 让用户确认
```

## 同步验证清单（修改后必做）

修改前端文件后，按以下顺序验证：

```bash
# 1. 本地磁盘确认
grep -o 'node-name">[^<]*<' /opt/komari/data/theme/index.html | head -3

# 2. 同步到远程（如果架构是双机）
scp -P 46748 -i ~/.ssh/hermes_admin \
  /opt/komari/data/theme/index.html \
  root@<荷兰_IP>:/opt/komari/data/theme/index.html

# 2b. ⚠️ 验证远程机监听的是 python3（proxy）还是 komari
ssh -p 46748 -i ~/.ssh/hermes_admin root@<荷兰_IP> \
  "ss -tlnp | grep 25774"
# → python3: proxy 模式，SCP 同步后应该立即生效
# → komari: native 模式，需要切换架构！

# 3. 确认远程文件同步成功
ssh -p 46748 -i ~/.ssh/hermes_admin root@<荷兰_IP> \
  "wc -c /opt/komari/data/theme/index.html"

# 4. 通过本地 proxy 验证
curl -s http://localhost:25774/index.html | grep -o 'node-name">[^<]*<' | head -3

# 5. 通过 Cloudflare 验证
curl -s 'https://<监控面板域名>/?v='$(date +%s) | grep -o 'node-name">[^<]*<' | head -3

# 6. 浏览器验证（清缓存或硬刷新后再看）
```

## 常见陷阱

### `curl` vs 浏览器的结果不一致

**可能原因：**
1. **Cloudflare 缓存差异** — curl 和浏览器可能使用不同的 User-Agent/headers，命中不同缓存
2. **JavaScript 运行时修改** — 初始 HTML 干净但 JS 执行后 DOM 被替换（`grid.innerHTML = filtered.map(renderCard)...`）
3. **浏览器 tool 的渲染状态** — `browser_navigate` 后可能未等 JS 执行完就查询

**处理方法：**
- 每次都等 2-5s 再检查 DOM
- 同时检查原始 HTML（`document.documentElement.outerHTML`）和 JS 修改后的 DOM
- 如果 curl 和 browser 不一致，增加 `?v=N` 缓存破坏

### JS 字符串拼接中的隐藏字符

```javascript
// ❌ 问题代码：renderCard 中的多余转义
'<div class=\"node-name\">\\''+(n.name||...)+'</div>'
//                          ^^^ — 这会在 HTML 中渲染出单引号

// ✅ 正确代码：改成空字符串
'<div class=\"node-name\">''+(n.name||...)+'</div>'
//                           ^^ — '' 是空字符串，不影响渲染

// ⚠️ 边界情况：'' 和 \\' 在视觉上差一个 \
//      '' 是空字符串 → 不输出任何字符
//      \\' 是转义单引号 → 输出字符 '
```

**检查方法：** `grep -o 'node-name[^<]*<'` 显示实际的 HTML 内容比读 JS 代码更快。

### 有多份 index.html

某些部署存在多份 index.html（disk / galaxy-proxy embedded / komari-old built-in），需确认实际服务的是哪一份：

```bash
# 确认 proxy 的 THEME_DIR 路径
grep -n "THEME_DIR" /opt/komari/*.py

# 确认哪个 komari 进程监听在 <监控面板域名> 的实际端口
ss -tlnp | grep 25774
```

### 双机部署的文件不一致

这是最常见的陷阱。本地修改了文件，但远程还有一份：

```bash
# 症状：curl 本地 proxy 返回正确，浏览器看到错误
# 根因：浏览器通过 cloudflared 走远程机，远程机文件未更新
#      或者远程机是 native 模式（komari 直连），文件改了也没用

# 检查方法：
# 1. 查 cloudflared 在哪台机器上运行
ps aux | grep cloudflared
# → ssh ... root@<荷兰_IP> "cloudflared tunnel --url ..." — 远程机

# 2. 查 Python proxy 在哪台机器上运行
ps aux | grep galaxy-proxy
# → 可能同时有本地和远程实例

# 3. 查 <监控面板域名> 的 DNS 指向
dig +short <监控面板域名>
# → 104.21.x.x / 172.67.x.x — Cloudflare IP
# Cloudflare → cloudflared tunnel → 远程机 → 远程机上的 proxy 或 komari

# 4. 验证远程机端口谁在监听
ssh -p 46748 -i ~/.ssh/hermes_admin root@<荷兰_IP> \
  "ss -tlnp | grep 25774"
# → python3 → 读磁盘，SCP 同步即可
# → komari  → 内嵌主题，需部署 galaxy-proxy

# 5. 验证远程机的文件内容
ssh -p 46748 -i ~/.ssh/hermes_admin root@<荷兰_IP> \
  "grep -o 'node-name\">[^<]*<' /opt/komari/data/theme/index.html | head -3"
```

### SCP 同步后仍然无效：远程机是 native 模式

**这是 2026-05-19 新发现的第 6 层陷阱：** 即使文件大小一致（SCP 同步成功），如果远程机跑的是 komari 直连（embedded theme），修改磁盘文件毫无效果。

**症状：**
- `wc -c` 本地 == 远程（文件已同步）
- `curl localhost:25774` 返回正确
- 浏览器访问公网域名仍然看到老版本
- `ss -tlnp | grep 25774` 显示 `users:(("komari",...))`

**原因：** komari 二进制内嵌了主题文件（Go embed）。它使用数据库中的 `theme_configurations` 表决定激活哪个内嵌主题，从不读磁盘上的 index.html。磁盘文件只是给 galaxy-proxy.py 用的。

**修复：** 见 `komari-server-ops` 技能中「从 native 模式切换到 proxy 模式」章节。

**预防：** 修改前端文件前，永远先检查目标机的监听进程：`ss -tlnp | grep 25774`。
