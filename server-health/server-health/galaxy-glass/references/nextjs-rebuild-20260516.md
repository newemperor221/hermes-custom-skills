# GalaxyGlass Next.js 重建设计记录 (2026-05-16)

## 起因

用户反感 clip-path:url() + border-radius 近似方案，要求真正的 Squircle（超椭圆连续曲率），并指定 tech stack：
- Framework: Next.js（output: export 静态导出）
- UI: Tailwind CSS v4
- 动画: Framer Motion
- 3D: Three.js
- 图标: Lucide React

## 架构

```
用户浏览器 → stat.357561.xyz
  → Cloudflare CDN (tunnel)
  → galaxy-proxy.py (波兰主控 31.58.51.127:25774)
  → 静态文件: /opt/komari/data/theme/
  → API 代理: /api/* → localhost:25776 (Komari panel)
```

**部署方式：** 本地构建 Next.js 静态导出 → tar → SCP 到 VPS → 解压到 theme 目录

## Komari API 结构

所有响应包裹在 `{status, success, data}` 信封中：

| 端点 | 用途 | 响应 data 类型 |
|------|------|---------------|
| `/api/public` | 站点配置 | `{sitename, theme_settings, ...}` |
| `/api/nodes` | 节点列表（静态信息） | `RawNode[]` 含 uuid, name, os, region, price 等 |
| `/api/recent/{uuid}` | 节点最近监控数据 | `RecentData[]` 含 cpu/ram/disk/network/uptime |
| `/api/proxy/online-count` | 实时在线人数 | `{online: number}` |
| `/api/proxy/exchange-rate` | 汇率 | exchange rate API 原始响应 |

**关键设计：** 没有批量端点。每个节点需单独调 `/api/recent/{uuid}`。GalleryGlass 用 `Promise.all` 批处理（6个一批）并发取数据。

## SquircleClip 组件

路径：`src/components/SquircleClip.tsx`

**正确实现真正的超椭圆（superellipse n=4）连续曲率：**

```tsx
// 控制点因子 k=0.461（苹果同款，圆用 0.552）
const k = 0.461;
const R = radius; // 像素值，统一 x/y 方向

// 路径 = 矩形 + 4个超椭圆边角（userSpaceOnUse）
const path = `M ${R},0 L ${w-R},0 
  C ${w-R*(1-k)},0 ${w},${R*(1-k)} ${w},${R} 
  L ${w},${h-R} 
  C ${w},${h-R*(1-k)} ${w-R*(1-k)},${h} ${w-R},${h} 
  L ${R},${h} 
  C ${R*(1-k)},${h} 0,${h-R*(1-k)} 0,${h-R} 
  L 0,${R} 
  C 0,${R*(1-k)} ${R*(1-k)},0 ${R},0 Z`;
```

**为什么用 `userSpaceOnUse` 不是 `objectBoundingBox`：**
- `objectBoundingBox` 的比例随元素宽高比变化 → 宽元素（如 stat-card）的边角变成椭圆形（x 半径大 y 半径小）
- `userSpaceOnUse` + 固定像素半径 → 边角始终是正圆（只是曲率是超椭圆）
- 半径 R 在 x/y 方向**相同**，完美圆角 + 超椭圆连续曲率

**生命周期：**
1. 首次渲染：`{w:0, h:0}` → 无 clip-path
2. `ResizeObserver` 测量实际尺寸 → 注入 SVG `<clipPath>` 到 DOM
3. 尺寸变化 → 更新 path → 浏览器重新剪辑
4. 使用 `requestAnimationFrame` + `pending` 标志防抖（16ms 帧对齐）

**如何包裹任意元素：**
```tsx
<SquircleClip radius={20} className="...flex flex-col...">
  <div>卡片内容</div>
</SquircleClip>
```

**当前 Squircle 半径值：**
- 节点卡: radius=20px
- 统计卡: radius=14px

## ThreeBackground 组件

简约星河粒子系统，纯 Three.js（不依赖 @react-three/fiber）：

- 800 粒翠绿星点 (0x10b981)，size=0.12，opacity=0.4，AdditiveBlending
- 60 粒淡紫 accent 星点 (0x818cf8)，size=0.2，opacity=0.25
- 缓慢自转：stars.rotation.y += 0.0002/帧
- 响应式 resize 处理
- 动态 import('three') 规避 SSR 问题
- `position: fixed; inset: 0; z-index: -20` 置于所有内容后方

## 代理修改

galaxy-proxy.py 需要处理 `/_next/static/*` 静态文件路径：

```python
# 在 do_GET 的静态条件中增加：
if clean_path.startswith("/styles/") or clean_path.startswith("/scripts/") 
   or clean_path.startswith("/_app/") or clean_path.startswith("/_next/"):
    rel = clean_path.lstrip("/")
    return self._serve_static(rel)
```

**启动方式（Alpine Linux 无 systemd/screen/at）：**
```bash
sshpass -p 'PASSWORD' ssh -p PORT -f root@HOST "cd /opt/komari/data/theme && python3 /opt/komari/galaxy-proxy.py"
```

`ssh -f` 让 SSH 在后台 fork 后执行命令。

## 部署流程

```bash
# 1. 构建
cd /home/woioeow/galaxy-glass-next
npm run build

# 2. 打包并上传
tar czf - -C out . | sshpass -p 'PASSWORD' ssh -p PORT root@HOST \
  'rm -rf /opt/komari/data/theme && mkdir -p /opt/komari/data/theme && cd /opt/komari/data/theme && tar xzf -'

# 3. 重启代理
sshpass -p 'PASSWORD' ssh -p PORT root@HOST "pkill -f galaxy-proxy"
sshpass -p 'PASSWORD' ssh -p PORT -f root@HOST \
  "cd /opt/komari/data/theme && python3 /opt/komari/galaxy-proxy.py"
```

## 新增组件（2026-05-16 补全）

### WallpaperBackground

路径：`src/components/WallpaperBackground.tsx`

双层壁纸 + 暗色覆盖层，完全尊重用户「壁纸极暗」的原有偏好：

- Poster (`img.357561.xyz/image-wallpaper2.png`) + Video (`wallpaper1.mp4`)
- `filter: brightness(0.35)` 降低壁纸亮度
- `rgba(2,2,3,0.55)` 暗色覆盖层（与 `--bg-deepest` 同色系）
- Video 通过 `onCanPlay` 回调淡入（opacity 0→1, 600ms 过渡）
- `z-index: -30` 位于 ThreeBackground (-z-20) 之后
- 自动播放被拦截时绑定 click/touchstart 重试

### AnimatedCounter（GSAP）

路径：`src/components/AnimatedCounter.tsx`

GSAP 驱动的数字滚动动效：

```tsx
<AnimatedCounter value={cpuUsage} decimals={1} suffix="%" />
```

- 用 `gsap.fromTo` 做 `textContent` 动画（`snap` 控制小数位）
- 只响应 `value` prop 变化，首次渲染从 0→target 滚动
- 应用于 StatsBar 的「在线服务器数」和「月度开销」
- 纯 client component，`"use client"` 声明

### Online Count 集成

Navbar 从 `visitorCount` prop 接收 `/api/proxy/online-count` 结果，60s 轮询一次。
旧 v2 的 per-tab UUID 心跳机制未移植（当前显示 0 是正常的，因为没有浏览器 tab 注册心跳）。

**如果要激活心跳，参考旧版 data.js 做法：**
```ts
const tabId = sessionStorage.getItem('gg-tab') || crypto.randomUUID();
sessionStorage.setItem('gg-tab', tabId);
fetch(`/api/proxy/online-count?t=${tabId}`);
```

## 待完善

- [x] 壁纸背景（poster/video）— 2026-05-16 完成
- [x] 在线人数 /api/proxy/online-count 集成 — Navbar 显示 visitorCount
- [x] GSAP 动画 — AnimatedCounter 组件完成
- [ ] 搜索框输入时按 online/region 排序
- [ ] 详情页（节点点击进入详细视图）
- [ ] 移动端响应式适配
