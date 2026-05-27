---
name: scrapling-search
description: Scrapling-powered web search — bypass AI contamination, scrape raw results with anti-detection
---

# Scrapling Search

使用 Scrapling (D4Vinci/Scrapling) 直接爬取搜索结果，绕过 AI 污染和反爬机制。

## 触发条件

- 用户要求搜索、查资料
- 需要绕过 AI 摘要污染
- 目标站点有反爬/Cloudflare

## 两种模式

### 快速模式 (Fetcher)
无JS执行，只能爬简单站点。用 DuckDuckGo HTML。
```python
from scrapling import Fetcher
f = Fetcher()
resp = f.get("https://html.duckduckgo.com/html/?q=关键词",
             headers={"User-Agent": "Mozilla/5.0"})
results = resp.css("div.result")
for r in results:
    title = r.css("h2 a")[0].get_all_text().strip()
    href = r.css("h2 a")[0].attrib.get("href", "")
    snippet = r.css("a.result__snippet")
    text = snippet[0].get_all_text().strip() if snippet else ""
```

### 隐身模式 (StealthyFetcher)
Playwright 浏览器引擎，可过 Cloudflare。
```python
from scrapling import StealthyFetcher
sf = StealthyFetcher()
resp = sf.fetch("https://example.com",
                solve_cloudflare=True,  # 过关CF Challenge
                network_idle=True,      # 等待网络空闲
                wait=3)                 # 额外等待秒数
text = resp.get_all_text()
```

## 默认搜索策略

```
你问问题 → Scrapling + DuckDuckGo（首选）
              ↓ 失败
           内置 web_search（fallback）
```

用户要求：**Scrapling + DuckDuckGo 是默认搜索引擎**，内置 web_search 仅做备用。

## Scrapling API 速查

| 概念 | 用法 |
|------|------|
| **Fetcher** | `Fetcher()` → 基本 HTTP。`f.get(url)` |
| **StealthyFetcher** | `StealthyFetcher()` → 浏览器引擎。`sf.fetch(url)`（不是 `.get()`！） |
| **Response.body** | 原始 bytes — `.decode('utf-8', errors='replace')` |
| **CSS 选择** | `resp.css("div.foo")` → Selector 列表 |
| **属性访问** | `el.attrib` — 字典。不是 `.attributes` 或 `.attr` |
| **文本提取** | `el.get_all_text()` — 完整可见文本。不是 `.text_content()` |
| **HTML** | `el.html_content` — 原始内层 HTML |
| **子元素** | `el.children` |
| **标签名** | `el.tag` |
| **XPath** | `resp.xpath("//div")` |
| **自适应** | `el.find_similar()` / `el.relocate()` — 页面变化时自动重定位 |

### StealthyFetcher 参数

| 参数 | 说明 |
|------|------|
| `solve_cloudflare` | 自动解决 Cloudflare Turnstile（约 15-25 秒） |
| `network_idle` | 等待网络请求全部完成 |
| `wait` | 页面加载后额外等待秒数 |
| `retries` | 失败重试次数 |
| `timeout` | ⚠️ v0.4.8 传 int 可能当 ms 处理，传 float 或省略 |
| `google_search` | Google 搜索模式 |
| `extra_headers` | 额外 HTTP 头 |
| `headless` | 是否无头模式 |

## 各站点实测

| 站点 | Fetcher | StealthyFetcher | 关键参数 |
|------|---------|----------------|---------|
| DuckDuckGo | ✅ | ✅ | 默认引擎，无需配置 |
| Hacker News | ✅ | ✅ | 无防爬 |
| 博客园 | ✅ | ✅ | 无防爬 |
| V2EX (节点页) | ✅ | ✅ | `/go/xxx` 直接通 |
| **Google 搜索** | ❌ JS壳 | ⚠️ | CONSENT cookie + network_idle |
| **Linux Do** | ❌ CF | ✅ | `solve_cloudflare=True`，或 Discourse JSON API |
| **知乎专栏** | ❌ 403 | ✅ | `zhuanlan.zhihu.com/p/...` |
| **掘金** | ❌ SPA | ⚠️ | `network_idle=True` + `wait >= 8` |
| 知乎主站 | ❌ 403 | ❌ | 全站 403 无解 |
| NodeSeek | ❌ CF | ❌ | Cloudflare 太严 |
| Reddit | ❌ 403 | ❌ | IP 段封禁 |

### 🔑 Discourse JSON API（绕过 Cloudflare）

很多 Discourse 论坛（linux.do 等）有 Cloudflare Challenge，但暴露 **JSON API 端点**无需 JS。给任意话题 URL 加 `.json` 后缀即可：

```
https://linux.do/t/topic/888560.json
```

返回结构化 JSON（帖子、作者、内容、时间戳），无 Cloudflare 墙，`curl` 直接通。

**优先级**：对 Discourse 站点，先试 `.json` API 再试 StealthyFetcher。

## Script 用法

```bash
# 快速搜索
python3 ~/.hermes/scripts/scraple_search.py "关键词"

# 隐身模式（过简单反爬）
python3 ~/.hermes/scripts/scraple_search.py --stealth "关键词"

# 过 Cloudflare
python3 ~/.hermes/scripts/scraple_search.py --stealth --solve-cf "关键词"

# 限制结果数
python3 ~/.hermes/scripts/scraple_search.py "关键词" --limit=5
```

## Pitfalls

### timeout 参数 bug（v0.4.8）
```python
# ❌ 错误 — 20 会被当 20ms
sf.fetch(url, timeout=20)

# ✅ 正确
sf.fetch(url, network_idle=True, wait=5)
```

### 掘金 SPA 需要耐心
- 必须 `network_idle=True` + `wait >= 8`
- 首屏 2KB 空壳是正常的
- 不要用 Fetcher 试，永远拿不到内容

### Google CONSENT cookie 过期
- cookie 过期后 Google 返回 redirect 页
- 症状：`"Please click here if you are not redirected"`
- 不要反复重试，必须续 cookie
