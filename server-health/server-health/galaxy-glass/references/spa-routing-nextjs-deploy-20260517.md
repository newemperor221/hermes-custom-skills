# GalaxyGlass Next.js SPA 路由与部署 (2026-05-17)

## 背景

用户要求 GalaxyGlass Next.js 版本同时上线主页 + 详情页。Next.js 静态导出（`output: 'export'`）生成：
- `/index.html` (主页)
- `/detail.html` + `/detail/` (详情页，含元数据目录)

## Python proxy SPA 路由问题

`galaxy-proxy.py` 使用 `http.server.SimpleHTTPRequestHandler` 提供静态文件。当请求路径为 `/detail` 时：

1. Python 检测到存在 `/opt/komari/data/theme/detail/` 目录
2. 自动返回 `301 Moved Permanently` → `/detail/`
3. 浏览器访问 `/detail/` → Python 寻找 `detail/index.html`
4. 但 Next.js 没有生成 `detail/index.html`（只有元数据文件）
5. → 404

### 尝试过的方案

**方案 1：patch proxy 的 do_GET**
在 fallback 到 `index.html` 之前检查 `detail.html` 是否存在。代码正确但 `os.path.isfile()` 在运行中的 Python 进程里返回不一致结果（外部测试正确，进程内 404）。
**原因推测：** Python 进程的 cwd 或 `__pycache__` 缓存干扰。

**方案 2：删除 detail/ 目录**
`rm -rf /opt/komari/data/theme/detail` → `/detail` 不再 301，但走到 proxy 的 fallback 逻辑（`self.path = "/index.html"`）→ 404。证明 proxy 的 `detail.html` 映射正确执行了但 404，说明 `os.path.isfile()` 确实返回 False（原因不明）。

**方案 3（采用）：copy detail.html → detail/index.html**
```bash
mkdir -p /opt/komari/data/theme/detail
cp /opt/komari/data/theme/detail.html /opt/komari/data/theme/detail/index.html
```
- `/detail` → 301 `/detail/`（Python 目录检测）
- `/detail/` → 200 `detail/index.html`
- 浏览器自动跟随 301，用户无感

## 部署流程

```bash
# 1. Build
cd /home/woioeow/galaxy-glass/nextjs
npm run build

# 2. Upload to server
tar czf - -C out . | sshpass -p 'OX8w$nE9A%tfqb6v' ssh -p 46748 root@31.58.51.127 \
  'rm -rf /opt/komari/data/theme/* && cd /opt/komari/data/theme && tar xzf -'

# 3. Fix SPA routing for /detail
sshpass -p 'OX8w$nE9A%tfqb6v' ssh -p 46748 root@31.58.51.127 \
  'mkdir -p /opt/komari/data/theme/detail && cp /opt/komari/data/theme/detail.html /opt/komari/data/theme/detail/index.html'

# 4. Restart proxy
rc-service galaxy-proxy restart

# 5. Verify
curl -sI http://127.0.0.1:25774/ | head -3        # 200
curl -sIL http://127.0.0.1:25774/detail | head -5  # 301 + 200
```

## Next.js 项目结构

路径: `/home/woioeow/galaxy-glass/nextjs/`

```
src/
├── app/
│   ├── globals.css          # Tailwind v4 + 自定义 CSS
│   ├── layout.tsx            # "use client" + Background + page wrapper
│   ├── page.tsx              # 主面板（StatsBar + 筛选 + 卡片网格/表格 + 页脚）
│   └── detail/
│       ├── page.tsx          # Suspense wrapper for useSearchParams
│       └── DetailContent.tsx # 详情页（指标卡 + 系统信息 + Canvas 图表）
├── components/
│   ├── Background.tsx        # 视频壁纸
│   ├── NodeCard.tsx          # 服务器卡片（glassmorphism + framer-motion + Lucide）
│   └── SquircleClip.tsx      # SVG clipPath squircle wrapper
└── lib/
    ├── api.ts                # Komari API 客户端
    └── utils.ts              # bytes/uptime/flag/price 工具函数
```

### 关键文件说明

**layout.tsx - "use client":** 因为 `Background` 组件使用 `useEffect`，整个 layout 需要 client 模式。

**detail/page.tsx - Suspense 边界：** `useSearchParams()` 需要父级提供 `<Suspense>`，否则 Next.js 报错 `missing-suspense-with-csr-bailout`。`DetailContent` 用 `lazy()` 动态导入。

**next.config.ts:**
```ts
const nextConfig = {
  output: 'export',
  images: { unoptimized: true },
};
```

## 技术栈指定（用户明确要求）

| 方向 | 技术 |
|------|------|
| 框架 | Next.js 16 (App Router) |
| UI | Tailwind CSS v4 |
| 动效 | Framer Motion |
| 3D | Three.js (未实现) |
| 滚动动画 | GSAP (未实现) |
| 图标 | Lucide React |
| 圆角 | Squircle (22px border-radius) |

未实现的 Three.js 和 GSAP 可以后续补上。

## 强毛玻璃公式（Next.js 版）

```tsx
style={{
  background: "rgba(255,255,255,0.03)",           // 极浅透明白底
  backdropFilter: "blur(100px) saturate(200%) brightness(150%)",  // 高模糊 + 亮度补偿
  WebkitBackdropFilter: "blur(100px) saturate(200%) brightness(150%)",
  border: "1px solid rgba(255,255,255,0.12)",
}}
```

节点卡和详情页指标卡/图表卡/系统信息卡使用同一套毛玻璃参数，视觉统一。

## StatBar 毛玻璃（独立参数）

```tsx
style={{
  background: "rgba(255,255,255,0.04)",
  backdropFilter: "blur(60px) saturate(200%) brightness(130%)",
  WebkitBackdropFilter: "blur(60px) saturate(200%) brightness(130%)",
  border: "1px solid rgba(255,255,255,0.08)",
}}
```

统计卡因为内容更小（只有数值+标签），模糊略低（60px vs 100px）更显精致。
