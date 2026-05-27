# GalaxyGlass Mobile Adaptation Patterns

## 核心原则

移动端 (<640px) 的 CSS 改动必须包裹在 `@media (max-width: 639px)` 内，桌面端不受影响。

## ⚠️ 改 CSS 前的强制步骤（用户因多次不读源码发火）

**改任何 CSS 之前必须先做的三件事：**

1. **读 renderCard()/renderRow() 的 HTML 模板**（line ~1263 / ~1333），确认 DOM 类名/id 对应的到底是不是你以为的元素
2. **读全部 CSS 规则**，确认 `.metric-value`、`.node-footer`、`.footer` 等类名有几个定义、分别在哪段上下文（卡片 vs 详情 vs 表格）
3. **区分是哪个视图的样式**：grid（卡片）、table（表格）、detail（详情页）—— 三个视图各有独立的 `.metric-value`/`.metric-label`/`.metric-bar` 规则
4. **区分是页面级元素还是卡片级元素**：`footer` 是页面页脚，`node-footer` 是卡片底部，不要搞混

### 高频混淆清单

| 类名 | 位置 | 用途 |
|------|------|------|
| `.footer` / `.footer-inner` | 页面底部 | 品牌/版权/运行时间 |
| `.node-footer` / `.node-footer-row` | 每个节点卡片内部 | 流量/价格/到期等行 |
| `.metric-value` (line ~408) | 详情视图 detail | CPU/内存/磁盘 % 数值 |
| `.metric-value` (line ~710) | 卡片视图 grid | CPU/内存/磁盘 % 数值 |
| `.cell-value` (line ~575) | 表格视图 table | 表格列数值 |
| `.stats-grid` | 顶部统计栏 | 4个统计卡 |
| `.nodes-grid` | 卡片网格 | 节点卡片容器 |

## 已实现的移动端适配

### 1. 视图切换（view-toggle）隐藏
```css
.view-toggle {
  display: none;
  grid-template-columns: 1fr 1fr;
  position: relative;
  /* ...其他属性... */
}
@media (min-width: 640px) {
  .view-toggle { display: inline-grid; }
}
```

### 2. JS 强制卡片模式
```javascript
function render() {
  const filtered = getFiltered();
  const isMobile = window.matchMedia('(max-width: 639px)').matches;
  if (isMobile) viewMode = 'grid';
  // ...
}
```

### 3. 表格视图在移动端完全隐藏
```css
@media (max-width: 639px) {
  .table-view { display: none !important; }
}
```

### 4. 页面页脚（footer）单列居中

**⚠️ CSS 顺序坑（多次被用户指出）**：移动端媒体查询必须写在桌面端 `*:first-child`、`*:nth-child(2)`、`*:last-child` 规则**之后**，否则同优先级下后定义的规则覆盖先定义的。如果桌面规则写在后面，移动端不会生效。

```css
/* ✅ 正确顺序：桌面规则在前，媒体查询在后 */
.footer-inner {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  /* ... */
}
.footer-inner > *:first-child { justify-self: start; }
.footer-inner > *:nth-child(2) { justify-self: center; }
.footer-inner > *:last-child { justify-self: end; }

@media (max-width: 639px) {
  .footer-inner {
    grid-template-columns: 1fr !important;
    gap: 6px;
    text-align: center;
  }
  .footer-inner > * { justify-self: center !important; }
  .footer-brand { justify-content: center !important; }
}
```

**`!important` 是安全网**：即使顺序对了，移动端 `justify-self: center` 也可能被桌面端规则覆盖。加 `!important` 确保覆盖。

### ❌ 错误示例（不要这样写）
```css
/* 媒体查询在前... */
@media (max-width: 639px) {
  .footer-inner > * { justify-self: center; }
}
/* ...桌面规则在后 → 桌面规则覆盖媒体查询 → 移动端不生效 */
.footer-inner > *:first-child { justify-self: start; }
```

### 5. 指标数值 font-size
- 卡片页（grid 视图）百分比数值 `.metric-value`：**14px**（统一，不再 20px）
- 详情页（detail 视图）百分比数值 `.metric-value`：**14px**
- 表格页（table 视图）数据 `.cell-value`：**12px**
- 标签 `.metric-label`：**10px**

### 6. 底部栏（卡片内 node-footer）
移动端保持原样（flex row），不改为纵向。页面页脚才改为纵向单列。

## 部署流程

git push（GitHub）+ scp（56idc-la）两步独立，缺一不可：
```bash
git push origin main
sshpass -p 'Y@BU1%wmP#xFs8bK' scp -P 42185 /local/index.html root@<洛杉矶2_IP>:/data/theme/GalaxyGlass/dist/index.html
```

## 回滚

如果改坏了，从 git log 找上一个稳定 commit 恢复：
```bash
git log --oneline -10
git checkout <稳定commit> -- index.html
```
