# Preview 预览图生成

Komari 主题需要一张预览图（`preview.webp`），展示主题实际运行效果。

## 生成流程

1. 打开目标页面（浏览器导航到实际站点）
2. 截图（使用 `browser_vision` 或 `browser_snapshot`）
3. 转换 PNG → WebP

## 转换工具

### cwebp（推荐，已预装）
```bash
cwebp -q 85 input.png -o preview.webp
```

### 无工具时的备用方案
如果 `cwebp` 不可用：
```bash
pip install Pillow --break-system-packages
python3 -c "
from PIL import Image
img = Image.open('input.png')
img.save('preview.webp', 'WEBP', quality=85)
"
```

## 验证
```bash
file preview.webp
# → Web/P image, ...
ls -la preview.webp  # 目标 ~100KB
```
