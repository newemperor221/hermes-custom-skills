# Komari 内嵌 JS 模板单引号 bug

## 问题

探针面板 `stat.357561.xyz` 上所有服务器卡片名称前显示多余的 `'` 字符：

```
'无聊云 | 洛杉矶    ← 多了一个 '
```

## 根因

### 数据库是干净的

```sql
sqlite3 /opt/komari/data/komari.db "SELECT name FROM clients;"
-- 无聊云 | 洛杉矶      ← 无前导单引号
-- Acck | 东京
```

### 问题出在 komari 二进制的 JS 模板

Komari v1.2.0 二进制内嵌了完整的前端 HTML/JS 模板（43MB 二进制中包含构建产物）。JS 渲染模板中有如下代码：

```
// 原始模板（komari 二进制内嵌，无法直接修改）
\'+(n.name||n.uuid||'—')
```

`\'` 在 JavaScript 字符串中是转义的单引号字符，渲染结果为 `'无聊云 | 洛杉矶`。

### SSR vs CSR 差异

- **SSR（server-side render）**：komari 服务端渲染的初始 HTML 中节点名是干净的（无 `'`）
- **CSR（client-side render）**：JS 模板中的 `\'` 在每次数据更新/重渲染时添加 `'` 前缀

所以首次加载时名字正常，一旦 JS 动态更新数据就会出现 `'` 前缀。

## 修法

唯一的修复是绕过 komari 的内嵌模板，用 galaxy-proxy.py 服务磁盘上的 index.html：

1. 准备修复后的 index.html（去掉 `\'`）：
   ```
   // 修复后
   ''+(n.name||n.uuid||'—')
   ```
2. 部署 galaxy-proxy.py + index.html 到服务器
3. komari 切到 25776（后端 API 模式）
4. galaxy-proxy 在 25774 服务静态 HTML
5. 重启 cloudflared 隧道

详见 `SKILL.md` 中「从 native 模式切换到 proxy 模式」章节。
