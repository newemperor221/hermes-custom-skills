# 56idc LXC 磁盘清理记录

**2026-05-04**

## 磁盘现状
- 1.2G 总容量，LXC 容器，无 Docker
- 清理前：64%（731M）
- 清理后：43%（494M）
- 可用：658M

## 清理操作

### 1. apt 缓存
```bash
apt-get clean
rm -rf /var/cache/apt/archives/*.deb
```
释放 ~176M（apt cache）

### 2. /tmp 临时文件
```bash
rm -rf /tmp/nodeget-komari-theme
rm -rf /tmp/nodeget-server
rm -f /tmp/cloudflared_*.log
rm -f /tmp/ng.sh /tmp/ng-install.sh
```
释放 ~15M

### 3. 删除 GCC 编译工具链（关键！）
```bash
apt-get purge -y gcc-12 g++-12 build-essential gcc g++
apt-get autoremove -y
```
**释放 95MB**。这批东西在 LXC 探针上完全没必要——编译在本地做，传二进制过去。

## 教训
- **56idc 只有 1.2G 磁盘**，任何非必要软件包都要谨慎
- build-essential/gcc/g++ 这类工具链**不应安装在探针上**
- 用户原话："有编译任务在你机器上编译了再传过去"
- 监控磁盘占用：`df -h /`

## /usr 目录构成（正常，不必清理）
| 目录 | 大小 | 说明 |
|------|------|------|
| /usr/lib | 229M | 系统库、Python 3.11、GCC |
| /usr/share | 129M | 文档、本地化、vim 配置 |
| /usr/bin | 78M | 系统命令 |
| /usr/local | 28M | 本地软件 |
| /usr/include | 11M | C 头文件 |

这些都是 Debian 基础系统文件，不可删除。
