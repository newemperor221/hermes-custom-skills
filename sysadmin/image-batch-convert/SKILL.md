---
name: image-batch-convert
description: 批量图像格式转换 — PNG→WebP, JPEG→WebP, MP4→WebM/VP9。使用 cwebp/ffmpeg 一键递归转换，质量参数调优，确认输出。触发："转 WebP"、"转 WebM"、"批处理图片"、"图片优化"、"转格式"、"convert images"。
---

# 批量图像格式转换

## 适用场景

- 将 PNG/JPEG 批量转 WebP（用户偏好格式）
- 将 MP4 批量转 WebM/VP9（用户偏好格式）
- 递归处理目录中的图像
- 指定质量/压缩率参数
- 转换后对比文件大小

## 前置安装

```bash
# 安装 webp 工具（cwebp, dwebp, gif2webp 等）
sudo apt install webp       # Debian/Ubuntu
sudo apk add libwebp-tools  # Alpine

# ffmpeg（视频转 WebM）
sudo apt install ffmpeg     # Debian/Ubuntu
sudo apk add ffmpeg         # Alpine

# 可选：ImageMagick（备用方案）
sudo apt install imagemagick
```

## 常用命令

### 1. 单文件 PNG → WebP

```bash
cwebp -q 85 input.png -o output.webp
```

质量参数说明：
- `-q 80`：有损，视觉无损级别（推荐，大小/质量平衡好）
- `-q 90-95`：高质量，文件较大
- `-q 100`：无损（不推荐，文件比 PNG 还大）
- 不加 `-q`：默认 75

### 2. 递归批处理全部 PNG → WebP（推荐脚本）

```bash
# 当前目录下所有 PNG 转 WebP，保持目录结构
find . -name "*.png" -type f | while read f; do
  output="${f%.png}.webp"
  cwebp -q 85 "$f" -o "$output"
  echo "→ $output ($(du -h "$output" | cut -f1), original: $(du -h "$f" | cut -f1))"
done
```

### 3. 递归批处理全部 JPEG/JPG → WebP

```bash
find . -name "*.jpg" -o -name "*.jpeg" | while read f; do
  output="${f%.*}.webp"
  cwebp -q 85 "$f" -o "$output"
done
```

### 4. 一键转全部（PNG+JPG）

将此脚本保存为 `to-webp.sh`：

```bash
#!/bin/sh
find . \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" \) -type f | while read f; do
  dir=$(dirname "$f")
  base=$(basename "$f")
  name="${base%.*}"
  output="$dir/$name.webp"
  if [ ! -f "$output" ]; then
    cwebp -q 85 -quiet "$f" -o "$output"
    echo "✓ $output (was $base)"
  else
    echo "− $output (already exists, skipping)"
  fi
done
```

### 5. 批量压缩已有 WebP（降低质量）

```bash
find . -name "*.webp" -type f | while read f; do
  mv "$f" "$f.bak"
  cwebp -q 75 "$f.bak" -o "$f" && rm "$f.bak"
done
```

### 6. MP4 → WebM（VP9 编码）

```bash
# 基本转换
ffmpeg -i input.mp4 -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus output.webm

# 高质量（推荐，CRF 越小质量越高）
ffmpeg -i input.mp4 -c:v libvpx-vp9 -crf 25 -b:v 0 -c:a libopus output.webm

# 更小文件（CRF 35-40，适合壁纸等不要求画质的场景）
ffmpeg -i input.mp4 -c:v libvpx-vp9 -crf 35 -b:v 0 output.webm

# 指定分辨率（如 1920x1080）
ffmpeg -i input.mp4 -vf "scale=1920:1080" -c:v libvpx-vp9 -crf 30 -b:v 0 output.webm

# 15 秒循环壁纸（截取前 15 秒）
ffmpeg -i input.mp4 -t 15 -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus output.webm
```

### 7. 批量 MP4 → WebM 递归

```bash
find . -name "*.mp4" -type f | while read f; do
  output="${f%.mp4}.webm"
  ffmpeg -i "$f" -c:v libvpx-vp9 -crf 30 -b:v 0 -c:a libopus "$output" -y -loglevel error
  echo "✓ $output"
done
```

### 8. 静态壁纸 → 内嵌 data URL

```bash
# 先转 WebP
cwebp -q 85 wallpaper.png -o wallpaper.webp

# 生成 data URL（直接嵌入 HTML）
echo "data:image/webp;base64,$(base64 -w0 wallpaper.webp)"
```

复制输出粘贴到 HTML 的 `src` 属性。

### 9. 查看图像信息

```bash
# WebP 信息
webpinfo image.webp

# 通用图像信息
ffprobe image.webp
identify image.webp   # ImageMagick
```

## 踩坑记录

1. **VP9 编码很慢** — libvpx-vp9 编码速度远慢于 H.264 转 MP4。小文件用 `-deadline realtime`，大文件要等几十秒
2. **WebM 不含字幕/多音轨** — ffmpeg 默认只取第一轨
3. **已经转过的文件会再次转** — 上面脚本用 `[ -f "$output" ]` 检查跳过已存在的，避免重复转换
4. **透明 PNG 转 WebP** — cwebp 自动保留 alpha 通道，无需特殊参数
5. **动画 PNG/GIF → 动画 WebP** — 用 `gif2webp`（libwebp-tools 包含）

## 验证步骤

```bash
# 对比大小
ls -lh original.png converted.webp

# 检查 WebP 有效性
webpinfo converted.webp | head -5

# 确认 WebM 可播放
ffprobe converted.webm 2>&1 | grep -E "Duration|Stream"
```
