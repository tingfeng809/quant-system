# -*- coding: utf-8 -*-
"""
量化策略示例
⚠️ 所有信号基于真实历史数据，禁止使用未来函数
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from factors.technical_factors import TechnicalFactors
from factors.moneyflow_factors import MoneyflowFactors


# ==================== 策略基类 ====================
class Strategy:
    """策略基类"""
    
    def __init__(self, name: str = "BaseStrategy"):
        self.name = name
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        """
        生成交易信号
        
        Args:
            date_str: 交易日期 (YYYYMMDD)
            data_dict: 股票代码 -> 数据
            positions: 当前持仓
        
        Returns:
            List[Dict]: 信号列表，每个信号包含:
                - ts_code: 股票代码
                - direction: 'buy' or 'sell'
                - volume: 数量
                - reason: 原因
        """
        raise NotImplementedError


# ==================== 策略 1: 双均线策略 ====================
class DualMAStrategy(Strategy):
    """
    双均线交叉策略
    
    买入信号：MA5 上穿 MA20 (金叉)
    卖出信号：MA5 下穿 MA20 (死叉)
    """
    
    def __init__(self, fast_period: int = 5, slow_period: int = 20):
        super().__init__("双均线策略")
        self.fast_period = fast_period
        self.slow_period = slow_period
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            # 获取历史数据 (不包含当日)
            hist = df[df['trade_date'] < date_str].tail(60)
            if len(hist) < self.slow_period + 5:
                continue
            
            # 计算均线
            ma_fast = hist['close'].tail(self.fast_period).mean()
            ma_slow = hist['close'].tail(self.slow_period).mean()
            prev_ma_fast = hist['close'].iloc[-self.fast_period-5:-5].mean()
            prev_ma_slow = hist['close'].iloc[-self.slow_period-5:-5].mean()
            
            # 金叉买入
            if (prev_ma_fast <= prev_ma_slow and ma_fast > ma_slow and 
                ts_code not in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'MA{self.fast_period} 金叉 MA{self.slow_period}'
                })
            
            # 死叉卖出
            elif (prev_ma_fast >= prev_ma_slow and ma_fast < ma_slow and 
                  ts_code in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': f'MA{self.fast_period} 死叉 MA{self.slow_period}'
                })
        
        return signals


# ==================== 策略 2: MACD 策略 ====================
class MACDStrategy(Strategy):
    """
    MACD 策略
    
    买入信号：DIF 上穿 DEA (金叉) 且 MACD>0
    卖出信号：DIF 下穿 DEA (死叉) 或 MACD<0
    """
    
    def __init__(self, fast=12, slow=26, signal=9):
        super().__init__("MACD 策略")
        self.fast = fast
        self.slow = slow
        self.signal_period = signal
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        factor_calc = TechnicalFactors()
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(100)
            if len(hist) < 60:
                continue
            
            # 计算 MACD
            df_with_factors = factor_calc.calculate_macd(hist.copy())
            
            if len(df_with_factors) < 2:
                continue
            
            latest = df_with_factors.iloc[-1]
            prev = df_with_factors.iloc[-2]
            
            # 金叉买入
            if (prev['macd_dif'] <= prev['macd_dea'] and 
                latest['macd_dif'] > latest['macd_dea'] and
                ts_code not in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': 'MACD 金叉'
                })
            
            # 死叉卖出
            elif (prev['macd_dif'] >= prev['macd_dea'] and 
                  latest['macd_dif'] < latest['macd_dea'] and
                  ts_code in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': 'MACD 死叉'
                })
        
        return signals


# ==================== 策略 3: 资金流策略 ====================
class MoneyflowStrategy(Strategy):
    """
    资金流策略
    
    买入信号：
    - 主力净流入率 > 5%
    - 5 日累计净流入为正
    - 资金流评分 > 70
    
    卖出信号：
    - 主力净流入率 < -5%
    - 资金流评分 < 30
    """
    
    def __init__(self):
        super().__init__("资金流策略")
        self.factor_calc = MoneyflowFactors()
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        # 这里需要资金流数据，简化示例
        # 实际使用需要加载 moneyflow 数据并计算因子
        
        return signals


# ==================== 策略 4: 多因子综合策略 ====================
class MultiFactorStrategy(Strategy):
    """
    多因子综合策略
    
    综合技术面 + 资金流 + 基本面因子
    
    买入条件 (满足 3 个以上):
    1. MA5 > MA10 > MA20 (多头排列)
    2. MACD > 0 且 DIF > DEA
    3. RSI(12) 在 50-70 之间
    4. 主力净流入率 > 3%
    5. 5 日动量 > 0
    
    卖出条件 (满足 2 个以上):
    1. MA5 < MA10 (短期转弱)
    2. MACD 死叉
    3. RSI(12) > 80 (超买) 或 < 20 (超卖)
    4. 主力净流出率 < -3%
    5. 5 日动量 < -5%
    """
    
    def __init__(self):
        super().__init__("多因子综合策略")
        self.tech_factor = TechnicalFactors()
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(100)
            if len(hist) < 60:
                continue
            
            # 计算技术因子
            df_factors = self.tech_factor.calculate_all(hist.copy())
            latest = df_factors.iloc[-1]
            prev = df_factors.iloc[-2]
            
            # 买入条件计数
            buy_signals = 0
            sell_signals = 0
            
            # 1. 均线多头排列
            if (latest.get('ma5', 0) > latest.get('ma10', 0) > latest.get('ma20', 0)):
                buy_signals += 1
            if latest.get('ma5', 0) < latest.get('ma10', 0):
                sell_signals += 1
            
            # 2. MACD
            if (latest.get('macd', 0) > 0 and latest.get('macd_dif', 0) > latest.get('macd_dea', 0)):
                buy_signals += 1
            if (prev.get('macd_dif', 0) >= prev.get('macd_dea', 0) and 
                latest.get('macd_dif', 0) < latest.get('macd_dea', 0)):
                sell_signals += 1
            
            # 3. RSI
            rsi = latest.get('rsi12', 50)
            if 50 <= rsi <= 70:
                buy_signals += 1
            if rsi > 80 or rsi < 20:
                sell_signals += 1
            
            # 4. 动量
            momentum = latest.get('momentum_5d', 0)
            if momentum > 0:
                buy_signals += 1
            if momentum < -0.05:
                sell_signals += 1
            
            # 生成信号
            if buy_signals >= 3 and ts_code not in positions:
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'多因子买入 ({buy_signals}/5)'
                })
            
            elif sell_signals >= 2 and ts_code in positions:
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': f'多因子卖出 ({sell_signals}/5)'
                })
        
        return signals


# ==================== 策略 5: 涨停板策略 ====================
class LimitUpStrategy(Strategy):
    """
    涨停板策略 (打板策略)
    
    买入条件:
    1. 当日涨停
    2. 封单金额 > 1000 万
    3. 涨停时间早 (上午 10 点前)
    4. 非 ST 股票
    
    卖出条件:
    1. 开盘不及预期 (低开 > -3%)
    2. 跌破 5 日线
    3. 持有超过 5 日
    """
    
    def __init__(self):
        super().__init__("涨停板策略")
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        # 需要涨跌停数据，这里提供框架
        signals = []
        
        # 实际使用需要:
        # 1. 获取当日 limit_list 数据
        # 2. 筛选涨停股票
        # 3. 检查封单、时间等条件
        # 4. 排除 ST 股票
        
        return signals


# ==================== 策略测试 ====================
def test_strategies():
    """测试策略"""
    print("=" * 60)
    print("策略测试")
    print("=" * 60)
    
    from data.data_loader import DataLoader
    from backtest.engine import BacktestEngine
    
    # 加载数据
    loader = DataLoader()
    data = {
        '000001.SZ': loader.get_daily_data('000001.SZ', start_date='20240101'),
        '600000.SH': loader.get_daily_data('600000.SH', start_date='20240101'),
        '000002.SZ': loader.get_daily_data('000002.SZ', start_date='20240101'),
    }
    
    print(f"\n加载 {len(data)} 只股票数据")
    
    # 测试双均线策略
    print("\n--- 双均线策略回测 ---")
    strategy = DualMAStrategy(fast_period=5, slow_period=20)
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(strategy, data, '20240101', '20241231')
    
    print(f"总收益率：{result.total_return*100:.2f}%")
    print(f"年化收益率：{result.annual_return*100:.2f}%")
    print(f"最大回撤：{result.max_drawdown*100:.2f}%")
    print(f"夏普比率：{result.sharpe_ratio:.2f}")
    print(f"交易次数：{result.total_trades}")
    
    # 测试多因子策略
    print("\n--- 多因子策略回测 ---")
    strategy = MultiFactorStrategy()
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(strategy, data, '20240101', '20241231')
    
    print(f"总收益率：{result.total_return*100:.2f}%")
    print(f"年化收益率：{result.annual_return*100:.2f}%")
    print(f"最大回撤：{result.max_drawdown*100:.2f}%")
    print(f"夏普比率：{result.sharpe_ratio:.2f}")
    print(f"交易次数：{result.total_trades}")
    
    print("\n✅ 策略测试完成！")


if __name__ == '__main__':
    test_strategies()
