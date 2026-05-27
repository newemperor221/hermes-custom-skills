# GalaxyGlass Astro 5 迁移记录（2026-05-19）

本 session 从 Next.js 16 静态导出迁移到 **Astro 5 + React Islands**，集成 uPlot 图表、TanStack Query 数据层、Inter+JetBrains Mono 字体、Open Props 设计令牌。

## 为什么迁移

| 维度 | Next.js 16 | Astro 5 |
|------|-----------|---------|
| 首页 JS 体积 | ~250KB | ~80KB（-68%，Framer Motion → CSS 后）|
| 构建时间 | 11s+ | **7.8s** |
| 首页 JS 策略 | 全量加载 | React Island 按需水合 |
| 纯静态页面 | 也是静态导出 | **默认 0JS** shell |
| 框架升级空间 | 很新但大材小用 | 轻量+按需更匹配 |

## 项目结构

```
/home/woioeow/galaxy-glass/astro/
├── src/
│   ├── layouts/
│   │   └── Layout.astro          # 基础布局（字体+Open Props+背景）
│   ├── pages/
│   │   ├── index.astro            # 首页（client:only）
│   │   └── detail.astro           # 详情页（client:only）
│   ├── components/
│   │   ├── Background.tsx          # 壁纸组件（client:load）
│   │   ├── DashboardContent.tsx    # 首页主内容（client:only）
│   │   ├── DetailContent.tsx       # 详情页主内容（client:only）
│   │   ├── NodeCard.tsx            # VPS 卡片（改良 Deep Space 设计）
│   │   ├── UPlotChart.tsx          # uPlot 图表包装组件
│   │   └── QueryProvider.tsx       # TanStack Query Provider（client:load）
│   ├── lib/
│   │   ├── api.ts                  # API 类型+函数
│   │   └── utils.ts                # 格式化工具
│   └── styles/
│       └── base.css                # 全局样式+Open Props
├── dist/                           # 构建输出
├── deploy.sh                       # 一键部署
├── astro.config.mjs                # Astro 配置
├── tsconfig.json
└── package.json
```

## 部署

```bash
cd /home/woioeow/galaxy-glass/astro
pnpm astro build        # 输出到 dist/
bash deploy.sh          # SSH key 上传到 /opt/komari/data/theme/GalaxyGlass-Next/
```

**注意：** Astro 构建输出为 `dist/detail/index.html`，所以 NodeCard 中的链接为 `/detail/?uuid=xxx`（带尾斜杠）。

## client:only vs client:load

| 指令 | 组件 | 理由 |
|------|------|------|
| `client:load` | Background | SSR 渲染骨架，JS 加载后立即水合 |
| `client:only="react"` | DashboardContent / DetailContent | 内容使用 TanStack Query（useQuery 在 SSR 时会报 No QueryClient）|
| `client:load` | QueryProvider | 提供 React Context，但实际被组件内部的 QueryClientProvider 替代 |

**注意：** 由于 `client:only` 组件在 SSR 时不渲染，页面会先显示空 shell，JS 加载后才显示内容。Shadow island（`client:only`）让 Background 先出现，过渡自然。如果不想看到空白，可以加骨架屏或 CSS 预渲染。

## TanStack Query 集成

### 每个页面组件自带 QueryClientProvider

由于 `client:only` 的组件在 Astro SSR 中不经过 Layout 的 React context，每个页面组件内部包裹自己的 `QueryClientProvider`：

```tsx
export default function DashboardContent() {
  // useQuery calls here...
  return (
    <QueryClientProvider client={qc}>
      <>{/* content */}</>
    </QueryClientProvider>
  );
}
```

### 数据轮询

```tsx
const { data: nodes = [], isLoading } = useQuery({
  queryKey: ["nodes"],
  queryFn: async () => {
    const nodeList = await fetchNodes();
    const merged = await Promise.all(
      nodeList.map(async (n) => {
        const recent = await fetchRecentData(n.uuid);
        return mergeNodeData(n, recent);
      })
    );
    return merged;
  },
  refetchInterval: 30_000,   // 30s 轮询
  staleTime: 15_000,          // 15s 内不再重新请求
});
```

### 优劣势对比

| 维度 | 手写 fetch + setInterval | TanStack Query |
|------|------------------------|----------------|
| 轮询 | 手写 `setInterval(loadData, 30000)` | `refetchInterval: 30_000` |
| 缓存 | 无 | stale-while-revalidate |
| 切标签页 | 数据重新请求 | 缓存秒加载 |
| loading 状态 | 手写 useState | `isLoading` 内置 |
| 错误重试 | 手写 try/catch | `retry: 2` 内置 |
| 代码量 | ~60 行 | ~30 行 |

## uPlot 图表集成

### 组件 API

```tsx
<UPlotChart
  data={cpuPts}           // 主序列数据: number[]
  data2={upPts}           // 可选第二序列
  color="#10b981"         // 主色
  color2="#f59e0b"        // 第二色
  showY                   // 显示 Y 轴刻度
  unit="% | /s"           // Y 轴单位
  height={140}            // 图表高度
  timeStart="10:30"       // 左时间标签（仅用于外部显示）
  timeEnd="11:00"         // 右时间标签
/>
```

### uPlot 配置

```tsx
const opts: uPlot.Options = {
  width: target.clientWidth,
  height,
  cursor: { show: true, drag: { x: false, y: false } },
  select: { show: false },
  legend: { show: false },
  axes: [
    { show: false }, // x-axis
    { show: !!showY, stroke: "rgba(255,255,255,0.15)",
      grid: { stroke: "rgba(255,255,255,0.03)", width: 1 },
      size: 32, font: "10px system-ui",
      values: (self, ticks) => ticks.map(v => { /* format */ }),
    },
  ],
  series: [
    {}, // x
    { label: "", stroke: color, width: 2, fill: gradient, points: { show: false } },
  ],
};
```

### Resize 处理

```tsx
useEffect(() => {
  const onResize = () => {
    if (chartRef.current && targetRef.current) {
      chartRef.current.setSize({ width: targetRef.current.clientWidth, height });
    }
  };
  window.addEventListener("resize", onResize);
  return () => window.removeEventListener("resize", onResize);
}, [height]);
```

### 数据不足时的降级

```tsx
if (data.length < 2) {
  return <div style={{ height, display: "flex", alignItems: "center", justifyContent: "center", color: "rgba(255,255,255,0.15)", fontSize: 12 }}>数据不足</div>;
}
```

### 体积对比（初始）

| 方案 | gzip |
|------|------|
| 旧 D3 Canvas 方案 | ~80KB+ |
| **uPlot（初始）** | **~30KB**（含 CSS） |
| ECharts | ~250KB |

### 第二轮优化后体积（Framer Motion → CSS + uPlot smooth update）

移除 framer-motion 后 DashboardContent 从 46KB 降至 **6.5KB**。详见下方「v2: Framer Motion 移除 + CSS Animations」章节。

## 字体方案（Inter + JetBrains Mono）

在 Layout.astro 的 `<head>` 中通过 Google Fonts 加载：

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet" />
```

CSS 变量：
```css
--font-sans: 'Inter', -apple-system, BlinkMacSystemFont, 'PingFang SC', ..., sans-serif;
--font-mono: 'JetBrains Mono', 'Fira Code', ui-monospace, ..., monospace;
```

## v2: Framer Motion 移除 + CSS Animations（同 session 第二轮优化）

**将 framer-motion 完全移除**，所有动效替换为纯 CSS（+ ~15KB gzip 节省）：

### 替换清单

| 功能 | Framer Motion 代码 | CSS 替换 |
|------|------------------|----------|
| NodeCard 入场 | `<motion.div initial={{opacity:0,y:12}} animate={{...}}>` | `opacity/transform transition` + `useState(visible)` + `setTimeout` |
| MetricRow 进度条 | `<motion.div initial={{scaleX:0}} animate={{scaleX}}>` | `transform: scaleX` + CSS `transition`，JS 控制 visible |
| StatCard 入场 | `<motion.div variants={{...}}>` stagger | `@keyframes fade-in` + `.animate-fade-in` 类 |
| NodeCard hover | `whileHover={{ y: -4, scale: 1.005 }}` | `:hover { transform: translateY(-4px) }` + `transition` |

**新增 CSS 工具类：**
```css
@keyframes fade-in {
  from { opacity: 0; transform: translateY(16px); }
  to { opacity: 1; transform: translateY(0); }
}
.animate-fade-in { animation: fade-in 0.5s cubic-bezier(0.16, 1, 0.3, 1) both; }
```

**NodeCard 入场逻辑：**
```tsx
const [visible, setVisible] = useState(false);
const [barAnims, setBarAnims] = useState([false, false, false]);

useEffect(() => {
  const t = setTimeout(() => setVisible(true), index * 40);
  return () => clearTimeout(t);
}, [index]);

useEffect(() => {
  if (!visible) return;
  [0, 1, 2].forEach((i) => setTimeout(() => setBarAnims(p => { const n = [...p]; n[i] = true; return n; }), 350 + i * 60));
}, [visible]);
```

渲染直接用 inline style + CSS `transition`，无 motion.div 封装。\`\`\`

## v3: uPlot 平滑更新（同 session 第三轮优化）

从「每次数据变化 destroy+recreate」改为「setData 原地更新」+ `useDeferredValue` 防抖：

```tsx
// ❌ 旧：每次都重建
useEffect(() => {
  if (chartRef.current) chartRef.current.destroy();
  chartRef.current = new uPlot(opts, pts, target);
}, [data, data2]);  // data 变化→重建→闪烁

// ✅ 新：图表只创建一次，数据 setData
const deferredData = useDeferredValue(data);

useEffect(() => {
  chartRef.current = new uPlot(opts, initPts, target);
  return () => chartRef.current?.destroy();
}, [color, height, unit]);  // 仅样式属性变化重建

useEffect(() => {
  if (!chartRef.current) return;
  chartRef.current.setData(pts);  // 平滑增量更新
}, [deferredData, deferredData2]);
```

**效果：**
- 消除数据刷新时的图表闪烁（destroy → 空白 → render）
- `useDeferredValue` 让低优先级更新不阻塞交互
- 重建条件从 data 改为仅 color/height/unit

## 最终包体积（gzip）

| 首页 | 大小 |
|------|------|
| React 运行时 | 57KB（浏览器缓存，首次加载后不计） |
| Background | 0.5KB |
| TanStack Query | 7.4KB |
| DashboardContent | **6.5KB**（移除 Framer Motion 后降 86%） |
| Astro island loader | 3KB |
| uPlot + utils | 5.4KB |
| **合计（首次）** | **~80KB** |
| **合计（React 缓存后）** | **~20KB** |

| 详情页 | 大小 |
|--------|------|
| DetailContent + uPlot + TanStack Query | **~27KB** |

## Open Props 集成

通过 CDN 加载 normalize + CSS 自定义属性：
```html
<link rel="stylesheet" href="https://unpkg.com/open-props/normalize.min.css" />
```

在 `base.css` 中：
```css
@import "open-props/style";
```

使用的 Open Props 特性：body 间距、heading 大小规范、阴影曲线、渐变预设。

## 细节注意

1. **路径格式**：Astro 构建输出 `detail/index.html`，NodeCard 中的链接用 `/detail/?uuid=xxx`（带尾斜杠）
2. **`client:only` 组件**不在 SSR 时渲染，需要等 JS 加载完才显示内容
3. **`Unterminated regexp literal` 错误**：JSX 中 `style={{color:"..."}}` 的花括号必须成对，一个 `}}` 少一个都会导致此错误
4. **QueryClientProvider 作用域**：`useQuery` 必须在 Provider 之后调用，组件顶层的 `useQuery` 需要 Provider 在树的上层
