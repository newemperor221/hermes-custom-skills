---
name: tab-heartbeat-online-count
description: 实现真实在线人数追踪——每个浏览器标签页发 UUID 心跳，后端维护 TTL 活跃列表。比 session 计数或 WebSocket 连接计数更准确。
trigger: 在线人数不准、开多个标签页数字不变、做的在线人数统计
---

# Tab UUID Heartbeat — 在线人数追踪

## 问题
- sessions 表按 session cookie 分组 -> 同浏览器多标签页只算 1 个
- WebSocket 连接计数 -> 会误算探针 agent 等后台 WS 连接
- 用户期望：开 N 个标签页就显示 N

## 方案
前端每个标签页生成唯一 UUID（存 sessionStorage），随心跳请求带上。后端维护 {uuid: last_seen}，TTL 过期自动清除。

## 实现步骤

### 1. 后端代理层（Python HTTP Server 示例）

```python
import time, threading

TAB_TTL = 90  # 90 秒无心跳即视为离线

_tabs = {}
_tabs_lock = threading.Lock()

def tab_heartbeat(tab_id):
    with _tabs_lock:
        _tabs[tab_id] = time.monotonic()

def tab_purge():
    now = time.monotonic()
    cutoff = now - TAB_TTL
    with _tabs_lock:
        dead = [tid for tid, ts in _tabs.items() if ts < cutoff]
        for tid in dead:
            del _tabs[tid]
        return len(_tabs)
```

在 HTTP handler 中：

```python
from urllib.parse import urlparse, parse_qs

parsed = urlparse(self.path)
qs = parse_qs(parsed.query)
tab_id = qs.get("t", [None])[0]
if tab_id:
    tab_heartbeat(tab_id)
count = tab_purge()
# 返回 {"online": count}
```

### 2. 前端修改

在轮询在线人数的代码前，生成/获取 tab UUID：

```javascript
// sessionStorage 是 per-tab 的，开新标签页生成新 UUID，刷新同个页面保留 UUID
var _tabId = sessionStorage.getItem('gg-tab') || crypto.randomUUID();
sessionStorage.setItem('gg-tab', _tabId);
```

轮询时带上：

```javascript
var oc = await fetchJSON('/api/proxy/online-count?t=' + _tabId);
```

### 3. 关键设计点

| 项 | 选择 | 原因 |
|---|---|---|
| 存储 | sessionStorage | 每个标签页独立，关闭即销毁 |
| UUID 生成 | crypto.randomUUID() | 浏览器原生，无需 polyfill |
| 心跳间隔 | 匹配前端原有轮询间隔（如 60s） | 零额外请求 |
| TTL | 轮询间隔 x 1.5（如 90s） | 容忍一次丢包 |
| 清理 | 每次请求时 purge | 无需额外定时器 |

## 验证

```bash
# 不带 tab -> 0
curl -s /api/proxy/online-count

# 带 tab -> 递增
curl -s '/api/proxy/online-count?t=tab-a'  # -> 1
curl -s '/api/proxy/online-count?t=tab-b'  # -> 2

# 90 秒后自动归零
```

## 注意事项

- 不要用 WebSocket 连接计数来判断人在看面板——agent 的长连接会污染数据
- 不要用 sessions 表判断实时在线——30 分钟窗口太宽，且同浏览器只计一次
- threading.Lock() 保护共享字典，Python GIL 不保证 dict 操作的原子性
- 如果前端有 Service Worker 或 PWA，sessionStorage 在 SW 中不可用——建议在页面主线程中生成
- 每次修改后必须告知用户硬刷新（Ctrl+F5）加载最新 JS/CSS
- 完整项目案例见 galaxy-glass skill（<监控面板域名> 面板，含前端 JS 模板、Python 代理层路由、CSS 样式统一等内容）
