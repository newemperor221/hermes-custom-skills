# 朝鲜国旗 🇰🇵 不显示 — 根因分析（2026-05-09）

## 核心发现

komari 有**两套国旗渲染逻辑**，存在于不同位置：

### 1. komari-web 源码（正确方案）
`src/components/Flag.tsx` — 使用 `getTwemojiUrl()` 通用方案：
```typescript
const getTwemojiUrl = (emoji: string): string => {
  const codePoints = Array.from(emoji)
    .map((char) => char.codePointAt(0)!.toString(16))
    .join("-");
  return `https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/${codePoints}.svg`;
};
```
🇰🇵 → `1f1f0-1f1f5` → `https://cdn.jsdelivr.net/gh/twitter/twemoji@14.0.2/assets/svg/1f1f0-1f1f5.svg` ✅

### 2. komari binary embed.FS（硬编码方案，缺 🇰🇵）
komari binary 编译时将主题 HTML 嵌入，走根路径 `/` 的 JS 里硬编码：
```javascript
function flagEmoji(code) {
  const emojiToCode = { '🇺🇸': 'us', '🇯🇵': 'jp', '🇭🇰': 'hk', '🇰🇷': 'kr',
    '🇸🇬': 'sg', '🇩🇪': 'de', '🇬🇧': 'gb', '🇫🇷': 'fr', '🇨🇳': 'cn',
    '🇹🇼': 'tw', '🇦🇺': 'au', '🇨🇦': 'ca' };  // ← 缺 🇰🇵
  if (emojiToCode[code]) return emojiToCode[code];
  // ... fallback 逻辑
}
```
`flagEmoji('🇰🇵')` 返回 `''`（空字符串）→ `src="flagcdn.com/.svg"` → 图片隐藏。

## 验证命令

```bash
# 确认根路径 embed.FS 里 emojiToCode 缺 🇰🇵
curl -s http://localhost:25774/ | grep -o 'emojiToCode = {[^;]*}'

# 确认 flagcdn kp.svg 本身可用
curl -sI https://flagcdn.com/kp.svg | head -1
# HTTP/2 200 ✅

# 对比根路径 vs /themes/ 路由的 MD5
curl -s http://localhost:25774/ | md5sum
curl -s http://localhost:25774/themes/NodeGetGlass/dist/index.html | md5sum
# 不同 → 确认两套独立路径
```

## 解法

| 方案 | 难度 | 效果 |
|------|------|------|
| **GalaxyGlass 主题 JS 加一行（已验证 2026-05-10）** | **低** | **✅ 已修** |
| 从源码 build komari（改 Flag.tsx 用 twemoji） | 高 | 彻底修复 |
| 等作者修 emojiToCode + 发布新 binary | 低 | 看作者心情 |
| 删掉朝鲜节点 | 无 | 回避问题 |

### ✅ GalaxyGlass 主题修复（已验证可行）

在 `index.html` 的 `flagEmoji()` 函数中两处补上 🇰🇵：

```javascript
// 1. emojiToCode map
const emojiToCode = { '🇺🇸': 'us', '🇯🇵': 'jp', ..., '🇰🇵': 'kp' };

// 2. regionMap（防 DB region 是文字的情况）
const regionMap = { '东京': 'jp', ..., '朝鲜': 'kp' };
```

**上传方式**：scp 部署（不是 curl GitHub raw）：
```bash
scp -P 42185 /local/index.html root@107.172.231.70:/data/theme/GalaxyGlass/dist/index.html
```

**注意**：这个修复只对 GalaxyGlass 主题生效（因为只改了主题 JS，没有改 komari binary embed.FS）。如果你走的是 komari 内置主题的 `/` 根路径，还是要重新编译 binary。

**源码 build 步骤**：
```bash
git clone https://github.com/komari-monitor/komari-web
cd komari-web
# 修改 src/components/Flag.tsx：用 getTwemojiUrl 替换 emojiToCode 硬编码
npm run build

git clone https://github.com/komari-monitor/komari
cp -r komari-web/dist komari/public/defaultTheme/dist/
cp komari-theme.json komari/public/defaultTheme/
go build -o komari
# 替换 /opt/komari/komari，重启
```

## 为什么上传 GalaxyGlass 主题文件到 `/opt/komari/data/theme/` 没用

komari 路由分配：
- `GET /` → binary embed.FS（`emojiToCode` 缺 🇰🇵）
- `GET /themes/GalaxyGlass/...` → 磁盘文件（这套路由和根路径完全独立）

用户上传 GalaxyGlass 文件到 `/opt/komari/data/theme/GalaxyGlass/`，走的是 `/themes/` 路由，但用户访问的是 `/` 根路径。所以 patch 永远不生效。

## 数据库 region 字段 vs 国旗显示

- 数据库 `clients.region = '🇰🇵'` 只是字符串存储
- 前端 `flagEmoji()` 负责把 emoji 转成国家码
- `flagEmoji('🇰🇵')` → `''` → `flagcdn.com/.svg` → 看不到国旗
- **不等于** flagcdn.com/kp.svg 本身有问题（它返回 200）
