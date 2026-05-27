# 朝鲜国旗 🇰🇵 不显示 — 根因与解法（2026-05-09 修正）

## 状态

**未完全修复**。filter 按钮（`🇰🇵` 按钮）可显示，但节点卡片图标仍不显示。

## 根因：komari 的 theme 三层机制

komari 有三层独立的 theme 配置，**优先级从高到低**：

| 层级 | 来源 | 内容 | 朝鲜 🇰🇵 |
|------|------|------|----------|
| 1 | 二进制 `embed.FS` | 编译时嵌入，komari 启动后直接读内存 | ❌ 缺 🇰🇵 |
| 2 | 文件系统 `/opt/komari/data/theme/GalaxyGlass/` | komari 不读取（已废弃） | ✅ 有 |
| 3 | 数据库 `theme_configurations` 表 | komari **完全不读这个表** | ✅ 有 |

komari server 启动后，HTML/JS 全部从**内存中的 embed.FS** 读取，完全不碰文件系统和数据库的 theme 配置。

```sql
-- 数据库里的 emojiToCode（komari 不使用！）
SELECT short, data FROM theme_configurations WHERE short = 'GalaxyGlass';
-- 返回: {"emojiToCode":{"🇺🇸":"us",...,"🇨🇦":"ca","🇰🇵":"kp"}}  ← 没用
```

## 为什么 filter 按钮能显示 🇰🇵 但卡片图标不行？

**filter 按钮**走的是 Unicode 区域指示符算法，不依赖硬编码 map：

```typescript
// 默认主题 Flag.tsx 源码
const chars = Array.from(emoji); // 🇰🇵 → ['🇰','🇵']
const letter1 = String.fromCodePoint(chars[0].codePointAt(0) - 0x1F1E6 + 0x41); // 'K'
const letter2 = String.fromCodePoint(chars[1].codePointAt(0) - 0x1F1E6 + 0x41); // 'P'
// return 'KP' ✅
```

**卡片图标**走 `flagEmoji()` 查硬编码 `emojiToCode` map：

```javascript
flagEmoji('🇰🇵')
  → emojiToCode['🇰🇵']  // undefined（map 缺 key）
  → `flagcdn.com/${undefined}.svg`  // 404
```

## 验证方法

```bash
# 1. 确认 embed.FS 里 emojiToCode 缺 🇰🇵
curl -s http://localhost:25774/ | grep -o 'emojiToCode = {[^}]*}'
# 返回: { '🇺🇸': 'us', '🇯🇵': 'jp', ..., '🇨🇦': 'ca' }  ← 无 🇰🇵

# 2. 确认文件系统有 🇰🇵（但不生效）
grep '🇰🇵' /opt/komari/data/theme/GalaxyGlass/index.html
# 返回 7 处匹配 ✅

# 3. 确认数据库有 🇰🇵（但不生效）
sqlite3 /opt/komari/data/komari.db \
  "SELECT data FROM theme_configurations WHERE short = 'GalaxyGlass'" | grep '🇰🇵'
# 返回 🇰🇵 ✅

# 4. 浏览器控制台验证
flagEmoji.toString()
```

## 正确解法

### 方案 A：改源码 + 重新编译（唯一有效方案）

```bash
# 1. Clone komari-web 源码
git clone https://github.com/komari-monitor/komari-web.git
cd komari-web

# 2. 找到 emojiToCode 位置，添加：'🇰🇵': 'kp'

# 3. 重新编译并替换 /opt/komari/komari

# 4. 重启
rc-service komari restart   # Alpine
```

### 方案 B：提 issue/PR 等作者修复

- 仓库：https://github.com/komari-monitor/komari

## 已验证错误路径（不要做）

- ❌ 修改文件系统 `/opt/komari/data/theme/GalaxyGlass/index.html`（komari 不读取）
- ❌ 修改 `theme_configurations.data` 的 `emojiToCode`（komari 不读这个表）
- ❌ 二进制补丁（43MB Go binary，emoji 字节串不在 binary 中；BusyBox sed 会卡死）
- ❌ 认为 CDN 缓存问题（cloudflared tunnel 不是 CDN）
- ❌ 重启 komari server（embed.FS 在编译时固定，不受重启影响）
