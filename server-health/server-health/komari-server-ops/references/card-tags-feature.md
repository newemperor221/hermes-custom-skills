# GalaxyGlass 卡片标签行

在 `renderCard()` 中，于 `.node-card-header` 和 `.card-metrics` 之间插入标签行。

## CSS

```css
.card-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 6px;
  margin-bottom: 4px;
}
```

## JS（renderCard 函数内）

原有的拼接：
```js
+'</div>'  // 关闭 .node-card-header
+'<div class="card-metrics">'  // 打开 metrics
```

改为：
```js
+'</div>'
+(n.tags?'<div class="card-tags">'+String(n.tags).split(',').filter(function(t){return t.trim()}).map(function(t){return '<span class="tag-chip">'+t.trim()+'</span>'}).join('')+'</div>':'')
+'<div class="card-metrics">'
```

逻辑：
- `n.tags` 是逗号分隔的字符串（如 `"洛杉矶,年付,NAT"`）
- 有 tags → 渲染 `.card-tags` 容器，每个标签一个 `.tag-chip` 毛玻璃胶囊
- 无 tags → 跳过（输出空字符串）

## 现有 CSS 类（复用）

`.tag-chip` 已存在于 GalaxyGlass 主题中：
```css
.tag-chip {
  padding: 3px 9px;
  border-radius: var(--radius-full);
  font-size: 12px;
  background: var(--glass-bg);
  border: 1px solid var(--glass-border);
  color: var(--text-primary);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
}
```

## 部署注意事项

- GalaxyGlass 是单文件内联 script，JS 语法错误会使整个 IIFE 不执行。
- 修改后需验证 JS 语法：`node --check`（提取 script 内容检查）。
- Proxy 无缓存，修改 index.html 后立即生效（绕过 Cloudflare 则需 purge cache）。
