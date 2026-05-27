# DediRock IPv6 跳板代理部署（将军鸡接入方案）

**2026-05-08**

## 背景

将军鸡（欢乐云 NAT 小鸡）只有 IPv6 `2001:470:e2db:100:0:5459:389:6b27`，无法直接访问 56idc-la 的 komari server（IPv4-only + cloudflared IPv4 tunnel）。56idc-la 的 IPv6 是 ULA 私地址（`fd42:...`），公网不可达。

DediRock 洛杉矶有公网 IPv6 `2607:9d00:2000:1e6::d2f1:4f14`，能同时连通将军鸡和 56idc-la，适合做 IPv6→IPv4 跳板。

## 网络路径

```
将军鸡(IPv6) → DediRock(IPv6:25775) → TCP forward → 56idc-la(IPv4:25774)
```

## DediRock 上部署代理

### 1. 创建代理脚本

```bash
ssh -p 58193 root@155.94.180.55 "cat > /tmp/proxy.py << 'PYEOF'
import socket, threading

listen_host = '::'
listen_port = 25775
target_host = '107.172.231.70'
target_port = 25774

def pipe(src, dst):
    try:
        while True:
            data = src.recv(4096)
            if not data: break
            dst.sendall(data)
    except: pass
    finally:
        try: src.close()
        except: pass
        try: dst.close()
        except: pass

def handler(client_sock, client_addr):
    try:
        target_sock = socket.create_connection((target_host, target_port), timeout=10)
        t1 = threading.Thread(target=pipe, args=(client_sock, target_sock), daemon=True)
        t2 = threading.Thread(target=pipe, args=(target_sock, client_sock), daemon=True)
        t1.start(); t2.start()
    except Exception as e:
        client_sock.close()

s = socket.socket(socket.AF_INET6, socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((listen_host, listen_port))
s.listen(50)
print(f'Listening on [{listen_host}]:{listen_port} -> {target_host}:{target_port}')
while True:
    cli, addr = s.accept()
    threading.Thread(target=handler, args=(cli, addr), daemon=True).start()
PYEOF"
```

### 2. 启动代理（后台运行）

```bash
ssh -p 58193 root@155.94.180.55 "cd /tmp && python3 proxy.py &"
# 或用 nohup
ssh -p 58193 root@155.94.180.55 "nohup python3 /tmp/proxy.py > /tmp/proxy.log 2>&1 &"
```

### 3. 验证端口监听

```bash
ssh -p 58193 root@155.94.180.55 "ss -tlnp | grep 25775"
# 预期: LISTEN 0 50 *:25775 *:* 或类似输出
```

### 4. 验证 DediRock 能通 56idc-la:25774

```bash
ssh -p 58193 root@155.94.180.55 "curl -s --connect-timeout 5 http://107.172.231.70:25774"
# 预期: 返回 404 或 JSON（komari API 响应）
```

### 5. 验证将军鸡能连通 DediRock IPv6

将军鸡上执行：
```bash
timeout 5 bash -c 'echo > /dev/tcp/[2607:9d00:2000:1e6::d2f1:4f14]/25775' && echo '通'
```

## 将军鸡上重装 komari-agent

将军鸡 IPv6-only，参照 nodeseek 朝鲜探针教程：

```bash
# 卸载旧 agent
pkill komari-agent
rm -f /etc/init.d/komari-agent  # 或对应的 init script

# 重新安装，指向 DediRock IPv6 跳板
wget -qO- https://raw.githubusercontent.com/komari-monitor/komari-agent/refs/heads/main/install.sh | bash -s -- \
  -e "http://[2607:9d00:2000:1e6::d2f1:4f14]:25775" \
  -t f00d9d5eaf26a34124b6b14ac278f6b6 \
  --disable-web-ssh
```

## 连通性验证

| 路径 | 测试命令 | 预期 |
|------|---------|------|
| DediRock → 将军鸡 | `ping -6 -c 2 2001:470:e2db:100:0:5459:389:6b27` | 0% loss |
| 将军鸡 → DediRock | `timeout 5 bash -c 'echo > /dev/tcp/[2607:9d00:2000:1e6::d2f1:4f14]/25775'` | 通 |
| DediRock → 56idc-la | `curl -s http://107.172.231.70:25774` | 有响应 |
|将军鸡 → DediRock:25775 | `curl -s http://[2607:9d00:2000:1e6::d2f1:4f14]:25775/api/heartbeat` | komari响应 |

## 注意

- DediRock 自己的 komari server 占着 25774，代理用 25775
- komari WebSocket 连接走 HTTP（不是 HTTPS），不需要证书验证
- 如果代理脚本需要重启，`pkill -f proxy.py` 后重新 `nohup python3 /tmp/proxy.py &`
