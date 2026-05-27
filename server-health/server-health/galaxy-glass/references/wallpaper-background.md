# 背景海报 + 动态壁纸实现

## 旧版（vanilla JS）HTML 结构

```html
<div class="bg-layer">
  <img id="poster" src="" alt="">
  <video id="bg-video" muted loop playsinline autoplay></video>
</div>
```

## CSS 控制（关键）

```css
.bg-layer { position: fixed; inset: 0; z-index: -1; background: var(--bg-deep); }
.bg-layer img { opacity: 1; transition: opacity 0.6s ease; }
.bg-layer video { opacity: 0; transition: opacity 0.6s ease; }
```

- Poster 默认可见 (opacity: 1)
- Video 默认隐藏 (opacity: 0)
- 两者叠加用 absolute + inset: 0 + object-fit: cover

## JS 逻辑（loadData 内）

```js
// 先设 fallback 保底，再被 API 覆盖
$('poster').src = 'https://img.<用户域名>/image-wallpaper2.png';
$('bg-video').src = 'https://img.<用户域名>/wallpaper1.mp4';

// 从 API 覆盖
if (siteData && siteData.theme_settings) {
  var ts = siteData.theme_settings;
  if (ts.posterUrl) $('poster').src = ts.posterUrl;
  if (ts.videoUrl)  $('bg-video').src  = ts.videoUrl;
}
```

## 视频播放 + 切换（loadData().then 内）

```js
loadData().then(function(){
  var v = $('bg-video');
  v.play().then(function(){
    v.style.opacity = '1';      // video 淡入
    $('poster').style.opacity = '0';  // poster 淡出
  }).catch(function(){})         // 播放失败 → poster 保持可见
});
```

## 历史踩坑（v2.6.0 修复）

| 问题 | 后果 | 修复 |
|------|------|------|
| poster/video 无初始 opacity CSS | 两者叠在一起互相遮挡 | 加 CSS `.bg-layer img { opacity: 1 }` + `.bg-layer video { opacity: 0 }` |
| 视频无 fallback URL (`ts.videoUrl \|\| ''`) | API 不返回 videoUrl 时视频空白 | 先设 fallback `/wallpaper1.mp4`，再被 API 覆盖 |
| 双重 play() 调用 | loadData 内和 .then() 各一次，可能冲突 | 只在 .then() 调一次 |
| poster/video src 设置在 `if(theme_settings)` 内 | API 不返回 theme_settings 时两者空白 | 移出 if 块，永远先设 fallback |

## 当前使用的壁纸文件

- Poster: `https://img.<用户域名>/image-wallpaper2.png` (5.4MB PNG)
- Video:  `https://img.<用户域名>/wallpaper1.mp4` (17MB MP4)
- 都托管在 WebDAV 网盘 `drive.<用户域名>` 的 img 子域名下

## Next.js 版（WallpaperBackground 组件，2026-05-16）

路径：`src/components/WallpaperBackground.tsx`

**关键参数（延续旧版极暗壁纸偏好）：**
- `filter: brightness(0.35)` — 极暗，用户曾明确反对 brightness(>1.0) 让壁纸过亮
- `rgba(2,2,3,0.55)` 暗色覆盖层 — 与 `--bg-deepest` 同色系，比旧版 `0.85` 更通透
- 视频通过 `onCanPlay` 回调触发 `opacity: 0→1` 过渡（600ms）
- 自动播放被拦截时绑定 DOM click/touchstart 重试
- `z-index: -30` 置于 ThreeBackground (-20) 之后

```tsx
export function WallpaperBackground() {
  return (
    <div className="fixed inset-0 -z-30 overflow-hidden" aria-hidden="true">
      <img src={POSTER_URL} className="..." style={{ filter: "brightness(0.35)" }} />
      <video src={VIDEO_URL} ... className="..." style={{ filter: "brightness(0.35)" }} />
      <div className="absolute inset-0 bg-[rgba(2,2,3,0.55)]" />
    </div>
  );
}
```
