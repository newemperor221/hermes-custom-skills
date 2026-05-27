# HMAC 签名鉴权测试指南

IP-Sentinel webhook 的所有动作端点都受 HMAC-SHA256 签名保护，需要 `?t=<timestamp>&sign=<hex>` 参数。

## 鉴权原理

```
AUTH_TOKEN = CHAT_ID 的值（config.conf 中的 PSK）
msg        = f"{req_path}:{req_t}".encode('utf-8')
sign       = hmac.new(AUTH_TOKEN, msg, sha256).hexdigest()
```

- `req_t` = Unix 时间戳（秒），必须在当前时间 ±60 秒内
- 同一签名 60 秒内不可重放（USED_SIGNS 缓存池）

## Python 生成签名 + 调用

```python
import hmac, hashlib, time, urllib.request

AUTH_TOKEN = '8101587606'  # 即 CHAT_ID
req_path = '/trigger_report'
req_t = str(int(time.time()))
msg = f'{req_path}:{req_t}'.encode('utf-8')
sign = hmac.new(AUTH_TOKEN.encode('utf-8'), msg, hashlib.sha256).hexdigest()

url = f'https://{IP}:{PORT}{req_path}?t={req_t}&sign={sign}'
req = urllib.request.Request(url)
resp = urllib.request.urlopen(req, timeout=10)
print(resp.read().decode())
```

## 可用端点

| 端点 | 说明 |
|------|------|
| `/trigger_run` | 执行运行器（runner.sh） |
| `/trigger_google` | Google 区域纠偏 |
| `/trigger_trust` | IP 信用净化 |
| `/trigger_report` | 发送 TG 战报 |
| `/trigger_log` | 抓取日志并通过 TG 发送 |

> 注意：所有端点必须走 HTTPS（如果 cert.pem 存在），HTTP 会收到 `Connection reset by peer`。

## 一键测试脚本

保存为 `/opt/ip_sentinel/core/test_trigger.sh`：

```bash
#!/bin/sh
CONFIG="/opt/ip_sentinel/config.conf"
. "$CONFIG"
PORT="${AGENT_PORT:-42186}"
# CHAT_ID = AUTH_TOKEN
REQ_PATH="$1"
TS=$(date +%s)
SIGN=$(echo -n "${REQ_PATH}:${TS}" | openssl dgst -sha256 -hmac "$CHAT_ID" | awk '{print $NF}')
curl -sk -m 10 "https://127.0.0.1:${PORT}${REQ_PATH}?t=${TS}&sign=${SIGN}"
```

用法：`sh test_trigger.sh /trigger_report`
