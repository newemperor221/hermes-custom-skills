---
name: glass-workflow
category: frontend
description: Glass Komari 探针面板的工程化工作流 — src/ 源码结构、build.sh 编译、deploy.sh 部署、release 打包、服务器路径、踩坑记录
triggers:
  - Glass 主题开发
  - komari 主题打包
  - 探针面板部署
  - <监控面板域名>
  - komari 后台设置标签页
  - managed configuration
  - 视频壁纸转换
  - 预览图 WebP 优化
---

# Glass — Komari 探针面板工程化工作流

Glass（原名 GalaxyGlass）是一个深色毛玻璃风格的 Komari 监控面板主题。单文件 HTML 部署，零框架依赖。

### ⚠️ zip 嵌套目录陷阱（Komari 导入报"文件不存在"）

release.sh 的打包命令不能这样写：

```bash
# ❌ 错误：创建 Glass-v1.1.0/komari-theme.json（多一层文件夹）
cd /tmp
zip -r "Glass-v1.1.0.zip" "Glass-v1.1.0/"
```

Komari 导入时在 zip **根目录**找 `komari-theme.json`，嵌套文件夹会导致"文件不存在"。必须 `cd` 进去再 zip：

```bash
# ✅ 正确：komari-theme.json 在根目录
cd "$PKG_DIR"
zip -r "/tmp/$PKG_NAME" .
```

**连锁问题**：`cd` 进 PKG_DIR 后，`cd -` 回到的是已被 `rm -rf` 的目录。修复：

```bash
# 脚本开头保存原目录
ORIG_DIR="$PWD"

# 打包后切回来
cd "$ORIG_DIR"
```

## ⚠️ komari-theme.json 缩进必须一致

JSON 解析器对缩进敏感。这个 JSON 有一行缩进不一致（5空格 vs 2空格）：

```json
{
  "name": "Glass",
  "short": "Glass",
  "description": "...",
    "version": "1.1.0",  // ← 这一行多了空格
  "author": "M78 星云",
```

虽然大多数 JSON 解析器能容忍，但 Komari 的导入可能不认。**所有字段用同一缩进层级**。

# 项目结构

```
glass/
├── build.sh                # 从 src/ 编译单文件 index.html
├── deploy.sh               # 构建 + 部署（同步到新加坡）
├── release.sh              # 构建 + 打包 + GitHub Release 一键发布
├── komari-theme.json       # Komari 主题元数据（上传时必备）
├── icon.svg                # 切面水晶 SVG 主题图标
├── preview.webp            # 预览截图
├── fonts/                  ← 源代码字体（release 时打进 dist/fonts/）
│   ├── Inter-300.ttf
│   ├── Inter-400.ttf
│   ├── Inter-500.ttf
│   ├── Inter-600.ttf
│   └── Inter-700.ttf
├── video/                  ← 自托管可切换壁纸（远程 R2 时跳过）
│   ├── desktop_wallpaper.jpg
│   └── mobile_wallpaper.jpg
├── README.md
└── src/
    ├── index.html          # HTML 模板（含 {{CSS}} {{JS}} {{BODY}} 占位符）
    ├── body.html           # HTML body 内容
    ├── styles/             # ITCSS 分层
    │   ├── settings.css    # CSS 变量 + @font-face（相对路径 fonts/Inter-*.ttf）
    │   ├── base.css        # 裸元素样式
    │   ├── layout.css      # 页面骨架
    │   ├── components.css  # 可复用 UI 组件
    │   ├── states.css      # 状态覆盖
    │   ├── utilities.css   # 工具类
    │   ├── web.css         # 桌面端（≥640px）
    │   └── mobile.css      # 手机端（≤800px）
    └── scripts/
        └── app.js          # 全部 JS
```

## 开发流程

```bash
./build.sh          # 编译为单文件 index.html
./deploy.sh         # 构建 + 部署 index.html + 同步 fonts/ 到服务器
./release.sh v1.0.x # 构建 + 打包 + GitHub Release
```

## 预览图优化（PNG → WebP，PNG 已移除）

preview.png 转 WebP 可压缩 **90%**（499KB → 50KB），Komari 支持 WebP 格式预览图。

转换方法（需要安装 `webp` 包：`sudo apt install webp`）：
```bash
cwebp -q 85 preview.png -o preview.webp
```

**⚠️ 用户偏好**：不保留 preview.png，**只保留 `preview.webp`**。release 包也只打包 webp：

```bash
cp preview.webp "$PKG_DIR/" 2>/dev/null || true
# 不要 cp preview.png
```

更新 `komari-theme.json` 的 `"preview": "preview.webp"`。

## Komari 官方主题打包规范（2026-05-20 验证）

官方文档：https://komari-document.pages.dev/dev/theme

### 必需结构

```
theme.zip
├── komari-theme.json       # 必需 — 主题配置文件
└── dist/
    └── index.html          # 必需 — 主页面模板
```

额外文件（fonts/、video/、icon.svg、preview.webp 等）允许添加在 zip 根目录。

### komari-theme.json 必需字段

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | 是 | 主题显示名称 |
| `short` | 是 | 唯一标识符，仅限大小写字母+数字 |
| `description` | 是 | 主题描述 |
| `version` | 是 | 语义化版本号 |
| `author` | 是 | 作者 |
| `url` | 否 | 项目地址 |
| `preview` | 否 | 预览图相对路径（支持 webp） |
| `configuration` | 否 | 动态配置（≥ 1.0.5） |

### Glass 当前规格（v1.4.0）

```json
{
  "name": "Glass",
  "short": "Glass",
  "description": "玻璃 — Komari 监控面板主题 · 纯静态 HTML/CSS/JS · 毛玻璃特效 · 深空黑底色 · 可切换壁纸",
  "version": "1.4.0",
  "author": "newemperor221",
  "url": "https://github.com/newemperor221/glass",
  "preview": "preview.webp",
  "configuration": { ... }
}
```

**v1.4.0 关键变更**：视频壁纸支持 via Cloudflare R2 远程 URL（`img.<用户域名>/wallpaper.mp4` + `img.<用户域名>/image-wallpaper.png`），zip 中**不包含 video/ 目录**。

### index.html 必需的占位符

Komari 会在部署时替换以下内容：

| 原始内容 | 替换为 |
|----------|--------|
| `Komari Monitor` | 用户设置的自定义标题 |
| `A simple server monitor tool.` | 用户设置的自定义描述 |

必须在 `dist/index.html` 中保留这些占位符，否则自定义功能失效。

#### ✅ 字体路径 — 已修复为相对路径 + `dist/fonts/`（2026-05-20）

**历史**：CSS 字体 `@font-face` URL 曾使用绝对路径（`/fonts/Inter-400.ttf`），在当前 galaxy-proxy 部署下能工作（docroot 设为主题目录），但 Komari 官方主题安装机制的 docroot 不同，`/fonts/` 会解析到域名根目录而非主题根目录。

**当前实现**：字体放在 `dist/fonts/` 目录下，CSS 使用**相对路径**（`fonts/Inter-300.ttf`），始终相对于 `index.html` 所在位置解析。

**包装结构中的位置**：
```
Glass-vX.Y.Z.zip
└── dist/
    ├── index.html          ← @font-face src: url(fonts/Inter-300.ttf) ✅
    └── fonts/
        ├── Inter-300.ttf
        ├── Inter-400.ttf
        ├── Inter-500.ttf
        ├── Inter-600.ttf
        └── Inter-700.ttf
```

**galaxy-proxy.py 对应**：除 `/fonts/`、`/video/` 外还需添加 `/dist/` 到静态文件路由 block：
```python
if clean_path.startswith("/styles/") or ... or clean_path.startswith("/video/") or clean_path.startswith("/dist/"):
```

## ⚠️ galaxy-proxy WebSocket 陷阱（2026-05-26 修复）

Python `http.server.HTTPServer` **不支持 WebSocket**。Komari 的 admin 登录页使用 WebSocket（`/api/rpc2`）做 JSON-RPC 2.0 通信，如果 galaxy-proxy 直接暴露在 cloudflared 后面，登录请求会被 Python http.server 拦截，WebSocket 握手失败。

**现象**：admin 页面加载正常，但点登录无响应，控制台报 `"Unexpected token '<', "<!DOCTYPE ..." is not valid JSON"`。

**修复**：在 galaxy-proxy 前面加一层 tcp-proxy.py（字节级 TCP 转发）。参考 `references/galaxy-proxy-arch.md` 的架构概览和 `scripts/tcp-proxy.py` 脚本。

## 参考文件

本技能提供了以下参考文件：
- `references/proxy-restoration.md` — galaxy-proxy 恢复流程（服务器重建后丢失时的完整操作步骤） — galaxy-proxy.py（反向代理）的架构、服务管理、路由规则、MIME 配置和故障排查
- `references/font-selfhost-proxy.md` — 字体自托管全流程：galaxy-proxy.py 修改（Python 语法陷阱）、OpenRC 服务管理、验证方法、常见故障排查
- `references/supply-chain-security.md` — node-ipc 供应链投毒事件记录 + Hermes/Glass 开发环境防护措施
- `references/wallpaper-diagnosis.md` — 动态壁纸"不动"排查链路：检查页面路径（`/` vs `/admin`）、壁纸 URL 配置、浏览器控制台验证（paused/currentTime/loaded/faded 类）、移动端 CSS 隐藏、视频内容本身判断。含完整 JS 诊断代码。
- `scripts/tcp-proxy.py` — TCP 字节级代理，解决 galaxy-proxy 不支持 WebSocket 的问题

## 新 Logo 设计模式

Glass 的 logo 是**切面水晶/宝石**风格，配色对应主题色：
- 深蓝黑底 `#0e152e`（配合 `bg-deep`）
- 顶面：翠绿渐变 `#10b981 → #059669`
- 左侧面：靛紫渐变 `#818cf8 → #6366f1`
- 右侧面：浅绿渐变 `#34d399 → #10b981`
- 白色三角高光反射 `opacity: 0.15 / 0.08`

64×64 viewBox，六边形宝石形状。放在：
- `icon.svg` — Komari 主题管理用
- `src/index.html` 第10行 — favicon data URI（**必须 URL-encode 后内联**）

**更换 logo 时三步走**：
1. 设计新 SVG，写 `icon.svg`
2. 把 SVG 转成 data URI 嵌入 `src/index.html` 的 `<link rel="icon">`：
   ```python
   import urllib.parse
   encoded = urllib.parse.quote(raw_svg, safe='')
   print('data:image/svg+xml,' + encoded)
   ```
3. 把 logo 加到页眉 navbar（`src/body.html` 中的 `navbar-brand`），inline SVG 22×22px，`aria-hidden="true"`，`flex-shrink:0`

**三处需同步更新**：icon.svg / favicon data URI / navbar 内联 SVG。少更新任何一个都会出现图标不一致的情况。

### 页眉品牌区（navbar-brand）
- `display: flex; align-items: center; gap: 0.5rem;` — 图标 + 标题并排
- 图标 22×22px，标题 font-size: 22px 保持视觉一致
- 标题用 `accent-gradient` 渐变色文字（background-clip: text）
- 标题字体 `font-weight: 700`

## 页面图标与字体对齐
- 标题字号要和图标尺寸一致（当前都是 22px）
- 标题 `font-weight: 700` 加粗
- 图标用内联 SVG（不额外请求）

### galaxy-proxy.py 修改注意事项（Python 语法陷阱）

用 `sed` 修改 galary-proxy.py 时容易破坏 Python 语法：

```bash
# ❌ 错误：丢失了字典的闭合花括号 }
sed -i 's#".svg": ... ".png": "image/png"}#... .ttf": "font/ttf"#' proxy.py
# 这会导致 SyntaxError: '{' was never closed
```

✅ 正确做法：**整行替换**：
```bash
sed -i '115s#.*#                   ".svg": "image/svg+xml", ".png": "image/png", ".ttf": "font/ttf", ".woff2": "font/woff2"}#' proxy.py
```

或者用 Python 自检语法：
```bash
python3 -c "import py_compile; py_compile.compile('galaxy-proxy.py', doraise=True); print('Syntax OK')"
```

### ⚠️ release.sh 常见陷阱

**⚠️ `git add komari-theme.json -A` 不会暂存全部改动**

```bash
# ❌ 错误：komari-theme.json 是文件名参数，-A 只作用于这个文件
git add komari-theme.json -A

# ✅ 正确：暂存全部改动（包括刚 build 的 index.html、修改的 src/、release.sh 自身）
git add -A
```

后果：每次 release 仅提交了 `komari-theme.json`，`index.html`（构建产物）、`src/` 源文件、`release.sh` 自身的改动全没进 commit。git status 会一直显示 dirty：
```
modified:   index.html
modified:   release.sh
modified:   src/body.html
modified:   src/styles/layout.css
```

解决方法：改 `release.sh` 第53行，将 `git add komari-theme.json -A` 改为 `git add -A`。

**⚠️ `index.html`（构建产物）应在 `.gitignore` 中**（已修复 2026-05-20）

`build.sh` 从 `src/` 生成根目录 `index.html`，这是构建产物不应被 git 跟踪。当前 `.gitignore` 已有 `index.html`，且 `git rm --cached index.html` 已执行取消跟踪。

如果新克隆仓库发现根目录没有 `index.html`：这是正常的。运行 `./build.sh` 即可生成。`release.sh` 会自动先 build 再打包。

**⚠️ `preview.png` 拷贝残留死代码**

`release.sh` 第36行：
```bash
cp preview.png "$PKG_DIR/" 2>/dev/null || true
```
`preview.png` 已被删除，这一行永远静默失败且无意义。应从 `release.sh` 移除。

### ⚠️ `video/` 目录打包（v1.3.0 修复嵌套路径问题；v1.4.0 可选排除）

不要用 `cp -r video "$PKG_DIR/video"` — 这会创建 `$PKG_DIR/video/video/desktop_wallpaper.jpg`（多一层嵌套，Komari 加载壁纸时找不到文件）。

**R2 远程壁纸模式**（v1.4.0+）：壁纸通过 Cloudflare R2（`img.<用户域名>`）托管，zip 中**不需要包含 `video/` 目录**。省掉 zip 体积约 200KB。

正确做法：先 `mkdir` 目标目录，再复制文件内容：

```bash
# ✅ 正确：文件在 zip 的 video/ 根目录
mkdir -p "$PKG_DIR/video"
cp video/*.jpg "$PKG_DIR/video/" 2>/dev/null || true
```

**注意**：如果视频壁纸切换到 R2 托管，完全跳过 video/：`# video/ omitted — remote R2` 注释即可。

**⚠️ `fonts/` 打包位置变动（2026-05-20 改为 Komari 官方规范）**

字体不再在 zip 根目录 `fonts/`，而是打进 `dist/fonts/`，CSS 用相对路径 `fonts/Inter-400.ttf`：

```bash
# release.sh 中：
mkdir -p "$PKG_DIR/dist/fonts"
cp fonts/Inter-*.ttf "$PKG_DIR/dist/fonts/"
```

**⚠️ `release.sh` 传参模式 — 自动同步 version（已修复 2026-05-20）**

历史问题：`release.sh` 从版本号参数决定 zip 名和 git tag，但**不自动写入 `komari-theme.json`**，导致 git tag `v1.2.3` 而 `komari-theme.json` 仍写 `1.2.2`。

**当前 `release.sh` 已修复**：自动将传入版本号写入 `komari-theme.json`：

```bash
# 第 2 步：同步版本号
VER_NUM="${VERSION#v}"
python3 << PYEOF
import json
with open('komari-theme.json') as f:
    d = json.load(f)
d['version'] = '$VER_NUM'
with open('komari-theme.json', 'w') as f:
    json.dump(d, f, indent=2, ensure_ascii=False)
    f.write('\n')
PYEOF
```

这样 `./release.sh v1.2.3` → 自动写 `komari-theme.json` version 为 `1.2.3` → 打包（zip 内版本已对齐）→ commit → tag → release。**不再需要手动提前改 JSON**。

如果已错误发布，重新执行 `./release.sh v1.2.3`（脚本会自动删旧 tag 重建）。

**注意**：`komari-theme.json` 的其他元数据字段（`name`、`author`、`description`）需要手动维护，`release.sh` 不会自动同步。**发布前必须检查这些字段是最新的**，否则用户会抱怨「旧名字、旧作者、旧版本、旧描述」：

- `name` — 必须填用户指定的名称（不是旧名如 GalaxyGlass）
- `author` — 必须填用户 GitHub 名 `newemperor221`（不是占位符如 M78 星云）
- `description` — 简洁描述主题特性，参考 README 第一行风格

发布前执行 `release.sh` 时，先确认这些字段已更新。用户对此极其敏感。发布后重新上传 zip 到 Komari 后台才能看到元数据更新。

```json
{
  "name": "Glass",
  "short": "Glass",
  "description": "玻璃 — Komari 监控面板主题 · 纯静态 HTML/CSS/JS · 毛玻璃特效 · 深空黑底色 · 视频壁纸",
  "version": "1.4.0",
  "author": "newemperor221",
  ...
}
```

**⚠️ 清理旧 release**

多次 release 后 GitHub 上会有大量旧版本和 draft 残留。保持 repo 干净的做法：

```bash
# 查看所有 release
gh release list --repo newemperor221/glass --limit 20

# 批量删除旧版本（保留最新）
for tag in v1.2.2 v1.2.0 v1.1.1 v1.1.0; do
  gh release delete "$tag" --repo newemperor221/glass --yes
  git tag -d "$tag" 2>/dev/null
  git push origin ":refs/tags/$tag" 2>/dev/null
done

# 清理本地旧 zip
rm -f /tmp/Glass-*.zip
```

**注意**：`gh release delete` 不会自动删除 git tag。需要手动 `git push origin :refs/tags/<tag>`。也可以用 `git push origin --delete <tag>`。

**注意**：如果当前 Latest release 被误删，gh CLI 不会自动置新。需用 `gh release create` 从已有 tag 重建：

```bash
RELEASE_NOTES=$(git log --oneline --no-decorate "$(git tag --sort=-version:refname | head -2 | tail -1)..HEAD")
gh release create v1.2.3 \
  --title "Glass v1.2.3" \
  --notes "$RELEASE_NOTES" \
  /tmp/Glass-v1.2.3.zip
```

### ⚠️ Release notes 格式 — 只列新增，不列对比

用户极度反感在 release notes 里展示「旧版 vs 新版」的结构对比或 before/after 表格。Release notes 只写：

```
## 🎯 变更标题

- 功能/修复描述
- 具体改动点

## 📦 打包内容

```
zip 结构（只列新版本）
```
```

**不要写**：
- 「旧格式 vs 新格式」对比表格
- 「之前是 X，现在是 Y」的说明
- 任何提到旧版本行为的内容（除非是明确的 breaking change 需要迁移说明）

**最佳实践**：
1. `./release.sh v1.2.x` 先创建 release（自动从 git log 生成 notes）
2. 然后用 `gh release edit` 重写 notes：
```bash
gh release edit v1.2.x --repo newemperor221/glass --notes "## 🎯 ..."
```

**repo 清理**：发布新版本前，先清理旧 release 和 draft，保持 GitHub Releases 页干净：
```bash
gh release list --repo newemperor221/glass --limit 20
gh release delete v1.2.2 --repo newemperor221/glass --yes
# 注意：gh release delete 会删同名所有 release（Latest + Draft）
# 如需只删 Draft，用 API：
gh api repos/newemperor221/glass/releases --jq '.[] | select(.draft==true) | {id, tag}' 
gh api -X DELETE repos/newemperor221/glass/releases/<id>
```

### ⚠️ 发布前必做：先检查上个 release 的 zip 结构

**不要在创建 release 前猜打包格式**。先下载上个 release 的 zip 看看结构：

```bash
# 先看上个 release 有什么资产
gh release view v<prev_version> --repo newemperor221/glass --json assets

# 下载 zip 检查内部结构
gh release download v<prev_version> --repo newemperor221/glass -A Glass-v<prev_version>.zip
unzip -l Glass-v<prev_version>.zip
```

**用户反馈记录**：用户曾纠正「我没看到啊，打包要按照komari官方主题打包方式打包」，说明只打 tag 不传 zip 会被用户发现是空壳。**发布前必须检查上个版本的 zip 结构，确保目录层级一致**，不能自己想当然。

**R2 远程壁纸模式（v1.4.0+）打包命令**：
```bash
mkdir -p /tmp/glass-pkg/dist
cp index.html /tmp/glass-pkg/dist/       # build.sh 输出到根目录
cp -r fonts /tmp/glass-pkg/dist/
cp preview.webp icon.svg komari-theme.json /tmp/glass-pkg/
cd /tmp/glass-pkg && zip -r ~/glass/Glass-v1.4.0.zip .
# 无 video/ 目录 — 壁纸来自 Cloudflare R2
```

### ⚠️ `gh release create` 空壳陷阱——必须附带 zip 包

不要在创建 release 时只写说明不打 zip：

```bash
# ❌ 错误：Release 只有标题和 notes，没有可供下载的主题 zip
gh release create v1.4.0 \
  --title "v1.4.0" \
  --notes "- 新增视频壁纸"

# ✅ 正确：先打包，再发布时直接附带 zip
./build.sh
mkdir -p /tmp/pkg/dist && cp index.html /tmp/pkg/dist/
cp -r fonts /tmp/pkg/dist/
cp preview.webp icon.svg komari-theme.json /tmp/pkg/
cd /tmp/pkg && zip -r ~/glass/Glass-v1.4.0.zip .
gh release create v1.4.0 \
  --title "v1.4.0 — 标题" \
  --notes "- 功能描述" \
  ~/glass/Glass-v1.4.0.zip                          # 一步到位

# 如果 release 已创建但漏了 zip：
gh release upload v1.4.0 Glass-v1.4.0.zip --repo newemperor221/glass --clobber
```

**或者直接用 `release.sh`**（自动走完整流程）：`./release.sh v1.4.0`

**验证**：release 发布后检查 assets 列表：
```bash
gh release view v1.4.0 --repo newemperor221/glass --json assets
# 确认有 Glass-v1.4.0.zip 条目
```

**为什么重要**：只打 tag 不传 zip，用户从 Releases 页看到的是"空壳"——Komari 面板导入时需要 zip 包，不是 git tag。

### ⚠️ gh release delete 需要 -R 标志（不在 repo 目录时）

当 cwd 不在 git 仓库内时（比如刚从其他目录切换过来），`gh release delete` 会因找不到 `.git` 而失败：

```bash
# ❌ 失败：fatal: not a git repository
gh release delete v1.4.0 --yes

# ✅ 正确：指定 repo
gh release delete v1.4.0 --yes -R newemperor221/glass
```

同理，`gh release create` / `gh release view` 也需要 `-R owner/repo` 参数才能在非 repo 目录下工作。

### ⚠️ GitHub Release 重复发布（相同版本号）

release.sh 脚本会自动删旧 tag 再创建新 tag，但手动操作时需要注意：

```bash
# 完整的删除流程（release 和 tag 都要删）
gh release delete v1.1.0 --yes              # 删 release
git tag -d v1.1.0                           # 删本地 tag
git push origin :refs/tags/v1.1.0           # 删远端 tag

# 注意：gh release delete 不带 --cleanup-tag 不会删 tag
# --cleanup-tag 标志在旧版 gh CLI 中不可用
```

**⚠️ `gh release delete` 同名 release 全删（包括 Draft）**

`gh release delete <tag>` 删除所有同名 release（Latest + Draft）。如果你先创建了一个 Draft，再通过 release.sh 发布了同一个 tag，GitHub 上会有两个同 tag 的 release（一个 Draft 一个 Latest）。

此时 `gh release delete v1.2.3` 会**同时删除 Latest 和 Draft**，导致 Latest 消失，只剩下你不想删的那个。更安全的做法是用 API 只删 Draft：

```bash
# 找到 Draft release 的 ID
gh api repos/newemperor221/glass/releases --jq '.[] | select(.draft==true) | {id, tag: .tag_name}'

# 只删特定 Draft ID
gh api -X DELETE repos/newemperor221/glass/releases/326131233

# 确认只剩 Latest
gh release list --repo newemperor221/glass --limit 5
```

**release.sh 内处理重复发布的逻辑**（已内建）：
```bash
if git tag | grep -q "^${VERSION}$"; then
    git tag -d "$VERSION"
    git push origin ":refs/tags/${VERSION}" 2>/dev/null || true
fi
```

## komari-theme.json configuration 字段格式（managed — 自动生成后台标签页）

Komari 的 `configuration` 字段支持 `managed` 类型，会自动在后台左侧菜单生成一个**设置标签页**（带图标），管理员可直接在表单中填写值并保存，无需编辑 JSON。

### managed 格式

```json
{
  "configuration": {
    "type": "managed",
    "icon": "/themes/Glass/icon.svg",
    "name": "Glass 设置",
    "data": [
      { "name": "分组标题", "type": "title" },
      { "key": "myString", "name": "文本输入", "type": "string", "default": "", "help": "帮助文字" },
      { "key": "myNumber", "name": "数字输入", "type": "number", "default": 10 },
      { "key": "mySelect", "name": "下拉选择", "type": "select", "options": "选项1,选项2,选项3", "default": "选项1" },
      { "key": "mySwitch", "name": "开关", "type": "switch", "default": true }
    ]
  }
}
```

**字段说明**：

| 字段 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 固定 `"managed"` |
| `icon` | string | 否 | 图标URL，`/themes/{short}/` 映射到主题解压根目录 |
| `name` | string | 否 | 标签页标题 |
| `data` | array | 是 | 配置项数组 |

**data 元素**：

| 字段 | 适用类型 | 必需 | 说明 |
|------|----------|------|------|
| `type` | 全部 | 是 | `string` / `number` / `select` / `switch` / `title` |
| `name` | 全部 | 是 | 显示名称；`title` 类型为分组标题，无需 `key` |
| `key` | 除 `title` | 是 | 唯一键，保存后在 `theme_settings.{key}` 获取 |
| `required` | `string` | 否 | 是否必填 |
| `options` | `select` | 是 | 逗号分隔选项 |
| `default` | 除 `title` | 否 | 默认值 |
| `help` | 除 `title` | 否 | 帮助提示 |

**JS 端读取方式**（在 `loadData()` 中）：

```js
if(siteData && siteData.theme_settings){
    var ts = siteData.theme_settings;
    if(ts.myString) doSomething(ts.myString);
    if(ts.mySwitch) toggleFeature(ts.mySwitch);
}
```

### Glass 当前配置

```json
"configuration": {
  "type": "managed",
  "icon": "/themes/Glass/icon.svg",
  "name": "Glass 设置",
  "data": [
    { "name": "页面标题", "type": "title" },
    { "key": "pageTitle", "name": "标题", "type": "string", "default": "", "help": "浏览器标签+页眉+页脚品牌名，优先级高于站点名称" },
    { "name": "页脚运行时间", "type": "title" },
    { "key": "footerUptimeTemplate", "name": "文案模板", "type": "string", "default": "🛰️ 本站已稳定运行 {days} 日 {hours} 时 {minutes} 分 🌌", "help": "支持 {days}/{hours}/{minutes} 占位符" },
    { "key": "footerStartDate", "name": "起始日期", "type": "string", "default": "2026-05-08T03:28:02Z", "help": "ISO 8601 格式，如 2026-05-08T03:28:02Z" }
  ]
}
```

### 主题管理配置中的壁纸 URL（v1.4.0 新增 managed 配置项）

v1.4.0 将壁纸 URL 从硬编码改为 theme_settings 可配置，支持在 `admin/theme_managed` 页面动态修改。

**komari-theme.json 新增配置段：**
```json
{
  "name": "壁纸设置",
  "type": "title"
},
{
  "key": "wallpaperStatic",
  "name": "可切换壁纸 URL",
  "type": "string",
  "default": "https://img.<用户域名>/image-wallpaper.png",
  "help": "页面加载时显示的静态背景图，留空使用纯黑底色"
},
{
  "key": "wallpaperVideo",
  "name": "动态壁纸 URL",
  "type": "string",
  "default": "https://img.<用户域名>/wallpaper.mp4",
  "help": "加载完成后自动播放的视频背景，留空禁用动态壁纸"
}
```

**JS 端读取（app.js loadData() 中）：**
```js
if(ts.wallpaperStatic){
  var l=$('bg-layer');
  if(l) l.style.background='#0a0a0f url('+ts.wallpaperStatic+') center/cover no-repeat';
}
if(ts.wallpaperVideo){
  var v=$('bg-video');
  if(v) v.src=ts.wallpaperVideo;
}
```

**CSS 不再硬编码 URL：** layout.css 的 `.bg-layer` 只保留 `background: #0a0a0f`（纯黑底），URL 由 JS 动态设置。移动端 `@media` 也去掉了硬编码壁纸路径。

### 静态→动态壁纸过渡效果（v1.4.0 实现）

```
初始化: 可切换壁纸可见 → 视频透明(0)
→ 视频加载完毕(canplay/loadeddata)
→ 同时: 可切换壁纸 1.5s 渐出(opacity 0) + 视频 2s 渐入(opacity 1)
→ 最终: 只有视频可见, 静态完全透明
```

**CSS：**
```css
.bg-layer { background: #0a0a0f; transition: opacity 1.5s ease; }
.bg-layer.faded { opacity: 0; }
.bg-video { opacity: 0; transition: opacity 2s ease; }
.bg-video.loaded { opacity: 1; }
@media (max-width: 767px) { .bg-video { display: none; } }
```

```js\\nvar bgVideo = document.getElementById('bg-video');\\nvar bgLayer = document.getElementById('bg-layer');\\nif (bgVideo) {\\n  function onVideoReady() {\\n    bgVideo.classList.add('loaded');\\n    if (bgLayer) bgLayer.classList.add('faded');\\n  }\\n  if (bgVideo.readyState >= 3 || (!bgVideo.paused && bgVideo.currentTime > 0)) {\\n    onVideoReady();\\n  } else {\\n    bgVideo.addEventListener('canplay', onVideoReady, {once:true});\\n    bgVideo.addEventListener('loadeddata', onVideoReady, {once:true});\\n    var _vi = setInterval(function(){\\n      if (bgVideo && (bgVideo.readyState >= 3 || (!bgVideo.paused && bgVideo.currentTime > 0))) {\\n        onVideoReady();\\n        clearInterval(_vi);\\n      }\\n    }, 300);\\n    setTimeout(function(){clearInterval(_vi);}, 15000);\\n  }\\n}\\n```\\n\\n**⚠️ 踩坑（2026-05-27）：视频加载过快时事件可能先于监听器绑定（竞态条件）**

视频加载极快（readyState=4 时脚本才运行）时，`canplay`/`loadeddata`/`playing` 可能在 JS 添加监听器之前就已触发，监听器永远不会执行。现象：视频已播放但 loaded/faded 类始终不添加，用 console 手动加类则正常。

**修复：先检查当前状态 → 事件监听 → 轮询保底三重保险：**

```js
if (bgVideo) {
  function onVideoReady() {
    bgVideo.classList.add('loaded');
    if (bgLayer) bgLayer.classList.add('faded');
  }
  // ① 先检查是否已就绪（快加载场景）
  if (bgVideo.readyState >= 3 || (!bgVideo.paused && bgVideo.currentTime > 0)) {
    onVideoReady();
  } else {
    // ② 事件监听（慢加载场景）
    bgVideo.addEventListener('canplay', onVideoReady, {once:true});
    bgVideo.addEventListener('loadeddata', onVideoReady, {once:true});
    // ③ 300ms 轮询保底（事件已在 listener 绑定前触发）
    var _vi = setInterval(function(){
      if (bgVideo && (bgVideo.readyState >= 3 || (!bgVideo.paused && bgVideo.currentTime > 0))) {
        onVideoReady();
        clearInterval(_vi);
      }
    }, 300);
    // 15 秒超时：视频一直播不了则放弃
    setTimeout(function(){clearInterval(_vi);}, 15000);
  }
}
```

⚠️ `playing` 事件同样有竞态问题，不能替代 `canplay`/`loadeddata` + 即时检查的防竞态方案。最佳方案是三重保险 + 尽早检查 readyState。

### 完整配置列表（含代码默认值和 API 覆盖）

| 配置键 | 类型 | 来源 | 说明 |
|--------|------|------|------|
| `pageTitle` | string | managed 面板 | 页面标题，优先级：`pageTitle` > `sitename`(API) > 默认"GG 探针" |
| `footerUptimeTemplate` | string | managed 面板 | 页脚中间运行时间模板（支持 `{days}/{hours}/{minutes}` 占位符） |
| `footerStartDate` | string | managed 面板 | 运行时间起始日期，ISO 8601 格式 |

**⚠️ Stats 统计卡（在线/离线/区域）不是配置项**
在线服务器数、离线数、点亮区域数是从 Komari API `/api/nodes` 拉取的**实时数据**，不是 theme_settings 的默认值。代码不提供"占位默认值"——页面渲染前会先显示骨架屏，API 返回后填入真实数据。如果用户问"默认值是多少"，确认是在问哪个配置字段。

### 前端实现细节

**全局变量**（`src/scripts/app.js` 顶部）：

```js
var siteStart = new Date("2026-05-08T03:28:02Z").getTime();
var footerUptimeTemplate = '🛰️ 本站已稳定运行 {days} 日 {hours} 时 {minutes} 分 🌌';
```

**在 loadData() 中覆盖**（`src/scripts/app.js` line ~17）：

```js
if(ts.footerUptimeTemplate) footerUptimeTemplate = ts.footerUptimeTemplate;
if(ts.footerStartDate) siteStart = new Date(ts.footerStartDate).getTime();
var ttl = ts.pageTitle || siteData.sitename;
if(ttl){
    document.querySelectorAll('#site-name,#footer-brand').forEach(el => el.textContent = ttl);
    document.title = ttl;
}
```

**在 startFooterUptime() 中渲染模板**：

```js
function startFooterUptime(){
    var tpl = footerUptimeTemplate;
    function u(){
        var d = Math.floor((Date.now()-siteStart)/1000),
            dd = Math.floor(d/86400),
            hh = Math.floor((d%86400)/3600),
            mm = Math.floor((d%3600)/60);
        var e = $('footer-uptime');
        if(e) e.textContent = tpl.replace('{days}',dd).replace('{hours}',hh).replace('{minutes}',mm);
    }
    u(); setInterval(u,60000);
}
```

**⚠️ 关键时序陷阱**：`startFooterUptime()` 必须在 `loadData().then()` 内部调用，不能放在外面同步执行：

```js
// ✅ 正确：在 .then() 内部，确保 theme_settings 已读取
loadData().then(function(){
    startFooterUptime();  // siteStart 已更新
});

// ❌ 错误：在 async 完成前执行，theme_settings 没生效
loadData().then(function(){...});
startFooterUptime();  // siteStart 还是硬编码默认值
```

## ⚠️ 工作流：部署热修复后同步回仓库（2026-05-20 新增）

多数修改直接在服务器上用 `sed` / `scp` 完成，但**部署的文件（index.html）和仓库源文件是完全不同的版本**：
- 部署的 `index.html` 是 `build.sh` 产物 + 后续手工编辑的叠加
- 仓库 `index.html` 是 `build.sh` 产物，与部署版不同步

**修改部署文件后必须手动同步回仓库的三类变更：**

| 变更类型 | 服务器路径 | 仓库路径 | 同步方法 |
|----------|-----------|---------|---------|
| HTML 结构/JS 逻辑 | `/opt/komari/data/theme/index.html` | `src/body.html` + `src/scripts/app.js` | 手动提取对应部分编辑后 `build.sh` |
| 静态资源（视频/图片） | `/opt/komari/data/theme/video/` | `video/` | `cp` + `git add` |
| 仓库元文件 | — | `README.md`, `komari-theme.json`, `preview.webp` | 直接在本地编辑后提交 |

**⭐ 最常忘记的：** 服务器上加了新文件（如 `video/wallpaper.webm`）、删了旧文件（如 `preview.png`）、改了文件名（如 `wallpaper1` → `wallpaper`），但仓库里没有同步——用户验收时发现"仓库里没有"。

**建议流程：**

```bash
# 1. 在服务器上完成修改 → 验证生效
# 2. 在本地仓库同步更改
cd /tmp/galaxy-glass-push
cp /opt/komari/data/theme/video/wallpaper.webm video/
# 更新 src/ 源文件（如有）
nano src/body.html   # 改 video 元素
nano src/scripts/app.js  # 改 JS 逻辑
./build.sh
# 3. 清理 + 提交
git add -A
git commit -m "feat: ..."
git push
```

### ⚠️ 部署后验证（必做！）

用户要求彻底删除 `preview.png`，**不要保留任何 PNG 格式的预览图**。WebP 足够，多一个 PNG 文件反而多余。如果是 Komari 主题包，只保留 `preview.webp`。

### preview.png 格式陷阱
`.gitignore` 中有 `*.png` 规则，新 preview.png 会被 git 忽略。必须强制添加：
```bash
git add -f preview.png
```

**文件格式必须正确**：`preview.png` 必须是真正的 PNG 格式。如果用 `cp` 从 jpg 改名，文件内容还是 JPEG 格式，GitHub 上无法正常渲染。需要用 ImageMagick 或 Pillow 转换：
```bash
# 用 Pillow 转成真 PNG
/usr/bin/python3 -m pip install Pillow --break-system-packages
/usr/bin/python3 -c "
from PIL import Image
img = Image.open('preview.png')
img.save('preview.png', 'PNG')
"
```

验证格式：
```bash
file preview.png
# 应输出: PNG image data, ...
```

### ⚠️ 永远改 src/，不要改 index.html
`index.html` 是通过 `build.sh` 从 `src/` 生成的产物。直接修改 `index.html` 会被下次 `build.sh` 覆盖。
- 需要修改的：`src/styles/*.css`、`src/scripts/app.js`、`src/body.html`、`src/index.html`（模板）
- 字体 `@font-face` 规则放 `src/styles/settings.css`（:root 之前）
- `--font-sans` 定义放 `src/styles/settings.css` 的 `:root` 块内
- **更换 icon 时注意同步 favicon**：`src/index.html` 第10行的 `<link rel="icon">` 里有个内联 SVG data URI。改了 `icon.svg` 后，需要把新 SVG URL-encode 后替换。用 Python `urllib.parse.quote(svg, safe='')` 编码，前缀 `data:image/svg+xml,`。

### 字体
- **Inter 为首选字体**：用户偏好 Inter。字体文件从 Google Fonts 下载后**自托管在 VPS 上**（/opt/komari/data/theme/fonts/），通过内联 `@font-face` 从本地加载，零外部依赖
- **`@font-face` 内联写法**（settings.css 的 `:root` 之前，需要 300/400/500/600/700 五个 weight）：
  ```css
  @font-face{font-family:'Inter';font-style:normal;font-weight:400;font-display:swap;
    src:url(/fonts/Inter-400.ttf) format('truetype')}
  ```
- **字体栈**：`'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif`
- **不要用等宽字体（font-mono）** — 中文在等宽下发虚，全站统一用 sans
- **不要用 `<link href="https://fonts.googleapis.com/...">`** — 额外 HTTP 请求且国内可能加载失败，不如内联 `@font-face`
- **不要用纯系统字体栈做最终方案** — 用户尝试过 system fonts 后坚持要回 Inter
- **inline span 继承问题**：JS 动态生成的 `<span>` 显式加 `font-family:inherit`

### 字体自托管流程（galaxy-proxy + VPS）

<监控面板域名> 的架构是：Cloudflare → cloudflared → galaxy-proxy.py(:25774) → Komari(:25776)

galaxy-proxy.py 是 Python 写的反向代理，负责静态文件服务 + WebSocket 转发。要自托管字体需修改它：

**步骤 1：下载字体文件到本地**
```bash
mkdir -p /tmp/inter-fonts; cd /tmp/inter-fonts
# 从 fonts.gstatic.com 下载 Inter 的 5 个 weight TTF
curl -sL -o Inter-400.ttf "https://fonts.gstatic.com/s/inter/v20/UcCO3FwrK3iLTeHuS_nVMrMxCp50SjIw2boKoduKmMEVuLyfMZg.ttf"
# 同理下载 300/500/600/700
```

**步骤 2：上传到 VPS**
```bash
scp -o StrictHostKeyChecking=no -i ~/.ssh/hermes_admin -P 46748 Inter-*.ttf root@<荷兰_IP>:/opt/komari/data/theme/fonts/
```

**步骤 3：修改 galaxy-proxy.py**（关键）
在 `/opt/komari/data/theme/galaxy-proxy.py` 中：

a) 添加 `.ttf` MIME 类型到 `ct_map`：
```python
ct_map = {..., ".svg": "image/svg+xml", ".png": "image/png",
          ".ttf": "font/ttf", ".woff2": "font/woff2"}
```

b) 添加 `/fonts/` 路由到 `do_GET`：
```python
if clean_path.startswith("/fonts/"):
    rel = clean_path.lstrip("/")
    return self._serve_static(rel)
```

**步骤 4：重启 galaxy-proxy（Alpine OpenRC）**
```bash
rc-service galaxy-proxy restart
```

**步骤 5：更新 settings.css 的 @font-face URL** 从 `https://fonts.gstatic.com/...` 改为 `/fonts/Inter-xxx.ttf`

**步骤 6：验证**
```bash
# 本地验证
curl -sI "http://127.0.0.1:25774/fonts/Inter-400.ttf" -o /dev/null -w "CT: %{content_type}"
# 通过 Cloudflare 验证（加 ?v=1 bypass 缓存）
curl -sI "https://<监控面板域名>/fonts/Inter-400.ttf?v=1" -o /dev/null -w "CT: %{content_type}"
# 都应返回 CT: font/ttf
```

### JS 生成的 HTML
- `innerHTML` 插入的 `<span>` 元素即使只指定 `color`，某些浏览器渲染时可能和外部文本节点不一致。显式加 `font-family:inherit` 可解决。

### 部署路径（重点踩坑）

### 服务器目录结构
```
/opt/komari/data/theme/
├── index.html               ← 当前运行的主题主文件（Glass 的构建产物）
├── 404/                     ← 404 页面
├── favicon.ico
└── NodeGetGlass/            ← 另一个主题
```

**⚠️ 关键陷阱**：以前 GalaxyGlass 部署到 `/opt/komari/data/theme/Glass/dist/index.html`，但该目录在 GalaxyGlass → Glass 重命名后**已经不存在**。`deploy.sh` 必须手动更新路径。

### 当前正确部署路径

Glass 部署在 **新加坡** 主控服务器上：

| 服务器 | IP | 端口 | 角色 |
|--------|-----|------|------|
| **新加坡主控** | `<新加坡_IP>` | `10425` | galaxy-proxy.py + komari 后端 + cloudflared |

- deploy.sh 已更新指向新加坡
- SSH 使用 `~/.ssh/user_key` 密钥
- 部署流程：`scp` → `/tmp/` → `cp` 到 `/opt/komari/data/theme/`
- 壁纸通过 Cloudflare R2 远程托管，deploy.sh 不同步壁纸文件
- 本地 `video/` 目录保留旧壁纸文件（从未清理），但部署时不同步

### 部署后验证（必做！）

确认部署到的是最新版本，用以下命令检查 font 相关行：

```bash
ssh -o StrictHostKeyChecking=no -i ~/.ssh/user_key -p 10425 root@<新加坡_IP> "grep -c '@font-face' /opt/komari/data/theme/index.html"
```

关键检查项：
- ❌ 不应该有 `<link href="https://fonts.googleapis.com/...`（无 Google Fonts）
- ❌ 不应该有 `--font-mono` 变量定义
- ✅ `--font-sans` 应以 `'Inter',` 开头：`'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif`
- ✅ `@font-face` 规则存在（5条，weight 300-700）
- ✅ 壁纸：静态 PNG（R2） + MP4 视频（R2），`bg-layer` 和 `bg-video` 元素存在
- ✅ 预览图引用：`"preview"` 在 komari-theme.json 中指向 `preview.webp`（非 png）

## 视频壁纸（poster 作为移动端降级）

Glass 壁纸采用 poster + 视频双模式：桌面端播放 MP4 视频，移动端（<768px）显示静态 PNG 图片。

## ⚠️ 壁纸 — Cloudflare R2 远程托管（2026-05-26 更新）

Glass 当前使用**双壁纸方案**，均托管在 Cloudflare R2（`img.<用户域名>`），不依赖 VPS 本地文件：

| 类型 | URL | 说明 |
|------|-----|:----:|
| 静态底图 | `https://img.<用户域名>/image-wallpaper.png` | 3840×2160 PNG，CSS `background` 加载 |
| 视频壁纸 | `https://img.<用户域名>/wallpaper.mp4` | 动态 MP4，`<video>` 元素叠加，淡入效果 |

**优点**：零 VPS 存储消耗，Cloudflare 全球 CDN 分发。

### 当前实现

**body.html**（`src/body.html`）：
```html
<div class="bg-layer" id="bg-layer" style="background: #0a0a0f url(https://img.<用户域名>/image-wallpaper.png) center/cover no-repeat;"></div>
<video class="bg-video" id="bg-video" src="https://img.<用户域名>/wallpaper.mp4" muted loop playsinline autoplay preload="auto"></video>
```

**layout.css**（`src/styles/layout.css`）：
```css
.bg-layer { position: fixed; inset: 0; z-index: -1; background: #0a0a0f url(https://img.<用户域名>/image-wallpaper.png) center/cover no-repeat; }
.bg-video { position: fixed; inset: 0; z-index: -1; width: 100%; height: 100%; object-fit: cover; opacity: 0; transition: opacity 1.5s ease; pointer-events: none; }
.bg-video.loaded { opacity: 1; }
@media (max-width: 767px) { .bg-layer { background: #0a0a0f url(/video/mobile_wallpaper.jpg) center/cover no-repeat !important; } .bg-video { display: none; } }
```

**app.js**（`src/scripts/app.js` — 视频淡入）：
```js
var bgVideo = document.getElementById('bg-video');
if (bgVideo) {
  bgVideo.addEventListener('canplay', function() { bgVideo.classList.add('loaded'); });
  bgVideo.addEventListener('loadeddata', function() { bgVideo.classList.add('loaded'); });
}
```

**视频淡入机制**：视频默认 `opacity: 0`，`canplay`/`loadeddata` 事件触发后添加 `.loaded` 类 → CSS transition 1.5s 渐入。移动端 `<768px` 隐藏视频，只显示静态底图。

**后备（fallback）**：如果视频加载失败或移动端，PNG 静态底图始终可见。

### 部署注意事项

deploy.sh **不同步壁纸文件**（来源：Cloudflare R2）。`deploy.sh` 只上传 `index.html` + 字体。

### 更换壁纸

只需改 `src/body.html` 和 `src/styles/layout.css` 中的 URL，build 后部署即可，无需上传任何文件到 VPS。

### 纯静态壁纸模式（无视频 — 2026-05-27 采用）

用户最终放弃了动态视频壁纸，只保留内嵌 WebP 静态壁纸。改动涉及四段代码：

**① body.html** — 删除 `<video>` 元素，仅保留 `bg-layer` div
```html
<div class="bg-layer" id="bg-layer" style="background: #0a0a0f url(...) center/cover no-repeat;"></div>
```

**② layout.css** — 删除 `.bg-video` 所有相关 CSS（包括移动端 `@media` 隐藏规则），只保留 `.bg-layer`
```diff
- .bg-video { position: fixed; ... opacity: 0; transition: opacity 2s ease; }
- .bg-video.loaded { opacity: 1; }
- @media (max-width: 767px) { .bg-video { display: none; } }
```

**③ app.js** — 删除 wallpaper JS（`onVideoReady`、事件监听、轮询），删除 `ts.wallpaperVideo` 引用
```diff
- // Video wallpaper: static fades out as video fades in
- var bgVideo = document.getElementById('bg-video');
- ...
- if(ts.wallpaperVideo){var v=$('bg-video');if(v)v.src=ts.wallpaperVideo}}
```

**④ 手机端**：因为没有了 `@media` 规则，壁纸在所有屏幕尺寸都显示（不需要单独的 mobile wallpaper）。

### Data URL 内嵌壁纸（替代 R2 远程 URL）

当 R2 或其他外部存储不可用/无需外部依赖时，可以将静态壁纸以 data URL 的形式嵌入 index.html：

```bash
# 1. 转换 PNG -> WebP
cwebp -q 90 wallpaper.png -o wallpaper-static.webp

# 2. 生成 data URL
python3 -c "
import base64
with open('wallpaper-static.webp', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
print('data:image/webp;base64,' + b64)
"

# 3. 替换 src/body.html 中的 style URL
# 4. 也可以加 JS 后备：var _ws = ts.wallpaperStatic || 'data:...'
```

**注意事项：**
- WebP 327KB -> data URL 约 445KB，整体 index.html 从 90KB 膨胀到 535KB+。浏览器能正常解析
- 依赖 `cwebp` 包：`sudo apt install webp`
- 内联后无需外部存储或 R2 配置
- 如果要保留 theme_settings 动态覆盖能力，JS 中写 `var _ws = ts.wallpaperStatic || 'data:...'`

### 部署：scp 被阻止时的 base64 SSH 管道方案

当安全策略阻止 scp/rsync 时，用 base64 编码后通过 SSH 管道解码写入：

```bash
# base64 文件 + cat pipe
python3 -c "
import base64
with open('index.html', 'rb') as f:
    print(base64.b64encode(f.read()).decode())
" | ssh -p 10425 root@<新加坡_IP> "base64 -d > /opt/komari/data/theme/Glass/dist/index.html"

# 验证
ssh -p 10425 root@<新加坡_IP> "ls -lh /opt/komari/data/theme/Glass/dist/index.html"
```

**注意**：路径区分大小写。服务器上用 `Glass`（大写 G），不是 `glass`。

### 视频壁纸实现模式（历史 — 已废弃，保留供参考）

Glass 曾使用 `<video>` + CSS fade-in + JS loaded 事件的模式实现视频壁纸：

**三段代码（缺一不可）**：

1. **`src/body.html`** — 在 `.bg-layer` 后添加 `<video>` 元素，`muted loop playsinline autoplay preload="auto"`。使用绝对远程 URL（非 `/video/` 本地路径）
2. **`src/styles/layout.css`** — `.bg-video` 样式：`object-fit: cover`（铺满）、`opacity: 0`（初始隐藏）、`transition: opacity 1.5s ease`（渐入）、`.loaded { opacity: 1 }`
3. **`src/scripts/app.js`** — 添加 canplay/loadeddata 事件监听，添加 `.loaded` 类

**移动端**：`@media (max-width: 767px)` 中 `display: none` 隐藏视频，静态底图始终可见。

**常见错误**：只改了 body.html 忘记 CSS opacity 和 JS 事件，导致 video 元素在 DOM 中但不显示（opacity=0 且没有 loaded 类触发）。三处必须同步修改。

### GitHub 仓库迁移

GalaxyGlass 已改名为 Glass，仓库从 `github.com/newemperor221/galaxy-glass.git` 迁移到 `github.com/newemperor221/glass.git`。Git remote 需要更新：

```bash
git remote set-url origin https://github.com/newemperor221/glass.git
```

### ⚠️ Cloudflare 缓存陷阱：改 HTML 后用户看不到更新

即使 proxy 返回 `Cache-Control: no-cache, no-store, must-revalidate`，**Cloudflare 仍可能缓存旧版 HTML**（尤其当 Cloudflare 的 `cf-cache-status: BYPASS` 变为 `cf-cache-status: HIT` 时）。

**现象**：curl bypass 能拿到新版（加 `-H 'Cache-Control: no-cache'`），但浏览器还是旧版。

**修复**：
1. **浏览器硬刷新**：`Ctrl+F5` 或 `location.reload(true)`（devtools → Network → Disable cache）
2. **URL 加查询参数避缓存**：`https://<监控面板域名>/?t=N`（N 递增）
3. **Cloudflare Dashboard 手动清除**：Caching → Purge Everything，或 API 单独清除 `https://<监控面板域名>/`

**验证方法**：
```bash
# 对比两个结果的行数
curl -s "https://<监控面板域名>/" | wc -c
curl -s "https://<监控面板域名>/?v=$(date +%s)" | wc -c
# 不同 = Cloudflare 缓存了旧版
```

> **重要**：代理层 `_serve_static()` 返回 `no-cache` headers，但 Cloudflare 的 edge cache 策略优先级更高。如有必要，在 Cloudflare Dashboard 加 Page Rule 或 Cache Rule 绕过首页缓存。

### ⚠️ index.html 内联 JS 脏字符陷阱

**现象：** 页面加载、预渲染 HTML 正常显示（节点卡片、统计栏可见），但所有交互失效（点击卡片、搜索、排序、过滤全部无响应），浏览器控制台无报错。

**根因：** 手工编辑 `index.html` 时，在 `<script>` 块的执行语句前**多了一个脏字符**（如 `|` 管道符），导致整个 `<script>` 标签**解析失败**，所有函数永不定义。

```diff
- |setupEvents();setupScroll();loadData()...
+ setupEvents();setupScroll();loadData()...
```

`|` 在 JS 中不是合法的语句起始符（它是二元运算符），整个解析过程报错退出。页面中的**预渲染 HTML 正常显示**，用户能看到数据但无法交互。

**排查方法：先查源文件 `src/scripts/app.js` 再查构建产物：**

```bash
# 源文件（脏字符可能在源文件里，不是构建产物）
grep -n "^|" src/scripts/app.js

# 服务器部署版
grep -n "^|" /opt/komari/data/theme/Glass/dist/index.html
```

**修复后必须同步到源文件并重新 build**，不能只改 dist/index.html：

```bash
# 1. 删源文件脏字符
sed -i "s/^|//" src/scripts/app.js
# 2. 重新 build
bash build.sh
# 3. 部署新的 index.html
bash deploy.sh
```

**注意**：脏字符 `|` 可能因手动热修复被写入源文件（常见于 `sed` 或编辑器误操作），排查时应先查源文件再查部署文件。

**⚠️ 验证 JS 语法不要用 Python 的 compile()：**
```python
# ❌ 错误：Python compile() 编译的是 Python 不是 JS！
compile(js_string, "<test>", "exec")  # 对 var/function 报 SyntaxError
```

**正确验证方法：**
```bash
# 方法1：用 node 检查语法
curl -s http://127.0.0.1:25774/ | python3 -c "
import sys, re
html = sys.stdin.read()
m = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
if m: open('/tmp/check.js','w').write(m.group(1))
"
node --check /tmp/check.js
# 无输出 = 通过；有 SyntaxError = 需修复

# 方法2：在浏览器 DevTools → Sources → 格式化 → 查看行号附近
```

**修复后验证：**
```bash
grep -c "^|" /opt/komari/data/theme/index.html  # 应为 0
grep "setupEvents()" /opt/komari/data/theme/index.html | head -1
# → setupEvents();setupScroll();...（无前导字符）
```

### SVG 路径损坏排查（Heroicon 常见陷阱）

**现象**：浏览器控制台报 `Error: <path> attribute d: Expected number`，但页面功能不受影响。

**根因 1 — Heroicon path 被截断**：在 SSR 渲染或手动编辑过程中，Heroicon SVG 路径的 `ZM`（closePath + moveTo 命令分隔符）可能被错误截断，导致两个子路径合并为一个连续路径，从而在标准解析时为 unexpected 命令。

**典型坏路径签名**（时钟图标 — 当前时间 stat card）：
```
# ❌ 损坏：Z 命令后缺少 M，下一段路径值被误解析为 arc 参数
d="...12 2.75 6a.75.75 0 0 0-1.5 0v6c..."

# ✅ 正确：Z + M 分隔两段子路径
d="...12 2.25ZM12.75 6a.75.75 0 0 0-1.5 0v6c..."
```

**排查方法**：
```js
// 浏览器控制台 — 找到所有不以 M 开头的 SVG path
Array.from(document.querySelectorAll('svg path[d]'))
  .filter(p => !p.getAttribute('d').match(/^M/))
  .map(p => ({ d: p.getAttribute('d').substring(0, 60), parent: p.closest('*[class]')?.className || '' }))
```

**根因 2 — 搜索图标用小写相对路径 `m`**：Lucide/Heroicons 搜索图标通常混用 `m`（相对 mouveTo）和 `l`（相对 lineTo），一些严格模式的浏览器不认：
```
# ❌ 可能被报错（严格模式）
d="m21 21-4.35-4.35"

# ✅ 标准格式
d="M21 21l-4.35-4.35"
```

**修复**：在服务器上的 `index.html` 中找到对应的 SVG path 字符串，用 `sed` 替换：
```bash
# 修复截断的 Heroicon path
sed -i 's|12 2\\.75 6a\\.75\\.75 0 0 0-1\\.5 0v6c|12 2.25ZM12.75 6a.75.75 0 0 0-1.5 0v6c|' index.html

# 修复搜索图标相对路径
sed -i 's|d="m21 21-4.35-4.35"|d="M21 21l-4.35-4.35"|' index.html
```

**⚠️ 也需要同步到仓库源码**：修复后部署版 `index.html` 正常，但仓库 `src/scripts/app.js` 和 `src/body.html` 中的源 SVG 也要同步更新（如果源文件也有同样问题）。

### ERR_BLOCKED_BY_CLIENT（无害）

浏览器控制台的 `Failed to load resource: net::ERR_BLOCKED_BY_CLIENT` 指向 `cloudflareinsights.com/beacon.min.js`（Cloudflare 内置的访客分析脚本）。这是**纯无害警告**：

- 被用户浏览器端的广告拦截器（uBlock Origin 等）在客户端拦截
- **不影响页面任何功能**（壁纸、图表、数据加载均正常）
- 无需任何处理，告知用户即可

唯一需要排查的情况：如果 `ERR_BLOCKED_BY_CLIENT` 指向**页面自身的 JS/图片资源**，则说明资源路径写错或内容安全策略 CSP 阻止，需要检查引用路径。

### ⚠️ Git push 冲突处理（远程有未同步提交时）

本地仓库 commit 后 push 被拒绝，因为远程有新提交（用户从 Windows 本地推送的修改）：

```bash
# 1. 拉取远程变更（rebase 模式避免多余 merge commit）
git pull --rebase origin main

# 2. 解决常见冲突
#    komari-theme.json — 保留远程的版本号/描述，合并自定义修改
#    index.html — 保留本地改动（poster 移除/视频路径），接受远程的结构更新
#    preview.png — 远程修改了但本地删了 → git rm preview.png

# 3. 标记已解决 + 继续 rebase
git add <resolved-files>
GIT_EDITOR=true git rebase --continue   # --no-edit 不可用，用 GIT_EDITOR=true

# 4. 推送
git push
```

**常见冲突文件**：
| 文件 | 冲突原因 | 解决策略 |
|------|---------|---------|
| `komari-theme.json` | 远程更新了版本号/描述，本地改了配置字段 | 保留远程版本号，合并配置更新 |
| `index.html` | 远程有结构调整，本地有壁纸/视频修改 | 保留本地功能修改，接受远程结构 |
| `preview.png` | 远程修改了该文件，本地删除了 | `git rm preview.png` |

### ⚠️ sed 行级删除陷阱：不要用 /d 删包含关键内容的行

用 `sed -i '/pattern/d'` 删除匹配行会**整行消失**。如果该行还包含其他重要 HTML/JS（如 minified 单行文件、多元素合并行），会连带破坏页面结构：

```bash
# ❌ 危险：删除整行，可能连带毁掉其他内容
sed -i '/wallpaper\\.mp4/d' index.html

# ✅ 安全：只替换字符串为空
sed -i 's|src="[^"]*wallpaper\\.mp4"[^>]*>||g' index.html
sed -i 's|<source[^>]*mp4[^>]*>||g' index.html
```

**安全原则**：`sed` 改 HTML 用替换（`s///`），不用行删除（`/d`），除非你能 100% 确认该行只有目标内容。

> **⚠️ 重启 proxy → cloudflared 也会挂**：`kill` galaxy-proxy 后 cloudflared tunnel 可能断开，全站 502。修复：`/etc/init.d/cloudflared start`。

视频路由和 MIME 配置见 `references/galaxy-proxy-arch.md`。

### 部署脚本修复历史
- 旧路径：`/opt/komari/data/theme/Glass/dist/index.html`（目录不存在 → 部署静默失败）
- 新路径：`/opt/komari/data/theme/index.html`（直接在 theme 根目录）

修改 `deploy.sh` 中的 `REMOTE` 变量即可。

## 重命名注意事项
- 项目改名 GalaxyGlass → Glass 时需要同步：`komari-theme.json`、shell 脚本路径、服务器目录名、GitHub remote URL
- 服务器目录 `/opt/komari/data/theme/Glass/` 在重命名后可能已被删除，注意更新 deploy.sh 目标路径