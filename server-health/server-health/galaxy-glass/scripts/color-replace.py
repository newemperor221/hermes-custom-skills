#!/usr/bin/env python3
"""
GalaxyGlass 全局色值替换工具

替换 index.html 中所有旧色值（含 CSS rgba 和 JS 硬编码 hex）为新色值。
安全替换：只要旧色值在新 HTML 中还被查到，说明替换不完全。

用法:
  python3 color-replace.py < index.html > index-new.html

或直接在源文件上操作:
  python3 -c "$(cat color-replace.py)" < /opt/komari/data/theme/index.html > /tmp/gg_new.html

生成替换映射表后，必须验证：
  node --check /tmp/gg_v.js   # 提取 inline script 验证 JS 语法
  grep '#10b981' index-new.html  # 应为 0
  grep '#818cf8' index-new.html  # 应为 0
"""

import re
import sys

REPLACEMENTS = [
    # --accent: emerald → natural green (from wallpaper grass)
    ('#10b981', '#2d9e6b'),
    # --accent-2: indigo → warm yellow (from wallpaper bus)
    ('#818cf8', '#c9a94e'),
    # All CSS rgba for old accent #10b981 → #2d9e6b
    ('rgba(16,185,129,', 'rgba(45,158,107,'),
    # All CSS rgba for old accent-2 #818cf8 → #c9a94e
    ('rgba(129,140,248,', 'rgba(201,169,78,'),
]

# --- Background color presets (wallpaper sky-extracted) ---
# Active since 2026-05-13: bright daytime wallpaper → lighter sky-tinted background
('#030512', '#081830'),   # --bg-deepest
('#080d24', '#0c1f3f'),   # --bg-deep
('#0e152e', '#12284a'),   # --bg-surface


def main():
    html = sys.stdin.read()
    total = 0
    for old, new in REPLACEMENTS:
        count = html.count(old)
        if count > 0:
            html = html.replace(old, new)
            total += count
            print(f'  [{count:2d}x] {old} → {new}', file=sys.stderr)
    
    # Verify
    for old, _ in REPLACEMENTS:
        remaining = html.count(old)
        if remaining > 0:
            print(f'⚠️  {remaining} x {old} still present!', file=sys.stderr)
    
    print(f'Total: {total} replacements', file=sys.stderr)
    sys.stdout.write(html)
    return 0 if total > 0 else 1


if __name__ == '__main__':
    sys.exit(main())
