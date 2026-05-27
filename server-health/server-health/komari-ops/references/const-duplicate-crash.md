# `const` 重复声明导致整段内联 JS 崩溃（2026-05-10）

## 现象

用户反馈 <监控面板域名> 一直显示"连接后端中…"（loading spinner 不消失）。API 正常返回 200，服务器文件大小正确，但浏览器 console 有未名 exception。

## 排查过程

1. **浏览器检查**：`document.querySelectorAll('.node-card').length` → 0，`typeof init` → `undefined`，`typeof fetchNodes` → `undefined`
2. **排除网络问题**：`curl http://127.0.0.1:25774/` 返回正确 HTML，`curl /api/nodes` 返回 200
3. **排除 Cloudflare 缓存**：服务器文件 md5sum 与本地一致，`curl localhost:25774` 也返回旧版
4. **最终发现**：`node -e "new Function(js)"` 抛错 `Identifier 'trafficLimit' has already been declared`

## 根因

`renderDetailSysinfo` 函数内两行：

```javascript
// Line 1944
const trafficLimit = node.traffic_limit || 0;

// Later... Line 1999 (同一函数！)
const trafficLimit = node.traffic_limit || 0; // ❌ 重复声明
```

JS 的 `const` 在同一作用域内不能声明两次。内联 `<script>` 中的任何语法错误导致**整个脚本块不执行**，`init()`、`fetchNodes()` 等全部未定义。

## 修复

删掉 L1999 的 `const`：
```javascript
// Before (broken):
const trafficUsed = ...;
const trafficLimit = node.traffic_limit || 0;
const trafficPct = trafficLimit > 0 ? ... : 0;

// After (fixed):
const trafficUsed = ...;
// trafficLimit 已在上方声明，直接复用
const trafficPct = trafficLimit > 0 ? ... : 0;
```

## 教训

- 内联 `<script>` 的任何 JS 语法错误 = 页面瘫痪（整块不执行）
- 不要只看浏览器控制台的网络 tab → 还要看 JS 解析错误
- `new Function(js)` 是检测内联 JS 语法错误的可靠方法
- 函数重构时注意同名 `const` 变量，尤其是同函数内不同块（如 sysinfo section + billing section）独立编写的部分
