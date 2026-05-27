# Komari 主题打包格式研究

## 来源

2026-05-20 用户要求创建 GalaxyGlass (后更名为 Glass) GitHub release。第一次打包格式错误（`index.html` 放在 zip 根目录），用户质疑后通过分析官方 komari-next release 确定了正确格式。本参考被 `galaxy-glass-workflow` 技能引用。

## 官方参考

- **komari-next** (tonyliuzj/komari-next): `https://github.com/tonyliuzj/komari-next/releases/latest/download/dist-release.zip`
- **komari-theme-naive** (lyimoexiao/komari-theme-naive): 通过 web UI 上传安装
- **NanoMuse** (saladinxp/komari-nano-muse): 另一个 Komari 主题示例

## 正确格式

```
zip 根目录
├── komari-theme.json      ← Komari 读取主题元数据
├── icon.svg               ← 主题图标
├── preview.png           ← 预览截图
└── dist/
    ├── index.html         ← 主题主页（Komari 服务此目录下的静态文件）
    ├── 404.html           ← 可选：404 页面
    ├── favicon.ico        ← 可选：站点图标
    └── assets/            ← 可选：静态资源
```

## 安装方式

1. **Web UI 上传**（推荐）：登录 Komari → 设置 → 主题管理 → 上传主题 → 选择 zip
2. **SSH 手动部署**：解压到 `/opt/komari/data/theme/`（仅适用于单文件主题直接用 komari 服务）

## 注意事项

- `komari-theme.json` **必须**在 zip 根目录（不能在 dist/ 内）
- `komari-theme.json` 的 `version` 字段应与 git tag 保持一致
- `index.html` **必须**在 `dist/` 下（不能在 zip 根目录）
- 上传后 Komari 读取 `komari-theme.json` 获取元数据，服务 `dist/` 下的文件
- 单文件主题（如 Glass 所有 CSS/JS 内联）只需一个 `dist/index.html`
- 框架类主题（Next.js/Vue 构建产物）需要包含完整静态目录
