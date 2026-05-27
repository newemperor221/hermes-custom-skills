# komari 1.2.0 detail.html 调试记录（2026-05-10）

## 事件经过

1. 用户说「详情页被你搞哪去了」
2. 查服务器文件发现 detail.html 只有 653 行（旧版），实际 git 仓库已有 729 行新版
3. 根因：`git push --force` 被 reject 后以为没 push 成功，没重试；SCP 是独立步骤没有同步做

## komari 1.2.0 detail.html 关键适配点

### 背景视频（theme_settings.videoUrl / posterUrl）

```javascript
async function fetchPublicInfo() {
  try {
    const res = await fetch('/api/public');
    const data = await res.json();
    return data.data || {};
  } catch { return {}; }
}

async function init() {
  const publicInfo = await fetchPublicInfo();
  const ts = publicInfo.theme_settings || {};
  const poster = document.getElementById('poster');
  const video = document.getElementById('bg-video');

  if (ts.posterUrl) {
    poster.src = ts.posterUrl;
    poster.style.opacity = '1';
  }
  if (ts.videoUrl) {
    video.src = ts.videoUrl;
    video.play().then(() => {
      video.style.opacity = '1';
      if (ts.posterUrl) poster.style.opacity = '0';
    }).catch(() => { poster.style.opacity = '1'; });
  }
}
```

### 新字段（komari 1.2.0）

```javascript
// node 静态信息
const cpuCores = node.cpu_cores || '-';
const swapTotal = node.swap_total || 0;
const trafficLimit = node.traffic_limit || 0;

// latest 实时数据
const load1 = latest?.load?.load1 ?? latest?.load1 ?? null;
const load5 = latest?.load?.load5 ?? latest?.load5 ?? null;
const load15 = latest?.load?.load15 ?? latest?.load15 ?? null;
const process = latest?.process || '-';
const tcp = latest?.connections?.tcp || '-';
```

### 负载 Badge 颜色逻辑

```javascript
function loadBadgeClass(v, cores) {
  if (v >= (cores || 1) * 2) return 'high';
  if (v >= (cores || 1) * 1) return 'medium';
  return 'low';
}
```

### Canvas 绘图要点

- HTML：`canvas id="chart-cpu" height="160"` — **不写 width**
- JS：双 requestAnimationFrame 等 layout 完成后再画
- 背景视频从 `/api/public → theme_settings` 读取

## git push --force 被拒的处理

```bash
git fetch origin main
git reset --hard origin/main
git cherry-pick <your-commit>
git push origin main
# SCP 是独立步骤！
scp -P 42185 detail.html root@<洛杉矶2_IP>:/data/theme/GalaxyGlass/detail.html
```
