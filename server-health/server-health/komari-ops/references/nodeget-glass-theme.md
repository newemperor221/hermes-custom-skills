# NodeGet Glass 主题

基于 NodeGet-Status 风格的 Komari 毛玻璃主题。

## 文件结构

```
NodeGetGlass/
├── komari-theme.json
└── dist/
    ├── index.html              # 完整主题（含 CSS/JS）
    └── assets/
        ├── images/
        │   ├── backdrop-desktop.jpg   # 1920x1080
        │   └── backdrop-mobile.jpg   # 1080x1920
        └── video/
            └── backdrop.mp4          # 可选，视频背景
```

## komari-theme.json

```json
{
  "name": "NodeGet Glass",
  "short": "NodeGetGlass",
  "description": "基于 NodeGet-Status 的液态玻璃风格主题",
  "version": "1.0.0",
  "author": "M78"
}
```

## 核心 CSS 变量

```css
:root {
  --glass-blur: 80px;
  --glass-opacity: 35;
  --glass-bg: rgba(0, 0, 0, calc(var(--glass-opacity) / 100));
  --glass-border: rgba(255, 255, 255, 0.1);
  --glass-border-strong: rgba(255, 255, 255, 0.15);
  --text-primary: rgba(255, 255, 255, 0.95);
  --text-secondary: rgba(255, 255, 255, 0.6);
  --text-muted: rgba(255, 255, 255, 0.45);
  --accent-color: #22c55e;
  --warning-color: #f59e0b;
  --danger-color: #ef4444;
  --radius: 16px;
  --radius-sm: 8px;
  --radius-full: 9999px;
}
```

## 毛玻璃效果类

| 类名 | 用途 |
|------|------|
| `.glass-card` | 主卡片容器，强模糊 |
| `.glass-nav` | 导航栏（滚动后模糊） |
| `.glass-btn` | 按钮 |
| `.glass-btn-icon` | 圆形图标按钮 |
| `.glass-input` | 胶囊输入框 |
| `.glass-badge` | 标签徽章 |

## 安装

1. 打包：`zip -r NodeGetGlass.zip NodeGetGlass/`
2. 上传到服务器：`scp -P 52137 NodeGetGlass.zip root@<洛杉矶2_IP>:/tmp/`
3. 解压到主题目录：`unzip -o /tmp/NodeGetGlass.zip -d /opt/komari/data/theme/`
4. 后台切换主题

## 背景视频：本地文件 vs 远程 URL

主题支持两种背景视频加载方式：

**方式 A：视频上传到主题包内（推荐）**
```html
video.src = '/assets/video/backdrop.mp4';
```
文件路径：`/opt/komari/data/theme/<theme>/dist/assets/video/backdrop.mp4`
上传：`scp -P 52137 video.mp4 root@<洛杉矶2_IP>:/opt/komari/data/theme/<theme>/dist/assets/video/`

**方式 B：远程直链（绕过服务器存储）**
```html
video.src = 'https://img.357561.xyz/wallpaper.mp4';
```
直接在 `index.html` 的 JS 中写入远程 URL，不占用服务器磁盘。
适合 56idc 这类极小磁盘（1.2G）的服务器。

> ⚠️ 远程 URL 必须是直链，服务器能访问，且 CORS 不限制 `<video>` 标签。

## 地区 + 标签筛选功能（buildTagFilters）

**Komari API 数据现状**：
- `tags` 字段是**空字符串** `""`，不是数组
- `region` 字段已经是 emoji 格式（如 `🇺🇸`、`🇯🇵`）
- 因此筛选器必须同时构建地区按钮和标签按钮

NodeGet-Status 原版有 `TagFilter` + `RegionFilter` 两个组件。定制主题需合并为一个 `buildTagFilters()` 函数：

```javascript
function buildTagFilters() {
  // === 地区筛选 ===
  const regionMap = new Map();
  nodesList.forEach(n => {
    const r = n.region || '';
    if (r) regionMap.set(r, (regionMap.get(r) || 0) + 1);
  });
  const regions = [...regionMap.entries()].sort((a, b) => b[1] - a[1]);

  const rContainer = document.getElementById('region-filters');
  if (rContainer) {
    if (regions.length > 0) {
      const rBtns = regions.map(([r, count]) => {
        const active = filterRegion === r;
        const s = active ? 'border-color:#10b981;color:#10b981;' : 'border-color:rgba(255,255,255,0.1);color:rgba(255,255,255,0.7);';
        const flagCode = flagEmoji(r);
        const flagImg = flagCode ? `<img src="https://flagcdn.com/${flagCode}.svg" alt="${r}" style="width:20px;height:14px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:6px;" loading="lazy" onerror="this.style.display='none'">` : '';
        return `<button class="glass-badge" style="${s}" data-region="${r}">${flagImg}${flagCode ? flagCode.toUpperCase() : r} <span style="font-size:11px;opacity:0.6;">(${count})</span></button>`;
      }).join('');
      const allActive = filterRegion === null;
      const allS = allActive ? 'border-color:#10b981;color:#10b981;' : 'border-color:rgba(255,255,255,0.1);color:rgba(255,255,255,0.7);';
      rContainer.innerHTML = `<div class="filters" style="display:flex;flex-wrap:wrap;gap:8px;">` +
        `<button class="glass-badge" style="${allS}" data-region="">全部</button>` + rBtns + `</div>`;
      rContainer.querySelectorAll('button').forEach(btn => {
        btn.style.cssText += 'background:rgba(255,255,255,0.05);';
        btn.addEventListener('click', () => {
          filterRegion = btn.dataset.region || null;
          buildTagFilters();
          render();
        });
      });
    } else {
      rContainer.innerHTML = '';
    }
  }

  // === 标签筛选（支持空 tags + 逗号分隔字符串）===
  const tagMap = new Map();
  nodesList.forEach(n => {
    (n.tags_list || []).forEach(t => { if (t) tagMap.set(t, (tagMap.get(t) || 0) + 1); });
    if (n.tags) {
      String(n.tags).split(',').filter(Boolean).forEach(t => tagMap.set(t.trim(), (tagMap.get(t.trim()) || 0) + 1));
    }
  });
  const allTags = [...tagMap.entries()].sort((a, b) => b[1] - a[1]);

  const tContainer = document.getElementById('tag-filters');
  if (tContainer) {
    if (allTags.length > 0) {
      const tBtns = allTags.map(([t, count]) => {
        const active = filterTag === t;
        const s = active ? 'border-color:#10b981;color:#10b981;' : 'border-color:rgba(255,255,255,0.1);color:rgba(255,255,255,0.7);';
        return `<button class="glass-badge" style="${s}" data-tag="${t}">${t} (${count})</button>`;
      }).join('');
      const allActive = filterTag === null;
      const allS = allActive ? 'border-color:#10b981;color:#10b981;' : 'border-color:rgba(255,255,255,0.1);color:rgba(255,255,255,0.7);';
      tContainer.innerHTML = `<div class="filters" style="display:flex;flex-wrap:wrap;gap:8px;">` +
        `<button class="glass-badge" style="${allS}" data-tag="">全部</button>` + tBtns + `</div>`;
      tContainer.querySelectorAll('button').forEach(btn => {
        btn.style.cssText += 'background:rgba(255,255,255,0.05);';
        btn.addEventListener('click', () => {
          filterTag = btn.dataset.tag || null;
          buildTagFilters();
          render();
        });
      });
    } else {
      tContainer.innerHTML = '';
    }
  }
}
```

**HTML 容器**（去掉 `hidden` 类）：
```html
<div id="region-filters"></div>
<div id="tag-filters"></div>
```

**调用时机**：`nodesList = merged` 之后、`render()` 之前：
```javascript
nodesList = merged;
buildTagFilters();  // ← 加载完成后调用一次
render();
```

**filter 逻辑**（`getFiltered()` 中）：
```javascript
// 地区筛选（直接比较 emoji）
if (filterRegion) {
  arr = arr.filter(n => n.region === filterRegion);
}
// 标签筛选
if (filterTag) {
  arr = arr.filter(n => {
    if (n.tags_list?.includes(filterTag)) return true;
    if (n.tags?.split(',').map(t => t.trim()).includes(filterTag)) return true;
    return false;
  });
}
```

## 国旗：图片 vs Emoji

Komari `/api/nodes` 的 `region` 已是 emoji（🇺🇸🇯🇵🇭🇰），但某些环境下 emoji 显示乱码。**用 flagcdn.com 图片代替 emoji**：

```javascript
// flagEmoji() 返回国家码字符串（如 'us' 'jp' 'hk'），用于拼接图片 URL
function flagEmoji(code) {
  if (!code) return '';
  const emojiToCode = { '🇺🇸': 'us', '🇯🇵': 'jp', '🇭🇰': 'hk', '🇰🇷': 'kr',
    '🇸🇬': 'sg', '🇩🇪': 'de', '🇬🇧': 'gb', '🇹🇼': 'tw' };
  if (emojiToCode[code]) return emojiToCode[code];
  const c = code.trim().toUpperCase();
  if (/^[A-Z]{2}$/.test(c)) return c.toLowerCase();
  return '';
}

// 卡片渲染国旗图片
${n.region ? `<img src="https://flagcdn.com/${flagEmoji(n.region)}.svg"
  alt="${n.region}" title="${n.region}" class="node-flag"
  loading="lazy" onerror="this.style.display='none'">` : ''}
```

## .glass-badge 样式（胶囊形筛选按钮）

nodeget-statusd 原版参数，**不要自己改**：

```css
.glass-badge {
  display: inline-flex;
  align-items: center;
  height: 2.25rem;              /* 36px，保证文字单行显示 */
  padding: 0 1rem;              /* nodeget-statusd 原版，不是 1.25rem */
  font-size: 14px;              /* 0.875rem = 14px */
  border-radius: 9999px;         /* 胶囊形，不是 8px */
  background: rgba(255,255,255,0.06);   /* 原版是 0.06 */
  backdrop-filter: blur(20px);           /* 原版是 20px */
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255,255,255,0.1);
  color: rgba(255,255,255,0.6);         /* 原版是 0.6 */
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  flex-shrink: 0;
}
```

**国旗图尺寸**：nodeget-statusd 原版是 `20×14px`（长方形 3:2），不是正方形：
```javascript
const flagImg = flagCode ? `<img src="https://flagcdn.com/${flagCode}.svg" alt="${r}"
  style="width:20px;height:14px;object-fit:cover;border-radius:2px;vertical-align:middle;margin-right:6px;"
  loading="lazy" onerror="this.style.display='none'">` : '';
```

激活态（选中）：`border-color:#10b981; color:#10b981;`

## 搜索框（点击展开、点别处收回）

用户明确要求：初始是 36×36 圆形图标按钮 → 点击后展开 240px 显示输入框 → 点击页面其他位置收回。

**CSS**：
```css
.search-box {
  display: flex;
  align-items: center;
  border-radius: 9999px;
  border: 1px solid rgba(255,255,255,0.1);
  background: rgba(255,255,255,0.06);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  transition: all 0.6s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  width: 36px;
  height: 36px;
  overflow: hidden;
}
.search-box.open { width: 240px; }
.search-box .search-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.search-box .search-icon svg { width: 16px; height: 16px; color: rgba(255,255,255,0.5); }
.search-box input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #fff;
  font-size: 13px;
  padding: 0 12px 0 0;
  opacity: 0;
  transition: opacity 0.4s 0.2s;
  min-width: 0;
}
.search-box.open input { opacity: 1; }
```

**HTML**：
```html
<div class="search-box" id="search-box">
  <div class="search-icon">
    <svg width="16" height="16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
    </svg>
  </div>
  <input type="search" id="search-input" placeholder="搜索节点…" style="flex:1;background:transparent;border:none;outline:none;color:#fff;font-size:13px;padding:0 12px 0 0;opacity:0;transition:opacity 0.4s 0.2s;min-width:0;">
</div>
```

**JS**：
```javascript
const searchBox = document.getElementById('search-box');
const searchInput = document.getElementById('search-input');

searchBox.addEventListener('click', (e) => {
  e.stopPropagation();
  searchBox.classList.add('open');
  searchInput.style.opacity = '1';
  setTimeout(() => searchInput.focus(), 300);
});

document.addEventListener('click', (e) => {
  if (!searchBox.contains(e.target)) {
    searchBox.classList.remove('open');
    searchInput.style.opacity = '0';
    searchInput.blur();
  }
});

searchInput.addEventListener('input', (e) => {
  searchQuery = e.target.value;
  render();
});
```

## 国旗 CSS 类

```css
.node-flag {
  width: 20px;
  height: 14px;
  object-fit: cover;
  border-radius: 1px;
  flex-shrink: 0;
}
```

## Komari API 完整端点

| 端点 | 认证 | 返回内容 |
|------|------|---------|
| `/api/public` | 否 | `{sitename, theme}` |
| `/api/nodes` | 否 | 节点静态信息，`region="🇺🇸"`, `tags=""`（空字符串） |
| `/api/recent/{uuid}` | 否 | 节点动态数据（CPU/内存/网络/uptime） |
| `/api/admin/node/list` | 是 | 返回 **HTML 页面**，非 JSON，主题别用这个 |

## tags 字段处理

Komari `/api/nodes` 的 `tags` 是**空字符串 `""`**，不是数组，也可能是逗号分隔字符串：

```javascript
// mergeNodeData 中转换
tags_list: node.tags ? String(node.tags).split(',').filter(t => t.trim()) : [],
```

## 站点名称（银河探针）

Komari `/api/public` 返回 `sitename` 字段，但主题默认显示硬编码名称。导航栏、页脚应显示"银河探针"：

```html
<!-- 导航栏 -->
<span class="navbar-title" id="site-name">银河探针</span>
<!-- 页脚 -->
<span id="footer-site">银河探针</span>
```

API 动态覆盖：
```javascript
if (siteInfo.sitename) {
  document.getElementById('site-name').textContent = siteInfo.sitename;
  document.title = siteInfo.sitename;
}
```

## 字体规格（实测值）

| 元素 | 正确值 | 常见错误 |
|------|--------|---------|
| 导航栏标题 `.navbar-title` | `18px` | `1rem` (14px，偏小) |
| 导航栏搜索框/按钮文字 | `14px` | — |
| 底部栏标题 `.footer-brand span` | `12px` | `14px`（不应加粗 `font-weight:600`）|
| 底部栏其他文字/链接 | `12px` | — |

> ⚠️ 导航栏左标题要和右边组件大小一致 → 用 18px。底部栏标题不加粗，保持 12px，和其他文字统一。

## 浏览器缓存问题

主题更新上传后，浏览器可能缓存旧 `index.html`。**必须 Ctrl+Shift+R 强制刷新**，或用隐身模式验证。

## 依赖资源

- 桌面端背景图：1920x1080，保存到 `dist/assets/images/backdrop-desktop.jpg`
- 移动端背景图：1080x1920，保存到 `dist/assets/images/backdrop-mobile.jpg`
- 视频背景（可选）：用方式 A 上传，或用方式 B 远程 URL
