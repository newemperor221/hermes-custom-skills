# 2026-05-14 综合代码审查发现的 Bug 与修复

## 审查范围
- `/opt/komari/data/theme/index.html` (GalaxyGlass 单文件, 672 行)
- `/opt/komari/galaxy-proxy.py` (Python 反向代理, 92 行)

## 🔴 严重

### 1. CSS `.detail-body` 嵌套选择器破坏 grid 布局

**文件**: `index.html` 第 356-361 行  
**类型**: CSS 解析错误  
**症状**: 详情页两列布局不是靠 grid 撑起来的，而是内部 flex 凑巧能并排。`display: grid; grid-template-columns: 1.2fr 0.8fr;` 从未生效。  

```css
/* ❌ 原始代码 — 非法嵌套 */
.detail-body {
.page { display: flex; ... }    /* CSS 不允许选择器嵌套！ */
#list-view { flex: 1; }          /* 同上 */
display: grid; ... }              /* 解析器已经关闭了 .detail-body */
```

**根因**: 标准 CSS 不支持选择器嵌套。浏览器解析到 `.page {` 时认为这是新选择器，关闭了 `.detail-body`，后面所有属性丢弃。这是 minify/拼接时的人为错误。

**修复**: 
```css
.detail-body {
  display: grid; grid-template-columns: 1.2fr 0.8fr; gap: var(--gap); margin-top: var(--gap);
}
@media (max-width: 800px) { .detail-body { grid-template-columns: 1fr; } }
```

### 2. `siteStart` 可能被 API 返回的 buildTime 覆盖

**文件**: `index.html` 第 565 行  
**类型**: 逻辑错误 — 数据优先级颠倒  
**症状**: 底部"稳定运行"时间可能显示错误天数。

```js
// ❌ buildTime 覆盖了硬编码的 2026-05-08
if(ts.buildTime){var p=new Date(ts.buildTime);if(!isNaN(p.getTime()))siteStart=p.getTime()}
```

**修复**: 删除 buildTime 覆盖逻辑。`siteStart` 保持硬编码的最早用户创建时间 `2026-05-08T03:28:02Z`。

### 3. 汇率 API key 硬编码在前端

**文件**: `index.html` 第 566 行  
**类型**: 安全 — API 凭据暴露  
**严重程度**: 高（免费额度可能被滥用）  

```js
fetchJSON('https://v6.exchangerate-api.com/v6/4eb672eb050aa81c7d8ddca1/latest/USD')
```

**修复**: 
1. 前端改为调用 `/api/proxy/exchange-rate`
2. `galaxy-proxy.py` 添加 `_handle_exchange_rate()` 方法在服务器端调用外部 API
3. 添加 fallback 返回固定汇率 `{"conversion_rates":{"CNY":6.82}}` 当外网不可达时

## 🟡 中等

### 4. 返回列表时不恢复过滤/搜索状态

**文件**: `index.html` 第 602 行  
**症状**: 从详情页返回列表后，之前的区域筛选和搜索关键词丢失。  
**修复**: `showListView()` 开头调用 `render()` 恢复状态。

### 5. `.page` 和 `#list-view` 重复声明

**文件**: `index.html` 第 357-358, 360-361 行  
**类型**: 代码质量  
**修复**: 随 CSS 修复一起移除重复声明。

## 🟢 轻微

### 6. `var _i` 变量泄漏

**文件**: `index.html` 第 623 行  
**修复**: `var _i` → `let _i`

### 7. 搜索聚焦延迟过长

**文件**: `index.html` 第 651 行  
**修复**: `setTimeout(..., 200)` → `setTimeout(..., 50)`

### 8. Back-to-top hover 颜色不统一

**文件**: `index.html` 第 435 行  
**修复**: 金色 `rgba(201,169,78,...)` → 靛蓝 `rgba(129,140,248,...)` 匹配 `--accent-2`

## 排查方法总结

### CSS 语法检查
```bash
# 找嵌套选择器（CSS 不合法）
grep -nE '^\s+\.[a-z].*\{.*\{' index.html

# 找 undefined CSS 变量
grep -oP 'var\(--[a-z-]+\)' index.html | sort -u | while read v; do
  key=${v#var\(}; key=${key%\)}
  grep -q "$key" index.html || echo "MISSING: $v"
done
```

### JS 安全检查
```bash
# API key 在 URL 中
grep -oE 'https?://[^/"]+/[A-Za-z0-9_-]{20,}' index.html

# 残存的 token/secret
grep -nE '(token|secret|api_key)\s*[:=]' index.html | grep -v '//.*'
```

### 运行时验证
```js
// 检查 detail-body grid 是否生效
getComputedStyle(document.querySelector('.detail-body')).display
// 应为 "grid"，不是 "block"

// 检查所有卡片是否正常渲染
document.querySelectorAll('.node-card').length

// 检查 CSS var 是否定义
getComputedStyle(document.documentElement).getPropertyValue('--chart-mem')
// 应为空？如果为空则缺少定义
```
