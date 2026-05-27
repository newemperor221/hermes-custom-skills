# LXC vs KVM — 探针/监控节点选型对比

## 核心区别（对探针工作负载）

| 维度 | LXC | KVM |
|------|-----|-----|
| 内核开销 | 共享宿主内核，**0 额外内存** | 独立内核，占 ~100-200MB RAM |
| CPU 隔离 | ❌ 共享时间片，邻居干扰表现为 sy/si | ✅ 独立 vCPU，邻居干扰表现为 st（steal time） |
| I/O 隔离 | ❌ 母鸡 HDD 慢，所有容器一起卡 | ⚠️ 有 IOPS 限制，但便宜鸡不设 |
| 最低配置 | 512MB / 1G 磁盘可跑探针 | 至少 1G RAM / 5G 磁盘 |
| 成本 | 低（¥10/年） | 高 |
| 启动速度 | 秒级 | 分钟级 |

## 对探针的影响

探针（komari agent / nodeget agent / ip_sentinel）资源消耗极低（~40MB 内存，<1% CPU），所以：

- **LXC 完全够用**，且更省资源
- **KVM 不会更好**，因为探针不需要独立内核
- **真正重要的是母鸡的磁盘类型（SSD vs HDD），不是虚拟化类型**

## 邻居干扰的显示方式

| 场景 | LXC top 显示 | KVM top 显示 |
|------|-------------|-------------|
| 母鸡正常 | 正常 | 正常 |
| 母鸡 CPU 超卖 | sy + si 虚高（**分不清**是自己还是邻居） | st 上升（**看得见**被抢了多少） |
| 母鸡 HDD 慢 | wa 飙升（I/O wait） | wa 飙升（一样） |

## 诊断方式

### 确定虚拟化类型
```bash
# LXC 特征：/proc/1/cgroup 包含 lxc 或 /proc/1/environ 没有 KVM 特征
cat /proc/1/cgroup | grep -i lxc || echo "not LXC"
# KVM 特征：有 virtio 设备
ls /sys/bus/virtio/devices/ 2>/dev/null && echo "KVM (virtio detected)"
# 通用检测
systemd-detect-virt 2>/dev/null  # 输出 "lxc" 或 "kvm"
```

### 区分 CPU 高负载类型

```bash
top -bn1 | head -5
```

| 特征 | 诊断 | 建议 |
|------|------|------|
| us>50% | 用户进程吃 CPU | 看 `ps aux --sort=-%cpu` 找进程 |
| sy>30%, id>20%, wa<2% | 网络/服务型负载 | 面板机正常，探针异常则排查 cron/脚本 |
| id≈0%, wa>30% | **HDD I/O 瓶颈** | ROTA=1 确认，软件无法解决，换 SSD |
| st>10% | KVM 被邻居偷 CPU | 换母鸡或升配置 |
| si>10% | 软中断密集 | 网络 I/O 多的服务正常，可忽略 |

### 磁盘类型确认（最重要）

```bash
lsblk -d -o NAME,ROTA,SIZE
# ROTA=0 = SSD/NVMe
# ROTA=1 = HDD（机械盘）
```

## 选型建议

### 面板主控（Komari server / Prometheus / Grafana）
→ **KVM 或给足资源的 VPS**（>1G RAM, SSD 磁盘）
理由：面板服务对磁盘 I/O 敏感、需要稳定持久化、独立内核故障恢复更可靠

### 纯探针节点（komari agent / nodeget agent）
→ **LXC 即可**，越便宜越好
理由：探针就是静态二进制 + 轻量脚本，LXC 的零额外开销正是优势

### IPv6-only 探针
→ **LXC 首选**
理由：IPv6 NAT 一般在 LXC 环境更常见且便宜（如 56idc 玩具 LXC 提供 HE IPv6 Tunnel）
注意：需要从有 IPv6 的中转机跳转 SSH（如通过 DediRock 155.94.180.55）
