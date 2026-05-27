# Python http.server IPv6 Dual-Stack 绑定（Alpine Linux）

Python 的 `http.server.HTTPServer` 默认创建 IPv4 套接字（`AF_INET`）。绑定到 `"0.0.0.0"` 或 `""` 都只监听 IPv4。

## 在 Alpine 上实现 IPv4+IPv6 双栈绑定

Alpine 默认 `net.ipv6.bindv6only=0`（IPv6 套接字自动接受 IPv4 连接）。

```python
import socket, http.server
from socketserver import ThreadingMixIn

class ThreadedHTTPServer(ThreadingMixIn, http.server.HTTPServer):
    address_family = socket.AF_INET6  # 关键：指定 IPv6 地址族

if __name__ == "__main__":
    s = ThreadedHTTPServer(("::", 25774), PH)
    s.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)  # 允许 IPv4 连接
```

## 为什么 `""` 不行

`http.server.HTTPServer` 继承 `socketserver.TCPServer`，其 `__init__` 创建套接字时使用类属性 `address_family`。默认值是 `socket.AF_INET`，所以绑定 `""` 或 `"0.0.0.0"` 都只创建 IPv4 套接字。`address_family = socket.AF_INET6` 告诉它创建 IPv6 套接字。

## cloudflared localhost 解析坑

在 Alpine 上，`localhost` 默认解析到 `::1`（IPv6）。如果 galaxy-proxy 只监听 IPv4（`0.0.0.0`），cloudflared 试图通过 `localhost` 连接时会失败：

```
cloudflared ERR Unable to reach the origin service: dial tcp [::1]:25774: connect: connection refused
```

**修复：** 让 galaxy-proxy 监听双栈（上述方法），或在 cloudflared 中明确使用 `127.0.0.1`（需在 Cloudflare Zero Trust Dashboard 中修改 ingress 配置）。

## 验证双栈

```bash
# 检查监听（双栈显示为 0.0.0.0:PORT 或 *:PORT 取决于 ss 版本）
ss -tlnp | grep 25774

# 测试 IPv4
curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:25774/

# 测试 IPv6
curl -s -o /dev/null -w '%{http_code}' --connect-timeout 5 http://[::1]:25774/
```
