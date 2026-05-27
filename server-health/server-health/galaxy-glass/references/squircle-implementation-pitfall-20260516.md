# Squircle 实现演进：从 CSS clip-path 到真超椭圆多点采样

> 2026-05-16 更新：涵盖从 v1（CSS border-radius）到 v4（真超椭圆采样）的完整演进。最新方案解决了单段贝塞尔的 G2 曲率不连续问题。

## 背景

GalaxyGlass 面板追求**深空毛玻璃审美**，卡片四角要求真正的 Squircle（超椭圆连续曲率），而非简单的 border-radius。

## 四次迭代

### v1 — 大 border-radius 近似（vanilla JS，2026-05-13）

用 border-radius: 22px 的大圆角 + backdrop-filter: blur(48-60px) 毛玻璃，视觉上近似连续曲率。

### v2 — 单段三次贝塞尔 + k=0.461（vanilla JS）

使用 SVG clipPath 的 `<path>` 配合 `C`（cubic bezier）命令，控制点系数 k=0.461。比 v1 更精确但仍有 G2 不连续。

### v3 — 同 v2 但迁移到 Next.js（2026-05-16 早）

Next.js 静态导出架构中重新实现 SquircleClip 组件（`src/components/SquircleClip.tsx`），用 `userSpaceOnUse` + ResizeObserver 解决 `objectBoundingBox` 在某些浏览器不可靠的问题。**但数学上仍是单段贝塞尔。**

### v4 — 真超椭圆多点采样（2026-05-16 改进，✅ 当前）

**为什么单段贝塞尔不够好？**

贝塞尔曲线在端点（与直线连接处）的曲率 ≠ 0，而直线曲率 = 0。这导致看得到的"突然变直"感。

**超椭圆采样修复公式：**

使用超椭圆方程 |x/R|ⁿ + |y/R|ⁿ = 1 直接采样。参数化：

```
x(θ) = w - R·cos(θ)^α,  y(θ) = R·sin(θ)^α    其中 α = 2/n
```

θ 从 0 到 π/2，采样 N=25 点/角。

**四个角的映射：**

| 角 | x(θ) | y(θ) |
|---|------|------|
| 右上 | w - R·cos^α | R·sin^α |
| 右下 | w - R·sin^α | h - R·cos^α |
| 左下 | R·cos^α | h - R·sin^α |
| 左上 | R·sin^α | R·cos^α |

**验证采样正确：**
- 右上角 θ=0: x = w-R·1 = w-R ✓, y = R·0 = 0 ✓
- 右上角 θ=π/2: x = w-R·0 = w ✓, y = R·1 = R ✓
- 路径始于 (w-R,0) 终于 (w,R)，完美吻合顶部直线段和右侧直线段

**当前参数：** n=3（α=0.667），radius 14px（统计卡）/ 20px（节点卡）

**实际路径对比（w=292, R=14）：**
```
v3 (bezier): M 14,0 L 278,0 C 284.454,0 292,7.546 292,14
v4 (sampled): M 14.0,0 L 278.0,0 L 278.0,2.2 L 278.1,3.5 L 278.2,4.6 ...
               L 278.3,5.5 L 278.5,6.4 L 278.7,7.2 ... L 292.0,14.0
```
v4 路径 1262 字符 (vs ~140 字符的 v3)，含 25 条 L 命令/角。

## 工程细节

### SquircleClip 组件（src/components/SquircleClip.tsx）

```tsx
export function SquircleClip({
  children,
  radius = 20,
  n = 3,
  className,
  style,
}: SquircleClipProps) {
  // ResizeObserver 测量尺寸 → buildSquirclePath() → SVG clipPath
}

function buildSquirclePath(w, h, R, α): string {
  const N = 25; // 采样点/角
  // 预计算 cos^α 和 sin^α 数组（避免重复计算）
  // 四个角分别构建 L-to 序列
}
```

### 阴影处理

clip-path 切掉 box-shadow → 改用 filter: drop-shadow() 让阴影跟随曲线。

### 部署注意事项

2026-05-16 整包覆盖部署后发现 proxy 502：`rm -rf /opt/komari/data/theme && mkdir` 使旧 proxy 进程的 cwd 变成已删除 inode。修复：重建目录后必须 `pkill -f galaxy-proxy` 重启。

## 参考

- 苹果 Squircle 参数：n≈4（更方），当前用 n=3（更圆润）
- 超椭圆公式：https://en.wikipedia.org/wiki/Superellipse
- PaintCode Squircle 研究：http://robb.is/working-on/squircle/
