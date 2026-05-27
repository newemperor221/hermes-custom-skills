---
name: log-search
description: 跨服务器日志搜索工具。触发场景："搜索日志"、"grep 服务器"、"查 error"、"跨服务器找关键词"。
---

# Log Search

跨服务器并行搜索日志关键词。

## 使用方式

```
log-search -k "error"                        # 搜索所有服务器
log-search -k "failed" -s "洛杉矶1,纽约"      # 只搜指定服务器
log-search -k "Connection refused" -l "/var/log/nginx/error.log"  # 指定日志路径
log-search -k "error" -n 100                  # 每服务器最多100条
log-search -k "error" -j                      # JSON输出
```

## 日志路径

默认扫描路径：
- `/var/log/syslog`
- `/var/log/auth.log`
- `/var/log/nginx/access.log` + `error.log`
- `/var/log/apache2/access.log` + `error.log`
- `/var/log/fail2ban.log`

用 `-l` 指定其他路径，可多次使用。

## 服务器配置

同 server-health（洛杉矶1/纽约/洛杉矶2/堪萨斯/亚特兰大）。

## 实现

- paramiko SSHClient，每服务器一条连接
- `grep -rn` 并行搜多个日志文件
- ThreadPoolExecutor 并发所有服务器
- 限制每服务器最大输出行数，避免输出爆炸
