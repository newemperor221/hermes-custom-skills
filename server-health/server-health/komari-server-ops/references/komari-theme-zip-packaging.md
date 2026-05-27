# Komari Theme Zip Packaging Format

## Standard Format

When packaging a Komari theme for admin-panel upload, the zip MUST have this structure:

```
Glass-v1.0.0.zip
├── komari-theme.json      ← zip root (Komari reads this for metadata)
├── icon.svg               ← theme icon (optional, used in theme selector)
├── preview.png            ← screenshot (optional, used in theme selector)
└── dist/
    └── index.html         ← THEME ENTRY POINT (served as static root)
```

## komari-theme.json

```json
{
  "name": "Glass",
  "short": "Glass",
  "description": "深色毛玻璃主题，视频壁纸，实时CPU/内存/网络图表",
  "version": "1.0.0",
  "author": "M78 星云",
  "url": "https://github.com/newemperor221/glass",
  "preview": "preview.png",
  "configuration": {}
}
```

## How to create a release

```bash
# 1. Build single-file index.html from src/
./build.sh

# 2. Package into Komari-compatible zip
mkdir -p /tmp/Glass-v1.0.0/dist
cp index.html /tmp/Glass-v1.0.0/dist/
cp komari-theme.json icon.svg preview.png /tmp/Glass-v1.0.0/
cd /tmp && zip -r Glass-v1.0.0.zip Glass-v1.0.0/

# 3. Create GitHub release
gh release create v1.0.0 \
  --title "Glass v1.0.0" \
  --notes "## Glass v1.0.0\n\nRelease notes here..." \
  /tmp/Glass-v1.0.0.zip
```

Or use the project's `release.sh` script which does all three steps:

```bash
./release.sh v1.0.0
```

## Single-file vs multi-directory themes

- **Single-file themes** (like Glass): all CSS/JS inlined into `index.html`. Only `dist/index.html` needed.
- **Multi-file themes** (like Komari-Next): `dist/` contains `index.html`, `_next/`, `assets/`, `404.html` etc.

Both work — Komari serves the entire `dist/` directory as static root.

## Deploy to theme directory (manual SCP)

```bash
# Direct placement
scp index.html root@server:/opt/komari/data/theme/Glass/dist/

# Also sync to theme root for backward compatibility
scp index.html root@server:/opt/komari/data/theme/
```

## Theme name migration (renaming)

If renaming a theme (e.g. GalaxyGlass → Glass):

1. Rename server directory: `mv /opt/komari/data/theme/GalaxyGlass /opt/komari/data/theme/Glass`
2. Update `komari-theme.json` name/short/version
3. Update root `komari-theme.json` if duplicate exists
4. Copy built `index.html` to both `Glass/dist/` and `theme/` root
5. Update local repo references, commit, push
6. Rename GitHub repo: `gh repo rename glass --repo old-org/old-name`
7. Update git remote: `git remote set-url origin git@github.com:user/glass.git`
