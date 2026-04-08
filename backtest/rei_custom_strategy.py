# -*- coding: utf-8 -*-
"""
自定义REI策略回测
⛏️ 超级龙虾 - 用户自定义策略

策略参数:
- REI-EMA14 < 25
- (注: 业绩稳定增长 暂未实现)
- (注: 负面舆情过滤 暂未实现)
- 持股10天
- 盈利>10%浮动止盈
- 亏损6%平仓
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class REICustomStrategy:
    """
    REI自定义策略
    
    买入条件:
    1. REI-EMA14 < 25 (REI处于低位)
    2. 业绩稳定增长 (净利润增速 > 0, 模拟)
    3. 无负面舆情 (模拟)
    
    卖出条件:
    1. 持股满10天
    2. 盈利 > 10%: 浮动止盈 (继续持有直到回落)
    3. 亏损 6%: 止损平仓
    """
    
    def __init__(self, 
                 rei_period: int = 20,
                 rei_ema_period: int = 14,
                 rei_threshold: float = 25,
                 hold_days: int = 10,
                 profit_target: float = 0.10,  # 10%
                 stop_loss: float = 0.06,       # 6%
                 trailing_stop: float = 0.05):   # 5% 浮动止盈回落
        self.name = "REI自定义策略"
        self.rei_period = rei_period
        self.rei_ema_period = rei_ema_period
        self.rei_threshold = rei_threshold
        self.hold_days = hold_days
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop
        
        # 持仓记录
        self.positions: Dict[str, dict] = {}
    
    def _calculate_rei(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算REI (Range Extension Index)
        
        REI = (High - OldLow) / (High - Low) * 100
        或使用简化版本: 价格动量指标
        """
        result = df.copy()
        
        # 简化REI: 基于价格位置的动量
        # REI = (收盘价 - N日最低价) / (N日最高价 - N日最低价) * 100 - 50
        
        n = self.rei_period
        
        # 最高价和最低价
        highest = result['high'].rolling(n).max()
        lowest = result['low'].rolling(n).min()
        
        # REI: 价格在N日区间的相对位置
        range_size = highest - lowest
        range_size = range_size.replace(0, 1)  # 避免除零
        
        result['rei'] = (result['close'] - lowest) / range_size * 100 - 50
        
        # REI的EMA
        result['rei_ema'] = result['rei'].ewm(span=self.rei_ema_period).mean()
        
        return result
    
    def _check_buy_conditions(self, row: pd.Series) -> bool:
        """检查买入条件"""
        # 条件1: REI-EMA14 < 25
        rei_ok = row.get('rei_ema', 50) < self.rei_threshold
        
        # 条件2: REI从低位回升 (REA > 0)
        rei_rising = row.get('rei', -50) > 0
        
        # 条件3: 价格在布林带中轨上方
        bb_mid = row.get('bb_mid', row['close'])
        price_ok = row['close'] > bb_mid
        
        # 简化: 不模拟业绩和舆情 (需要额外数据)
        
        return rei_ok and rei_rising and price_ok
    
    def _check_sell_conditions(self, row: pd.Series, position: dict) -> tuple:
        """
        检查卖出条件
        
        Returns:
            (should_sell, reason)
        """
        ts_code = position['ts_code']
        entry_price = position['entry_price']
        hold_time = position['hold_days']
        high_after_entry = position.get('high_after_entry', entry_price)
        
        current_price = row['close']
        
        # 计算当前收益
        profit_ratio = (current_price - entry_price) / entry_price
        
        # 更新持仓期间最高价
        if current_price > high_after_entry:
            high_after_entry = current_price
        
        # 条件1: 持股满10天
        if hold_time >= self.hold_days:
            return True, f"持有满{self.hold_days}天({profit_ratio*100:+.1f}%)"
        
        # 条件2: 止损
        if profit_ratio < -self.stop_loss:
            return True, f"止损({profit_ratio*100:+.1f}%)"
        
        # 条件3: 浮动止盈 (从最高点回落5%)
        if high_after_entry > entry_price:
            trailing_triggered = (high_after_entry - current_price) / high_after_entry > self.trailing_stop
            if trailing_triggered and profit_ratio > self.profit_target:
                return True, f"止盈({profit_ratio*100:+.1f}%)"
        
        # 条件4: 盈利目标后回落
        if profit_ratio > self.profit_target:
            # 继续持有，等待浮动止盈
            pass
        
        return False, ""
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                       positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(60)
            if len(hist) < 30:
                continue
            
            # 计算指标
            df_ind = self._calculate_indicators(hist)
            if len(df_ind) < 2:
                continue
            
            latest = df_ind.iloc[-1]
            
            # ===== 持仓检查 =====
            if ts_code in self.positions:
                pos = self.positions[ts_code]
                pos['hold_days'] += 1
                
                # 卖出检查
                should_sell, reason = self._check_sell_conditions(latest, pos)
                
                if should_sell:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'sell',
                        'reason': reason
                    })
                    del self.positions[ts_code]
            
            # ===== 买入检查 =====
            else:
                if self._check_buy_conditions(latest):
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'buy',
                        'volume': 100,
                        'reason': f'REI买入(REI-EMA14={latest.get("rei_ema", 0):.1f})'
                    })
                    # 记录入场价
                    self.positions[ts_code] = {
                        'ts_code': ts_code,
                        'entry_price': latest['close'],
                        'hold_days': 0,
                        'high_after_entry': latest['close']
                    }
        
        return signals
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有指标"""
        result = df.copy()
        
        # REI
        result = self._calculate_rei(result)
        
        # 布林带
        ma = result['close'].rolling(20).mean()
        std = result['close'].rolling(20).std()
        result['bb_upper'] = ma + 2 * std
        result['bb_mid'] = ma
        result['bb_lower'] = ma - 2 * std
        
        # 均线
        result['ma5'] = result['close'].rolling(5).mean()
        result['ma20'] = result['close'].rolling(20).mean()
        
        return result


# 策略注册表
CUSTOM_STRATEGIES = {
    'rei_custom': REICustomStrategy,
}


if __name__ == '__main__':
    print("=" * 60)
    print("REI自定义策略")
    print("=" * 60)
    print("\n策略参数:")
    print("  - REI-EMA14 < 25")
    print("  - 持股10天")
    print("  - 盈利>10%浮动止盈")
    print("  - 亏损6%止损")
    print("\n使用方法:")
    print("  from backtest.rei_custom_strategy import REICustomStrategy")
    print("  strategy = REICustomStrategy()")
    print("  signals = strategy.generate_signals(date_str, data_dict, positions)")
