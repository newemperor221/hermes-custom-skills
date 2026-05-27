# GalaxyGlass Next.js 重构（2026-05-17）

## 触发条件

当需要改 <监控面板域名> 主题时，先确认当前线上跑的是什么：
- 单 HTML → NodeGetGlass（vanilla JS，`/opt/komari/data/theme/NodeGetGlass/dist/index.html`）
- 新构建 → GalaxyGlass Next.js（`/home/woioeow/galaxy-glass/nextjs/`）

## 教训：不要改错了项目

之前犯了严重错误：在 GalaxyGlass Svelte 项目的 `NodeCard.tsx`/`StatsBar.tsx`/`SquircleClip.tsx` 上修改，以为在改线上版本——这些文件根本不存在于部署中。实际线上是 NodeGetGlass 的单 HTML。

## 用户指定技术栈

| 方向 | 技术 |
|------|------|
| 框架 | Next.js 16（`output: 'export'` 静态导出） |
| UI | Tailwind CSS v4 |
| 动效 | Framer Motion |
| 3D | Three.js（`@react-three/fiber`） |
| 滚动动画 | GSAP |
| 图标 | Lucide |
| 边角 | Squircle（`rounded-[22px]` 或 figma-squircle SVG clipPath） |

## 强毛玻璃公式（2026-05-17 验证）

背景壁纸是明亮场景（穿越时空の少女），必须让壁纸模糊透出来：

```
background: rgba(255,255,255,0.03)      ← 极浅白底
backdrop-filter: blur(100px) saturate(200%) brightness(150%)  ← 高模糊 + 亮度补偿
border: 1px solid rgba(255,255,255,0.12)
```

不要：`rgba(0,0,0,0.35)`（黑玻璃，盖死壁纸）、`bg-white/15`（白膜，不是毛玻璃）

## galaxy-proxy.py 多页面路由

Next.js 静态导出生成 index.html + detail.html。proxy 必须检查文件存在再 fallback：

```python
# 在 fallback 到 /index.html 之前插入：
rel = clean_path.lstrip("/")
if rel:
    fp_html = os.path.join(THEME_DIR, rel + ".html")
    if os.path.isfile(fp_html):
        return self._serve_static(rel + ".html")
```

## Alpine OpenRC 启动

```bash
rc-service galaxy-proxy start   # 已注册的 OpenRC 服务
rc-update add galaxy-proxy default
```

启动脚本在 `/etc/init.d/galaxy-proxy`，使用 `start-stop-daemon` 管理。
