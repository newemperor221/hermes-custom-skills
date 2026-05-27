# SSR 与 JS 模板不一致的调试

> 2026-05-20 发现并修复 · GalaxyGlass / Komari 探针

## 问题现象

所有卡片名字前都有 `'` 前缀，或者每张卡片标题行有两个状态圆点。

## 根因

Komari 二进制页面渲染分两层，两者可能不一致：

| 渲染层 | 何时生效 | 是否干净 |
|--------|---------|---------|
| **SSR**（Go 模板） | 首次页面加载 | 通常干净 |
| **JS 模板**（HTML 中的 `renderCard`） | 数据轮询更新后 | 可能有 bug |

## 调试步骤

```bash
# 1. 查看 SSR（初始加载）
curl -s https://stat.357561.xyz/ | grep -oP 'node-card-header">.*?</div></div>' | head -1

# 2. 查看 JS 模板（数据更新后使用）
curl -s https://stat.357561.xyz/ | grep -oP "renderCard.*?function" 
```

## 已确认的 JS 模板 bug（komari v1.2.0 内嵌）

```javascript
// renderCard() 中的卡片标题行：
+ '<div class=\"node-card-header\">'
+ '<div class=\"node-status '+(on?'online':'offline')+'\"></div>'    ← 圆点1
+ (oc?'<span class=\"node-os-icon\" data-os=\"'+oc+'\"></span>':'')
+ '<div class=\"node-name\">'
+ '<span class=\\\"status-dot '+(on?'online pulse':'offline')+'\\\"></span>'  ← 圆点2 BUG
+ '\\''                                                                    ← \' BUG
+ (n.name||n.uuid||'—')
+ '</div>'
+ ...
```

**两个 bug：**
1. `\\''+(n.name...)` → `\'` 在 JS 字符串中产生字面量 `'`，渲染为 `'Name`
2. `status-dot` span 嵌在 `node-name` 内部 → 两个圆点

## 修复（galaxy-glass 源码）

在 `src/scripts/app.js` 的 `renderCard()` 中：

1. 删除 `<span class=\\"status-dot ...">` 及其 `</span>` 闭合标签
2. 将 `\\'+(n.name...` 改为 `+(n.name...`（去掉 `\'`）

```javascript
// 修复后：
+ '<div class=\"node-name\">'
+ (n.name||n.uuid||'—')
+ '</div>'
```

## 部署

- komari 内嵌模板不可修改（Go 二进制编译进去的）
- 改为 galaxy-proxy 部署修复后的 galaxy-glass 源码
- 2026-05-20 验证：galaxy-proxy + 修复后的源码正常工作，无吕字型
