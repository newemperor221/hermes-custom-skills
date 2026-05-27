# Alpine Linux 网络调试补充

Alpine 容器/最小化环境缺少标准工具，替代方案：

## 查看监听端口

```bash
# Alpine 没有 ss，用 /proc/net/tcp
cat /proc/net/tcp
cat /proc/net/tcp6

# 端口是十六进制，0211 = 52137
# 0.0.0.0:port 表示监听所有接口
```

或者：
```bash
apk add iproute2   # 装 ss
apk add net-tools  # 装 netstat
```

## Alpine 用 OpenRC，不是 systemd

```bash
rc-service sshd restart   # 重启服务
rc-status                  # 查看服务状态
rc-update add sshd default  # 开机启动
```

## 快速装网络工具

```bash
apk add iproute2 net-tools tcpdump iptables iptables-openrc
```

## 防火墙（iptables）

Alpine 默认无防火墙规则，是全放通状态。如需加规则：
```bash
apk add iptables iptables-openrc
iptables -A INPUT -p tcp --dport 52137 -j ACCEPT
iptables-save > /etc/iptables/rules-save
rc-update add iptables default
```
