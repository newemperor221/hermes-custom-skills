---
name: network-recon
description: "网络侦察与排障 — nmap 扫描、tcpdump 抓包、traceroute 追踪、连通性诊断。触发：\"nmap\"、\"抓包\"、\"tcpdump\"、\"端口扫描\"、\"网络不通\"、\"traceroute\"、\"丢包\"。"
tags: [nmap, tcpdump, network, debugging, traceroute, packet-capture]
---

# 网络侦察与排障

## nmap 扫描

### 快速侦察
```bash
# 快速扫描常用端口（~10秒）
nmap -F -T4 <target>

# 全端口扫描（1-65535，慢但彻底）
nmap -p- -T4 --min-rate 10000 <target>

# 服务版本 + OS 检测
nmap -sV -O -T4 <target>

# 脚本扫描（漏洞+服务信息）
nmap -sC -sV -T4 <target>

# UDP 扫描（DNS/SNMP/53端口）
nmap -sU --top-ports 20 <target>
```

### 隐蔽扫描
```bash
# SYN 半开扫描（不完成握手，不留日志）
nmap -sS -T2 <target>

# 空闲扫描（利用僵尸主机）
nmap -sI zombie_host:port <target>

# 指定源端口（绕过简单防火墙规则）
nmap -g 53 -p 80,443 <target>
```

### 输出格式
```bash
nmap -oN scan.txt <target>      # 正常格式
nmap -oX scan.xml <target>      # XML（可导入）
nmap -oG scan.grep <target>     # Grepable
nmap -oA scan_result <target>   # 所有格式
```

## tcpdump 抓包

### 常用过滤
```bash
# 抓特定主机流量
tcpdump -i eth0 host 10.0.0.5

# 抓特定端口
tcpdump -i eth0 port 443

# 抓 TCP SYN 包（新连接）
tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn) != 0'

# 抓 HTTP GET 请求
tcpdump -i eth0 -A 'tcp port 80 and tcp[((tcp[12:1] & 0xf0) >> 2):4] = 0x47455420'

# 抓 DNS 查询
tcpdump -i eth0 port 53

# 抓包保存为 pcap（可用 Wireshark 打开）
tcpdump -i eth0 -w capture.pcap -c 1000

# 读取 pcap 文件
tcpdump -r capture.pcap -nn

# 限制包大小（只看头部）
tcpdump -i eth0 -s 96 port 80
```

### 高级过滤
```bash
# 抓特定子网
tcpdump -i eth0 net 10.0.0.0/24

# 排除特定主机
tcpdump -i eth0 not host 10.0.0.1

# 组合条件
tcpdump -i eth0 'host 10.0.0.5 and (port 80 or port 443)'

# 只抓 RST 包（连接被拒）
tcpdump -i eth0 'tcp[tcpflags] & (tcp-rst) != 0'

# 抓丢包重传
tcpdump -i eth0 'tcp[tcpflags] & (tcp-syn|tcp-fin|tcp-rst) != 0'
```

## 连通性诊断

### 标准流程
```bash
# 1. 本地网络
ping -c 3 127.0.0.1          # 本地协议栈
ip addr show                  # 接口 IP
ip route show                 # 路由表

# 2. 网关
ping -c 3 <gateway_ip>        # 到网关

# 3. 外部
ping -c 3 8.8.8.8             # 到公网 IP
ping -c 3 google.com          # DNS 解析

# 4. 追踪路由
traceroute -n <target>         # -n 不做 DNS 反查
mtr -n -c 100 <target>        # 持续追踪（更好用）

# 5. DNS 诊断
dig <domain> +short
dig <domain> @8.8.8.8         # 指定 DNS 服务器
nslookup <domain> <dns_server>
```

### mtr 解读
```
Host                   Loss%  Snt   Last   Avg  Best  Wrst
1. gateway              0.0%  100    1.2   1.5   0.8   5.2
2. isp-router           0.0%  100    5.1   5.8   4.2  12.3
3. ???                 100.0%  100    0.0   0.0   0.0   0.0  ← ICMP 被过滤
4. backbone            10.0%  100   15.2  16.1  14.8  25.3  ← 这里丢包
```

## 常见场景速查

### 场景：端口通但服务不响应
```bash
nc -zv <host> <port>           # TCP 连通性
curl -v http://<host>:<port>   # HTTP 层检查
telnet <host> <port>           # 手动交互
```

### 场景：间歇性丢包
```bash
# 持续 ping 记录
ping <target> | while read line; do echo "$(date '+%H:%M:%S') $line"; done > ping.log

# mtr 持续追踪
mtr -n -c 300 --report <target>

# 抓重传包
tcpdump -i eth0 'tcp[tcpflags] & tcp-syn != 0 and tcp[tcpflags] & tcp-ack == 0'
```

### 场景：MTU 问题
```bash
# 测试 MTU
ping -M do -s 1472 <target>    # 1472 + 28(IP+ICMP) = 1500
ping -M do -s 1300 <target>    # 逐步缩小找到可用 MTU
```

## Alpine Linux 最小化环境

Alpine 默认只有最简工具集，标准命令可能不存在。详见 `references/alpine-network-debugging.md`。

## 排错决策树
```
不通？
├── ping 自己通？ → 不通=网卡/协议栈问题
├── ping 网关通？ → 不通=本地网络/交换机
├── ping 公网 IP？ → 不通=ISP/路由问题
├── ping 域名？ → 不通=DNS 问题
├── nc 端口通？ → 不通=防火墙/端口未监听
└── curl HTTP？ → 不通=服务未启动/应用层问题
```
