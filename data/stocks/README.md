# A 股本地数据库

**数据源**: Tushare (8000+ 积分)
**最后更新**: 2026-04-06
**数据范围**: 2023-04 至今 (约 3 年)

---

## 📊 数据统计

| 数据类型 | 文件数量 | 说明 |
|---------|---------|------|
| **股票列表** | 1 个 | 5497 只 A 股上市公司 |
| **日线数据** | 5171 个 | 前复权日线行情 |
| **指数数据** | 待拉取 | 主要市场指数 |
| **资金流** | 待拉取 | 主力资金流向 |
| **财务数据** | 待拉取 | 财报指标 |

---

## 📁 目录结构

```
stocks/
├── stock_list.csv      # 股票列表 (5497 只)
├── daily/              # 日线数据 (CSV 格式)
│   ├── 000001_SZ.csv   # 平安银行
│   ├── 000002_SZ.csv   # 万科 A
│   ├── 600519_SH.csv   # 贵州茅台
│   └── ...
├── index/              # 指数数据 (待拉取)
├── moneyflow/          # 资金流 (待拉取)
└── fina/               # 财务数据 (待拉取)
```

---

## 📈 数据字段

### 日线数据 (daily/*.csv)

| 字段 | 说明 | 示例 |
|------|------|------|
| ts_code | 股票代码 | 000001.SZ |
| trade_date | 交易日期 | 2023-04-07 |
| open | 开盘价 | 1432.18 |
| high | 最高价 | 1445.85 |
| low | 最低价 | 1424.20 |
| close | 收盘价 | 1437.87 |
| pre_close | 前收盘价 | 1433.32 |
| change | 涨跌额 | 0.04 |
| pct_chg | 涨跌幅 (%) | 0.318 |
| vol | 成交量 (手) | 607925.26 |
| amount | 成交额 (千元) | 767354.80 |

---

## 🔧 使用方法

### Python API

```python
import pandas as pd

# 读取单只股票
df = pd.read_csv('daily/000001_SZ.csv')

# 批量读取
import glob
files = glob.glob('daily/*.csv')
all_data = [pd.read_csv(f) for f in files[:100]]  # 前 100 只
```

### 命令行工具

```bash
cd /home/li/.openclaw/workspace/quant

# 分析单只股票
python3 main.py analyze 000001.SZ

# 回测策略
python3 main.py backtest ma --codes 000001.SZ,600519.SH
```

---

## ⚡ 数据更新

```bash
# 重新拉取最新数据
python3 scripts/fetch_data.py
```

---

## 📝 注意事项

1. **数据为前复权** - 已考虑分红配股影响
2. **缓存机制** - 首次拉取后会自动缓存
3. **真实数据** - 来自 Tushare，无模拟数据

---

*淘金者量化系统 ⛏️*
