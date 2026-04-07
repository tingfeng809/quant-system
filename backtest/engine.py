# -*- coding: utf-8 -*-
"""
回测引擎
⚠️ 基于真实历史数据回测，禁止使用未来函数
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.settings import BACKTEST_CONFIG, logger


@dataclass
class Trade:
    """交易记录"""
    trade_date: str
    ts_code: str
    direction: str  # 'buy' or 'sell'
    price: float
    volume: int
    amount: float
    commission: float
    stamp_tax: float
    reason: str = ''


@dataclass
class Position:
    """持仓记录"""
    ts_code: str
    volume: int
    avg_cost: float
    market_value: float
    profit_loss: float
    profit_rate: float


@dataclass
class BacktestResult:
    """回测结果"""
    total_return: float  # 总收益率
    annual_return: float  # 年化收益率
    max_drawdown: float  # 最大回撤
    sharpe_ratio: float  # 夏普比率
    win_rate: float  # 胜率
    profit_factor: float  # 盈亏比
    total_trades: int  # 总交易次数
    avg_holding_days: float  # 平均持仓天数
    daily_returns: pd.Series  # 每日收益率序列


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = None, commission: float = None,
                 slippage: float = None, stamp_tax: float = None):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金
            commission: 佣金率
            slippage: 滑点
            stamp_tax: 印花税
        """
        self.initial_capital = initial_capital or BACKTEST_CONFIG['initial_capital']
        self.commission = commission or BACKTEST_CONFIG['commission']
        self.slippage = slippage or BACKTEST_CONFIG['slippage']
        self.stamp_tax = stamp_tax or BACKTEST_CONFIG['stamp_tax']
        
        self.capital = self.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.daily_values: List[float] = []
        self.daily_returns: List[float] = []
    
    def reset(self):
        """重置回测状态"""
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.daily_values = []
        self.daily_returns = []
    
    def _calculate_buy_amount(self, price: float, volume: int) -> tuple:
        """计算买入实际金额"""
        base_amount = price * volume
        # 加上滑点
        actual_price = price * (1 + self.slippage)
        actual_amount = actual_price * volume
        # 加上佣金 (最低 5 元)
        commission = max(actual_amount * self.commission, 5)
        total_cost = actual_amount + commission
        return actual_price, commission, total_cost
    
    def _calculate_sell_amount(self, price: float, volume: int) -> tuple:
        """计算卖出实际金额"""
        base_amount = price * volume
        # 减去滑点
        actual_price = price * (1 - self.slippage)
        actual_amount = actual_price * volume
        # 佣金
        commission = max(actual_amount * self.commission, 5)
        # 印花税 (仅卖出收取)
        stamp_tax = actual_amount * self.stamp_tax
        net_proceeds = actual_amount - commission - stamp_tax
        return actual_price, commission, stamp_tax, net_proceeds
    
    def buy(self, trade_date: str, ts_code: str, price: float, volume: int, 
            reason: str = '') -> bool:
        """
        买入
        
        Args:
            trade_date: 交易日期
            ts_code: 股票代码
            price: 买入价格
            volume: 买入数量
            reason: 交易原因
        
        Returns:
            bool: 是否成功
        """
        actual_price, commission, total_cost = self._calculate_buy_amount(price, volume)
        
        # 检查资金是否足够
        if total_cost > self.capital:
            logger.debug(f"资金不足：需要 {total_cost:.2f}, 可用 {self.capital:.2f}")
            return False
        
        # 执行买入
        self.capital -= total_cost
        
        # 更新持仓
        if ts_code in self.positions:
            pos = self.positions[ts_code]
            total_value = pos.volume * pos.avg_cost + total_cost
            pos.volume += volume
            pos.avg_cost = total_value / pos.volume
        else:
            self.positions[ts_code] = Position(
                ts_code=ts_code,
                volume=volume,
                avg_cost=actual_price,
                market_value=0,
                profit_loss=0,
                profit_rate=0
            )
        
        # 记录交易
        self.trades.append(Trade(
            trade_date=trade_date,
            ts_code=ts_code,
            direction='buy',
            price=actual_price,
            volume=volume,
            amount=total_cost,
            commission=commission,
            stamp_tax=0,
            reason=reason
        ))
        
        logger.debug(f"买入 {ts_code}: {volume}股 @ {actual_price:.2f}, 成本 {total_cost:.2f}")
        return True
    
    def sell(self, trade_date: str, ts_code: str, price: float, volume: int = None,
             reason: str = '') -> bool:
        """
        卖出
        
        Args:
            trade_date: 交易日期
            ts_code: 股票代码
            price: 卖出价格
            volume: 卖出数量 (None 表示全部卖出)
            reason: 交易原因
        
        Returns:
            bool: 是否成功
        """
        if ts_code not in self.positions:
            logger.debug(f"无持仓：{ts_code}")
            return False
        
        pos = self.positions[ts_code]
        if volume is None:
            volume = pos.volume
        
        if volume > pos.volume:
            logger.debug(f"持仓不足：需要 {volume}, 可用 {pos.volume}")
            return False
        
        actual_price, commission, stamp_tax, net_proceeds = self._calculate_sell_amount(price, volume)
        
        # 执行卖出
        self.capital += net_proceeds
        
        # 更新持仓
        pos.volume -= volume
        if pos.volume == 0:
            del self.positions[ts_code]
        
        # 记录交易
        self.trades.append(Trade(
            trade_date=trade_date,
            ts_code=ts_code,
            direction='sell',
            price=actual_price,
            volume=volume,
            amount=net_proceeds,
            commission=commission,
            stamp_tax=stamp_tax,
            reason=reason
        ))
        
        logger.debug(f"卖出 {ts_code}: {volume}股 @ {actual_price:.2f}, 所得 {net_proceeds:.2f}")
        return True
    
    def update_portfolio_value(self, prices: Dict[str, float]):
        """
        更新组合市值
        
        Args:
            prices: 股票代码 -> 当前价格
        """
        market_value = self.capital
        for ts_code, pos in self.positions.items():
            if ts_code in prices:
                pos.market_value = pos.volume * prices[ts_code]
                pos.profit_loss = pos.market_value - pos.volume * pos.avg_cost
                pos.profit_rate = pos.profit_loss / (pos.volume * pos.avg_cost)
                market_value += pos.market_value
        
        self.daily_values.append(market_value)
        
        # 计算日收益率
        if len(self.daily_values) > 1:
            daily_return = (self.daily_values[-1] - self.daily_values[-2]) / self.daily_values[-2]
            self.daily_returns.append(daily_return)
    
    def run(self, strategy, data_dict: Dict[str, pd.DataFrame], 
            start_date: str, end_date: str) -> BacktestResult:
        """
        运行回测
        
        Args:
            strategy: 策略对象 (必须有 generate_signals 方法)
            data_dict: 股票代码 -> 行情数据
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            BacktestResult: 回测结果
        """
        self.reset()
        
        # 获取所有交易日期
        all_dates = set()
        for df in data_dict.values():
            if 'trade_date' in df.columns:
                dates = pd.to_datetime(df['trade_date'])
                all_dates.update(dates)
        
        all_dates = sorted([d for d in all_dates 
                           if pd.Timestamp(start_date) <= d <= pd.Timestamp(end_date)])
        
        logger.info(f"回测区间：{start_date} - {end_date}, 共 {len(all_dates)} 个交易日")
        
        # 逐日回测
        for i, date in enumerate(all_dates):
            date_str = date.strftime('%Y%m%d')
            
            # 获取当日价格
            prices = {}
            for ts_code, df in data_dict.items():
                row = df[df['trade_date'] == date_str]
                if len(row) > 0:
                    prices[ts_code] = row.iloc[-1]['close']
            
            # 生成交易信号
            signals = strategy.generate_signals(date_str, data_dict, self.positions)
            
            # 执行交易
            for signal in signals:
                ts_code = signal['ts_code']
                direction = signal['direction']
                volume = signal.get('volume', 100)
                price = prices.get(ts_code)
                
                if price is None:
                    continue
                
                if direction == 'buy':
                    self.buy(date_str, ts_code, price, volume, 
                            reason=signal.get('reason', ''))
                elif direction == 'sell':
                    self.sell(date_str, ts_code, price, volume,
                             reason=signal.get('reason', ''))
            
            # 更新组合市值
            self.update_portfolio_value(prices)
        
        # 计算回测结果
        return self._calculate_result(start_date, end_date)
    
    def _calculate_result(self, start_date: str, end_date: str) -> BacktestResult:
        """计算回测结果指标"""
        if len(self.daily_values) < 2:
            return BacktestResult(
                total_return=0, annual_return=0, max_drawdown=0,
                sharpe_ratio=0, win_rate=0, profit_factor=0,
                total_trades=0, avg_holding_days=0,
                daily_returns=pd.Series()
            )
        
        daily_returns = pd.Series(self.daily_returns)
        
        # 总收益率
        total_return = (self.daily_values[-1] - self.initial_capital) / self.initial_capital
        
        # 年化收益率
        days = (pd.Timestamp(end_date) - pd.Timestamp(start_date)).days
        annual_return = (1 + total_return) ** (365 / days) - 1 if days > 0 else 0
        
        # 最大回撤
        cum_max = pd.Series(self.daily_values).cummax()
        drawdown = (pd.Series(self.daily_values) - cum_max) / cum_max
        max_drawdown = abs(drawdown.min())
        
        # 夏普比率 (假设无风险利率 3%)
        if len(daily_returns) > 0 and daily_returns.std() != 0:
            sharpe_ratio = (daily_returns.mean() - 0.03/252) / daily_returns.std() * np.sqrt(252)
        else:
            sharpe_ratio = 0
        
        # 胜率
        buy_trades = [t for t in self.trades if t.direction == 'buy']
        sell_trades = [t for t in self.trades if t.direction == 'sell']
        profitable_trades = len([t for t in sell_trades if t.reason != ''])  # 简化计算
        
        # 盈亏比
        if len(sell_trades) > 0:
            wins = [t.amount for t in sell_trades if t.amount > 0]
            losses = [t.amount for t in sell_trades if t.amount <= 0]
            avg_win = np.mean(wins) if wins else 0
            avg_loss = abs(np.mean(losses)) if losses else 1
            profit_factor = avg_win / avg_loss if avg_loss > 0 else 0
        else:
            profit_factor = 0
        
        # 平均持仓天数
        if len(buy_trades) > 0:
            holding_days = len(self.daily_values) / len(buy_trades)
        else:
            holding_days = 0
        
        return BacktestResult(
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=profitable_trades / len(sell_trades) if sell_trades else 0,
            profit_factor=profit_factor,
            total_trades=len(self.trades),
            avg_holding_days=holding_days,
            daily_returns=daily_returns
        )


# ==================== 测试函数 ====================
def test_backtest_engine():
    """测试回测引擎"""
    print("=" * 60)
    print("回测引擎测试")
    print("=" * 60)
    
    from data.data_loader import DataLoader
    
    # 加载数据
    loader = DataLoader()
    data = {
        '000001.SZ': loader.get_daily_data('000001.SZ', start_date='20240101'),
    }
    
    print(f"\n加载数据：{len(data['000001.SZ'])} 条")
    
    # 简单策略：均线金叉买入，死叉卖出
    class SimpleMAStrategy:
        def generate_signals(self, date_str, data_dict, positions):
            signals = []
            for ts_code, df in data_dict.items():
                hist = df[df['trade_date'] < date_str].tail(30)
                if len(hist) < 20:
                    continue
                
                ma5 = hist['close'].tail(5).mean()
                ma10 = hist['close'].tail(10).mean()
                prev_ma5 = hist['close'].iloc[-6:-1].mean()
                prev_ma10 = hist['close'].iloc[-11:-1].mean()
                
                # 金叉
                if prev_ma5 <= prev_ma10 and ma5 > ma10 and ts_code not in positions:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'buy',
                        'volume': 100,
                        'reason': 'MA 金叉'
                    })
                # 死叉
                elif prev_ma5 >= prev_ma10 and ma5 < ma10 and ts_code in positions:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'sell',
                        'reason': 'MA 死叉'
                    })
            return signals
    
    # 运行回测
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(
        SimpleMAStrategy(),
        data,
        start_date='20240101',
        end_date='20241231'
    )
    
    # 输出结果
    print("\n回测结果:")
    print(f"  总收益率：{result.total_return*100:.2f}%")
    print(f"  年化收益率：{result.annual_return*100:.2f}%")
    print(f"  最大回撤：{result.max_drawdown*100:.2f}%")
    print(f"  夏普比率：{result.sharpe_ratio:.2f}")
    print(f"  总交易次数：{result.total_trades}")
    
    print("\n✅ 回测引擎测试完成！")


if __name__ == '__main__':
    test_backtest_engine()
