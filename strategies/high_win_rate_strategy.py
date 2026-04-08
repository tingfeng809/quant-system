# -*- coding: utf-8 -*-
"""
高胜率优化策略
⛏️ 超级龙虾 - 宁可不出手，出手就要高胜率

核心理念:
1. 多因子确认 — KDJ + RSI + 布林带 三重确认
2. 宁缺毋滥 — 只做高确定性机会
3. 严格止损 — 3% 自动止损
4. 顺势而为 — 只做上升趋势中的回调买入
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from factors.technical_factors import TechnicalFactors


class HighWinRateStrategy:
    """
    高胜率策略
    
    买入条件 (需同时满足):
    1. KDJ 金叉 (K上穿D)
    2. RSI < 60 (上涨中的回调，不是超买)
    3. 价格在布林带中轨以上 (处于上升趋势)
    4. 成交量放大 (>5日均量1.2倍)
    
    卖出条件:
    1. KDJ 死叉
    2. 或 RSI > 70 (超买)
    3. 或价格跌破布林带中轨
    4. 或亏损 > 3% (止损)
    """
    
    def __init__(self, 
                 kdj_period: int = 9,
                 kdj_fast: int = 3,
                 kdj_slow: int = 3,
                 rsi_period: int = 14,
                 rsi_buy_max: int = 60,
                 rsi_sell_min: int = 70,
                 bb_period: int = 20,
                 bb_std: float = 2.0,
                 vol_period: int = 5,
                 vol_multiplier: float = 1.2,
                 stop_loss: float = 0.03):
        self.name = "高胜率策略"
        self.kdj_period = kdj_period
        self.kdj_fast = kdj_fast
        self.kdj_slow = kdj_slow
        self.rsi_period = rsi_period
        self.rsi_buy_max = rsi_buy_max
        self.rsi_sell_min = rsi_sell_min
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.vol_period = vol_period
        self.vol_multiplier = vol_multiplier
        self.stop_loss = stop_loss
        
        self.tech = TechnicalFactors()
        
        # 持仓成本记录 (用于止损判断)
        self.entry_prices: Dict[str, float] = {}
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算所有指标"""
        result = df.copy()
        
        # KDJ
        low_min = result['low'].rolling(self.kdj_period).min()
        high_max = result['high'].rolling(self.kdj_period).max()
        rsv = (result['close'] - low_min) / (high_max - low_min + 1e-10) * 100
        
        k = rsv.rolling(self.kdj_fast).mean()
        d = k.rolling(self.kdj_slow).mean()
        j = 3 * k - 2 * d
        
        result['kdj_k'] = k
        result['kdj_d'] = d
        result['kdj_j'] = j
        
        # KDJ 金叉/死叉
        result['kdj_gold'] = (result['kdj_k'] > result['kdj_d']) & (result['kdj_k'].shift(1) <= result['kdj_d'].shift(1))
        result['kdj_dead'] = (result['kdj_k'] < result['kdj_d']) & (result['kdj_k'].shift(1) >= result['kdj_d'].shift(1))
        
        # RSI
        delta = result['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.rsi_period).mean()
        rs = gain / loss
        result['rsi'] = 100 - (100 / (1 + rs))
        
        # 布林带
        result['bb_mid'] = result['close'].rolling(self.bb_period).mean()
        bb_std = result['close'].rolling(self.bb_period).std()
        result['bb_upper'] = result['bb_mid'] + bb_std * self.bb_std
        result['bb_lower'] = result['bb_mid'] - bb_std * self.bb_std
        result['bb_position'] = (result['close'] - result['bb_lower']) / (result['bb_upper'] - result['bb_lower'] + 1e-10)
        
        # 成交量
        result['vol_ma'] = result['vol'].rolling(self.vol_period).mean()
        result['vol_ratio'] = result['vol'] / result['vol_ma']
        
        # 均线多头 (判断趋势)
        result['ma5'] = result['close'].rolling(5).mean()
        result['ma20'] = result['close'].rolling(20).mean()
        result['uptrend'] = result['ma5'] > result['ma20']
        
        return result
    
    def _check_buy_conditions(self, row: pd.Series) -> tuple:
        """检查买入条件是否满足"""
        reasons = []
        
        # 条件1: KDJ金叉
        if row.get('kdj_gold', False):
            reasons.append('KDJ金叉')
        
        # 条件2: RSI处于合理区间 (30-60，上涨中回调)
        rsi = row.get('rsi', 50)
        if 30 < rsi < self.rsi_buy_max:
            reasons.append(f'RSI={rsi:.1f}')
        
        # 条件3: 价格在布林带中轨以上
        if row.get('close', 0) > row.get('bb_mid', 0):
            reasons.append('BB中轨以上')
        
        # 条件4: 成交量放大
        if row.get('vol_ratio', 0) > self.vol_multiplier:
            reasons.append(f'放量{row.get("vol_ratio", 0):.1f}倍')
        
        # 条件5: 上升趋势
        if row.get('uptrend', False):
            reasons.append('上升趋势')
        
        # 必须满足: KDJ金叉 + RSI条件 + (成交量放大 或 上升趋势)
        kdj_ok = row.get('kdj_gold', False)
        rsi_ok = 30 < rsi < self.rsi_buy_max
        vol_ok = row.get('vol_ratio', 0) > self.vol_multiplier
        trend_ok = row.get('uptrend', False)
        
        buy_score = sum([kdj_ok, rsi_ok, vol_ok or trend_ok])
        
        return buy_score >= 3, reasons
    
    def _check_sell_conditions(self, row: pd.Series, position: dict) -> tuple:
        """检查卖出条件"""
        ts_code = position['ts_code']
        entry_price = self.entry_prices.get(ts_code, row['close'])
        current_price = row['close']
        
        # 止损条件
        loss_ratio = (entry_price - current_price) / entry_price
        if loss_ratio > self.stop_loss:
            return True, f'止损({loss_ratio*100:.1f}%)'
        
        # KDJ死叉
        if row.get('kdj_dead', False):
            return True, 'KDJ死叉'
        
        # RSI超买
        if row.get('rsi', 0) > self.rsi_sell_min:
            return True, f'RSI超买({row.get("rsi", 0):.1f})'
        
        # 跌破布林带中轨
        if current_price < row.get('bb_mid', current_price) and row.get('close', 0) > row.get('bb_mid', 0):
            return True, '跌破BB中轨'
        
        return False, ''
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(60)
            if len(hist) < 30:
                continue
            
            df_ind = self._calculate_indicators(hist)
            if len(df_ind) < 2:
                continue
            
            latest = df_ind.iloc[-1]
            prev = df_ind.iloc[-2]
            
            # 持仓检查
            if ts_code in positions:
                pos = positions[ts_code]
                
                # 卖出检查
                should_sell, reason = self._check_sell_conditions(latest, 
                    {'ts_code': ts_code, 'price': self.entry_prices.get(ts_code, latest['close'])})
                
                if should_sell:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'sell',
                        'reason': reason
                    })
                    # 清空入场价记录
                    if ts_code in self.entry_prices:
                        del self.entry_prices[ts_code]
            
            # 空仓检查 - 买入条件
            else:
                buy_score, reasons = self._check_buy_conditions(latest)
                
                if buy_score:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'buy',
                        'volume': 100,
                        'reason': '|'.join(reasons)
                    })
                    # 记录入场价
                    self.entry_prices[ts_code] = latest['close']
        
        return signals


class ConservativeStrategy:
    """
    保守高胜率策略 — 极度谨慎版
    
    只在以下情况买入:
    1. 大盘处于上升趋势
    2. 个股 KDJ + RSI 双重超卖后回升
    3. 布林带下轨支撑明显
    4. 缩量整理后放量突破
    
    卖出:
    1. 盈利 > 5% 止盈
    2. 亏损立即止损
    3. KDJ死叉
    """
    
    def __init__(self):
        self.name = "保守高胜率策略"
        self.entry_prices: Dict[str, float] = {}
        self.target_profit = 0.05  # 5% 止盈
        self.stop_loss = 0.02       # 2% 止损
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算指标"""
        result = df.copy()
        
        # KDJ
        n = 9
        low_min = result['low'].rolling(n).min()
        high_max = result['high'].rolling(n).max()
        rsv = (result['close'] - low_min) / (high_max - low_min + 1e-10) * 100
        k = rsv.rolling(3).mean()
        d = k.rolling(3).mean()
        result['kdj_k'] = k
        result['kdj_d'] = d
        result['kdj_j'] = 3*k - 2*d
        
        # RSI
        delta = result['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        result['rsi'] = 100 - (100 / (1 + gain/loss))
        
        # 布林带
        ma = result['close'].rolling(20).mean()
        std = result['close'].rolling(20).std()
        result['bb_upper'] = ma + 2*std
        result['bb_mid'] = ma
        result['bb_lower'] = ma - 2*std
        result['bb_position'] = (result['close'] - result['bb_lower']) / (result['bb_upper'] - result['bb_lower'] + 1e-10)
        
        # 成交量
        result['vol_ma5'] = result['vol'].rolling(5).mean()
        result['vol_ratio'] = result['vol'] / result['vol_ma5']
        
        # 均线
        result['ma5'] = result['close'].rolling(5).mean()
        result['ma20'] = result['close'].rolling(20).mean()
        result['trend_up'] = result['ma5'] > result['ma20']
        
        return result
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(60)
            if len(hist) < 30:
                continue
            
            df_ind = self._calculate_indicators(hist)
            if len(df_ind) < 5:
                continue
            
            latest = df_ind.iloc[-1]
            prev = df_ind.iloc[-5:-1]  # 最近5天
            
            # ===== 卖出条件 =====
            if ts_code in positions:
                entry_price = self.entry_prices.get(ts_code, latest['close'])
                current_price = latest['close']
                profit_ratio = (current_price - entry_price) / entry_price
                
                # 止盈
                if profit_ratio > self.target_profit:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'sell',
                        'reason': f'止盈({profit_ratio*100:.1f}%)'
                    })
                    if ts_code in self.entry_prices:
                        del self.entry_prices[ts_code]
                    continue
                
                # 止损
                if profit_ratio < -self.stop_loss:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'sell',
                        'reason': f'止损({profit_ratio*100:.1f}%)'
                    })
                    if ts_code in self.entry_prices:
                        del self.entry_prices[ts_code]
                    continue
                
                # KDJ死叉
                if latest['kdj_k'] < latest['kdj_d'] and prev.iloc[-1]['kdj_k'] >= prev.iloc[-1]['kdj_d']:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'sell',
                        'reason': 'KDJ死叉'
                    })
                    if ts_code in self.entry_prices:
                        del self.entry_prices[ts_code]
                    continue
            
            # ===== 买入条件 =====
            else:
                # 条件1: 上升趋势
                if not latest.get('trend_up', False):
                    continue
                
                # 条件2: KDJ低位金叉 (K<50时金叉更可靠)
                kdj_gold = (latest['kdj_k'] > latest['kdj_d'] and 
                           prev.iloc[-1]['kdj_k'] <= prev.iloc[-1]['kdj_d'] and
                           latest['kdj_k'] < 50)
                
                # 条件3: RSI回调后回升 (从<50回到50-60区间)
                rsi_ok = 40 < latest['rsi'] < 65
                
                # 条件4: 价格在布林带中轨上方
                price_ok = latest['close'] > latest['bb_mid']
                
                # 条件5: 成交量温和放大
                vol_ok = 0.8 < latest['vol_ratio'] < 2.0
                
                # 综合评分
                buy_score = sum([kdj_gold, rsi_ok, price_ok, vol_ok])
                
                if buy_score >= 3:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'buy',
                        'volume': 100,
                        'reason': f'保守买入(KDJ={latest["kdj_k"]:.0f},RSI={latest["rsi"]:.0f})'
                    })
                    self.entry_prices[ts_code] = latest['close']
        
        return signals


# 策略注册表
HIGH_WIN_RATE_STRATEGIES = {
    'high_win': HighWinRateStrategy,
    'conservative': ConservativeStrategy,
}


if __name__ == '__main__':
    print("=" * 60)
    print("高胜率优化策略")
    print("=" * 60)
    print("\n可用策略:")
    for name, cls in HIGH_WIN_RATE_STRATEGIES.items():
        print(f"  - {name}: {cls.__name__}")
    print("\n核心理念: 宁可不出手，出手就要高胜率")
