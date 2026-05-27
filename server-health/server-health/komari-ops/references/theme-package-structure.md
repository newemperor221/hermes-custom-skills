# Komari 主题包标准结构

> 2026-05-05 新增，2026-05-10 更新打包方式。

## 标准主题包结构

```
theme.zip（文件直接在根目录，无外层文件夹）
├── komari-theme.json    # 主题配置（含 configuration managed）
├── preview.png          # 预览截图（必须）
├── icon.svg            # 主题图标
├── detail.html         # 详情页
└── dist/
    └── index.html      # 主页面（必须在 dist/ 内）
```

**⚠️ 关键：文件直接在 zip 根目录，不是外层文件夹！**

| 错误方式 | 正确方式 |
|---------|---------|
| `zip -r theme.zip my-theme/` | `cd my-theme && zip -r ../theme.zip file1 dist/ file2` |
| zip 里有 `my-theme/komari-theme.json` | zip 根目录直接是 `komari-theme.json` |
| komari 后台导入失败 | komari 后台导入成功 |

## GalaxyGlass 正确打包步骤

```bash
# 1. 克隆
cd /tmp && rm -rf galaxy-glass && git clone --depth=1 https://github.com/newemperor221/galaxy-glass

# 2. 创建正确结构（index.html 必须在 dist/ 内）
mkdir -p /tmp/gg-theme/dist
cp galaxy-glass/index.html /tmp/gg-theme/dist/
cp galaxy-glass/komari-theme.json /tmp/gg-theme/
cp galaxy-glass/preview.png /tmp/gg-theme/
cp galaxy-glass/detail.html /tmp/gg-theme/
cp galaxy-glass/icon.svg /tmp/gg-theme/

# 3. 检查路径（看源码，不要凭记忆）
grep -o 'wallpaper[^"'\'']*' /tmp/gg-theme/dist/index.html | sort -u
grep -o 'wallpaper[^"'\'']*' /tmp/gg-theme/komari-theme.json | sort -u

# 4. 打包 — 文件直接在 zip 根目录
cd /tmp/gg-theme && zip -r ../gg-theme.zip komari-theme.json dist/ preview.png detail.html icon.svg

# 5. 验证
unzip -l gg-theme.zip
# 正确：根目录直接是 komari-theme.json, dist/, preview.png...
```

## 上传到 GitHub release

```bash
cd /tmp/galaxy-glass
gh release delete <tag> --yes 2>/dev/null || true
gh release create <tag> /tmp/gg-theme.zip --title "GalaxyGlass v1.1" --notes "..."
```

## 官方文档

主题开发指南：https://komari-document.pages.dev/dev/theme.html
