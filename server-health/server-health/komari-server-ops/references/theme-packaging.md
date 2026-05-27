---
name: komari-theme
description: "Komari 监控面板主题开发、打包、部署全流程 — 主题结构、komari-theme.json 配置、dist 要求、预览图、zip 打包、面板上传"
version: 1.0.0
author: Hermes Agent
---

# Komari Theme Development

Komari 监控系统使用 ZIP 主题包格式。支持动态配置（服务器 ≥1.0.5）。

## 主题包结构

```
theme.zip
├── komari-theme.json      # 主题配置文件（必需）
├── preview.png            # 预览图（推荐）
└── dist/
    ├── index.html         # 主页面模板（必需）
    └── ...                # 其他构建文件
```

## 配置文件 komari-theme.json

### 基础字段

```json
{
  "name": "GalaxyGlass",
  "short": "GalaxyGlass",
  "description": "银河玻璃 — 深色毛玻璃主题",
  "version": "2.3.0",
  "author": "M78 星云",
  "url": "https://github.com/newemperor221/galaxy-glass",
  "preview": "preview.png",
  "configuration": {}
}
```

| 字段 | 类型 | 必需 | 描述 |
|------|------|------|------|
| `name` | string | 是 | 主题完整名称 |
| `short` | string | 是 | 唯一标识符（字母+数字） |
| `description` | string | 是 | 主题描述 |
| `version` | string | 是 | 语义化版本号 |
| `author` | string | 是 | 作者 |
| `url` | string | 否 | 项目/作者网址 |
| `preview` | string | 否 | 预览图相对路径 |
| `configuration` | object | 否 | 动态配置（≥1.0.5） |

## dist/index.html 必须项

```html
<title>Komari Monitor</title>
<meta name="description" content="A simple server monitor tool.">
```

**重要：** `title` 和 `description` 必须严格使用上述格式。Komari 服务端会将这些占位符替换为用户自定义标题/描述。如果用了自定义值（如 `GG 探针`），自定义标题功能会失效。

### 服务端替换规则

| 原始内容 | 替换为 |
|----------|--------|
| `<title>Komari Monitor</title>` | 用户设置的自定义标题 |
| `A simple server monitor tool.` | 用户设置的自定义描述 |
| `</head>` | 用户自定义头部内容 + `</head>` |
| `</body>` | 用户自定义底部内容 + `</body>` |

### SPA 路由

当服务端找不到请求的文件时，自动返回 `index.html`，支持客户端路由。

## 打包命令

```bash
# 创建临时目录，按主题结构组织文件
mkdir -p /tmp/themedist/dist
cp dist/index.html /tmp/themedist/dist/
cp komari-theme.json preview.png /tmp/themedist/

# 打包
cd /tmp/themedist && zip -r theme.zip .

# 验证
unzip -l theme.zip
```

## 部署方式

### 方式一：面板上传
Komari 管理面板 → 主题 → 上传主题包 → 选择 `theme.zip`

### 方式二：手动替换服务器文件
```bash
scp dist/index.html root@<server>:/opt/komari/data/theme/<ThemeName>/dist/index.html
```

## 引用文档

- 完整主题开发指南: https://komari-document.pages.dev/dev/theme
- API 接口文档: https://komari-document.pages.dev/dev/api.html
