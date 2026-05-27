# GalaxyGlass 节点卡片（node-card）布局规范

> 创建：2026-05-10 | 上次更新：2026-05-10 | **状态：✅ 用户确认定稿**（用户反馈："不错就这样"）

## 卡片整体布局

```
┌──────────────────────────────────────┐
│ ● 🐧 Acck | 东京            🇯🇵     │ ← header: status + os-icon + name + flag(28×20)
│ Debian · kvm · Intel                 │ ← specs: 一行硬件摘要
│ CPU   ████████░░ 4.0%               │
│ 内存 ██████░░░░ 25.6%  121MB/474MB  │ ← metrics: 3个进度条
│ 磁盘 ██░░░░░░░░ 17.1%  1.3G/7.8G    │
│ ↑ 5.5KB/s          ↓ 256B/s         │ ← network: 跟随 metrics 区，不在 footer
│──────────────────────────────────────│
│ 🕐 15天 · 📊 70G/500G · ¥148/年  286天│ ← footer: 单行，圆点分隔
└──────────────────────────────────────┘
```

## 网格布局（nodes-grid）

```css
.nodes-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  align-content: start;
  min-height: calc(100vh - 380px);
}
```

**用户确认 3 列布局**（2026-05-10）：在 1124px 容器下，`minmax(320px, 1fr)` 自然产生 3 列，单卡约 340px 宽、308px 内容区。比 2 列（太空）或 4 列（太挤）更平衡。移动端自动坍缩至 2 列/1 列，无需手写断点。

---

（以下内容不变，略缩显示...）

## 一、Header — node-card-header

### HTML 结构

```html
<div class="node-card-header">
  <span class="node-status online"></span>     <!-- 绿色圆点 / 红色圆点 -->
  <img src="os-icon" class="node-os-icon">     <!-- OS 图标（20×20） -->
  <span class="node-name">Acck | 东京</span>   <!-- 节点名，flex:1，ellipsis -->
  <div class="node-region">                    <!-- 国旗容器 -->
    <img src="flagcdn.com/jp.svg" class="node-flag">  <!-- 28×20 -->
  </div>
</div>
```

### 国旗（flag）与地区

```css
.node-flag { width: 28px; height: 20px; object-fit: cover; border-radius: 2px; flex-shrink: 0; }
.node-region { display: flex; align-items: center; gap: 6px; flex-shrink: 0; }
```

**重要**：`n.region` 的值是 emoji 国旗（`🇯🇵`、`🇺🇸`、`🇭🇰`），不是文字名。**不要加 `.node-region-text`**，因为 emoji 跟 flag 图片重复。直接显示 flag image 就够了。

**尺寸变化史**：20×14 → 28×20（2026-05-10 用户认可 ✅）

## 二、Specs 行 — node-specs

取代原来的 `.node-info`（只显示 OS · Virt 两段）：

```css
.node-specs {
  font-size: 11px;
  font-family: var(--font-mono);
  color: rgba(255,255,255,0.35);
  padding: 2px 0;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
```

### JS 生成逻辑

```javascript
const specParts = [];
if (n.os) specParts.push(n.os.split(' ')[0]);          // "Debian"
if (n.virtualization) specParts.push(n.virtualization); // "kvm"
if (n.cpu_name) specParts.push(
  n.cpu_name.replace(/\(R\).*$|\(TM\).*$|\s+[0-9].*$/, '').trim()
); // "Intel" / "AMD" / "QEMU" / "ARM"
```

**CPU 名称截取规则**：去掉 `(R)`/`(TM)` 品牌后缀 + 去掉型号数字部分，只留第一个词。
- `Intel(R) Xeon(R) Gold 5118` → `Intel`
- `AMD Ryzen 9 7950X` → `AMD`
- `QEMU Virtual CPU version 2.5+` → `QEMU`

**间距**：`gap: 8px`（flex wrap，超长时换行不挤压）

## 三、Metrics 区 — 3 个进度条 + 1 行网络

### CSS

```css
.metrics { display: flex; flex-direction: column; gap: 10px; }
.metric-row { display: flex; flex-direction: column; gap: 4px; }
.metric-header { display: flex; justify-content: space-between; font-size: 12px; }
.metric-label { color: rgba(255,255,255,0.6); font-size: 10px; }
.metric-value { font-weight: 500; color: var(--text-primary); font-size: 14px; }
.metric-bar { height: 6px; background: rgba(255,255,255,0.1); border-radius: 9999px; overflow: hidden; }
.metric-fill { height: 100%; border-radius: 9999px; transition: width 0.3s; }
.metric-fill.low { background: #10b981; }
.metric-fill.medium { background: #f59e0b; }
.metric-fill.high { background: #ef4444; }
.metric-sub { font-size: 10px; font-family: var(--font-mono); color: rgba(255,255,255,0.35); }
```

**CPU 不再显示 `.metric-sub`** — CPU 型号已移至 specs 行。
**ram 和 disk 保留 `.metric-sub`** — 显示 `121MB / 474MB` 等用量数值。

### 网络速率行（network-row）

```css
.network-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 2px 0;
}
.network-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-family: var(--font-mono);
  color: rgba(255,255,255,0.5);
}
.network-item svg { width: 12px; height: 12px; }
```

**为什么网络要移到 metrics 里**：网络速率是**实时指标**（跟 CPU/内存/磁盘同类），之前放在 footer 不合理。

### JS 模板

```html
<div class="network-row">
  <span class="network-item">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 10l7-7m0 0l7 7m-7-7v18"/>  <!-- ↑ 上传箭头 -->
    </svg>
    ${bytes(n.network_in || 0)}/s
  </span>
  <span class="network-item">
    <svg fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 14l-7 7m0 0l-7-7m7 7V3"/>  <!-- ↓ 下载箭头 -->
    </svg>
    ${bytes(n.network_out || 0)}/s
  </span>
</div>
```

## 四、Footer — 单行信息栏

### 改前（3 行）
```
↑ 5KB/s | ↓ 256B/s        ← 网络速率
🕐 15天          3秒前     ← 在线时长 + 更新时间
📊 70G/500G | ¥148/年 | 286天 ← 流量 + 价格 + 到期
```

### 改后（1 行）
```
🕐 15天 · 📊 70G/500G · ¥148/年  286天
```

### CSS

```css
.node-footer {
  padding-top: 8px;
  border-top: 1px solid rgba(255,255,255,0.06);  /* 细线代替虚线 */
  font-size: 12px;
  font-family: var(--font-mono);
  color: rgba(255,255,255,0.35);
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}
.node-footer-sep {
  width: 3px;
  height: 3px;
  border-radius: 50%;
  background: rgba(255,255,255,0.15);
  flex-shrink: 0;
}
.node-footer-item {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}
.node-footer-item svg { width: 12px; height: 12px; }
.node-footer-price {
  margin-left: auto;
  font-weight: 600;
  color: var(--accent);                       /* 绿色文字 */
  background: rgba(16,185,129,0.1);           /* 淡绿色背景 */
  padding: 1px 8px;
  border-radius: 9999px;                      /* 胶囊形 */
  font-size: 11px;
}
.node-footer-expire {
  color: rgba(255,255,255,0.4);
  white-space: nowrap;
}
```

### 删除的旧 CSS 类
- `.node-footer-row` — 不再需要（之前有3行，每行一个row）
- `.node-footer-time` — 不再需要（last_update 时间已移除）
- `.node-info` — 被 `.node-specs` 取代

### 价格 badge 样式

价格用绿色胶囊 badge（`margin-left: auto` 推到右侧）：
- 背景：`rgba(16,185,129,0.1)`（淡绿透明背景）
- 文字：`var(--accent)`（绿色 `#10b981`）
- 圆角：`9999px`（胶囊形）
- padding：`1px 8px`

示例：`¥148.88/年`、`¥10/月`、`¥297/3年`、`$6.45/年`

## 五、Footer 显示逻辑（JS）

```javascript
const uptimeStr = uptime(n.uptime);  // "15天19时"
const trafficUsed = bytes((n.network_total_received||0)+(n.network_total_transmitted||0));  // "70.6 GB"
const trafficLimit = n.traffic_limit || null;  // 500 GB 或 null
const priceStr = n.price
  ? `${n.currency||'¥'}${n.price}/${n.billing_cycle===365?'年':n.billing_cycle===30?'月':n.billing_cycle===0?'永久':'期'}`
  : '-';
const expireDays = n.expired_at
  ? Math.max(0, Math.ceil((new Date(n.expired_at).getTime()-Date.now())/86400000))+'天'
  : '-';
```

**格式说明**：
- uptime：始终有值（`0天` 也显示）
- traffic：带 limit 显示 `70G/500G`，无 limit 只显示 `70G`
- price：`¥148.88/年`、`-`（无价格）、`¥10/月`
- expire：`286天`、`-`、`0天`（已过期）

## 六、性能注意事项

### JS 预计算（避免模板内重复计算）

在 `renderCard()` 函数顶部预计算所有值，不要在模板字符串内多次调用 `uptime()`、`bytes()`：

```javascript
// ✅ 正确
const uptimeStr = uptime(n.uptime);
const trafficUsed = bytes(...);
const priceStr = ...;
const expireDays = ...;

// ❌ 错误（模板内调用函数，每次 render 重复执行）
<-- ${uptime(n.uptime)} ← 每次 render 都计算
```

### 删除的旧数据

从卡片模板中移除了：
- `age(n.last_update)` — 更新时间（footer line 2 已删除）
- CPU 型号的 `.metric-sub` — 移至 specs 行
- 网络速率的 `.node-footer-row` — 移至 metrics 区

## 七、标签（tags）位置

```css
.node-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 6px; }
.tag {
  padding: 2px 8px;
  font-size: 10px;
  border-radius: 6px;
  background: rgba(255,255,255,0.06);
  color: rgba(255,255,255,0.4);
}
```

Tags 在 footer 下面（`.node-footer` 下面，`.node-card` 闭合前）。如果卡片没 tags，整个 `.node-tags` div 不渲染。

## 八、用户确认的最终设计

| 设计项 | 状态 | 确认时间 |
|--------|------|---------|
| Flag 28×20，无文字 | ✅ 定稿 | 2026-05-10 |
| Specs 行含 CPU 型号 | ✅ 定稿 | 2026-05-10 |
| 网络速率在 metrics 区 | ✅ 定稿 | 2026-05-10 |
| Footer 单行（uptime · traffic · price · expire） | ✅ 定稿 | 2026-05-10 |
| 价格绿色胶囊 badge | ✅ 定稿 | 2026-05-10 |
| 3 列网格布局（auto-fill minmax 320px） | ✅ 定稿 | 2026-05-10 |
| 删除旧 CSS（.node-footer-row/.node-footer-time/.node-info） | ✅ 定稿 | 2026-05-10 |

**用户最终反馈**："不错就这样"

## 九、常见问题

### 问：为什么 region 文字不加了？
n.region 的值是 emoji 国旗（如 `🇯🇵`、`🇺🇸`），如果显示成文字就跟 flag 图片完全重复。flag 图片 28×20 已经足够大，能看清。

### 问：footer 单行放不下内容怎么办？
用 `flex-wrap: wrap`，超宽时自动换行。实际在 300-340px 宽的卡片上，footer 内容（uptime + traffic + price + expire）最多约 200px，有足够空间。

### 问：价格 badge 为什么用绿色？
`var(--accent)` = `#10b981` 是面板的主色。绿色 badge 传递"正向"（费用已付、仍在服务期）的视觉信息。到期为 0 或负数时不显示 badge（price = '-'）。
