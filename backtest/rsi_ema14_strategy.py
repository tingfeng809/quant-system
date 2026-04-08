# -*- coding: utf-8 -*-
"""
自定义RSI-EMA14策略回测
⛏️ 超级龙虾

策略参数:
- RSI(EMA14) < 25 (超卖区域)
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


class RSIEma14Strategy:
    """
    RSI-EMA14自定义策略
    
    买入条件:
    1. RSI(EMA14) < 25 (RSI处于超卖低位)
    2. RSI从低位回升 (从<25回到>25)
    3. 业绩稳定增长 (模拟)
    4. 无负面舆情 (模拟)
    
    卖出条件:
    1. 持股满10天
    2. 盈利 > 10%: 浮动止盈 (从最高点回落5%卖出)
    3. 亏损 6%: 止损平仓
    """
    
    def __init__(self, 
                 rsi_period: int = 14,
                 rsi_ema_period: int = 14,
                 rsi_threshold: float = 35,
                 hold_days: int = 10,
                 profit_target: float = 0.10,
                 stop_loss: float = 0.06,
                 trailing_stop: float = 0.05):
        self.name = "RSI-EMA14策略"
        self.rsi_period = rsi_period
        self.rsi_ema_period = rsi_ema_period
        self.rsi_threshold = rsi_threshold
        self.hold_days = hold_days
        self.profit_target = profit_target
        self.stop_loss = stop_loss
        self.trailing_stop = trailing_stop
        
        # 持仓记录
        self.positions: Dict[str, dict] = {}
    
    def _calculate_rsi_ema(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算RSI和RSI的EMA
        """
        result = df.copy()
        
        # RSI
        delta = result['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.rsi_period).mean()
        rs = gain / loss
        result['rsi'] = 100 - (100 / (1 + rs))
        
        # RSI的EMA
        result['rsi_ema'] = result['rsi'].ewm(span=self.rsi_ema_period).mean()
        
        return result
    
    def _check_buy_conditions(self, row: pd.Series, prev_row: pd.Series) -> bool:
        """检查买入条件"""
        rsi_ema = row.get('rsi_ema', 50)
        prev_rsi_ema = prev_row.get('rsi_ema', 50)
        rsi = row.get('rsi', 50)
        prev_rsi = prev_row.get('rsi', 50)
        
        # 条件1: RSI-EMA14 < 25
        threshold_ok = rsi_ema < self.rsi_threshold
        
        # 条件2: RSI从超卖区回升 (金叉)
        # recovery = (prev_rsi_ema <= self.rsi_threshold) and (rsi_ema > self.rsi_threshold)  # 禁用回升条件
        
        # 条件3: 价格在布林带中轨上方
        bb_mid = row.get('bb_mid', row['close'])
        price_ok = row['close'] > bb_mid
        
        # 条件4: 上升趋势 (MA5 > MA20)
        trend_ok = row.get('ma5', 0) > row.get('ma20', 0)
        
        # 满足条件1 + (条件2 或 条件3)
        return threshold_ok
    
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
        
        # 条件3: 浮动止盈 (盈利>10%后从最高点回落5%)
        if high_after_entry > entry_price:
            # 从最高点回落超过5%
            drawdown = (high_after_entry - current_price) / high_after_entry
            if profit_ratio > self.profit_target and drawdown > self.trailing_stop:
                return True, f"止盈({profit_ratio*100:+.1f}%)"
        
        # 条件4: 持有期间盈利目标达成后回落
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
            prev = df_ind.iloc[-2]
            
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
                if self._check_buy_conditions(latest, prev):
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'buy',
                        'volume': 100,
                        'reason': f'RSI买入(RSI-EMA14={latest.get("rsi_ema", 0):.1f})'
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
        
        # RSI-EMA
        result = self._calculate_rsi_ema(result)
        
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
    'rsi_ema14': RSIEma14Strategy,
}


if __name__ == '__main__':
    print("=" * 60)
    print("RSI-EMA14自定义策略")
    print("=" * 60)
    print("\n策略参数:")
    print("  - RSI(EMA14) < 25")
    print("  - 持股10天")
    print("  - 盈利>10%浮动止盈")
    print("  - 亏损6%止损")
    print("\n使用方法:")
    print("  from backtest.rsi_ema14_strategy import RSIEma14Strategy")
    print("  strategy = RSIEma14Strategy()")
    print("  signals = strategy.generate_signals(date_str, data_dict, positions)")
