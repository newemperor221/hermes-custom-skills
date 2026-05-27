# 掘金 SPA 渲染绕过

掘金是完全的**前端 SPA（Vue）**，不执行 JS 只能拿到 2KB 的空壳。

## 绕过方案

### 关键参数

```python
from scrapling import StealthyFetcher

sf = StealthyFetcher()
resp = sf.fetch(
    "https://juejin.cn/post/文章ID",
    network_idle=True,   # 等所有网络请求完成
    wait=8               # 额外等 SPA 渲染
)
```

- `network_idle=True` — 等待所有 XHR/API 请求完成
- `wait=8` — 给 Vue 编译渲染的时间（至少 5-8 秒）
- 不设置 `timeout`（v0.4.8 的 int→ms bug）

### 实测结果

| 页面 | Fetcher (裸HTTP) | **StealthyFetcher** |
|------|-----------------|-------------------|
| 首页 | 2.4KB JS 空壳 | **9.5KB** 含内容 |
| 文章页 | 2.4KB JS 空壳 | **12KB** 含正文 |

### 文章正文提取

```python
text = resp.get_all_text()  # 获取全文
# SPA 渲染后内容混在大量导航/侧栏文本中
# 用关键词范围截取可减少噪音
```

### 注意事项

- SPA 页面渲染时间不稳定（取决于 API 响应速度）
- 首屏内容一般在 5 秒内完成
- 掘金没有额外的 Cloudflare 或验证码保护，仅靠 SPA 反爬
