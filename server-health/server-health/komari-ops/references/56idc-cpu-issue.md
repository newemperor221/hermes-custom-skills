# 56idc LXC 高 CPU 占用（2026-05-04）

## 症状
- 容器 CPU 占用长时间在 30 以上（1核 CPU，负载 4-7）
- `top` 显示 system CPU 高，进程本身（cloudflared/komari/agent）占用正常

## 根因
LXD 宿主机上的 **gost agent**（LXD 容器管理 agent，pid 每批不同）每 5 秒尝试将 `/run/systemd/unit-root/` 以 `rw, rbind` 挂载，被 AppArmor 拒绝（`profile=lxd-lxd114513961742`），内核将 audit 日志写入容器的 dmesg，每分钟约 1200 条。

这些内核日志写入操作算在容器 CPU 里，属于**宿主机问题容器买单**。

## 证据
```
[3499131.500508] audit: type=1400 audit(...): apparmor="DENIED" operation="mount" class="mount"
  profile="lxd-lxd114513961742" name="/run/systemd/unit-root/" pid=4112480 comm="(gost)"
```
- 间隔约 5 秒/条
- `pid` 每次不同（gost 是 fork+exec 模式）
- `comm="(gost)"` 和 `comm="(ionclean)"` 两种进程名

## 容器内尝试过的解法（均失败）
| 尝试 | 结果 | 原因 |
|------|------|------|
| `sysctl -w kernel.printk_ratelimit=30` | Permission denied | 容器无 sysctl 权限 |
| `echo N > /proc/sys/kernel/printk` | No such file | 容器无此接口 |
| `dmesg -c` 清缓冲 | 临时有效，重来 | 不阻止新日志产生 |
| `apt-get purge auditd` | 未安装 | 不是 auditd 的问题 |

## 真正解法
联系 **56idc 客服**（宿主机管理员）：
1. 在宿主机上停止 gost agent 对该容器的挂载尝试
2. 或在宿主机修改 AppArmor 策略：`aa-complain lxd-lxd114513961742`
3. 或在宿主机 `lxc.apparmor.profile = unconfined`（不推荐，安全风险大）

## 受影响服务器
- 56idc LXC（<洛杉矶2_IP>，端口 52137）
- Komari cloudflared 隧道（mon.357561.xyz）不受影响，只是隧道出口
