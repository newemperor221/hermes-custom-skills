# 服务器基准对比 & NodeQuality 解读

## 场景

用户分享 NodeQuality / 类似跑分链接，要求对比「那台 vs 我们这台」的性能差异。

## 流程

### 1. 获取 NodeQuality 数据

打开链接后：
- 基本 Tab：CPU 型号、核心数、内存、磁盘、GB5 单核/多核
- IP质量 Tab：IP 类型、风险分、流媒体解锁（Netflix/ChatGPT/TikTok 等）
- 网络质量 Tab：三网延迟、丢包率
- 回程路由 Tab：路由路径

### 2. 获取本机（Hermes Agent 宿主）规格

```bash
# CPU
cat /proc/cpuinfo | grep "model name" | head -1
nproc

# 内存
free -h

# 磁盘
lsblk -d -o NAME,SIZE,ROTA,MODEL
cat /sys/block/vda/queue/rotational   # 0=SSD, 1=HDD

# 内核
uname -a
```

### 3. 对标基准测试命令

当用户问「我们这台」时，**指的就是 Hermes Agent 运行的宿主机**，不是某个特定服务的服务器。

#### 磁盘测试

```bash
# 顺序写（1M 块）
dd if=/dev/zero of=/tmp/bench.tmp bs=1M count=2048 conv=fdatasync 2>&1 | tail -1

# 随机 4K 写（无 fio 时用 Python 替代）
python3 -c "
import time, os
data = b'x' * 4096
start = time.time()
for i in range(10000):
    with open(f'/tmp/iotest_{i}.tmp', 'wb') as f:
        f.write(data)
elapsed = time.time() - start
print(f'10000 x 4K 写入: {elapsed:.2f}s, {10000/elapsed:.0f} IOPS, {10000*4/1024/elapsed:.1f} MB/s')
for i in range(10000):
    os.remove(f'/tmp/iotest_{i}.tmp')
"

# 有 fio 时
fio --name=randwrite --ioengine=posixaio --direct=1 --bs=4k --size=256m --runtime=15 --rw=randwrite --group_reporting 2>&1 | grep -E "IOPS|WRITE:"
fio --name=randread --ioengine=posixaio --direct=1 --bs=4k --size=256m --runtime=15 --rw=randread --group_reporting 2>&1 | grep -E "IOPS|READ:"

# 清理
rm -f /tmp/bench.tmp /tmp/iotest_*.tmp
```

#### CPU 简易基准

```bash
# 素数计算（100万以内，约8秒）
time python3 -c "
n = 1000000
count = 0
for i in range(2, n):
    for j in range(2, int(i**0.5)+1):
        if i % j == 0:
            break
    else:
        count += 1
print(f'1到{n}的素数: {count}个')
"

# 有 sysbench 时
sysbench cpu run --time=10 2>&1 | grep -E "events per second|total number of events"

# 有 openssl 时
openssl speed sha256 -evp sha256 2>&1 | grep -E "^[0-9]|type"
```

### 4. 对比分析关键维度

| 维度 | NodeQuality 显示 | 本地测试 |
|------|-----------------|---------|
| CPU 核心 | 直接显示 | `nproc` |
| CPU 频率 | 型号含频率 | `cat /proc/cpuinfo` |
| 内存总量 | 直接显示 | `free -h` |
| 磁盘容量 | 直接显示 | `lsblk` |
| 磁盘顺序IO | SEQ1M/Q1 (MB/s) | `dd bs=1M` |
| 磁盘随机IO | RND4K/Q1 (IOPS) | fio / Python |
| GB5 分数 | 单核+多核 | 无直接对比项，用素数计算/openssl 作参考 |

### 5. NodeQuality 结果常见解读陷阱

- **GB5 单核 vs 多核可能显示异常**：某些环境下单核分 > 多核分可能是截图/显示错误，或者测试环境受限
- **磁盘 ROTA 误报**：KVM virtio 有时 ROTA=1 但实际性能是 SSD（顺序写 >400MB/s 一定是 SSD）
- **IP 质量**：数据中心 IP 的 AbuseIPDB 风险分通常很高（>90），但实际使用没问题
- **服务器位置**：NodeQuality 的时间戳和时区可推断实际机房位置

## 对比报告骨架

```
## 对比：{机器A} vs {机器B}

### 基础规格

| 项目 | {A} | {B} |
|------|-----|-----|

### CPU 性能

### 磁盘性能

### 综合结论
| 维度 | 差异 |
|------|------|
| 🏆 CPU | ... |
| 🏆 磁盘 | ... |
| 🏆 内存 | ... |
```
