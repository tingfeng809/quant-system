# -*- coding: utf-8 -*-
"""
量化交易系统架构
⛏️ 淘金者版 - 完整交易系统

系统模块:
1. 行情数据系统
2. 策略与回测系统
3. 交易执行接口
4. 订单与持仓管理
5. 实时风控系统
6. 监控告警系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# ==================== 系统架构图 ====================
"""
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
"""


# ==================== 1. 行情数据系统 ====================

class MarketDataService:
    """
    行情数据服务
    
    功能:
    - 实时行情接入
    - K 线数据管理
    - 资金流数据
    - 数据缓存
    """
    
    def __init__(self):
        self.data_cache = {}  # 数据缓存
        self.subscribers = []  # 行情订阅者
    
    def subscribe(self, callback):
        """订阅行情"""
        self.subscribers.append(callback)
    
    def get_kline(self, ts_code, timeframe='daily'):
        """获取 K 线数据"""
        # 从本地数据库加载
        pass
    
    def get_tick(self, ts_code):
        """获取 Tick 数据"""
        # 实时 Tick
        pass
    
    def get_moneyflow(self, ts_code):
        """获取资金流数据"""
        # 资金流
        pass
    
    def notify_subscribers(self, data):
        """通知订阅者"""
        for callback in self.subscribers:
            callback(data)


# ==================== 2. 策略与回测系统 ====================

class StrategyManager:
    """
    策略管理器
    
    功能:
    - 策略注册
    - 信号生成
    - 回测执行
    - 绩效分析
    """
    
    def __init__(self):
        self.strategies = {}  # 已注册策略
        self.active_strategies = []  # 运行中策略
    
    def register(self, strategy):
        """注册策略"""
        self.strategies[strategy.name] = strategy
    
    def enable(self, strategy_name):
        """启用策略"""
        if strategy_name in self.strategies:
            self.active_strategies.append(strategy_name)
    
    def generate_signals(self, market_data):
        """生成交易信号"""
        signals = []
        for name in self.active_strategies:
            strategy = self.strategies[name]
            signal = strategy.on_market_data(market_data)
            if signal:
                signals.append(signal)
        return signals


# ==================== 3. 交易执行接口 ====================

class ExecutionService:
    """
    交易执行服务
    
    功能:
    - 订单路由
    - 券商接口
    - 成交确认
    - 执行算法
    """
    
    def __init__(self):
        self.broker = None  # 券商连接
        self.order_router = None
    
    def connect_broker(self, broker_config):
        """连接券商"""
        # 连接券商 API
        pass
    
    def submit_order(self, order):
        """提交订单"""
        # 发送订单到券商
        pass
    
    def cancel_order(self, order_id):
        """撤销订单"""
        pass
    
    def get_execution_report(self, order_id):
        """获取成交回报"""
        pass


# ==================== 4. 订单与持仓管理 ====================

class OrderManager:
    """
    订单管理器
    
    功能:
    - 订单生命周期
    - 订单状态跟踪
    - 成交记录
    """
    
    def __init__(self):
        self.orders = {}  # 所有订单
        self.active_orders = {}  # 活跃订单
        self.filled_orders = {}  # 已成交订单
    
    def create_order(self, ts_code, direction, volume, price=None):
        """创建订单"""
        order_id = f"ORD_{len(self.orders)+1}"
        order = {
            'order_id': order_id,
            'ts_code': ts_code,
            'direction': direction,  # buy/sell
            'volume': volume,
            'price': price,
            'status': 'pending'
        }
        self.orders[order_id] = order
        self.active_orders[order_id] = order
        return order
    
    def update_order(self, order_id, status, filled_volume=0, filled_price=0):
        """更新订单状态"""
        if order_id in self.orders:
            order = self.orders[order_id]
            order['status'] = status
            if status == 'filled':
                order['filled_volume'] = filled_volume
                order['filled_price'] = filled_price
                self.filled_orders[order_id] = order
                del self.active_orders[order_id]


class PositionManager:
    """
    持仓管理器
    
    功能:
    - 持仓跟踪
    - 成本计算
    - 盈亏计算
    """
    
    def __init__(self):
        self.positions = {}  # 持仓
        self.total_value = 0  # 总资产
    
    def update_position(self, ts_code, volume, price, direction):
        """更新持仓"""
        if ts_code not in self.positions:
            self.positions[ts_code] = {
                'volume': 0,
                'avg_cost': 0,
                'current_price': price
            }
        
        pos = self.positions[ts_code]
        if direction == 'buy':
            # 买入：增加持仓，更新成本
            total_cost = pos['volume'] * pos['avg_cost'] + volume * price
            pos['volume'] += volume
            pos['avg_cost'] = total_cost / pos['volume']
        else:
            # 卖出：减少持仓
            pos['volume'] -= volume
            if pos['volume'] <= 0:
                del self.positions[ts_code]
    
    def get_unrealized_pnl(self, current_prices):
        """计算浮动盈亏"""
        total_pnl = 0
        for ts_code, pos in self.positions.items():
            if ts_code in current_prices:
                current_price = current_prices[ts_code]
                pnl = (current_price - pos['avg_cost']) * pos['volume']
                total_pnl += pnl
        return total_pnl


# ==================== 5. 实时风控系统 ====================

class RiskManager:
    """
    风险管理器
    
    功能:
    - 仓位控制
    - 止损止盈
    - 资金监控
    - 风险指标
    """
    
    def __init__(self, config):
        self.config = config
        self.risk_limits = {
            'max_position': config.get('max_position', 0.3),  # 单票最大仓位 30%
            'max_total_position': config.get('max_total_position', 0.95),  # 总仓位上限 95%
            'max_drawdown': config.get('max_drawdown', 0.1),  # 最大回撤 10%
            'stop_loss': config.get('stop_loss', 0.08),  # 止损线 8%
            'take_profit': config.get('take_profit', 0.2),  # 止盈线 20%
        }
        self.risk_log = []  # 风控日志
    
    def check_order(self, order, portfolio_value, current_positions):
        """订单风控检查 - 增加日志记录"""
        import pandas as pd
        
        # 检查单票仓位
        position_ratio = (order['volume'] * order['price']) / portfolio_value
        if position_ratio > self.risk_limits['max_position']:
            log_entry = {
                'timestamp': pd.Timestamp.now(),
                'type': 'reject',
                'reason': 'single_position_limit',
                'details': f"{order['ts_code']} 仓位{position_ratio:.2%} > 限制{self.risk_limits['max_position']:.2%}"
            }
            self.risk_log.append(log_entry)
            return False, f"单票仓位超限：{position_ratio:.2%} > {self.risk_limits['max_position']:.2%}"
        
        # 检查总仓位
        total_position = sum(p['volume'] * p['avg_cost'] for p in current_positions.values())
        new_total = total_position + order['volume'] * order['price']
        if new_total / portfolio_value > self.risk_limits['max_total_position']:
            log_entry = {
                'timestamp': pd.Timestamp.now(),
                'type': 'reject',
                'reason': 'total_position_limit',
                'details': f"总仓位超限"
            }
            self.risk_log.append(log_entry)
            return False, f"总仓位超限"
        
        # 记录通过的风控检查
        log_entry = {
            'timestamp': pd.Timestamp.now(),
            'type': 'approve',
            'reason': 'all_checks_passed',
            'details': f"{order['ts_code']} 通过风控检查"
        }
        self.risk_log.append(log_entry)
        return True, "通过"
    
    def check_stop_loss(self, ts_code, current_price, avg_cost):
        """止损检查 - 增加日志记录"""
        import pandas as pd
        pnl_ratio = (current_price - avg_cost) / avg_cost
        if current_price < avg_cost * (1 - self.risk_limits['stop_loss']):
            log_entry = {
                'timestamp': pd.Timestamp.now(),
                'type': 'stop_loss_triggered',
                'ts_code': ts_code,
                'details': f"{ts_code} 触发止损，亏损{pnl_ratio:.2%}"
            }
            self.risk_log.append(log_entry)
            return True, f"触发止损：{pnl_ratio:.2%}"
        return False, ""
    
    def check_take_profit(self, ts_code, current_price, avg_cost):
        """止盈检查 - 增加日志记录"""
        import pandas as pd
        pnl_ratio = (current_price - avg_cost) / avg_cost
        if current_price > avg_cost * (1 + self.risk_limits['take_profit']):
            log_entry = {
                'timestamp': pd.Timestamp.now(),
                'type': 'take_profit_triggered',
                'ts_code': ts_code,
                'details': f"{ts_code} 触发止盈，盈利{pnl_ratio:.2%}"
            }
            self.risk_log.append(log_entry)
            return True, f"触发止盈：{pnl_ratio:.2%}"
        return False, ""


# ==================== 6. 监控告警系统 ====================

class MonitorService:
    """
    监控告警服务
    
    功能:
    - 实时监控
    - 异常检测
    - 告警通知
    - 日志记录
    """
    
    def __init__(self):
        self.alerts = []  # 告警记录
        self.alert_callbacks = []  # 告警回调
    
    def add_alert_callback(self, callback):
        """添加告警回调"""
        self.alert_callbacks.append(callback)
    
    def send_alert(self, level, message, data=None):
        """发送告警"""
        alert = {
            'timestamp': pd.Timestamp.now(),
            'level': level,  # INFO/WARNING/ERROR/CRITICAL
            'message': message,
            'data': data
        }
        self.alerts.append(alert)
        
        # 通知回调
        for callback in self.alert_callbacks:
            callback(alert)
    
    def check_system_health(self):
        """系统健康检查"""
        # 检查连接状态
        # 检查数据延迟
        # 检查资源使用
        pass
    
    def log_trade(self, trade):
        """记录交易"""
        # 记录到日志
        pass


# ==================== 系统集成 ====================

class QuantTradingSystem:
    """
    量化交易系统 - 总集成
    
    整合所有子系统
    """
    
    def __init__(self, config):
        # 初始化各子系统
        self.market = MarketDataService()
        self.strategy_mgr = StrategyManager()
        self.execution = ExecutionService()
        self.order_mgr = OrderManager()
        self.position_mgr = PositionManager()
        self.risk_mgr = RiskManager(config)
        self.monitor = MonitorService()
        
        self.config = config
        self.is_running = False
    
    def get_risk_log(self, limit=10):
        """获取风控日志"""
        return self.risk_mgr.risk_log[-limit:]
    
    def start(self):
        """启动系统"""
        self.is_running = True
        self.monitor.send_alert('INFO', '量化交易系统启动')
    
    def stop(self):
        """停止系统"""
        self.is_running = False
        self.monitor.send_alert('INFO', '量化交易系统停止')
    
    def on_market_data(self, data):
        """行情数据到达"""
        # 1. 策略生成信号
        signals = self.strategy_mgr.generate_signals(data)
        
        # 2. 风控检查
        for signal in signals:
            passed, msg = self.risk_mgr.check_order(
                signal,
                self.position_mgr.total_value,
                self.position_mgr.positions
            )
            
            if passed:
                # 3. 创建订单
                order = self.order_mgr.create_order(
                    signal['ts_code'],
                    signal['direction'],
                    signal['volume'],
                    signal.get('price')
                )
                
                # 4. 执行订单
                self.execution.submit_order(order)
                
                self.monitor.send_alert('INFO', f'执行交易：{signal}')
            else:
                self.monitor.send_alert('WARNING', f'风控拦截：{msg}')
    
    def on_order_filled(self, order):
        """订单成交回报"""
        # 更新持仓
        self.position_mgr.update_position(
            order['ts_code'],
            order['filled_volume'],
            order['filled_price'],
            order['direction']
        )
        
        # 更新订单状态
        self.order_mgr.update_order(
            order['order_id'],
            'filled',
            order['filled_volume'],
            order['filled_price']
        )
        
        self.monitor.send_alert('INFO', f'订单成交：{order}')


# ==================== 使用示例 ====================

def demo_system():
    """系统演示"""
    print("=" * 70)
    print("量化交易系统 - 架构演示")
    print("=" * 70)
    
    # 配置
    config = {
        'max_position': 0.3,
        'max_total_position': 0.95,
        'max_drawdown': 0.1,
        'stop_loss': 0.08,
        'take_profit': 0.2,
    }
    
    # 创建系统
    system = QuantTradingSystem(config)
    
    # 启动系统
    system.start()
    
    # 模拟订单
    order = {
        'ts_code': '000001.SZ',
        'direction': 'buy',
        'volume': 100,
        'price': 12.5
    }
    
    # 风控检查
    portfolio_value = 100000
    passed, msg = system.risk_mgr.check_order(order, portfolio_value, {})
    print(f"风控检查：{msg}")
    
    if passed:
        # 创建订单
        created_order = system.order_mgr.create_order(
            order['ts_code'],
            order['direction'],
            order['volume'],
            order['price']
        )
        print(f"订单创建：{created_order['order_id']}")
        
        # 模拟成交
        created_order['filled_volume'] = 100
        created_order['filled_price'] = 12.5
        system.on_order_filled(created_order)
        
        # 查看持仓
        positions = system.position_mgr.positions
        print(f"当前持仓：{list(positions.keys())}")
        print(f"持仓成本：{positions['000001.SZ']['avg_cost']:.2f}")
    
    # 停止系统
    system.stop()
    
    print("\n✅ 系统演示完成！")


if __name__ == '__main__':
    import pandas as pd
    demo_system()
