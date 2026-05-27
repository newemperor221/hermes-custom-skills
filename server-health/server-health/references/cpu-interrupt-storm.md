# CPU 中断风暴诊断

> 适用于：1 核 LXC 容器、cloudflared 隧道环境、低配 VPS
> 典型症状：负载 3~13 但 CPU 空闲仍有 40%+，不卡但数字吓人

## 识别公式

```
中断风暴嫌疑判定：
  %idle > 30%  AND  %sy > 20%  AND  load > (core_count × 3)
  → 大概率是中断风暴，非 CPU 饱和
```

**正常值：** `in < 5000/s`, `%sy < 10%`, `load ≈ core_count × 0.3~0.7`

## 根因

| 贡献者 | 原理 | 典型影响 |
|--------|------|---------|
| cloudflared | tun/tap + TLS 加密，每次包都触发系统调用→virtio 中断 | +50%~100% 中断 |
| LXC virtio 驱动 | 网络/磁盘请求都要经过宿主机内核→容器内核两次中断 | +20%~50% 中断 |
| komari agent | 定期探针 → 网络 I/O，频率越高中断越多 | +5%~20% 中断 |
| 宿主机 CPU 太老 | E5-2670 v2 (2013) 中断处理能力远不如现代 CPU | 阈值效应 |

## 诊断命令集

```bash
# 1. 快速定位：CPU 空闲 + 系统 CPU 占比
top -bn1 | head -3 | grep '%Cpu'

# 2. 中断频率（关键指标）
vmstat 1 3 | tail -3 | awk '{print "中断/s:", $11, " 上下文切换/s:", $12}'

# 3. 中断来源分布
cat /proc/interrupts | grep -E "virtio|eth" | head -10

# 4. 进程累计 CPU 时间（区分长期消耗 vs 突发）
for pid in $(pgrep -f "cloudflared|komari|webhook|tg_master"); do
    name=$(ps -p $pid -o comm= 2>/dev/null)
    cpu=$(ps -p $pid -o cputime= 2>/dev/null)
    elapsed=$(ps -p $pid -o etimes= 2>/dev/null)
    echo "$name (PID $pid): CPU=$cpu, uptime=${elapsed}s"
done

# 5. I/O 确认（不是磁盘问题）
iostat -x 1 2 | tail -5

# 6. 一键结论
echo "Load: $(cat /proc/loadavg | cut -d' ' -f1-3)"
echo "Interrupts/s: $(vmstat 1 2 | tail -1 | awk '{print $11}')"
echo "Context switches/s: $(vmstat 1 2 | tail -1 | awk '{print $12}')"
```

## 输出解读

```
=== 健康服务器参考值 ===
中断/s:       1,000 ~ 5,000     ← 正常
上下文切换/s:  5,000 ~ 10,000   ← 正常
%sy:          5% ~ 10%          ← 正常

=== 56idc 无聊云实测值 ===
中断/s:       101,243           ← 异常 (20× 正常)
上下文切换/s:  328 → 23,000      ← 偏高
%sy:          39%               ← 异常 (4× 正常)
负载:         13.26 / 6.36      ← 虚高
%idle:        43%               ← CPU 其实不饱和
```

## 是否要处理

| 情况 | 建议 |
|------|------|
| 服务正常运行，不卡 | 忽略。中断风暴影响的是"看起来很吓人"，实际不影响功能 |
| 服务偶尔卡顿 | 降低 cloudflared 探测频率，或减少 komari agent 上报间隔 |
| 服务频繁超时 | 换宿主机或迁移到非 LXC 环境 |
| 你想知道真相 | 告诉别人"这不是 CPU 不够用，是虚拟化中断太多" |

## 关联

- cloudflared 运行时长越长，中断累计值越大
- LXC 容器比 KVM 虚拟机更容易出现此现象（多一层虚拟化）
- E5 v2/v3 系列宿主机上此问题尤为明显
