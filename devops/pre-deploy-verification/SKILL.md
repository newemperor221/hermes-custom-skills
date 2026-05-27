---
name: pre-deploy-verification
description: 部署前校验三步走——修改 <监控面板域名> 的 HTML/CSS 时，部署前必须执行的语法检查、内容验证、Cloudflare 缓存流程。先在本地/服务器做完校验再通知用户看。
---

# 部署前校验流程

## 适用场景
修改 `<监控面板域名>` 的 HTML/CSS 后部署。有两个部署目标，根据修改的是 **Komari 面板主题**还是 **GG 探针（GalaxyGlass）页面**选择。

## 部署目标

### 目标 A：Komari 面板主题（NodeGetGlass）
- 位置：56idc-la VPS
- SSH：`sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP>`
- 远程路径：`/root/data/theme/GalaxyGlass/dist/index.html`
- 内网验证 URL：`http://127.0.0.1:25774/`
- 对应 `komari` 面板管理页

### 目标 B：GG 探针（GalaxyGlass Astro 版）
- 位置：荷兰主控 VPS
- SSH：`ssh -p 46748 -i ~/.ssh/hermes_admin root@<荷兰_IP>`（⚠️ 密码认证已禁用，必须用密钥）
- 远程路径：`/opt/komari/data/theme/`
- 部署脚本：`/home/woioeow/galaxy-glass/astro/deploy.sh`（一键编译+推送）
- 内网验证 URL：`http://127.0.0.1:25774/`
- 对应 `<监控面板域名>` 探针页面
- **编译后在远程服务器直接用 `curl -s http://localhost:25774/` 验证，不要相信本机 `/opt/komari/data/theme/` 的状态**
- 背景壁纸来自 WebDAV `img.<用户域名>`（drive.<用户域名>），部署后检查壁纸是否正常加载

## 强制三步走

### 第一步：部署前语法检查

在 scp 之前，必须在**服务器上**对当前 index.html 做检查。选择目标 A 或 B 的路径/SSH：

```bash
# 目标 A（Komari 面板）
SERVER="sshpass -p 'Y@BU1%wmP#xFs8bK' ssh -p 42185 root@<洛杉矶2_IP>"
FILE=/root/data/theme/GalaxyGlass/dist/index.html

# 目标 B（GG 探针 GalaxyGlass）
SERVER="sshpass -p 'OX8w$nE9A%tfqb6v' ssh -p 46748 root@<荷兰_IP>"
FILE=/opt/komari/data/theme/index.html

# 1. HTML 标签闭合
OPEN=$($SERVER "grep -c '<html' $FILE 2>/dev/null || echo 0")
CLOSE=$($SERVER "grep -c '</html>' $FILE 2>/dev/null || echo 0")
echo "HTML 标签: $OPEN open / $CLOSE close"

# 2. CSS 花括号平衡
OB=$($SERVER "grep -o '{' $FILE | wc -l")
CB=$($SERVER "grep -o '}' $FILE | wc -l")
echo "CSS 花括号: $OB open / $CB close"

# 3. 文件大小
SIZE=$($SERVER "wc -c < $FILE")
echo "文件大小: $SIZE bytes（应 > 50000）"
```

**检查项：**
- ✅ 文件不为空，大小 > 50KB
- ✅ HTML `<html>` 和 `</html>` 成对
- ✅ CSS `{` 和 `}` 数量相等
- ✅ 目标 A：关键函数存在（`init()`, `renderCards()`, `renderTable()`, `setupRouter()`）
- ✅ 目标 B：关键内容存在（`GG 探针`, `drawNetChart`, `drawLineChart`）

### 第二步：部署

**目标 B（GG 探针 Astro 版）— 用 deploy.sh 一键部署：**
```bash
cd /home/woioeow/galaxy-glass/astro && bash deploy.sh
```

目标 A 或其他手动部署场景：
```bash
# 1. 服务器上备份旧文件
SERVER="ssh -p 46748 -i ~/.ssh/hermes_admin root@<荷兰_IP>" 
FILE=/opt/komari/data/theme/index.html
$SERVER "cp $FILE ${FILE}.bak"

# 2. scp 直推
scp -P 46748 -i ~/.ssh/hermes_admin ./index.html root@<荷兰_IP>:$FILE
```

### 第三步：部署后验证

```bash
# 目标 B 验证方式：
SERVER="ssh -p 46748 -i ~/.ssh/hermes_admin root@<荷兰_IP>"
FILE=/opt/komari/data/theme/index.html

# 1. 验证文件大小
LOCAL_SIZE=$(wc -c < /home/woioeow/galaxy-glass/astro/dist/index.html)
REMOTE_SIZE=$($SERVER "wc -c < $FILE")
echo "本地: $LOCAL_SIZE / 远程: $REMOTE_SIZE"

# 2. 验证内容包含关键标记
$SERVER "grep -q '银河探针' $FILE && echo '✅ 内容正常' || echo '❌ 内容异常'"

# 3. curl 内网验证（注意：要检查远程服务器！不是本机）
$SERVER "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:25774/"

# 4. 验证 Astro 组件正确加载
$SERVER "curl -s http://127.0.0.1:25774/ | grep -q 'astro-island' && echo '✅ Astro 组件正常' || echo '❌ 缺少 Astro 组件'"
```

## 禁止操作
  - ❌ **不要通过 SSH pipe 推文件** —— SSH cat 管道 + base64 编码经过 hermes `terminal()` 工具时，输出会被 50KB 截断，导致部署文件损坏。必须用 `scp` 直推或远程 `sed/cp`。
  - ❌ **不要用 `curl URL | ssh ... 'cat > file'` 中转**——上次404覆盖文件导致面板崩溃
- ❌ **不要跳过语法检查直接部署**
- ❌ **部署后不要问用户"你刷新看看"就走**——要告诉用户改了什么、看哪里
- ❌ **不要用全局 `sed -i 's/旧/新/'` 修改 CSS**——会命中文件中所有匹配行，误伤其他选择器。本 session 两次踩坑：(1) `s/grid-template-columns: 1fr 1fr;/...repeat(3, 1fr).../` 误改了 `#table-body` 和 480px 媒体查询；(2) `s/repeat(3, 1fr)/repeat(2, 1fr)/` 误改了 `.metrics-grid`、`.sysinfo-grid`。**替代方案**：先用 `grep -n '目标'` 确认所有匹配行，确认目标唯一后，用行号精确的 `sed -i '行号s/旧/新/'`。

## 已知技术坑总结

### ⚠️ Cloudflare 隧道映射的是远程服务器，不是本机（2026-05-19 新增）

`<监控面板域名>` 的访问链路：
```
Cloudflare edge → cloudflared tunnel (在荷兰主控 <荷兰_IP> 上运行)
    → 远程服务器的 localhost:25774 (galaxy-proxy.py)
    → /opt/komari/data/theme/ 提供静态文件
```

**不要在本地 `/opt/komari/data/theme/` 做任何修改，那不会生效。** 所有文件必须 scp 到远程服务器 <荷兰_IP>（端口 46748，密钥认证）。使用 `deploy.sh` 自动处理。

### GalaxyGlass Astro 版部署（2026-05-19 新增）

当前线上版本是 Astro 项目 `galaxy-glass/astro/`。**不要编译/修改 `galaxy-glass-next/`**（那是旧的 Next.js 版）。

一键编译+部署：`cd /home/woioeow/galaxy-glass/astro && bash deploy.sh`

### GalaxyGlass 部署版本差异
- GitHub repo（`/home/woioeow/galaxy-glass/`）标记 v2.2.0，但部署版实际运行 v2.7.0+
- 部署版领先于 repo 的改动包括：横排图例、navbar 滚动毛玻璃、颜色体系 `--accent-2: #818cf8`（repo 仍为 `#6366f1`）、响应式细节、背景色为蓝色系（repo 为绿色系）
- 部署前应抓取公网版本 `curl -s https://<监控面板域名>/ > /tmp/deployed.html` 作为工作基准，而非直接修改 repo 版本
- 同步 repo 时注意 CSS 变量和结构可能已大幅偏离

### `sed -i` 全局替换误伤
- **场景**：修改单行 CSS 值（如 `grid-template-columns`、`padding`、`font-size`）
- **风险**：该模式可能在文件其他位置重复出现（如注释、媒体查询、其他选择器）
- **解法**：
  1. 先 `grep -n '模式' 文件` 查看所有匹配行
  2. 确认只有目标行应该被替换
  3. 用 `sed -i '行号s/旧/新/'` 精确定位
  4. 或者用 `sed -i '/唯一的上下文/s/旧/新/'` 用上下文限定范围
  5. 部分 CSS 属性（如 `grid-template-columns: 1fr 1fr`）在多个选择器中重复出现是常态，必须行号定位
- **验证**：替换后 `grep -n '新值'` 确认只有预期行被修改

### Git rebase 恢复（用于回退到可靠状态）
当本地 repo 处于 rebase 中（`git status` 显示 "You are currently editing a commit while rebasing"）：
1. `git rebase --abort` — 中止 rebase，回到 rebase 开始前的 commit
2. 如果 rebase abort 导致本地 main 落后于 origin/main：`git reset --hard origin/main`
3. ⚠️ `reset --hard` 会销毁未提交的修改。如果本地有未提交的修改，先 `git stash` 或 `git diff > /tmp/patches.patch`
4. 重新下载远程部署版：`curl -s https://<监控面板域名>/ > index.html`
5. 提交并推送到 GitHub

常见场景：之前尝试交互式 rebase 整理 commit 历史，中途被中断（SSH 断线、超时），导致 repo 卡在 rebase 状态。

### SSH host key 变更
- 服务器重装/重置后 host key 变化，sshpass 拒绝连接
- 修复：`ssh-keygen -f ~/.ssh/known_hosts -R "[$IP]:$PORT"`
- 部署前应先用 `sshpass -o StrictHostKeyChecking=no` 测试连接

### 三视图对齐检查
- `.main { padding: 1.5rem 0 }` 覆盖了 `.container { padding: 0 1.5rem }`
- 因此 `.nodes-grid`、`.table-view`、`#region-filters` 等子元素必须独立设置水平 padding
- 修改 alignment 时必须在卡片/表格/详情三个视图上各检查一次

## 用户通知模板
部署后通知用户：
> 已部署 ✅ 改动：xxx。请硬刷新 `<监控面板域名>`（Ctrl+Shift+R）查看。特别注意：xxx 部分。

## 参考文件
- `references/galaxyglass-mobile-patterns.md` — GalaxyGlass 移动端响应式修复模式（stat卡片溢出、筛选栏滚动、详情页紧凑、加载态闪白/长方块、毛玻璃可见性）
- `references/css-layer-architecture.md` — GalaxyGlass CSS 6 层架构说明（修改已有样式时的隔离指南）
