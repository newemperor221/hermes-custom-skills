# stat.357561.xyz 部署架构确认 — 2026-05-04

## 正确架构

```
用户浏览器 → Cloudflare DNS (104.21.1.221) → cloudflared 隧道 → 107.172.231.70:45774 komari
```

stat.357561.xyz **就是** 56idc 服务器上本地 komari 的 cloudflared 隧道出口。DNS 指向 Cloudflare 边缘 IP 是因为 cloudflared 隧道协议本身走 Cloudflare 基础设施，不代表部署在 Cloudflare Pages 上。

## 关键发现

```bash
# 服务器 komari 实际监听 45774，不是 25774
ssh -p 52137 root@107.172.231.70 "ss -tlnp | grep komari"
# → /opt/komari/komari server -l 0.0.0.0:45774

# 本地 curl 端口 45774 返回完整主题（48637字节）
ssh -p 52137 root@107.172.231.70 "curl -s localhost:45774/ | wc -c"
# → 48637

# 端口 25774 返回 1940 字节（komari 默认重定向前缀页）
ssh -p 52137 root@107.172.231.70 "curl -s localhost:25774/ | wc -c"
# → 1940

# 外部访问 stat.357561.xyz 返回 48199 字节（与 45774 接近，差异为 gzip）
curl -s https://stat.357561.xyz/ | wc -c
# → 48199

# cloudflared 代理端口
ssh -p 52137 root@107.172.231.70 "ss -tlnp | grep cloudflared"
# → 127.0.0.1:20242 ← cloudflared 监听，转发给 komari
```

## 教训

**不要用端口 25774 硬编码判断**。komari 重启后可能换端口。正确姿势：

```bash
# 第一步：确认 komari 实际端口
ssh -p 52137 root@107.172.231.70 "ss -tlnp | grep komari"

# 第二步：对比主题文件 hash
ssh -p 52137 root@107.172.231.70 "md5sum /opt/komari/data/theme/NodeGetGlass/dist/index.html"
curl -s https://stat.357561.xyz/ | md5sum

# 第三步：只有 hash 匹配才说明是同一份文件
```

## 后续修复记录（2026-05-04）

### 表格列挤

**症状**：表格视图列宽太窄，CPU/内存/磁盘等数据挤在一起。

**修复（已验证）**：
```css
.table-view { padding: 0 2rem; }
.table-header, .table-row {
  grid-template-columns: 44px 1fr 100px 90px 90px 90px 110px 100px;
  gap: 6px;
  padding: 8px 12px;   /* header */
  padding: 10px 12px;  /* row */
}
```

### 导航栏登录按钮

在 navbar-actions 末尾添加，链接到 `https://stat.357561.xyz/admin`（注意不是 mon.357561.xyz）。

### 诊断：字节数对比法

```bash
# 本地 komari
ssh -p 52137 root@107.172.231.70 "curl -s localhost:45774/ | wc -c"
# → 48637（完整主题）

# 外部隧道访问
curl -s https://stat.357561.xyz/ | wc -c
# → 48199（gzip 压缩差异，正常）

# 如果外部返回 ~1940：komari 端口已变，隧道还连着旧端口
```

> **不需要重启 komari**：主题文件是按需读取的，SCP 推送后直接生效。
