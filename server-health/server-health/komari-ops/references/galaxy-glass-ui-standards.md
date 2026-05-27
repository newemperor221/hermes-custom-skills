# GalaxyGlass UI 迭代标准（2026-05-10）

## 主题打包结构

```
gg-theme.zip 根目录（直接放文件，不包外层文件夹）:
├── komari-theme.json   ← 主题清单
├── icon.svg            ← 图标
├── preview.png         ← 预览图
└── dist/
    └── index.html      ← 必须是 dist/ 子目录
```

**常见错误**：`zip -r gg-theme.zip gg-theme/` 会在 zip 里产生 `gg-theme/` 外层目录，komari 后台导入失败。

## GitHub Release 打包流程

```bash
# 1. 克隆最新源码
cd /tmp && rm -rf gg-src && git clone --depth=1 https://github.com/newemperor221/galaxy-glass

# 2. 打包（源文件直接放 zip 根目录）
rm -rf /tmp/gg-theme && mkdir /tmp/gg-theme
cp /tmp/gg-src/index.html /tmp/gg-theme/dist/
cp /tmp/gg-src/komari-theme.json /tmp/gg-theme/
cp /tmp/gg-src/preview.png /tmp/gg-theme/
cp /tmp/gg-src/icon.svg /tmp/gg-theme/

# 3. 验证结构
unzip -l /tmp/gg-theme.zip
# ✅ 正确：zip 根目录有 komari-theme.json, dist/, preview.png, icon.svg
# ❌ 错误：zip 根目录是 gg-theme/ 文件夹

# 4. 部署
sshpass -p 'Y@BU1%wmP#xFs8bK' scp -o StrictHostKeyChecking=no -P 42185 \
  /tmp/gg-theme.zip root@<洛杉矶2_IP>:/tmp/

# 5. GitHub release（tag 已存在则先删重建）
gh release delete v1.2.0 --repo newemperor221/galaxy-glass -y 2>/dev/null || true
gh release create v1.2.0 --repo newemperor221/galaxy-glass \
  --title "GalaxyGlass v1.2.0" --notes "..."
gh release upload v1.2.0 /tmp/gg-theme.zip --repo newemperor221/galaxy-glass
```

## 统计卡（stats-grid）图标尺寸

```css
.stat-card svg { width: 2rem; height: 2rem; color: rgba(255,255,255,0.4); flex-shrink: 0; }
```

- 从 1.25rem → 2rem（用户要求大一号）
- 流量概览卡片大图标可替换为自定义 SVG

## 流量概览 / 网络速率 标签间距

```css
.label { gap: 2px 16px; }   /* 标签列间距 16px */
.stat-sub-row { gap: 2px 16px; }  /* 数据列间距 16px */
```

- 标签列和数据列间距统一 16px

## 芯片（chip）分组标签

```css
.filters { gap: 16px; }          /* 标签之间间距 */
.chip {
  gap: 8px;                      /* 图标和文字间距 */
  padding: 8px 16px;             /* 上下左右 padding */
}
```

## CPU/内存/磁盘百分比大小（必须先确认视图）

**高频混淆点**：卡片视图（grid）和表格视图（table）和详情视图（detail）是三套完全不同的 CSS 类名。

| 视图 | CSS 类名 | font-size |
|------|---------|-----------|
| 卡片页 grid（CPU/内存/磁盘 %） | `.metric-value` | **14px**（2026-05-10 用户纠正 20px→14px） |
| 详情页 detail | `.metric-value` | 14px |
| 表格页 table | `.cell-value` | 12px |

```css
/* 详情页 — 14px，不能小 */
.detail-view .metric-value { font-size: 14px; }

/* 表格页 */
.cell-value { font-size: 12px; font-weight: 600; }
```

## Grid 响应式布局规范

```css
.nodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}
```

- **禁止用固定断点**（`repeat(2,1fr)` / `repeat(3,1fr)` / `repeat(4,1fr)`），会导致平板设备在两列和三列之间跳变
- `auto-fill` + `minmax(300px, 1fr)` 实现平滑自适应，手机→平板→桌面全覆盖

## GPU 加速规范

```css
.node-card { will-change: transform; }
```

- 大量节点卡片叠加 `backdrop-filter: blur()` 时滚动掉帧
- 加 `will-change: transform` 强制 GPU 渲染层，避免复合层重绘

## JS 容错规范（updateStats）

```javascript
// ✅ 用 Optional Chaining 防止 null/undefined 报错
const totalValue = nodesList.reduce((sum, n) => sum + toCNY(n?.price, n?.currency), 0);
const cycle = parseInt(n?.billing_cycle) || 30;
const expiredAt = n?.expired_at ? new Date(n.expired_at).getTime() : now + cycle * 86400000;
```

- `updateStats()` 中所有节点财务字段必须用 `?.` 可选链
- 价格为空时显示 0，不应导致 JS 报错

## 图标替换规范

### 流量概览（stat-transmitted / stat-received）

```html
<!-- 上传（橙） -->
<svg ... style="color:#f97316"><path d="M5.25589 16C...M12 21V11M12 11L9 14M12 11L15 14"/></svg>

<!-- 下载（绿） -->
<svg ... style="color:#10b981"><path d="M5.25589 16C...M12 21V11M12 21L9 18M12 21L15 18"/></svg>
```

### 网络速率（stat-netout / stat-netin）

- 上行速率：`M5 10l7-7m0 0l7 7m-7-7v18`（长柄向上箭头）
- 下行速率：`M19 14l-7 7m0 0l-7-7m7 7V3`（长柄向下箭头）

## 移动端适配规范（2026-05-10 完整版）

### 隐藏视图切换 + 强制卡片模式

移动端（<640px）不要表格视图，只显示卡片。移动端搜索按钮排在导航栏右侧，旧桌面胶囊搜索框隐藏：

```css
/* 视图切换按钮完全隐藏 */
.view-toggle { display: none; }
@media (min-width: 640px) {
  .view-toggle { display: inline-grid; }
}

/* 表格元素完全隐藏 */
@media (max-width: 639px) {
  .table-view { display: none !important; }
}
```

```javascript
// JS 层双重保护：每次 render() 时检测移动端，强制卡片模式
function render() {
  const filtered = getFiltered();
  const isMobile = window.matchMedia('(max-width: 639px)').matches;
  if (isMobile) viewMode = 'grid';
  // ...
}
```

### 页面页脚（footer）移动端单列

```css
.footer-inner {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
}
@media (max-width: 639px) {
  .footer-inner {
    grid-template-columns: 1fr;
    gap: 6px;
    text-align: center;
  }
  .footer-inner > *:first-child { justify-self: center; }
  .footer-inner > *:nth-child(2) { text-align: center; }
  .footer-inner > *:last-child { text-align: center; }
}
```

### ⚠️ 术语区分（容易搞错）

| 用户说 | 实际指 | CSS 类 |
|--------|--------|--------|
| 底部栏 / 页脚 | **页面 footer**（无背景，全透明，含站点名+在线时间+Powered by） | `.footer` / `.footer-inner` |
| 卡片底部 | 每张节点卡的尾部（含流量/价格/到期时间） | `.node-footer` / `.node-footer-row` |

修改前一定要问清楚是哪个，两个完全不是同一个东西。

## 常见 Bug 模式与修复（2026-05-10）  

### scroll 检测用 setInterval 轮询（CPU 浪费）

**问题**：`setupScroll()` 用 `setInterval(..., 100)` 每 100ms 轮询 `window.scrollY`。详情页又单独挂了 scroll 事件监听，两套并存。

**修复**：改用 passive scroll 事件 + requestAnimationFrame 节流：

```javascript
function setupScroll() {
  const navbar = document.getElementById('navbar');
  const backToTop = document.getElementById('back-to-top');
  let isScrolled = false, scrollTicking = false;
  window.addEventListener('scroll', () => {
    if (!scrollTicking) {
      window.requestAnimationFrame(() => {
        const y = window.scrollY || document.documentElement.scrollTop;
        if (y > 25 && !isScrolled) { isScrolled = true; navbar.classList.add('scrolled'); backToTop.classList.add('visible'); }
        else if (y <= 25 && isScrolled) { isScrolled = false; navbar.classList.remove('scrolled'); backToTop.classList.remove('visible'); }
        scrollTicking = false;
      });
      scrollTicking = true;
    }
  }, { passive: true });
}
```

### 移动端搜索弹不出来

**问题**：`navbar-mobile-search` 初始 hidden，但页面上**没有任何按钮**能触发它显示。移动端用户无法搜索。

**修复**：在 navbar-actions 加一个搜索按钮（只在 <640px 显示），同时**隐藏旧的桌面胶囊搜索框**避免重复入口：

```css
@media (max-width: 639px) {
  #mobile-search-btn { display: inline-flex !important; }
  .search-box { display: none !important; }  /* ← 隐藏桌面胶囊搜索 */
}
@media (min-width: 640px) {
  #mobile-search-btn { display: none !important; }
}
```

```html
<!-- 在 navbar-actions 里添加 -->
<button class="icon-btn round" id="mobile-search-btn" type="button" style="display:none;">
  <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
  </svg>
</button>
```

```javascript
document.getElementById('mobile-search-btn').addEventListener('click', (e) => {
  e.stopPropagation();
  const mobile = document.getElementById('mobile-search');
  mobile.classList.toggle('hidden');
  if (!mobile.classList.contains('hidden')) {
    setTimeout(() => document.getElementById('search-input-mobile').focus(), 100);
  } else {
    // 关闭时清空搜索
    document.getElementById('search-input-mobile').blur();
    searchQuery = ''; searchInput.value = ''; document.getElementById('search-input-mobile').value = '';
    render();
  }
});
```

**分工**：
- 桌面（≥640px）：胶囊搜索 ✅，移动端搜索按钮 ❌ 隐藏
- 移动（<640px）：移动端搜索按钮 ✅，胶囊搜索 ❌ 隐藏

### 页脚 uptime 每秒更新（性能浪费）

**问题**：`setInterval(updateFooterUptime, 1000)` 每秒做 Date 运算 + DOM 更新。没人读 uptime 到秒。

**修复**：改为 60 秒。`setInterval(updateFooterUptime, 60000);`

### 详情页 N+1 API 调用

**问题**：`loadDetailData()` 每次打开详情页都重新请求 `/api/nodes` 再请求 `/api/recent/{uuid}`。已有缓存 `nodesList` 可用。

**修复**：先查缓存，有缓存时只请求 `/api/recent/{uuid}`：

```javascript
const cachedNode = nodesList.find(n => n.uuid === uuid);
const nodePromise = cachedNode ? Promise.resolve(cachedNode) : fetch('/api/nodes').then(r => r.json()).then(d => (d.data || []).find(n => n.uuid === uuid));

nodePromise.then(node => {
  if (!node) {
    return Promise.all([fetch('/api/nodes').then(r => r.json()), fetch('/api/recent/' + uuid).then(r => r.json())])
      .then(([nodesData, recentData]) => ({ node: (nodesData.data||[]).find(x => x.uuid === uuid), recent: recentData.data||[] }));
  }
  return fetch('/api/recent/' + uuid).then(r => r.json()).then(recentData => ({ node, recent: recentData.data||[] }));
}).then(({ node, recent }) => {
  // ... 后续处理
});
```

### Cloudflare HTML 缓存不更新

**问题**：Cloudflare 缓存了旧版 HTML（即使通过 tunnel 模式也会缓存），更新文件后浏览器仍显示旧版。

**修复**：部署时在 HTML 加版本注释 + Cache-Control meta 标签：

```html
<!DOCTYPE html>
<!-- GalaxyGlass v1.2.1 -->  <!-- ← 版本号每次部署递增 -->
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
  <meta http-equiv="Pragma" content="no-cache">
  <meta http-equiv="Expires" content="0">
```

注意：
- **版本注释 + 实质性内容变化双保险**：只改版本号 Cloudflare 可能不认为是新内容（因为 HTML 主体没变）。meta 标签会要求浏览器不缓存，但 Cloudflare 可能会忽略 HTML meta 标签（它看的是 HTTP 响应头）。
- **如果 Cloudflare 仍缓存**：用户浏览器 Ctrl+Shift+R 硬刷新可绕过
- **部署验证流程**：
  ```bash
  # 第1步：先验证本地（绕过 CF）
  curl -s http://127.0.0.1:25774/ | grep -c "v1.2.1"
  
  # 第2步：再通过 CF 验证（可能仍是旧版）
  curl -s https://<监控面板域名>/ | grep -c "v1.2.1"
  
  # 如果本地有新版但公网是旧版 → Cloudflare 缓存，让用户硬刷新
  ```

### 事件绑定重复（init 只应执行一次）

`setupEvents()` 在 `init()` 内调用，如果 `init()` 被调用多次，事件监听器会重复绑定。当前 `init()` 只执行一次所以没问题，但未来如果加重试机制必须注意。

## 4 张统计卡（stats-grid）设计与优化

### 卡片布局

```html
.stats-grid { display: grid; grid-template-columns: 1fr 1fr 1.5fr 1.5fr; gap: 16px; }
@media (max-width: 639px) { .stats-grid { grid-template-columns: repeat(2, 1fr); } }
/* 比例说明：①②各1份（时间+在线=简单），③④各1.5份（流量+开销=内容丰富）。改前确认每张卡的内容量。 */
```

### 第③卡：流量概览 + 网络速率

**主图标**（大图标，卡左侧）：使用**环形网络/三节点** SVG，比云朵/上下箭头更贴合"流量"概念：

```html
<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"/>
```

这个 SVG 绘制三个圆形节点（12点钟、7点钟、5点钟位置）通过线条相连，视觉上暗示\"数据传输\"。注意路径较长但 icon 本身很小（32×32），所以线条密集是正常的。

第③卡同时显示**总量**和**瞬时速率**，用两列子行布局（`stat-sub-row` 的 `grid-template-columns: 1fr 1fr`）：

**图标规范**：
- 总量行（transmitted/received）→ ☁️ 云朵+箭头（上传橙色 `#f97316`、下载绿色 `#10b981`）
- 速率行（netout/netin）→ ⚡ **闪电图标**（上行橙色、下行绿色），不能再用云朵——用户需要一眼区分"总量"和"速率"

```html
<!-- 总量（云朵+箭头） -->
<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color:#f97316">
  <path d="M5.25589 16C3.8899...M12 21V11M12 11L9 14M12 11L15 14"/>
</svg>

<!-- 速率（闪电） -->
<svg fill="none" stroke="currentColor" viewBox="0 0 24 24" style="color:#f97316">
  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 2L4 14h7v8l9-12h-7z"/>
</svg>
```

### 第④卡：月度开销 + 剩余折旧

**数据来源**：
- 各节点价格来自 `clients.price`（原始值，含美元/人民币）
- 汇率：从 `exchangerate-api.com` 实时获取 USD→CNY，默认值 `6.82`（2026-05-10 实测）
- 月费折算：`monthlyPrice(price, currency, billingCycle)` — 不同周期统一成月费
- 剩余折旧：`remainingPrice(price, currency, billingCycle, expiredAt)` — 按剩余天数/周期天数比例

**展示格式**（两行）：
```
[月度开销       ]  [剩余折旧            ]
¥107/月           ¥1065
≈ $16/月 @6.82    ¥1154 · 92%
```

**算法要点**：

```javascript
// 月费折算：将任何计费周期转换成月均费用
function monthlyPrice(price, currency, billingCycle) {
  const p = toCNY(price, currency);
  if (!p) return 0;
  const cycle = parseInt(billingCycle);
  if (cycle === 0) return 0; // 永久不计月费
  return p * (30 / (cycle || 30)); // 折成30天
}

// 剩余价值折旧：按已用天数比例递减
function remainingPrice(price, currency, billingCycle, expiredAt) {
  const p = toCNY(price, currency);
  if (!p) return 0;
  const cycle = parseInt(billingCycle);
  if (cycle === 0) return p; // 永久：全额，不折旧
  const daysInCycle = cycle || 30;
  if (expiredAt) {
    const remainMs = new Date(expiredAt).getTime() - Date.now();
    if (remainMs <= 0) return 0;
    return p * Math.min(1, (remainMs / 86400000) / daysInCycle);
  }
  // 无到期 + 月付 → 已扣当月费，剩余0
  if (daysInCycle <= 30) return 0;
  return p; // 无到期 + 年付 → 假设刚续费
}
```

**特殊处理**：
- `billing_cycle=0`（永久节点）：`parseInt(0)` = 0，不加 `|| 30` fallback（否则永久节点被当30天周期算），永久 = 全价不折旧
- USD→CNY 汇率默认 `6.82`（2026-05-10 实测 API 返回值），API 挂掉时用默认值，**不要拍脑袋写 7.24（2026-05-10 教训）**
- `<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">` 必须加在 HTML `<head>` 里，防 Cloudflare 缓存旧版

**计算实例**（2026-05-10 数据）：
- 13台 VPS，含月付（¥2-10/月）、年付（¥10-¥148/年）、3年付（¥297/3年）
- 月费总和 ≈ ¥107/月
- USD 等值 ≈ $16/月 @6.82
- 剩余折旧 ≈ ¥1065（预付 ¥1154 的 92%）

## 详情页（detail-view）设计与优化（v1.2.1+）

### 导航栏（detail-nav）

```html
🇯🇵 🐧 Acck | 东京 — 日本 · KVM · Debian
```

**元素**：
- 国旗图片（`.detail-flag`，22×16px，from flagcdn.com）
- OS 图标（14×14px，from devicon）
- 标题（`.detail-title`, 15px, bold）：节点名称
- 副标题（`.detail-subtitle`, flex, gap 6px）：国旗 + OS 图标 + 区域 · 虚拟化 · OS

```javascript
// 加载到 nav（loadDetailData 中）
const flagImg = node.region ? `<img src="https://flagcdn.com/${flagEmoji(node.region)}.svg" class="detail-flag">` : '';
const osIcon = getOSIcon(node.os);
const osImg = osIcon ? `<img src="${osIcon}" style="width:14px;height:14px;">` : '';
document.getElementById('detail-meta').innerHTML = `${flagImg}${osImg} ${parts.join(' · ')}`;
```

**CSS**：
```css
.detail-flag { width: 22px; height: 16px; border-radius: 2px; object-fit: cover; flex-shrink: 0; }
.detail-subtitle { display: flex; align-items: center; gap: 6px; }
```

### Metrics 卡片（metrics-grid）

**布局**：`grid-template-columns: 1fr 1fr`（2×3 = 6张卡：CPU、内存、磁盘、上行、下行、在线时长）

```css
.metrics-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
```

**每张卡片结构**：
```
┌─ metric-card ────────────────┐
│ CPU          (metric-label)   │ ← 10px uppercase, muted
│ 5.0%         (metric-value)  │ ← 22px bold, monospace
│ 122MB/474MB  (metric-sub)    │ ← 10px muted（仅 CPU/内存/磁盘有）
│ ████████░░   (metric-bar)    │ ← 3px progress bar（仅 CPU/内存/磁盘有）
└──────────────────────────────┘
```

**核心改动**：
- `.metric-value`：14px → **22px**（2026-05-10 用户确认）
- 新增 `.metric-sub`（10px，font-mono）：显示已用/总量（内存、磁盘）
- CPU 无 sub（CPU 没有常用的"已用/总量"概念）
- 上行/下行/在线时长无线条、无 sub

```css
.metric-value { font-size: 22px; font-weight: 700; font-family: var(--font-mono); line-height: 1.1; }
.metric-sub { font-size: 10px; font-family: var(--font-mono); color: rgba(255,255,255,0.3); margin-top: -2px; }
```

### 系统信息 + 账单（sysinfo-card）

**布局**：左360px（`detail-left`），右 flex（`detail-right`）放3个图表。

**sysinfo-card 结构**：
```
┌─ sysinfo-card ──────────────────┐
│ ┌─ sysinfo-grid (2列) ──────┐   │
│ │ CPU 型号    AMD ...       │   │
│ │ 核心数      × 2           │   │
│ │ 架构        x86_64        │   │ ← 8行左列
│ │ ...                       │   │
│ ├───────────────────────────┤   │
│ │ 内存总量    474 MB        │   │
│ │ Swap 总量   无            │   │ ← 7行右列（含负载均值load-badge）
│ │ ...                       │   │
│ └───────────────────────────┘   │
│ ───────── (sysinfo-sep) ────── │
│ 💰 ¥148.88/年  📊 70G/500G  📅 285天  │ ← sysinfo-bill（3个bill-chip）
└──────────────────────────────────┘
```

**关键改动**：
- `.sysinfo-grid`：`grid-template-columns: 1fr 1fr`，将 15 行分成两列（ceil(15/2)=8+7）
- `.sysinfo-sep`：分隔线，`border-top: 1px solid rgba(255,255,255,0.08)`
- `.sysinfo-bill`：flex row，`justify-content: center`，gap 12px
- `.bill-chip`：圆角胶囊，绿色（正常）或红色（danger），`font-family: monospace`

```javascript
// JS 渲染逻辑（renderDetailSysinfo 中）
const mid = Math.ceil(rows.length / 2);
const leftRows = rows.slice(0, mid);
const rightRows = rows.slice(mid);
```

**账单信息生成**（使用节点数据：price, currency, billing_cycle, traffic_limit, expired_at）：
```javascript
const priceStr = `${node.currency||'¥'}${node.price}/${周期}`;
const trafficStr = `${bytes(used)}/${bytes(limit)}`;
const daysStr = `${daysLeft}天`;
document.getElementById('detail-sysinfo').innerHTML = `
  <div class="sysinfo-grid">${leftCol}${rightCol}</div>
  <div class="sysinfo-sep"></div>
  <div class="sysinfo-bill">
    <span class="bill-chip">${priceStr}</span>
    <span class="bill-chip ${trafficClass}">📊 ${trafficStr}</span>
    <span class="bill-chip ${daysClass}">📅 ${daysStr}</span>
  </div>
`;
```

### Canvas 图表（3个：CPU、内存、网络）

**图表布局**：右列 3 个 `.chart-card`，各含标题 + badge + canvas(height=160)

**端点圆点（v1.2.1 新增）**：

```javascript
// 在 drawDetailLine 最后添加
const lastPt = linePts[linePts.length - 1];
ctx.beginPath();
ctx.arc(lastPt.x, lastPt.y, 4, 0, Math.PI * 2);
ctx.fillStyle = color;
ctx.fill();
ctx.beginPath();
ctx.arc(lastPt.x, lastPt.y, 2, 0, Math.PI * 2);
ctx.fillStyle = '#fff';
ctx.fill();
// 当前值标签
ctx.fillStyle = 'rgba(255,255,255,0.6)';
ctx.font = 'bold 11px ui-monospace, monospace';
ctx.textAlign = 'center';
ctx.fillText(points[points.length - 1].toFixed(1) + '%', lastPt.x, lastPt.y - 10);
```

网络图表（`drawDetailNet`）同样加端点，上行橙 `#f97316`、下行绿 `#10b981`：
```javascript
function drawEndpoint(pts, color) {
  const last = pts.slice(0, len).length - 1;
  const x = last * stepX;
  const y = padY + (1 - pts[last]/max) * chartH;
  ctx.arc(x, y, 4, 0, Math.PI*2); ctx.fillStyle = color; ctx.fill();
  ctx.arc(x, y, 2, 0, Math.PI*2); ctx.fillStyle = '#fff'; ctx.fill();
  ctx.fillText(bytes(pts[last])+'/s', x, y-10);
}
```

### 详情页在表格视图中的位置

表格视图（最终版 v3：2列网格紧凑卡片）也有 `row-footer`，用圆点分隔 ↓速度·↑速度·运行·价格·流量·到期：
```css
.row-footer { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; border-top: 1px solid rgba(255,255,255,0.06); }
.row-footer .sep { width: 2px; height: 2px; border-radius: 50%; background: rgba(255,255,255,0.15); }
.footer-price { font-weight: 600; color: #10b981; background: rgba(16,185,129,0.1); padding: 0 6px; border-radius: 9999px; }
```

### 部署验证：详情页改动必须两步验证

```bash
# 第1步：本地验证（绕过 Cloudflare）
curl -s http://127.0.0.1:25774/ | grep -c 'sysinfo-grid'
# 应 >0

# 第2步：通过公网验证
curl -s https://<监控面板域名>/ | grep -c 'sysinfo-grid'
# 如果第1步有但第2步无 → Cloudflare 缓存，让用户硬刷新
```

### 详情页 UI 迭代历史

| 版本 | 改动 | 验证人 |
|------|------|--------|
| v1 (初始) | 6个metric卡 + sysinfo 1列 + 3个Canvas图表 | 用户 |
| v1.2.1 | 导航加国旗/OS图标、metric-value 14px→22px、metric-sub绝对值、sysinfo 2列网格、账单chip、图表端点圆点 | 用户 ✅ |

## 🇰🇵 国旗修复（flagEmoji 缺朝鲜）

GalaxyGlass 主题的 `flagEmoji()` 函数有两层映射：

1. `emojiToCode`：emoji → 国家码（`'🇰🇵': 'kp'`）
2. `regionMap`：地区名 → 国家码（`'朝鲜': 'kp'`）

**两处都必须补**，缺一不可：

```javascript
const emojiToCode = { '🇺🇸': 'us', '🇯🇵': 'jp', ..., '🇰🇵': 'kp' };  // ← 加入
const regionMap = { '东京': 'jp', ..., '朝鲜': 'kp' };              // ← 加入
```

之前被 MiniMax 搞了几天没搞出来，其实就加两个字符串的事。这个修复只对 GalaxyGlass 主题生效，komari binary 内置的根路径 `/` 仍然是缺 🇰🇵 的（需重新编译）。

```javascript
// ✅ 正确
if (uuid) {
  history.pushState({ uuid }, '', '/instance/' + encodeURIComponent(uuid));
  showDetailView(uuid);  // 必须手动调用
}

// ❌ 错误（URL 变但视图不切换）
if (uuid) history.pushState({ uuid }, '', '/instance/' + encodeURIComponent(uuid));
```