# Google Search Cookie Bypass

Google 搜索对自动化爬虫有**多层防护**：
1. JS 渲染依赖（结果靠 JavaScript 生成）
2. CONSENT cookie 验证（GDPR 弹窗）
3. 行为检测（鼠标移动、滚动、点击间隔）

## 绕过方案

### 核心：CONSENT cookie 预置

使用 StealthyFetcher 时，在请求前注入以下 cookie：

```python
from scrapling import StealthyFetcher
from scrapling.core._types import SetCookieParam

sf = StealthyFetcher()
resp = sf.fetch(
    "https://www.google.com/search?q=关键词&num=10",
    cookies=[
        SetCookieParam(
            name="CONSENT",
            value="YES+cb.20260517-01-p0.en+FX+",
            url="https://www.google.com/"
        ),
        SetCookieParam(
            name="SOCS",
            value="CAISHAgBEhJnd3NfMjAyNjA1MTctMDFfcmExEgVkZW4gARgB",
            url="https://www.google.com/"
        ),
    ],
    network_idle=True,
    wait=3
)
```

### 结果提取

Google 搜索结果的 h3 标签就是标题，父元素 `<a>` 包含链接：

```python
h3s = resp.css("h3")
for h3 in h3s:
    title = h3.get_all_text().strip()
    parent = h3.parent
    if parent:
        links = parent.css("a")
        if links:
            href = links[0].attrib.get("href", "")
```

### Cookie 有效期

- CONSENT cookie 大约**几天到一周**有效
- 失效时 Google 会再次返回 redirect 页面
- 重新获取：在浏览器中打开 google.com，从 DevTools → Application → Cookies 复制新值
- 搜索参数 `&num=10` 控制结果数

### 已知问题

- `timeout` 参数传 int 在 Scrapling v0.4.8 中被当毫秒处理（20 → 20ms）
- 用 float 传 timeout 或省略该参数
- Google 搜索结果页不含 `div.g` 选择器，只能用 h3 + parent 提取
