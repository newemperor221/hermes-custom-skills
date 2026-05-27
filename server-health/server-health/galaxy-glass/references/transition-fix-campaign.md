# GalaxyGlass Transition 修复战役（v1.2.3）

> 2026-05-12 完成。目标：`transition:all` 和 `transition:width` 在 `impeccable lint` 下清零。

## 修复统计

| 类别 | 修复数量 | 状态 |
|------|---------|------|
| `transition: all` → 明确属性列表 | 8 处 | ✅ 清零 |
| `transition: width` → `transform: scaleX` | 4 处 CSS + 1 处 JS | ✅ 清零 |
| JS `style.width` → `style.transform: scaleX` | 1 处 | ✅ 清零 |

## transition:all 修复清单（9 处）

| # | 选择器 | 位置（repo v1.2.3） | 旧值 | 新值 |
|---|--------|-------------------|------|------|
| 1 | `.search-box` | ~L154 | `all 0.6s` | `max-width 0.6s, background 0.3s, border-color 0.3s` |
| 2 | `.icon-btn` | ~L200 | `all 0.2s` | `color 0.2s, background 0.2s` |
| 3 | `.stat-card` | ~L333 | `all 0.3s` | `background 0.3s, border-color 0.3s, box-shadow 0.3s` |
| 4 | `.chip` | ~L359 | `all 0.2s` | `color 0.2s, background 0.2s, border-color 0.2s` |
| 5 | `.node-card` | ~L391 | `all 0.3s` | `transform 0.3s, box-shadow 0.3s, border-color 0.3s` |
| 6 | `.view-toggle button` | ~L466 | `all 0.3s` | `color 0.3s, background 0.3s, border-color 0.3s` |
| 7 | `.table-row` | ~L494 | `all 0.3s` | `transform 0.3s, box-shadow 0.3s, border-color 0.3s` |
| 8 | `.back-btn` | ~L625 | `all 0.2s` | `color 0.2s, background 0.2s, border-color 0.2s` （⚠️ 易遗漏！） |

## transition:width → scaleX 修复（4 处 CSS + 1 处 JS）

| # | 选择器 | 位置 | 旧值 | 新值 |
|---|--------|------|------|------|
| 1 | `.metric-fill`（卡片视图） | ~L423 | `transition: width 0.3s` | `transform-origin: left; transition: transform 0.3s` |
| 2 | `.meter-fill`（表格视图） | ~L516 | `transition: width 0.3s` | `transform-origin: left; transition: transform 0.3s` |
| 3 | `.metric-fill`（详情视图） | ~L662 | `transition: width 0.4s` | `transform-origin: left; transition: transform 0.4s` |
| 4 | `.traffic-bar-fill`（详情流量条） | ~L707 | `transition: width 0.4s` | `transform-origin: left; transition: transform 0.4s` |
| 5 | JS 内联 `style="width:${pct}%"` | ~L2099 | `style="width:${pct}%"` | `style="transform:scaleX(${Math.min(1,pct/100)});transform-origin:left"` |

## impeccable lint 已知误报

v1.2.3 运行 `npx impeccable lint dist/index.html` 后仍有 3 条警告（均为误报）:

1. `[overused-font] helvetica` — 系统字体堆栈，对中文站点是正确实践，不可替换
2. `[overused-font] arial` — 同上
3. `[layout-transition] transition: max-width` — 搜索框单击展开动画（36px↔240px），一次性交互非持续更新，可忽略

**判断标准**: 部署前只需确认 `transition:all` 和 `transition:width` 被消灭。max-width 和 font 警告是安全放行的。

## 部署陷阱

1. **zip 结构**: `komari-theme.json + dist/index.html`（index.html 必须在 dist/ 子目录下，不能放根目录）
2. **激活**: 上传后必须 `theme/set?theme=GalaxyGlass` — 上传不会自动激活
3. **Cloudflare 缓存**: 即使上传成功，CF 可能服务旧版 HTML 达数小时。用 `curl -s -H 'Cache-Control: no-cache'` 验证
