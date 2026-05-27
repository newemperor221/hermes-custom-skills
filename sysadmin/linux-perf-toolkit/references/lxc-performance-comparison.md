# 三台 LXC 性能对比实录

**日期：** 2026-05-12
**场景：** 比较 56idc-la（主控降级为探针）、将军鸡（IPv6-only）、荷兰新机（波兰 LXC）三台 LXC 的 CPU/负载/IO

## 并发采集结果

### 56idc-la（107.172.231.70）— 已运行 4 天
```
top:  13.3% us, 53.3% sy, 20.0% id,  0.0% wa, 13.3% si, 0.0% st
load: 11.43 / 10.33 / 9.05
mem:  488MB total, 45MB used
disk: ROTA=1 (HDD)
uptime: 4 days
services: komari agent（已清理面板/主控/cloudflared）
```
**分析：** sy 53% + si 13% = 内核/网络中断开销巨大。原因为曾是 Komari 面板 + IP Sentinel 主控机。清理后预计大幅下降。

### 荷兰机（31.58.51.127）— 刚开机 23 分钟
```
top:   0.0% us,  0.0% sy, 100% id,  0.0% wa, 0.0% si, 0.0% st
load:  3.56 / 3.41 / 3.00
mem:   488MB total, 22MB used
disk:  ROTA=1 (HDD)
uptime: 23 min
```
**分析：** 空载 100% 空闲。开机时曾有 50% iowait（初始读盘），23 分钟后已归零。负载 3.56 是开机残留。

### 将军鸡（2001:470:e2db::2）— 已运行 4.6 天
```
top:  16.7% us, 16.7% sy, 66.7% id,  0.0% wa, 0.0% si, 0.0% st
load:  5.62 / 5.16 / 4.43
mem:  122MB total, 13MB used
disk: 无 ROTA 信息（极小系统）
uptime: 4.6 days
```
**分析：** 最令人意外——66% 空闲，0% iowait。122MB 内存但仅用 13MB（含 komari agent 14MB）。负载高是因资源太小，非性能问题。

## 关键发现

1. **ROTA=1（HDD）不一定等于高 iowait** — 56idc-la 跑满负载仍 0% wa，看母鸡的 IO 竞争程度
2. **刚开机时的 iowait 不可信** — 系统初始化会大量读盘，等 >15 分钟再看
3. **LXC 的 sy+si 可能是邻居的锅** — 56idc-la 的 53% sy + 13% si 在清理后看是否下降
4. **将军鸡 122MB 跑 komari agent 完全够** — 14MB RSS，还有 100MB+ 空闲
5. **硬件健康度排行**：将军鸡 > 56idc-la（清理后） > 荷兰机

## 诊断命令

```bash
# 单行获取所有关键指标
ssh server 'echo "---TOP---"; top -bn1 | head -5; echo "---LOAD---"; cat /proc/loadavg; echo "---CPU---"; grep "cpu " /proc/stat; echo "---DISK---"; cat /sys/block/vda/queue/rotational 2>/dev/null; lsblk -d -o NAME,ROTA 2>/dev/null | grep -v loop; echo "---MEM---"; free -m; echo "---UPTIME---"; cat /proc/uptime'
```
