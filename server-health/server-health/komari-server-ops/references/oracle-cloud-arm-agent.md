# Oracle Cloud ARM — Komari Agent 部署

## 机型规格
- **类型**：Oracle Cloud Infrastructure (OCI) ARM 实例（Free Tier）
- **位置**：Seoul (ap-seoul-1) / Singapore (ap-singapore-1)
- **CPU**：Neoverse-N1 (ARM64), 1 core（每实例）
- **RAM**：256MB（每实例。注意：`free -m` 显示宿主机总内存~24GB，但 cgroup 限制是 256MB；用 `cat /sys/fs/cgroup/memory.max` 或 `cat /proc/meminfo` 确认实际配额）
- **磁盘**：~974MB squaishfs 根卷（loop 设备，宿主分配的引导卷更大但容器内只见到此挂载点）
- **系统**：Alpine Linux v3.17+
- **虚拟化**：LXC 容器
- **网络**：IPv4 + IPv6

## 部署步骤

### 1. SSH 连接

```bash
sshpass -p '<PASSWORD>' ssh -o StrictHostKeyChecking=no -o PubkeyAuthentication=no \
  -p <PORT> root@<IP> 'command'
```

⚠️ 如果提示 "Too many authentication failures"，加 `-o PubkeyAuthentication=no`。

### 2. 安装依赖（Alpine）— 然后运行面板安装命令

```bash
apk update && apk add curl bash wget
```

### 3. 在 admin 面板添加节点 + 获取安装命令

1. 登录 https://<监控面板域名>/admin （用户名 admin）
2. 点击 "Add" → 输入节点名称（如 "Oracle | 首尔" 或 "Oracle | 新加坡"）
3. 新节点出现在列表最下方，点击该节点的 "Install command" 按钮
4. 复制生成的安装命令（含唯一 token）

### 4. 在目标机器上运行安装命令

```bash
# ⚠️ 复制面板生成的命令，不要手动拼 token！
wget -qO- https://raw.githubusercontent.com/komari-monitor/komari-agent/refs/heads/main/install.sh | bash -s -- -e https://<监控面板域名> -t <TOKEN>
```

**此脚本在 Alpine LXC 上工作正常**（会检测 init 系统为 OpenRC 并自动配置服务）。无需手动下载二进制。如果 Alpine 缺 wget，先 `apk add curl bash wget`。

### 5. 验证

- admin 面板节点列表出现 IP 地址和版本号
- `/api/nodes` 返回含新节点 uuid 的条目
- 节点卡片出现在 <监控面板域名> 主页

## 坑

- `free -m` 在 LXC 容器内显示宿主机内存，不是容器配额！务必用 `cat /sys/fs/cgroup/memory.max` 或 `cat /proc/meminfo | head` 查 MemTotal
- region 自动检测基于 IP 归属。Seoul → 🇰🇷，Singapore → 🇸🇬
- ARM64 二进制与 amd64 不同，install.sh 会自动下载正确架构
- Alpine 无 sudo/systemd，install.sh 会自动检测 OpenRC 并配置服务
- Oracle 免费 ARM 实例总配额：4 核 24GB 内存。可以创建多个实例，每个实例配额不限，总和不超过总配额
- 多个实例即使分布在不同地区（如 Seoul + Singapore），共享同一个免费层配额
