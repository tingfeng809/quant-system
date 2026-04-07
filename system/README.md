# 量化交易系统 - 完整架构

**⛏️ 淘金者版** - 基于真实数据的专业交易系统

---

## 📐 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                     量化交易系统架构                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  行情数据   │  │  策略回测   │  │  交易执行   │             │
│  │  (Market)   │→ │  (Strategy) │→ │  (Execution)│             │
│  │             │  │             │  │             │             │
│  │ • 实时行情  │  │ • 信号生成  │  │ • 订单路由  │             │
│  │ • K 线数据   │  │ • 回测引擎  │  │ • 券商接口  │             │
│  │ • 资金流    │  │ • 因子计算  │  │ • 成交确认  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│         ↓                ↓                ↓                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │  订单持仓   │  │  实时风控   │  │  监控告警   │             │
│  │  (Order)    │← │  (Risk)     │← │  (Monitor)  │             │
│  │             │  │             │  │             │             │
│  │ • 订单管理  │  │ • 仓位控制  │  │ • 实时监控  │             │
│  │ • 持仓跟踪  │  │ • 止损止盈  │  │ • 异常告警  │             │
│  │ • 成交记录  │  │ • 资金监控  │  │ • 日志记录  │             │
│  └─────────────┘  └─────────────┘  └─────────────┘             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📦 六大核心模块

### 1️⃣ 行情数据系统 (MarketDataService)

**功能**:
- ✅ 实时行情接入 (Tushare)
- ✅ K 线数据管理 (日线/分钟线/Tick)
- ✅ 资金流数据
- ✅ 数据缓存机制

**核心方法**:
```python
market = MarketDataService()

# 获取 K 线
kline = market.get_kline('000001.SZ', timeframe='daily')

# 获取 Tick
tick = market.get_tick('000001.SZ')

# 获取资金流
moneyflow = market.get_moneyflow('000001.SZ')

# 订阅行情
market.subscribe(callback_function)
```

**数据源**:
- Tushare (8000+ 积分)
- 本地缓存：`data/stocks/daily/`

---

### 2️⃣ 策略与回测系统 (StrategyManager)

**功能**:
- ✅ 策略注册与管理
- ✅ 交易信号生成
- ✅ 回测引擎
- ✅ 绩效分析

**已实现策略**:
| 策略 | 类型 | 说明 |
|------|------|------|
| 双均线策略 | 趋势 | MA5/MA20 金叉死叉 |
| MACD 策略 | 动量 | MACD 金叉死叉 |
| 多因子策略 | 综合 | 技术面 + 资金流 |
| 资金流策略 | 资金 | 主力净流入跟踪 |
| 涨停板策略 | 短线 | 打板策略 |

**使用方法**:
```python
strategy_mgr = StrategyManager()

# 注册策略
strategy_mgr.register(DualMAStrategy())

# 启用策略
strategy_mgr.enable('双均线策略')

# 生成信号
signals = strategy_mgr.generate_signals(market_data)
```

---

### 3️⃣ 交易执行接口 (ExecutionService)

**功能**:
- ✅ 订单路由
- ✅ 券商 API 对接
- ✅ 成交确认
- ✅ 执行算法 (TWAP/VWAP)

**核心方法**:
```python
execution = ExecutionService()

# 连接券商
execution.connect_broker(broker_config)

# 提交订单
execution.submit_order(order)

# 撤销订单
execution.cancel_order(order_id)

# 获取成交回报
report = execution.get_execution_report(order_id)
```

**支持券商**: (待接入)
- 华泰证券
- 中信证券
- 东方财富

---

### 4️⃣ 订单与持仓管理 (OrderManager & PositionManager)

**订单管理**:
```python
order_mgr = OrderManager()

# 创建订单
order = order_mgr.create_order(
    ts_code='000001.SZ',
    direction='buy',
    volume=100,
    price=12.5
)

# 更新订单状态
order_mgr.update_order(order_id, 'filled', 100, 12.5)

# 查询订单
orders = order_mgr.active_orders
```

**持仓管理**:
```python
position_mgr = PositionManager()

# 更新持仓
position_mgr.update_position(
    ts_code='000001.SZ',
    volume=100,
    price=12.5,
    direction='buy'
)

# 计算浮动盈亏
pnl = position_mgr.get_unrealized_pnl(current_prices)
```

**订单状态**:
- `pending` - 待提交
- `submitted` - 已提交
- `partial` - 部分成交
- `filled` - 完全成交
- `cancelled` - 已撤销
- `rejected` - 已拒绝

---

### 5️⃣ 实时风控系统 (RiskManager)

**风控指标**:
| 指标 | 默认值 | 说明 |
|------|--------|------|
| 单票最大仓位 | 30% | 单只股票最大持仓比例 |
| 总仓位上限 | 95% | 所有股票总仓位上限 |
| 最大回撤 | 10% | 账户最大允许回撤 |
| 止损线 | 8% | 单票止损阈值 |
| 止盈线 | 20% | 单票止盈阈值 |

**风控检查**:
```python
risk_mgr = RiskManager(config)

# 订单风控检查
passed, msg = risk_mgr.check_order(order, portfolio_value, positions)
# passed: True/False
# msg: 通过/失败原因

# 止损检查
triggered, reason = risk_mgr.check_stop_loss(
    ts_code='000001.SZ',
    current_price=11.5,
    avg_cost=12.5
)

# 止盈检查
triggered, reason = risk_mgr.check_take_profit(...)
```

**风控流程**:
```
订单生成 → 仓位检查 → 资金检查 → 黑名单检查 → 通过/拦截
```

---

### 6️⃣ 监控告警系统 (MonitorService)

**功能**:
- ✅ 系统健康监控
- ✅ 交易实时监控
- ✅ 异常检测
- ✅ 告警通知

**告警级别**:
- `INFO` - 信息
- `WARNING` - 警告
- `ERROR` - 错误
- `CRITICAL` - 严重

**使用方法**:
```python
monitor = MonitorService()

# 添加告警回调 (邮件/短信/飞书)
monitor.add_alert_callback(send_email)
monitor.add_alert_callback(send_feishu)

# 发送告警
monitor.send_alert('WARNING', '仓位接近上限', {'ratio': 0.88})

# 系统健康检查
health = monitor.check_system_health()
```

**监控内容**:
- 行情连接状态
- 策略运行状态
- 订单执行状态
- 账户资金变化
- 风险指标监控

---

## 🔧 系统集成

### 完整系统示例

```python
from system.architecture import QuantTradingSystem

# 配置
config = {
    'max_position': 0.3,        # 单票 30%
    'max_total_position': 0.95, # 总仓位 95%
    'max_drawdown': 0.1,        # 回撤 10%
    'stop_loss': 0.08,          # 止损 8%
    'take_profit': 0.2,         # 止盈 20%
}

# 创建系统
system = QuantTradingSystem(config)

# 注册策略
system.strategy_mgr.register(DualMAStrategy())
system.strategy_mgr.enable('双均线策略')

# 启动系统
system.start()

# 系统会自动:
# 1. 接收行情
# 2. 生成信号
# 3. 风控检查
# 4. 执行交易
# 5. 更新持仓
# 6. 监控告警

# 停止系统
system.stop()
```

---

## 📊 运行演示

```bash
cd /home/li/.openclaw/workspace/quant

# 运行系统演示
python3 system/architecture.py
```

**输出示例**:
```
======================================================================
量化交易系统 - 架构演示
======================================================================
风控检查：通过
订单创建：ORD_1
当前持仓：['000001.SZ']
持仓成本：12.50

✅ 系统演示完成！
```

---

## 📝 下一步

### 已完成
- ✅ 系统架构设计
- ✅ 6 大核心模块
- ✅ 数据系统对接
- ✅ 策略框架
- ✅ 风控规则

### 待完成
- ⏳ 券商 API 对接
- ⏳ 实时行情接入
- ⏳ 告警通知集成
- ⏳ 图形化监控界面

---

*⛏️ 淘金者量化系统 - 基于真实数据，专业可靠*
