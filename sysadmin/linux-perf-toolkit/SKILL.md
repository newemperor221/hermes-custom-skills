---
name: linux-perf-toolkit
description: "Linux 性能分析工具箱 — USE 方法论、top/vmstat/iostat/strace/perf 实战、OOM 排查、CPU/内存/IO/网络四维诊断。触发：\"性能\"、\"卡顿\"、\"OOM\"、\"load高\"、\"io wait\"、\"内存泄漏\"、\"CPU 100%\"。"
tags: [performance, linux, profiling, debugging, oom, cpu, memory, io]
---

# Linux 性能分析工具箱

## USE 方法论（Utilization / Saturation / Errors）

| 资源 | Utilization | Saturation | Errors |
|------|-------------|------------|--------|
| CPU | `top` %CPU | `vmstat` r 列 | `perf stat` |
| 内存 | `free` used% | `vmstat` si/so | `dmesg` OOM |
| 磁盘 | `iostat` %util | `iostat` avgqu-sz | `smartctl` |
| 网络 | `sar -n DEV` | `ss -s` | `netstat -s` |

## 参考文件

- [`references/lxc-performance-comparison.md`](references/lxc-performance-comparison.md) — 三台 LXC 并发性能对比实录，含 ROTA 检测、跨服诊断命令
- [`references/server-benchmark-comparison.md`](references/server-benchmark-comparison.md) — NodeQuality 跑分解读 + 对标基准测试命令（dd/fio/Python）+ 对比分析骨架。触发：用户分享跑分链接要求对比时加载

## 快速诊断流程

### Step 1: 整体概览
```bash
# 负载 + 运行时间 + 用户数
uptime
# 输出: 14:23:01 up 45 days, load average: 45.20, 32.10, 18.50
# load avg > CPU 核心数 = 饱和

# CPU 核心数
nproc  # 或 lscpu | grep "^CPU(s)"

# 内存
free -h
# 关注: available（可用）, swap used（交换区使用）

# 磁盘
df -h
# 关注: Use% > 80% 需要清理
```

### Step 2: 谁在消耗资源？
```bash
# CPU Top 10
top -b -n 1 -o %CPU | head -20
# 或
ps aux --sort=-%cpu | head -11

# 内存 Top 10
ps aux --sort=-%mem | head -11

# 磁盘 IO Top
iotop -aoP -n 1 -b | head -20
# 或
pidstat -d 1 3
```

### Step 3: 是 CPU 密集还是 IO 密集？
```bash
vmstat 1 5
# 关注:
#   r (run queue) > CPU 核心数 → CPU 饱和
#   b (blocked) > 0 → IO 等待
#   wa (iowait) > 20% → IO 瓶颈
#   us (user CPU) > 80% → 应用 CPU 密集
#   sy (system CPU) > 30% → 内核开销大
```

### Step 4: 深入分析

#### CPU 分析
```bash
# 进程级 CPU 使用
pidstat -u 1 5

# 系统调用分析
strace -c -p <PID> -e trace=all  # 统计系统调用
strace -p <PID> -c -S time        # 按耗时排序

# CPU 性能计数器
perf top -p <PID>                  # 实时热点函数
perf record -g -p <PID> -- sleep 30  # 采样 30 秒
perf report                        # 查看报告

# 火焰图
perf record -F 99 -g -p <PID> -- sleep 30
perf script | stackcollapse-perf.pl | flamegraph.pl > flame.svg
```

#### 内存分析
```bash
# 详细内存使用
cat /proc/meminfo
# 关注: MemAvailable, Buffers, Cached, SwapUsed

# 进程内存详情
pmap -x <PID> | tail -1
# 或
cat /proc/<PID>/status | grep -E "VmRSS|VmSize|VmSwap"

# 内存泄漏检测
valgrind --leak-check=full ./myapp  # 需要编译时带调试信息

# slab 内存（内核对象缓存）
slabtop -s c

# OOM 历史
dmesg | grep -i "oom\|killed process"
journalctl -k | grep -i oom
```

#### 磁盘 IO 分析
```bash
# 磁盘利用率
iostat -xz 1 5
# 关注:
#   %util > 80% → 磁盘饱和
#   await > 10ms (SSD) 或 > 20ms (HDD) → 延迟高
#   avgqu-sz > 1 → 队列积压

# 文件系统 IO
iotop -aoP

# 特定进程 IO
pidstat -d 1 5 -p <PID>

# 文件访问追踪
strace -e trace=open,read,write -p <PID>
```

#### 网络分析
```bash
# 连接统计
ss -s
# 关注: timewait 数量, established 数量

# 带宽使用
sar -n DEV 1 5
# 或
iftop -nNP

# 丢包/错误
netstat -s | grep -E "error|drop|retransmit"
# 或
cat /proc/net/snmp | grep -E "Tcp:|Udp:"

# TCP 重传（网络质量问题）
ss -ti state established | grep retrans
```

## OOM 排查流程

```bash
# 1. 确认 OOM 事件
dmesg | grep -i "oom\|killed"
journalctl -k --since "1 hour ago" | grep -i oom

# 2. 查看被杀进程
# dmesg 输出: Out of memory: Kill process 12345 (java) score 800

# 3. 分析内存使用趋势
# 安装: apt install sysstat
sar -r ALL -s $(date -d '1 hour ago' '+%H:%M:%S')

# 4. 检查内存泄漏
# 对比进程 RSS 变化
while true; do
  ps -p <PID> -o pid,rss,vsz,comm
  sleep 60
done > mem_trend.log

# 5. 检查是否有大页/缓存占用
cat /proc/meminfo | grep -E "HugePages|Cached|Buffers|Slab"

# 6. 临时缓解
# 调低 swappiness
sysctl vm.swappiness=10
# 设置 OOM score 调整
echo -1000 > /proc/<PID>/oom_score_adj  # 保护关键进程
```

## 高频场景速查

### load 高但 CPU 不高
→ 通常是 IO 等待。检查 `vmstat` 的 `wa` 列和 `iostat` 的 `%util`。

#### 区分 CPU 负载 vs IO 负载
load average 包含三种任务：
- **Running (r)** — 正在使用 CPU，占 `us+sy`
- **Uninterruptible sleep (D)** — 等待 IO 完成，占 `wa`
- 当 load 远高于 CPU% 时，一定是 IO 负载积压

```bash
# 查看 run queue + blocked 进程
vmstat 1 3
# r 列 = running，b 列 = blocked（IO 等待）
# 如果 b > 0 且 wa > 0，就是 IO 瓶颈
```

### LXC 容器性能诊断的特殊性

LXC 共享宿主内核，CPU 指标解读与 KVM 不同：

| 指标 | LXC 含义 | KVM 含义 |
|------|---------|---------|
| **sy**（system） | 可能含邻居容器开销，无法区分 | 纯自己的内核调用 |
| **si**（softirq） | 网络中断处理，邻居流量也会体现在你这里 | 自己的网络中断 |
| **st**（steal） | LXC 不暴露 steal（无此指标） | 明确表示被超卖抢走 |
| **wa**（iowait） | 共享宿主的磁盘 IO 竞争 | 自己的磁盘 IO |

**LXC 下判断邻居在搞事：**
- sy 持续 >40% 但没有对应进程 → 可能是邻居
- si >10% 但网络流量低 → 邻居在跑大量网络操作
- 高负载 + 高 sy + 高 si = 母鸡超卖典型症状

### 磁盘类型检测（HDD vs SSD）

```bash
# 检查磁盘是否为机械盘（ROTA=1=HDD, ROTA=0=SSD）
cat /sys/block/vda/queue/rotational
# 如果是 loop 设备，检查物理盘:
lsblk -d -o NAME,ROTA | grep -v loop

# 如果 ROTA=1（HDD），低价 LXC 玩具机通病
# 症状: 空载时 50% iowait + 负载虚高
# 注意: 刚开机时的 iowait 瞬高可能是系统初始化读盘，等几分钟再看
```

### 跨服务器横向对比

同时对比多台服务器的 CPU/负载/IO，每台执行相同命令：

```bash
# 标准诊断命令集（并发执行）
ssh server1 'top -bn1 | head -5; cat /proc/loadavg; grep "cpu " /proc/stat; cat /sys/block/*/queue/rotational; free -m; cat /proc/uptime'
# 然后对 server2、server3 执行同样的命令
# 对比关键指标: %id / %wa / %si / %st / loadavg / ROTA
```

核心关注点对比：
| 关注点 | 好 | 差 |
|--------|----|----|
| 空闲(id) | >30% | <10% |
| I/O wait(wa) | <5% | >20% |
| 软中断(si) | <5% | >10% |
| 磁盘 ROTA | 0 (SSD) | 1 (HDD) |
| 负载/核心 | <1.0 | >3.0 |

### CPU 100% 但应用不慢
→ 可能是 GC（Java）、死循环、或者后台任务。用 `top -H -p <PID>` 看线程级 CPU。

### 内存持续增长
→ 内存泄漏。用 `valgrind`（C/C++）或 `tracemalloc`（Python）或 `--inspect`（Node.js）。

### 间歇性卡顿
→ 通常是 GC pause、IO spike、或 cron job 抢占资源。用 `sar` 看历史趋势。

### 网络慢但带宽够
→ TCP 重传、DNS 解析慢、或连接池耗尽。用 `ss -ti` 看重传，`dig` 测 DNS。
