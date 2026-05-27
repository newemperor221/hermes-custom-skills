# Astro Code Audit Session — 2026-05-19

## P0 Bugs Found & Fixed

### QueryClientProvider 每次渲染重建
- **问题**: `new QueryClient(...)` 写在 JSX 里 → 每次 render 新建实例 → 子组件重新挂载→丢失缓存
- **修复**: `const [queryClient] = useState(() => new QueryClient({...}))`
- **文件**: `DashboardContent.tsx`, `DetailContent.tsx`

### 详情页 404（Astro 输出结构差异）
- **问题**: Astro 输出 `/detail/index.html`，但 Komari 服务器需要 `/detail.html`
- **修复 1**: 部署时 `mv detail/index.html detail.html && rm -rf detail`
- **修复 2**: 链接从 `/detail/?uuid=` → `/detail?uuid=`（无尾部斜杠）
- **根因**: 旧 Next.js `detail.html` 在 theme 根目录，Astro 输出 `detail/index.html` → 服务端不识别子目录

### Open Props CDN 双重加载
- **根因**: 布局 `<head>` 有 CDN `<link>` + CSS 中 `@import "open-props/style"` → 双重请求+潜在冲突
- **修复**: 移除 CDN `<link>`，只保留 npm `@import`

### DetailContent 背景使用 getElementById
- **问题**: `document.getElementById("detail-poster")` 脆皮，若 id 不存在/被复用则静默失败
- **修复**: 改用 `useRef<HTMLImageElement>` / `useRef<HTMLVideoElement>`

## P1 Issues Found

### 未使用代码
- `Gauge` 图标导入未使用（DashboardContent.tsx:5）
- `c()` 辅助函数未使用（DashboardContent.tsx:111）
- `fetchSiteInfo` 查询在详情页中未使用（DetailContent.tsx:33）— 已移除
- `viewMode` state 定义了 setter 但无切换 UI（用户无法切换表格/网格视图）

### CSS 变量未使用
- `--glass-saturate` 定义在 CSS 中但所有组件硬编码 `saturate(180%)`

### 间距问题
- Sysinfo 行 `px-[2px]` → 水平间距几乎没有 → 修复为 `px-[14px]`（匹配静态版）

## P2 Polish

### 入口动画不完整
- 只有统计卡有 `animate-fade-in` 类，其他内容（过滤器、卡片网格）无入场动画
- 修复: 删除帧运动后，所有动画改为 CSS，无额外动画后添加

### 无骨架屏
- 加载中只显示 spinner，无内容骨架
- 建议: 当 `isLoading` 时渲染灰条骨架

### 无 Error Boundary
- React Island 崩溃 → 整个页面消失（黑暗一片）
- 建议: 包 `<ErrorBoundary>` fallback = 错误提示+重试按钮

### UPlotChart 未消费 timeStart/timeEnd
- `timeStart` `timeEnd` props 传入但组件未使用 (props accepted but unused)
- 建议: 用时间戳 x 轴，或移除未用 props

## Architecture Lessons

### Astro + TanStack Query SSR conflict
- `useQuery` 在 SSR 时找不到 `QueryClientProvider`
- 三种解法: `client:only="react"` / 组件内自包 Provider / 全局 Provider 但跳过 Server 渲染

### 详情页数据获取效率
- `fetchNodes()` 获取所有节点再 `.find()` 定位单个节点
- 建议: 使用专用 API `/api/node/:uuid` 避免每次加载详情页请求全部节点数据

### mx-auto 在 flex 容器中不生效
- `flex-1` + `mx-auto` → flex-1 拉伸元素抵消 mx-auto
- 正确居中: 父容器 `items-center`，子容器 `w-full max-w-[1124px]`

## 与本 skill 其他内容的关系

- Astro 迁移详情: `references/astro-migration-20260519.md`
- 设计系统: `references/deep-space-squircle-design-system-20260519.md`
- 完整代码审计检查清单: `references/code-audit-checklist-20260519.md`
