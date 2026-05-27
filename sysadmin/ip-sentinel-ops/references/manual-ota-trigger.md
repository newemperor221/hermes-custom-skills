# 手动触发 OTA 升级（绕过 Bot 面板）

当 TG Bot 面板的全网 OTA 按钮不可用，或需要直接对节点下发升级指令时使用。

## 原理
- IP-Sentinel 的每个 Agent 监听 HTTPS 端口，所有指令通过 HMAC-SHA256 签名鉴权
- PSK（预共享密钥）= `CHAT_ID`（来自 master.conf）
- 签名格式：`hmac_sha256(CHAT_ID, "<path>:<unix_timestamp>")` → hex 字符串
- 防重放：60 秒时间窗口

## Python 脚本（推荐方式）

```python
import hmac, hashlib, time, urllib.request, ssl

CHAT_ID = "<CHAT_ID>"  # 从 /opt/ip_sentinel_master/master.conf 获取
agents = [
    ("acck-tokyo", "<东京_IP>", 33020),
    ("yecaoyun-hk", "<香港_IP>", 42387),
    ("ccs-la1", "<洛杉矶1_IP>", 30910),
]

ctx = ssl._create_unverified_context()
for name, ip, port in agents:
    path = "/trigger_ota"
    ts = str(int(time.time()))
    sign = hmac.new(CHAT_ID.encode(), f"{path}:{ts}".encode(), hashlib.sha256).hexdigest()
    url = f"https://{ip}:{port}{path}?t={ts}&sign={sign}"
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url), context=ctx, timeout=10)
        print(f"✅ {name}: {resp.read().decode()[:80]}")
    except Exception as e:
        print(f"❌ {name}: {e}")
```

## 执行位置
- 签名必须在 **Master 所在服务器** 生成（需要 CHAT_ID 作为 PSK）
- 当前 Master：56idc-la (<洛杉矶2_IP>:42185)
- Agent 连接可用性：Master 可以访问所有 Agent 的 Agent Port（非 SSH Port）

## Alpine 远程执行 Python 的陷阱

在 Alpine SSH 会话中执行 Python 单行命令时：
- ✅ `python3 -c "..."` 可以用于简单语句
- ❌ 多行脚本、嵌套引号 → `ssh` 命令行会吃掉引号或断行
- ✅ **复杂脚本必须先本地写文件，再 `scp` 到服务器执行**
- Alpine 的 `busybox sh` 不支持 `$'...'` 转义语法，`sed -i` 行为与 GNU sed 不同

## 历史使用记录
- 2026-05-11：通过此方法成功触发三个节点（acck-tokyo、yecaoyun-hk、ccs-la1）OTA 升级，所有节点返回 `Action Accepted: trigger_ota`
