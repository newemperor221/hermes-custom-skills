# 汇率 API 后端代理 — 隐藏前端 API key

## 问题

汇率 API key `4eb672eb050aa81c7d8ddca1` 直接写在 index.html 中，任何用户查看网页源码即能获取。

## 方案

用 Python 代理做中转，前端只请求本地端点 `/api/proxy/exchange-rate`。

## 后端代理实现

在 `galaxy-proxy.py` 中添加：

```python
import json

EXCHANGE_API_URL = "https://v6.exchangerate-api.com/v6/4eb672eb050aa81c7d8ddca1/latest/USD"

def _handle_exchange_rate(self):
    """Proxy exchange rate — API key stays on server."""
    try:
        resp = urllib.request.urlopen(EXCHANGE_API_URL, timeout=10)
        data = resp.read()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "max-age=3600")
        self.end_headers()
        self.wfile.write(data)
    except Exception:
        # 回退固定汇率（外部 API 不可用时）
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Cache-Control", "max-age=300")
        self.end_headers()
        self.wfile.write(json.dumps({
            "result": "success",
            "conversion_rates": {"CNY": 6.82}
        }).encode())


def do_GET(self):
    # 必须放在最前面，在所有路由判断之前
    if self.path == "/api/proxy/exchange-rate":
        return self._handle_exchange_rate()
    # ... 其余路由不变
```

## 前端改动

```js
// ❌ 旧：API key 暴露
var rateData = await fetchJSON('https://v6.exchangerate-api.com/v6/4eb672eb050aa81c7d8ddca1/latest/USD');

// ✅ 新：走本地代理
var rateData = await fetchJSON('/api/proxy/exchange-rate');
```

## 注意事项

- **路由优先级**：`/api/proxy/exchange-rate` 必须在 `do_GET` 最优先匹配，防止被 `startswith("/api/")` 的通用转发逻辑或 SPA catch-all 拦截
- **回退值**：当外部 API 不可用时，返回固定汇率 6.82（USD/CNY），避免页面完全依赖外部服务
- **缓存**：设置 `Cache-Control: max-age=3600` 减少重复请求。回退时用 300s 更快恢复
- **CORS**：代理同源提供服务，无需跨域头。但加了 `Access-Control-Allow-Origin: *` 以防后续有其他前端调用
- **Alpine LXC 网络**：部分低配 LXC 容器可能无法访问外部 HTTPS API。此时回退机制自动生效，不影响页面功能
