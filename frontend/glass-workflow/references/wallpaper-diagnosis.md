# Glass 动态壁纸不动 — 排查记录（2026-05-27）

## 现象

用户反馈动态壁纸"没动"——页面上看到的是静态背景图而非视频动画。

## 排查链路

### 第 0 步：确认你在看正确的页面

Glass 主题在 `https://<监控面板域名>/`（根路径），komari 内置 admin 在 `/admin`。**不要在 `/admin` 页面检查壁纸**——那是 komari 默认主题，没有 Glass 壁纸元素。

### 第 1 步：确认壁纸 URL 配置

登录 komari admin 后台 → 左侧菜单 **Glass 设置**，检查：

| 字段 | 当前值 | 说明 |
|------|--------|------|
| 静态壁纸 URL | `https://img.<用户域名>/image-wallpaper.png` | PNG 静态底图（3840×2160） |
| 动态壁纸 URL | `https://img.<用户域名>/wallpaper.mp4` | MP4 视频（17MB, H.264, 15s 循环） |

两个 URL 都能通过 `curl -sI` 确认 HTTP 200。

### 第 2 步：检查视频源是否可达

```bash
curl -sI "https://img.<用户域名>/wallpaper.mp4"
# → HTTP/2 200, content-type: video/mp4, content-length: 17420091
```

### 第 3 步：浏览器控制台逐一验证

```javascript
// 1. DOM 元素是否存在
document.getElementById('bg-video')      // → <video> 元素
document.getElementById('bg-layer')      // → <div> 元素

// 2. 视频播放状态
const v = document.getElementById('bg-video');
v.paused           // → false（在播放）
v.currentTime      // → 在增长（数据在流）
v.readyState       // → 4 = HAVE_ENOUGH_DATA（缓冲完毕）
v.error            // → null（无报错）
v.muted            // → true（必须静音才能自动播放）
v.loop             // → true（循环）
v.duration         // → 15（秒）

// 3. CSS 类是否正确
v.classList.contains('loaded')                          // → true（视频透明→可见）
document.getElementById('bg-layer').classList.contains('faded')  // → true（静态透明→隐藏）

// 4. 计算样式
getComputedStyle(v).opacity                             // → "1"
getComputedStyle(document.getElementById('bg-layer')).opacity  // → "0"

// 5. 完整快照
(() => {
  const v = document.getElementById('bg-video');
  const l = document.getElementById('bg-layer');
  return {
    videoExists: !!v,
    videoSrc: v?.src,
    paused: v?.paused,
    currentTime: v?.currentTime,
    loadedClass: v?.classList.contains('loaded'),
    fadedClass: l?.classList.contains('faded'),
    videoOpacity: getComputedStyle(v).opacity,
    layerOpacity: getComputedStyle(l).opacity,
    error: v?.error?.message || null
  };
})()
```

如果以上都正常（paused=false, currentTime 在增长, loaded/faded 类存在, 无报错），说明 **壁纸代码和视频本身都正常**。需要排查用户侧原因。

### 第 4 步：检查移动端

CSS 在 `@media (max-width: 767px)` 中隐藏了视频：

```css
@media (max-width: 767px) { .bg-video { display: none; } }
```

手机/小屏设备看不到动态壁纸，只会显示静态图片。这是有意为之的设计（移动端流畅优先）。

### 第 5 步：视频内容本身可能看起来像静态

用户偏好 WebM/VP9，但当前配置使用 MP4（H.264）。如果视频是慢镜头/延时摄影（慢速云海、日落等），用户直观感受可能是"没动"。需要确认视频实际内容：

```bash
# 下载检查（ffprobe）
curl -sL "https://img.<用户域名>/wallpaper.mp4" -o /tmp/w.mp4
ffprobe -v quiet -show_format -show_streams /tmp/w.mp4
# 关注: duration, avg_frame_rate
```

## 已知限制（无法解决的）

| 场景 | 原因 | 处理方式 |
|------|------|---------|
| 手机端（≤767px） | CSS `display: none` | 设计如此，静态图足够 |
| 用户偏好 WebM | 当前用 MP4，R2 上无 `.webm` 文件 | 如果要切 WebM，在 img.<用户域名> 上传 `/video/wallpaper.webm` 并改 theme_settings |
| 截图工具说"静态" | vision 工具只取一帧，无法感知运动 | 以 console 数据为准 |
| 浏览器自动播放策略 | 某些浏览器要求用户先交互才允许 autoplay | 检查 `v.paused` 和 `v.muted` |

## 过渡逻辑总结

```
页面加载:
  1. bg-layer: opacity 1（静态图可见）
  2. bg-video:  opacity 0（视频隐藏）

视频已就绪（readyState ≥ 3 或已开始播放）:
  3. bg-video  + .loaded  → opacity 1（2s transition）
  4. bg-layer  + .faded   → opacity 0（1.5s transition）

15 秒超时保底:
  如果 15 秒后视频还没播放（loaded 类未加）:
    放弃轮询，静态图保持可见
```

## ⚠️ 竞态条件：事件可能在 listener 绑定前就触发了

**现象**：视频 paused=false, currentTime 在增长, 但 loaded/faded 类始终不添加。用 console 手动 `v.classList.add('loaded')` 和 `l.classList.add('faded')` 则正常。

**根因**：视频加载极快（readyState=4）时，`canplay`/`loadeddata`/`playing` 事件在 JS 代码到达 `addEventListener` 行之前就已经触发了。监听器永不执行。

**三重保险修复**：
1. **即时检查**：先看 `bgVideo.readyState >= 3` 或 `!bgVideo.paused && bgVideo.currentTime > 0`
2. **事件监听**：`canplay` + `loadeddata`（{once:true}，慢加载场景）
3. **轮询保底**：300ms 间隔检查 readyState，防止第②步的监听器已错过触发事件

**验证**：在浏览器 DevTools 的 Elements 面板检查 `<video>` 元素是否有 `.loaded` 类。或运行：
```js
document.getElementById('bg-video').classList.contains('loaded')
```

## 内嵌 data URL 消除外部依赖

如果外部壁纸 URL（R2 等）不可用/不便上传，可将静态壁纸作为 **base64 data URL** 直接嵌入 index.html：

```bash
# 1. 转换 PNG → WebP（压缩 90%+）
cwebp -q 90 static.png -o static.webp
# 2. 创建 data URL 替换到 HTML
#   - 替换 bg-layer 的 inline style 中的 URL
#   - 替换 JS 中的 theme_settings 回退
```

**JS 回退写法**（替换原有的 `wallpaperStatic` 行）：
```js
var _ws = ts.wallpaperStatic || 'data:image/webp;base64,...';
var l = $('bg-layer');
if (l) l.style.background = '#0a0a0f url(' + _ws + ') center/cover no-repeat';
```

**优点**：零外部依赖，不依赖 R2/WebDAV/其他文件服务器。**缺点**：HTML 文件变大（327KB WebP → ~435KB base64），不适合大文件。

**⚠️ 注意**：内嵌 data URL 后 index.html 可能超过 500KB，某些 headless 浏览器 snapshot 可能解析失败，但真实浏览器通常可以正常渲染（已验证 Chrome）。

## ⚠️ 脏字符排查：先查源文件 src/scripts/app.js

**现象**：页面预渲染 HTML 正常显示，但所有交互失效（点击卡片、搜索、排序、过滤全部无响应），浏览器控制台无报错。

**根因**：`<script>` 块的执行语句前多了一个脏字符（如 `|` 管道符），导致整个标签**解析失败**，所有函数永不定义。

```diff
- |setupEvents();setupScroll();loadData()...
+ setupEvents();setupScroll();loadData()...
```

**排查方法**：先查**源文件**再查构建产物：

```bash
# 检查源文件（脏字符可能来自源文件而不是构建产物）
grep -n '^|' src/scripts/app.js
# 检查构建产物
grep -n '^|' /opt/komari/data/theme/Glass/dist/index.html
```

**修复脏字符后，必须同步到源文件并重新 build**，不能只改服务器上的 index.html，否则下次 build.sh 会覆盖回来。
