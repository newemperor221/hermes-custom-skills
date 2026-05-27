# NodeCard 毛玻璃调优记录（2026-05-17）

## 用户需求

1. 毛玻璃不见了 → 恢复模糊，让玻璃效果更明显
2. 卡片可以增大 → 让卡片更大
3. 其他全部不变

## 改动

文件：`src/components/NodeCard.tsx`

| 属性 | 旧值 | 新值 | 效果 |
|------|------|------|------|
| 背景色 | `rgba(255,255,255,0.08)` | `rgba(255,255,255,0.04)` | 更透明→更多背景透过→毛玻璃更明显 |
| 模糊 | `backdrop-blur-[60px]` | `backdrop-blur-[80px]` | 更糊 |
| 内边距 | `px-4 py-3.5` | `px-5 py-5` | 大一圈（16px→20px） |
| 内部间距 | `gap-2.5` | `gap-3` | 配大卡片 |

## 部署

```bash
cd /home/woioeow/galaxy-glass-next && npm run build
tar czf /tmp/gg-deploy.tar.gz -C out .
sshpass -p 'OX8w$nE9A%tfqb6v' scp -P 46748 /tmp/gg-deploy.tar.gz root@<荷兰_IP>:/tmp/
sshpass -p 'OX8w$nE9A%tfqb6v' ssh -p 46748 root@<荷兰_IP> \
  "cd /opt/komari/data/theme && rm -rf * && tar xzf /tmp/gg-deploy.tar.gz && rm /tmp/gg-deploy.tar.gz"
# 无需重启 proxy（rm -rf * 保留目录 inode → cwd 有效）
```

## 踩坑

**Turbopack 哈希不变 → 浏览器旧缓存：**
- JS 文件名（如 `14vf..5rfgs1o.js`）和 `_buildManifest` 哈希（`Uta72SnjosHJgLLDCbEE5`）在前后两次构建中完全一致
- Cloudflare 返回新内容，但浏览器看到相同 URL → 读取本地缓存旧版
- 验证对比：`getComputedStyle(card).backdropFilter` 在浏览器 console 报 `blur(60px)`（旧），但 `curl` Cloudflare 的 JS 已含 `80px`（新）
- 解决：硬刷新 `Ctrl+F5` / `Cmd+Shift+R`
