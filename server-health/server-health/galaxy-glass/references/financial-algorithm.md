# 财务算法（月度开销 + 剩余折旧）

数据来源：节点 API 的 `price`, `billing_cycle`, `currency`, `expired_at`。

## 核心函数

```js
// 在 updateStats() 中运行
const exchangeRate = await fetchExchangeRate(); // fallback: 6.82
let totalMonthly = 0, totalRemaining = 0, totalPrepaid = 0;

nodes.forEach(n => {
  const price = n.price || 0;
  const currency = n.currency || '¥';
  const billingCycle = parseInt(n.billing_cycle);
  const expiredAt = n.expired_at;
  const priceCNY = currency === '$' ? price * exchangeRate : price;

  // 月费折算
  if (billingCycle === 0) { /* 永久: 不计入月费 */ }
  else if (billingCycle >= 30) {
    totalMonthly += priceCNY * 30 / billingCycle;
  }

  // 剩余折旧
  if (billingCycle === 0) {
    totalRemaining += priceCNY; // 永久: 原价不折旧
    totalPrepaid += priceCNY;
  } else if (expiredAt) {
    const remainMs = new Date(expiredAt).getTime() - Date.now();
    const totalMs = billingCycle * 86400000;
    if (remainMs > 0) {
      totalRemaining += priceCNY * (remainMs / totalMs);
      totalPrepaid += priceCNY;
    }
  }
  // 月付也按到期日折旧
});
```

## 四个统计卡

### 第④卡：月度开销 + 剩余折旧

```
行1: ¥107/月                 ¥1065
行2: ≈ $16/月 @6.82          ¥1154 · 92%
     └─ USD对照+实时汇率       └─ 总预付 · 剩余占比
```

### 渲染

```js
const totalUSD = totalMonthly / exchangeRate;
statCard4HTML = `
  <div class="stat-value" style="font-weight:600">¥${totalMonthly.toFixed(0)}/月
    <span class="stat-sub" style="font-size:11px;opacity:0.5">≈ $${totalUSD.toFixed(0)}/月 @${exchangeRate.toFixed(2)}</span>
  </div>
  <div class="stat-value" style="font-weight:600">¥${totalRemaining.toFixed(0)}
    <span class="stat-sub" style="font-size:11px;opacity:0.5">¥${totalPrepaid.toFixed(0)} · ${totalPrepaid > 0 ? (totalRemaining/totalPrepaid*100).toFixed(0) : '0'}%</span>
  </div>
`;
```

## 周期映射

| billing_cycle | 显示文字 | 月费折算 | 折旧方式 |
|---------------|---------|---------|---------|
| 0 | 永久 | 不计入 | 不折旧，全价剩余 |
| 30 | 月 | `price` | 按到期日比例 |
| 365 | 年 | `price / 12` | `price × remainDays/365` |
| 1095 | 3年 | `price / 36` | `price × remainDays/1095` |

## 汇率

```js
async function fetchExchangeRate() {
  const url = 'https://v6.exchangerate-api.com/v6/YOUR_KEY/latest/USD';
  try {
    const res = await fetch(url);
    const data = await res.json();
    return data.conversion_rates.CNY;
  } catch(e) {
    // 保留上次成功值或使用默认 6.82
    return 6.82;
  }
}
```

⚠️ 使用 exchangerate-api.com 免费版，数据源为欧洲央行(ECB)+IMF，日更新。对监控面板足够，但不适合财务记账。
