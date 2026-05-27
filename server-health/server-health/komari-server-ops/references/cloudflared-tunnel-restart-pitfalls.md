# cloudflared 隧道重启陷阱

## 快速重启导致 "no more connections active and exiting"

多次连续重启 cloudflared（kill → start → kill → start 间隔 <5s），隧道会进入无法恢复的状态：

```
ERR no more connections active and exiting
```

所有 4 个 QUIC 连接（connIndex 0-3）注册成功后全部被 cancel。公网访问返回 **530**。

**根因：** Cloudflare edge 缓存隧道连接状态，快速重启导致新旧连接冲突。旧连接的 context 未完全超时，新连接复用同一 token 但 edge 侧的状态机不一致。

**修复步骤：**

1. `kill -9 $(pgrep -f cloudflared) 2>/dev/null`
2. `sleep 5`（关键等待）
3. 确认 `pgrep -f cloudflared` 无输出
4. 重新启动：`nohup cloudflared tunnel --no-autoupdate run --token TOKEN --url http://localhost:25774 > /tmp/cf.log 2>&1 &`
5. 等待 8-12 秒让隧道完成 4 个 QUIC 连接注册
6. 验证：`grep -c "Registered" /tmp/cf.log` → 应为 4
7. 公网验证：`curl -s -o /dev/null -w "%{http_code}" https://<监控面板域名>/` → 200

## --url 标志 vs 无 --url

- 带 `--url http://localhost:25774`：cloudflared 将隧道流量转发到本地 25774 端口（tcp-proxy 或 komari）
- 不带 `--url`：隧道使用 Cloudflare Dashboard 上配置的 ingress 规则。如果 Dashboard 上配置了不同的转发目标，结果可能不一致
- 两种模式不要混用。如果从一种切换到另一种，必须完整 kill + wait + restart

## SSH background 模式 vs nohup 模式

通过 Hermes `terminal(background=true)` 启动 cloudflared 时：
- stdin/stdout/stderr 是 **pipes**，输出被 Hermes process manager 读取
- `process(action='log')` 可以读输出，但如果进程写入速度慢，可能长时间为空

通过 `nohup ... > /tmp/cf.log 2>&1 &` 启动时：
- 输出写入日志文件
- 可以用 `tail -f /tmp/cf.log` 或 `grep` 读取
- 进程与 SSH 会话解耦，SSH 断开后继续运行

**最佳实践：** 需要查看日志时用 nohup + 文件。简单启动不在意日志时用 background 模式。
