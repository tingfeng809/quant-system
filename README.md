# A 股量化分析系统 - 淘金者版 ⛏️

> 基于真实市场数据的专业量化分析框架
> 
> **核心原则：所有数据必须来自真实数据源，禁止使用模拟、随机、测试数据**

---

## 📋 系统架构

```
quant/
├── config/              # 配置文件
│   └── settings.py      # 系统配置 (Tushare token、回测参数等)
├── data/                # 数据模块
│   └── data_loader.py   # 数据加载器 (基于 Tushare)
├── factors/             # 因子计算
│   ├── technical_factors.py  # 技术因子 (MA/MACD/RSI/KDJ 等)
│   └── moneyflow_factors.py  # 资金流因子 (主力净流入、资金流评分等)
├── strategies/          # 策略库
│   └── example_strategies.py # 示例策略
├── backtest/            # 回测引擎
│   └── engine.py        # 回测引擎 (支持多策略)
├── output/              # 输出目录 (回测结果、图表等)
├── data/cache/          # 数据缓存
├── main.py              # 主程序 (CLI)
└── README.md            # 本文档
```

---

## 🚀 快速开始

### 1. 环境准备

已安装依赖：
- Python 3.12+
- Tushare (8000+ 积分权限)
- pandas, numpy, matplotlib
- TA-Lib (技术分析库)

### 2. 命令行使用

```bash
cd /home/li/.openclaw/workspace/quant

# 查看帮助
python3 main.py --help

# 获取股票列表
python3 main.py list

# 获取个股数据
python3 main.py fetch daily --code 000001.SZ

# 分析股票 (技术面 + 资金流)
python3 main.py analyze 000001.SZ

# 回测策略
python3 main.py backtest ma --codes 000001.SZ,600000.SH --start 20240101 --end 20241231
python3 main.py backtest macd --codes 000001.SZ
python3 main.py backtest multi --codes 000001.SZ,600000.SH,000002.SZ
```

### 3. Python API 使用

```python
from data.data_loader import DataLoader
from factors.technical_factors import TechnicalFactors
from backtest.engine import BacktestEngine
from strategies.example_strategies import DualMAStrategy

# 加载数据
loader = DataLoader()
df = loader.get_daily_data('000001.SZ', start_date='20240101')

# 计算技术因子
tech = TechnicalFactors()
df_with_factors = tech.calculate_all(df)

# 运行回测
strategy = DualMAStrategy()
engine = BacktestEngine(initial_capital=100000)
result = engine.run(strategy, {'000001.SZ': df}, '20240101', '20241231')

print(f"总收益率：{result.total_return*100:.2f}%")
print(f"夏普比率：{result.sharpe_ratio:.2f}")
```

---

## 📊 可用策略

### 1. 双均线策略 (`DualMAStrategy`)
- **买入**: MA5 上穿 MA20 (金叉)
- **卖出**: MA5 下穿 MA20 (死叉)
- **适用**: 趋势行情

### 2. MACD 策略 (`MACDStrategy`)
- **买入**: DIF 上穿 DEA (金叉) 且 MACD>0
- **卖出**: DIF 下穿 DEA (死叉)
- **适用**: 震荡 + 趋势

### 3. 多因子综合策略 (`MultiFactorStrategy`)
- **买入**: 满足 3 个以上条件
  - 均线多头排列 (MA5>MA10>MA20)
  - MACD>0 且 DIF>DEA
  - RSI(12) 在 50-70
  - 5 日动量>0
- **卖出**: 满足 2 个以上条件
  - MA5<MA10
  - MACD 死叉
  - RSI>80 或<20
  - 5 日动量<-5%
- **适用**: 综合选股

### 4. 资金流策略 (`MoneyflowStrategy`)
- **买入**: 主力净流入率>5% + 资金流评分>70
- **卖出**: 主力净流出率<-5% + 资金流评分<30
- **适用**: 跟随主力

### 5. 涨停板策略 (`LimitUpStrategy`)
- **买入**: 涨停 + 封单>1000 万 + 早盘涨停
- **卖出**: 低开>3% 或跌破 5 日线
- **适用**: 短线打板

---

## 🔬 因子库

### 技术因子 (TechnicalFactors)

| 类别 | 因子 | 说明 |
|------|------|------|
| **趋势** | MA5/10/20/60 | 移动平均线 |
| | EMA12/26 | 指数移动平均 |
| | MACD(DIF/DEA/MACD) | 平滑异同移动平均 |
| | Bollinger Bands | 布林带 |
| **动量** | RSI6/12/24 | 相对强弱指标 |
| | KDJ(K/D/J) | 随机指标 |
| | Williams %R | 威廉指标 |
| | Momentum(5/10/20d) | 动量因子 |
| **波动率** | ATR14/20 | 平均真实波幅 |
| | Volatility(20/60d) | 收益率标准差 |
| **成交量** | Volume MA | 成交量均线 |
| | OBV | 能量潮 |
| | VR | 成交量比率 |

### 资金流因子 (MoneyflowFactors)

| 因子 | 说明 |
|------|------|
| net_inflow | 净流入额 (万元) |
| net_inflow_rate | 净流入率 (%) |
| main_inflow | 主力净流入 (大单 + 超大单) |
| main_inflow_rate | 主力净流入率 (%) |
| flow_sum_Nd | N 日累计净流入 |
| flow_positive_ratio_Nd | N 日净流入为正的比例 |
| large_buy_ratio | 大单买入占比 |
| flow_score | 综合资金流评分 (0-100) |
| top/bottom_divergence | 价格 - 资金流背离信号 |

---

## 📈 回测报告指标

| 指标 | 说明 |
|------|------|
| total_return | 总收益率 |
| annual_return | 年化收益率 |
| max_drawdown | 最大回撤 |
| sharpe_ratio | 夏普比率 (风险调整后收益) |
| win_rate | 胜率 |
| profit_factor | 盈亏比 |
| total_trades | 总交易次数 |
| avg_holding_days | 平均持仓天数 |

---

## ⚠️ 重要声明

1. **数据真实性**: 所有数据来自 Tushare 真实市场数据，绝无模拟/随机/测试数据
2. **回测局限性**: 回测结果不代表未来表现，实盘需考虑滑点、冲击成本等
3. **风险提示**: 量化策略有风险，入市需谨慎
4. **持续优化**: 策略需要根据市场变化持续迭代优化

---

## 🛠️ 扩展开发

### 添加新策略

```python
from strategies.example_strategies import Strategy

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__("我的策略")
    
    def generate_signals(self, date_str, data_dict, positions):
        signals = []
        # 实现你的策略逻辑
        return signals
```

### 添加新因子

```python
from factors.technical_factors import TechnicalFactors

class MyFactors(TechnicalFactors):
    def calculate_my_factor(self, df):
        df = df.copy()
        # 实现你的因子计算
        return df
```

---

## 📝 更新日志

- **2026-04-06**: 初始版本
  - ✅ 数据加载模块 (Tushare 8000+ 积分权限)
  - ✅ 技术因子库 (20+ 因子)
  - ✅ 资金流因子库 (10+ 因子)
  - ✅ 回测引擎 (支持多策略)
  - ✅ 示例策略 (5 个)
  - ✅ CLI 命令行工具

---

## 👤 关于

- **作者**: 淘金者 (Gold Rush) ⛏️
- **用户**: 听风
- **数据源**: Tushare (8000+ 积分)
- **理念**: 在信息的矿藏中挖掘价值，基于真实数据做决策

---

_开始挖掘你的 Alpha!_ ⛏️📈
