# 卡片视图重设计（三阶段演变）

## v1 → 初始状态
```
header: ● 🐧 name 🇯🇵（国旗 20×14）
specs: OS · Virt
meters: CPU ████ / 内存 ████ / 磁盘 ████（3 行进度条）
────────────────────────
footer row 1: ↑ speed │ ↓ speed
footer row 2: 🕐 uptime │ updated
footer row 3: 📊 traffic │ ¥ price │ days
```
- 3 行 footer 太挤，信息层级扁平
- 国旗太小（20×14px）
- 网络速率放在 footer 不合适（它是实时指标，应跟 CPU/内存放一起）

## v2 → 最终状态 ✅
```
header: ● 🐧 name              🇯🇵（国旗 28×20）
specs: OS · virt · CPU model（一行硬件摘要）
meters: CPU ██████ 5.0%
        内存 ████████████ 25.5%  122M/474M
        磁盘 ██████░░░░ 17.1%   1.3G/7.8G
        ↑ 5.3K/s │ ↓ 0B/s（网络速率移到 meters 区）
────────────────────────
footer: 🕐 15天 · 📊 70G/500G · 🟢¥148/年  286天（单行）
```

### 具体改动

| 条目 | 改前 | 改后 |
|------|------|------|
| 国旗尺寸 | 20×14px | 28×20px，`object-fit: contain` |
| specs 行 | 单独 `Debian · KVM` | 合并 CPU 型号 `Debian · kvm · Intel` |
| metrics | 3 行（CPU/内存/磁盘） | 4 行（+ 网络速率） |
| footer | 3 行（uptime/traffic/price 分离） | 单行（圆点 · 分隔） |
| 价格 | 普通灰色字 | 绿色胶囊 badge `#29a944` |
| 标签 | 单独 chip 在卡片外 | 在 footer 行尾部显示 `[tag1] [tag2]` |

### CSS 要点
```css
.node-card { display: flex; flex-direction: column; gap: 8px; padding: 14px;
  background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.06);
  border-radius: 16px; backdrop-filter: blur(80px) brightness(1.1); }
.node-header { display: flex; align-items: center; gap: 8px; }
.node-specs { font-size: 11px; color: rgba(255,255,255,0.4); }
.metric-row { display: flex; align-items: center; gap: 8px; }
.metric-header { width: 36px; font-size: 11px; color: rgba(255,255,255,0.5); }
.metric-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.08); border-radius: 3px; }
.metric-value { width: 46px; text-align: right; font-size: 6px; font-weight: 600; }
.price-badge { background: #29a944; padding: 0 6px; border-radius: 4px; font-size: 10px; }
.flag-icon { width: 28px; height: 20px; object-fit: contain; border-radius: 2px; }
.node-status { width: 8px; height: 8px; border-radius: 50%; }
.node-status.online { background: #29a944; box-shadow: 0 0 6px rgba(41,169,68,0.6); }
.node-status.offline { background: #dc3545; }
```

### 标签显示
标签通过 komari 数据库的 `clients` 表的 `tags` 列存储（逗号分隔字符串）。通过 API 添加：
```sql
UPDATE clients SET tags = '主力,香港,CUG' WHERE uuid = 'acck-hk';
```
或通过 admin API `/api/admin/client/{uuid}/edit`。
页面显示为 `[tag1] [tag2] [tag3]` chip 样式，每个 10px green-bg badge。
