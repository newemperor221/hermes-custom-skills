# NodeDetailModal — 2026-05-17 新增

**组件位置：** `src/components/NodeDetailModal.tsx`

## 功能
点击 VPS 卡片弹出毛玻璃详情弹窗，展示以下信息：

| 区域 | 内容 |
|------|------|
| 头部 | 服务器名称、区域、在线状态点、OS 图标、关闭按钮 |
| Tags | tag 标签（空格分隔，逐个渲染为绿色小胶囊） |
| CPU | 使用率进度条 + Load 1/5/15 |
| 内存 | 使用率进度条 + 已用/总量 |
| 磁盘 | 使用率进度条 + 已用/总量 |
| 网络 | 上传/下载速度卡片（各含总计流量） |
| 详情 | 运行时间、进程数、操作系统、月费 |

## 交互
- **点击卡片** → 设置 `selectedNode` state → 弹窗淡入 + scale 动画
- **点击背景/关闭按钮/Escape** → 关闭弹窗
- **body scroll 锁定**：打开时 `document.body.style.overflow = "hidden"`，关闭时恢复
- **使用 Framer Motion**：`AnimatePresence` + `motion.div` 动画

## 实现细节
- `Dashboard.tsx` 管理 `selectedNode` state，渲染 `<NodeDetailModal>` 作为顶层 children
- `NodeCard.tsx` 接受 `onClick` prop，通过 `setSelectedNode(node)` 传递选中节点
- 组件使用 `SquircleClip` + `backdrop-blur-[60px]` 保持与卡片一致的毛玻璃风格
- 内部使用 `ProgressRow` 和 `DetailRow` 子组件简化布局

## ✅ fmt 函数 bug — 已修复（2026-05-17）

`ProgressRow` 组件的 `fmt()` 辅助函数在 `>= 1e6` 分支曾错误地返回 "GB" 而非 "MB"，导致 512MB 内存显示为 "512.0 GB"。

**修复内容：** 第64行 `" GB"` → `" MB"`

注意 `fmtBytes`（NodeCard.tsx 中，用于网络流量显示）的对应函数一直是正确的——只有 NodeDetailModal 内的局部 `fmt()` 有此问题。

**验证方法：** 在详情页查看内存行，512MB 的 VPS 应显示 "512.0 MB" 而非 "512.0 GB"。
