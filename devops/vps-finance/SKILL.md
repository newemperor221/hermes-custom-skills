---
name: vps-finance
description: VPS 财务资产管理——running cost tracking、到期预警、资产报告。脚本 ~/.hermes/scripts/vps-finance.py。定时任务 vps-expiry-watch（每周一10:00检查到期）。
---

# VPS 财务管理

## 数据源
所有服务器财务数据维护在 `~/.hermes/inventory/servers.yaml`，每个节点包含：

```yaml
- name: 东京1
  price: 148.88        # 总价
  billing_cycle: 365    # 天数（年付/月付/季付）
  currency: "¥"
  expired_at: "2027-02-19T00:00:00Z"  # ISO 格式到期日
  auto_renewal: false
```

## 脚本

### vps-finance.py

路径：`~/.hermes/scripts/vps-finance.py`

输出：每个服务器月均开销、到期倒计时、剩余价值 + 汇总（月度总开销、年度总开销、剩余资产总值）

```bash
# 终端查看
python3 ~/.hermes/scripts/vps-finance.py

# JSON 输出（供程序消费）
python3 ~/.hermes/scripts/vps-finance.py --json
```

### 到期预警

定时任务 `vps-expiry-watch`（每周一 10:00）：
- 运行脚本检查 `warnings`
- 有到期/过期服务器 → 醒目报告
- 一切正常 → "✅ 所有服务器均在有效期内"

## 采购调研 (Procurement Research)

在购买新 VPS 之前，需要做完整的产品调研和路由质量评估。

### 调研流程

```
1. 获取产品目录 → 浏览器打开 provider 商店页面
2. 精选候选产品 → 关注稀有地区/特殊线路/价格/配置
3. 查找真实评测 → NodeSeek 搜索 "provider 地区 延迟 路由"
4. 汇总路由数据 → 按运营商整理电信/联通/移动延迟
5. 对比推荐 → 按直连质量对候选排序
6. 核验预算 → vps-finance.py 计算总资产变化
```

### 数据源

| 来源 | 用途 | 优先级 |
|:-----|:-----|:------:|
| **Provider 官网** | 产品目录、价格、配置、库存 | 🥇 |
| **NodeSeek** | 真实用户评测、三网路由追踪、实际延迟 | 🥇 |
| **HostLoc / LowEndTalk** | 商家口碑、争议记录 | 🥈 |
| **VPS 融合怪脚本** | NodeSeek 帖子中常用的一键测试脚本 | 🥈 |
| **TG 频道 (@vps_reviews)** | 实时评测推送 | 🥉 |

### 路由质量评估

对于 **普通国际带宽**（非 CN2/CUII/CMIN2）的玩具 VPS，实际体验规律：

| 地区 | 直连延迟 | 特点 |
|:-----|:--------:|:-----|
| 🇺🇸 **洛杉矶/圣何塞** | 140~170ms | 美西最优，物理距离最近 |
| 🇺🇸 **达拉斯** | 200~230ms | 联通移动直连还行，电信约211ms |
| 🇺🇸 **芝加哥** | 200~280ms | 联通可能极差（>400ms） |
| 🇺🇸 **水牛城/纽约** | 220~250ms | 几乎无法直连 |
| 🇨🇦 **多伦多** | 200~250ms | 普通水平 |
| 🇳🇱 **荷兰** | 250~350ms | 欧洲绕路，最差 |
| 🇸🇬 **新加坡** | 80~150ms（理论上） | 地理最近，但看具体路由 |
| 🇯🇵 **日本** | 80~120ms（理论上） | 亚洲最优，但56idc日本是KVM ¥50/年起 |

### 路由分析命令（拿到 VPS 后实测）

```bash
# 查看三网回程路由（需要在 VPS 上跑）
curl -s https://raw.githubusercontent.com/oneclickvirt/backtrace/main/install.sh | bash

# mtr 追踪
mtr -n -c 50 <中国IP>

# 一键融合怪（流媒体+路由+性能）
curl -s https://raw.githubusercontent.com/oneclickvirt/ecs/main/ecs.sh | bash
```

### 展示格式

向用户展示推荐时使用结构化对比表 + 路由细节，按运营商拆分：

```
| 排名 | 地区 | 价格 | 电信 | 联通 | 移动 | 综合 |
|:----:|:----|:----:|:----:|:----:|:----:|:----:|
| 🥇 | ... | ... | 实测 | 实测 | 实测 | 评价 |
```

路由细节用缩进代码块展示 traceroute 摘要。

### 相关文件

- **`references/56idc-product-routing.md`** — 56idc 无聊云全线产品目录和实测路由数据

## 数据流
```
servers.yaml → vps-finance.py（脚本）→ 终端报告
             → komari API（已集成到 stat 面板第4张统计卡）
             → vps-expiry-watch（cron job → Telegram 推送）
```

## 汇率
固定汇率：1 USD = 6.81 CNY
