# 流量数据管道（准确度分析）

> komari agent 如何采集、上报网络流量数据，前端如何计算展示，以及准确度限制。

## 架构概览

```
VPS /proc/net/dev
      ↓ 读取原始 rx/tx 字节数
komari agent (Go, /opt/komari/agent)
      ↓ 计算差值: agent启动时的值vs当前值
      ↓ 每 ~60s 通过 WebSocket 上报到 server
komari server (Go, /opt/komari/komari server)
      ↓ 存储到 SQLite 时间序列表
      ↓ 通过 REST API 暴露
/api/nodes           → 节点静态信息（无 traffic_used！）
/api/recent/{uuid}   → 时间序列数据（含 network.totalUp / totalDown）
      ↓
前端 (index.html JS)
  network_total_received = latest.network?.totalDown || 0
  network_total_transmitted = latest.network?.totalUp || 0
  trafficUsed = totalUp + totalDown
  trafficLimit = n.traffic_limit  // 管理员在 komari 后台手动设置的限额
```

## 数据字段来源

| 字段 | API 路径 | 含义 |
|------|---------|------|
| `network.totalUp` | `/api/recent/{uuid}` → `data[-1].network.totalUp` | 自 agent 启动以来的**总上行字节数** |
| `network.totalDown` | 同上 | 自 agent 启动以来的**总下行字节数** |
| `network.up` | 同上 | 当前上行速率（字节/秒） |
| `network.down` | 同上 | 当前下行速率（字节/秒） |
| `traffic_limit` | `/api/nodes` → `data[i].traffic_limit` | 管理员在 komari 后台设置的流量限额（字节） |
| `traffic_limit_type` | 同上 | "sum"=上下行合计，"up"=仅上行，"down"=仅下行 |

## 关键坑

### 1. agent 重启 → 流量归零

`totalUp`/`totalDown` 不是绝对的 `/proc/net/dev` 值，而是**agent 启动以来的累计值**（agent 启动时记录初始值，后续值 = 当前值 - 初始值）。

**后果**：
- agent 重启/更新 → 流量从 0 重新累计
- 面板上显示的 `8.2 GB/299 GB` 可能只覆盖近几天，而非整个计费周期
- 如果 agent 曾在计费周期中间重启过，面板流量 < 实际流量

### 2. 不是流量计费系统数据

komari agent 报告的是 **Linux 网络接口累计流量**，不是 VPS 商家计费系统的数据。

**区别**：
| 维度 | komari 面板 | VPS 商家后台 |
|------|------------|-------------|
| 数据源 | `/proc/net/dev` | 虚拟化层 / 计费系统 |
| 覆盖范围 | agent 存活期 | 整个计费周期 |
| 受 agent 重启影响 | ✅ 是 | ❌ 否 |
| 精确度 | 字节级 | 字节级 |
| 推荐用途 | 看趋势、监控异常流量 | 核对账单、限额管理 |

### 3. `/api/nodes` 没有 `traffic_used`

前端不能直接从 `/api/nodes` 拿到 "已用流量"。必须先请求 `/api/recent/{uuid}` 拿到时间序列数据，再从最后一个数据点的 `totalUp + totalDown` 计算。

**N+1 问题**：如果有 15 个节点，需要 1 次 `/api/nodes` + 15 次 `/api/recent/{uuid}` = 16 次 HTTP 请求。当前前端用 `Promise.all` 并行请求。

### 4. 实时速率 vs 累计流量

| 显示项 | 计算方式 | 准确度 |
|--------|---------|--------|
| `↑ 1.2 KB/s` | `network.up` 直接从 agent 最近一次上报 | ✅ 准，秒级精度 |
| `📊 8.2 GB/299 GB` | `totalUp + totalDown`，agent 启动后累计 | ⚠️ 仅供参考 |
| 流量占百分比 | `(totalUp+totalDown) / traffic_limit * 100` | ⚠️ 同累计流量 |

## 验证方法

```bash
# 通过 komari API 查看某节点实时数据
curl -s http://127.0.0.1:25774/api/recent/{uuid} | jq '.data[-1].network'

# 输出示例:
# {
#   "up": 0,          # 当前上行速率 (B/s)
#   "down": 2070,     # 当前下行速率 (B/s)
#   "totalUp": 1527247579,   # 累计上行 (bytes ≈ 1.42 GB)
#   "totalDown": 7319130496  # 累计下行 (bytes ≈ 6.82 GB)
# }
```

## 如果用户问"流量统计准吗"

回答策略：
1. 实时速率（↑↓ B/s）是 **准的**（来自 `/proc/net/dev` 秒级差值）
2. 累计流量（`8.2G/300G`）是 **agent 启动以来**的累计值，**不是**计费周期流量
3. agent 重启会归零 → 面板可能低估实际用量
4. **精确账单**要去 VPS 商家后台看，komari 面板更适合**看趋势**
