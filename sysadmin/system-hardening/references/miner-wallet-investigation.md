# 矿池钱包取证 — 追溯攻击者收益

发现挖矿木马后，矿池钱包地址可以揭示攻击者的规模、收益、还有哪些肉鸡在挖。

## Kryptex Pool (xmr.kryptex.network)

攻击者的 XMRig 命令行中 `-u` 参数即为矿池账户/钱包地址。

### 查询步骤

1. 访问池子首页：`https://pool.kryptex.com/xmr`
2. 在搜索框输入钱包地址（`Enter your XMR wallet address`），点击 Search
3. 获取信息：

| 数据 | 说明 |
|------|------|
| Workers | 在线矿机数、名称、算力、版本 |
| Hashrate | 30min / 3h / 24h 平均算力 |
| Balance | 未支付余额（XMR + USD 换算） |
| Payouts | 7天/30天收益 + 累计已提现（关键！判断黑客规模） |
| Worker 详情 | 每台矿机名、30min/24h 算力、有效/过期/无效份额、XMRig 版本 |

### 典型解读

```
"worker" @ 132.61 KH/s  →  100+ 核的服务器或集群（主力肉鸡）
"systemp" @ 1.00 KH/s  →  1核小机子（伪装进程名）
"u7reyy-4C" @ 317 H/s  →  极低配设备
```

- 30天收益 $92.78 + 累计提现 $307.32 → 至少跑了 1-2 个月，不止一台肉鸡
- 未支付余额 → 即使 kill 了矿机，黑客还没提走的钱

### 钱包地址验证（未知矿池时）

手头只有钱包地址但不知道对应的矿池时，先用 Monero 区块链浏览器验证地址有效性：

```bash
# xmrchain.net — 无 JS、无 Cookie，适合脚本化查询
# 查询 URL：
#   https://xmrchain.net/search?value=<WALLET_ADDRESS>
#
# 返回信息：
# - Valid address ✅ → "Network type: Mainnet"
# - Associated public keys（view key + spend key）
# - "Transactions: Sorry, its not possible to find txs associated with normal addresses in Monero"
#
# 限制：Monero 是隐私币，地址级别不可查交易记录
#       只有拿到 view key 才知道已收金额
#       只有矿池 dashboard 能看到算力/收益
```

**真实案例**（荷兰鸡矿机 2026-05-18）：
```
地址: 47S6DU9Qm3K848Krv6fAfZGgRn75653nbEPMxx3CYrWXBeTYnttJaWCDxDErGhH53u2cmbwahUymzPx71qDPneMsGjQ5pj4
View key:  a5aff871ae40b94d6f371a6992735809aa68adb5d6f4e989359f8facbe86d68b
Spend key: 995137ebd36d2e2a2c2a70372dbca05dbe474fafdf6d0c5006e4d55deded9c3f
Transactions: 不可查（Monero 隐私限制）
```

**工作流**：xmrchain.net 确认地址有效 → 去主流矿池（Kryptex、SupportXMR、MineXMR、MoneroOcean）逐个搜 → 找到对应池子后取 worker 列表和收益数据。

### 限制

- 门罗币是隐私币，无法从链上查余额
- Kryptex 本身是把 XMR 换成 BTC 支付，实际黑客拿到的是 BTC
- 钱包地址仅在连接矿池期间可查，断连后矿池不再显示离线数据
- xmrchain.net 只能验地址——查不到交易和余额，必须有矿池 dashboard 才能看到算力/收益

### 应用场景

| 场景 | 做法 |
|------|------|
| 举报证据 | wallet address + pool stats + total paid 截图提交给云厂商 |
| 评估损失 | 对比他的 Total Paid vs 你的机器算力占比 |
| 发现更多肉鸡 | worker 列表显示了他手里还有多少台被控机器 |
