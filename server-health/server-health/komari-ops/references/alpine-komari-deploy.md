# Alpine Linux 部署 Komari Server

## 回答：Alpine 可以装 komari

komari 1.2.0（May）在 Alpine Linux 3.22.2 LXC 上**稳定运行**（hash:567d2b6），之前记录 1.2.0 SIGSEGV 有误。

## 环境

- 服务器：107.172.231.70（**Alpine Linux 3.22.2**，LXC 容器，SSH 42185）
- SSH 密码：`Y@BU1%wmP#xFs8bK`
komari 版本：1.2.0（working，43MB，May）
- komari 端口：25774
- 初始化系统：OpenRC（容器内）

## ⚠️ komari 版本选择（关键）

| 版本 | 大小 | 日期 | Alpine 可用 |
|------|------|------|-------------|
| 1.1.9 | ~31MB | March | ✅ 稳定运行 |
| 1.2.0 | ~43MB | May | ❌ SIGSEGV |

**komari 1.2.0** 在 Alpine 上稳定运行。

## ⚠️ GitHub 下载 URL 正确格式

```bash
# ✅ 正确（无 v 前缀）
wget https://github.com/komari-monitor/komari/releases/download/1.1.9/komari-linux-amd64

# ❌ 错误（多了 v 前缀，404）
wget https://github.com/komari-monitor/komari/releases/download/v1.1.9/komari-linux-amd64
```

## komari server 正确启动参数

```bash
# ✅ 正确：-l :port（listen）
nohup /opt/komari/komari server -l :25774 -d /opt/komari/data/komari.db > /var/log/komari.log 2>&1 &

# ❌ 错误：-e 不存在
/opt/komari/komari server -e http://:25774
```

## 安装步骤（Alpine 3.22）

### 1. 下载 komari 1.1.9

```bash
sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@107.172.231.70
mkdir -p /opt/komari/data
cd /tmp
curl -fsSL https://github.com/komari-monitor/komari/releases/download/1.1.9/komari-linux-amd64 -o komari
chmod +x komari
mv komari /opt/komari/komari
```

### 2. 启动（nohup，不能用 init 脚本）

```bash
# Alpine OpenRC 的 start-stop-daemon 无法 exec 某些二进制，直接 nohup 拉
nohup /opt/komari/komari server -l :25774 -d /opt/komari/data/komari.db > /var/log/komari.log 2>&1 &

# 验证
sleep 3
ps aux | grep 'komari server' | grep -v grep
curl -s http://127.0.0.1:25774/api/login -X POST -H 'Content-Type: application/json' -d '{"username":"admin","password":"Komari@2026"}'
```

### 3. 验证运行

```bash
ps aux | grep komari | grep -v grep
# 应该看到：/opt/komari/komari server -l :25774 ...

curl -s --max-time 3 http://127.0.0.1:25774/api/login -X POST \
  -H 'Content-Type: application/json' \
  -d '{"username":"admin","password":"Komari@2026"}'
# 返回 {"status":"success"...} 即成功
```

### 4. 设置开机自启（可选）

Alpine OpenRC init 脚本有 bug，建议用 cron @reboot 或直接 nohup 放到 /etc/local.d/：
```bash
cat >> /etc/local.d/komari.start << 'EOF'
nohup /opt/komari/komari server -l :25774 -d /opt/komari/data/komari.db > /var/log/komari.log 2>&1 &
EOF
chmod +x /etc/local.d/komari.start
rc-update add local
```

## 坑

- **Alpine LXC start-stop-daemon bug**：`rc-service komari start` 可能报 crashed 但进程可能已起。用 `ps aux | grep komari` 确认，或直接 nohup。
- **GitHub URL 404**：路径是 `download/1.1.9/`，tag 是 `v1.1.9` 但 URL 里无 v
- **komari 端口 25774**：默认端口，`-l :25774` 指定监听地址
- **SSH 端口**：42185（不是默认 22）
- **komari 1.2.0 SIGSEGV**：不要在 Alpine 上用 1.2.0，必须用 1.1.9
- **komari 二进制路径**：`/opt/komari/komari`（当前 working 1.1.9），`/opt/komari/komari_new`（1.2.0 SIGSEGV 备份）

## cloudflared 配置（已就绪）

```bash
# cloudflared 二进制位置
/tmp/cloudflared          # 进程使用
/usr/local/bin/cloudflared  # 复制备份

# init 脚本
/etc/init.d/cloudflared   # command 指向 /tmp/cloudflared ...

# 启动
/etc/init.d/cloudflared start
rc-service cloudflared status  # Running

# token（token 模式）
eyJhIjoiYzFkMTgwNGNiNTA3NGM2YTYwNGU1NDc0YjZjNTA4MTYiLCJ0IjoiYmE0ZThlYTctZThlMS00MTE1LTg0MGItNjRiODdlMTUyYjg1IiwicyI6IllqRmtOR1l6TW1VdE16WmlOUzAwWXpNNUxUZzBZakV0TldReU1qTTROakk1WWpFMSJ9
```
