# -*- coding: utf-8 -*-
"""
高级量化策略库
⛏️ 超级龙虾 - A股量化分析系统

包含:
1. 布林带策略 (Bollinger Bands)
2. RSI 策略
3. Squeeze Momentum 策略
4. KDJ 策略
5. 趋势跟踪策略
6. 波动率突破策略
"""

import pandas as pd
import numpy as np
from typing import Dict, List
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from factors.technical_factors import TechnicalFactors


# ==================== 策略基类 ====================
class Strategy:
    """策略基类"""
    
    def __init__(self, name: str = "BaseStrategy"):
        self.name = name
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        raise NotImplementedError


# ==================== 策略 6: 布林带策略 ====================
class BollingerBandStrategy(Strategy):
    """
    布林带策略 (Bollinger Bands)
    
    原理:
    - 中轨: N日简单移动平均线
    - 上轨: 中轨 + 2倍标准差
    - 下轨: 中轨 - 2倍标准差
    
    买入信号:
    1. 价格触及下轨 (超卖)
    2. RSI < 30 (配合确认)
    3. 布林带开口扩大
    
    卖出信号:
    1. 价格触及上轨 (超买)
    2. RSI > 70 (配合确认)
    3. 布林带收口
    """
    
    def __init__(self, period: int = 20, std_dev: float = 2.0, rsi_period: int = 14):
        super().__init__("布林带策略")
        self.period = period
        self.std_dev = std_dev
        self.rsi_period = rsi_period
        self.tech = TechnicalFactors()
    
    def _calculate_bollinger(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算布林带"""
        df = df.copy()
        df['bb_mid'] = df['close'].rolling(self.period).mean()
        df['bb_std'] = df['close'].rolling(self.period).std()
        df['bb_upper'] = df['bb_mid'] + self.std_dev * df['bb_std']
        df['bb_lower'] = df['bb_mid'] - self.std_dev * df['bb_std']
        
        # 布林带状态
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # RSI
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 带宽 (衡量波动率)
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
        
        return df
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(60)
            if len(hist) < self.period + 5:
                continue
            
            df_bb = self._calculate_bollinger(hist)
            if len(df_bb) < 2:
                continue
            
            latest = df_bb.iloc[-1]
            prev = df_bb.iloc[-2]
            
            # 买入: 价格触及下轨 + RSI超卖
            if (latest['close'] <= latest['bb_lower'] * 1.01 and 
                latest['rsi'] < 35 and 
                ts_code not in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'布林带超卖(下轨) RSI={latest["rsi"]:.1f}'
                })
            
            # 卖出: 价格触及上轨 + RSI超买
            elif (latest['close'] >= latest['bb_upper'] * 0.99 and 
                  latest['rsi'] > 65 and 
                  ts_code in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': f'布林带超买(上轨) RSI={latest["rsi"]:.1f}'
                })
            
            # 止损: 持有且价格跌破中轨
            elif (ts_code in positions and 
                  latest['close'] < latest['bb_mid'] and 
                  prev['close'] >= prev['bb_mid']):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': '布林带中轨止损'
                })
        
        return signals


# ==================== 策略 7: RSI 策略 ====================
class RSIStrategy(Strategy):
    """
    RSI 相对强弱指标策略
    
    原理:
    - RSI 衡量价格涨跌的相对强度
    - RSI > 70: 超买区域
    - RSI < 30: 超卖区域
    
    买入信号:
    1. RSI 从超卖区回升 (RSI > 30)
    2. RSI 上穿 50 中轴
    3. 配合价格底背离
    
    卖出信号:
    1. RSI 从超买区回落 (RSI < 70)
    2. RSI 下穿 50 中轴
    3. 配合价格顶背离
    """
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        super().__init__("RSI 策略")
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.tech = TechnicalFactors()
    
    def _calculate_rsi(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算RSI"""
        df = df.copy()
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(self.period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # RSI 平滑线
        df['rsi_ma'] = df['rsi'].rolling(5).mean()
        
        return df
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(60)
            if len(hist) < self.period + 10:
                continue
            
            df_rsi = self._calculate_rsi(hist)
            if len(df_rsi) < 2:
                continue
            
            latest = df_rsi.iloc[-1]
            prev = df_rsi.iloc[-2]
            prev2 = df_rsi.iloc[-3]
            
            # 买入: RSI 从超卖区回升
            if (prev['rsi'] <= self.oversold and 
                latest['rsi'] > self.oversold and
                ts_code not in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'RSI 超卖区回升 RSI={latest["rsi"]:.1f}'
                })
            
            # 买入: RSI 金叉中轴
            elif (prev2['rsi'] <= 50 and 
                  prev['rsi'] > 50 and
                  ts_code not in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'RSI 上穿中轴 RSI={latest["rsi"]:.1f}'
                })
            
            # 卖出: RSI 从超买区回落
            elif (prev['rsi'] >= self.overbought and 
                  latest['rsi'] < self.overbought and 
                  ts_code in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': f'RSI 超买区回落 RSI={latest["rsi"]:.1f}'
                })
            
            # 卖出: RSI 死叉中轴
            elif (prev2['rsi'] >= 50 and 
                  prev['rsi'] < 50 and 
                  ts_code in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': f'RSI 下穿中轴 RSI={latest["rsi"]:.1f}'
                })
        
        return signals


# ==================== 策略 8: Squeeze Momentum 策略 ====================
class SqueezeMomentumStrategy(Strategy):
    """
    Squeeze Momentum 策略 (布林带收口 + 肯特纳通道)
    
    原理:
    - 当布林带收口 (BB 带宽低于历史N周期均值) = 波动率压缩
    - 波动率压缩后必然扩张，产生大行情
    - 配合动量方向确认入场
    
    买入信号:
    1. Squeeze OFF (波动率开始扩张)
    2. 动量由负转正
    3. 价格站上 20 日均线
    
    卖出信号:
    1. 动量由正转负
    2. 或价格跌破 20 日均线
    """
    
    def __init__(self, bb_period: int = 20, bb_std: float = 2.0, 
                 kc_period: int = 20, kc_mult: float = 1.5):
        super().__init__("Squeeze Momentum 策略")
        self.bb_period = bb_period
        self.bb_std = bb_std
        self.kc_period = kc_period
        self.kc_mult = kc_mult
        self.tech = TechnicalFactors()
    
    def _calculate_squeeze(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算 Squeeze Momentum"""
        df = df.copy()
        
        # 布林带
        df['bb_mid'] = df['close'].rolling(self.bb_period).mean()
        df['bb_std'] = df['close'].rolling(self.bb_period).std()
        df['bb_upper'] = df['bb_mid'] + self.bb_std * df['bb_std']
        df['bb_lower'] = df['bb_mid'] - self.bb_std * df['bb_std']
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
        
        # 肯特纳通道 (ATR-based)
        df['tr'] = np.maximum(
            df['high'] - df['low'],
            np.maximum(
                abs(df['high'] - df['close'].shift(1)),
                abs(df['low'] - df['close'].shift(1))
            )
        )
        df['atr'] = df['tr'].rolling(self.kc_period).mean()
        df['kc_mid'] = df['close'].rolling(self.kc_period).mean()
        df['kc_upper'] = df['kc_mid'] + df['atr'] * self.kc_mult
        df['kc_lower'] = df['kc_mid'] - df['atr'] * self.kc_mult
        
        # Squeeze 状态 (布林带在肯特纳通道内 = 压缩)
        df['squeeze'] = (df['bb_upper'] < df['kc_upper']) & (df['bb_lower'] > df['kc_lower'])
        
        # 动量 (类似 LazyBear 的实现)
        highest_high = df['high'].rolling(self.kc_period).max()
        lowest_low = df['low'].rolling(self.kc_period).min()
        ma = df['close'].rolling(self.kc_period).mean()
        df['momentum'] = (df['close'] - (highest_high + lowest_low + ma) / 3) * 100
        
        # 20 日均线
        df['ma20'] = df['close'].rolling(20).mean()
        
        return df
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(60)
            if len(hist) < 40:
                continue
            
            df_sq = self._calculate_squeeze(hist)
            if len(df_sq) < 5:
                continue
            
            # 检查最近5个bar的squeeze状态变化
            recent = df_sq.iloc[-5:]
            squeeze_offsets = recent['squeeze'].values
            
            # squeeze 从 True 变成 False = 开始扩张
            squeeze_just_ended = (squeeze_offsets[-2] == True) and (squeeze_offsets[-1] == False)
            
            latest = df_sq.iloc[-1]
            prev = df_sq.iloc[-2]
            
            # 买入: Squeeze 结束 + 动量转正
            if (squeeze_just_ended and 
                prev['momentum'] <= 0 and 
                latest['momentum'] > 0 and
                ts_code not in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'Squeeze 突破 动量={latest["momentum"]:.2f}'
                })
            
            # 买入: 价格站上 MA20 + 动量为正
            elif (prev['close'] <= prev['ma20'] and 
                  latest['close'] > latest['ma20'] and
                  latest['momentum'] > 0 and
                  ts_code not in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'站上 MA20 动量={latest["momentum"]:.2f}'
                })
            
            # 卖出: 动量转负
            elif (prev['momentum'] > 0 and 
                  latest['momentum'] < 0 and 
                  ts_code in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': f'动量转负 动量={latest["momentum"]:.2f}'
                })
            
            # 卖出: 跌破 MA20
            elif (prev['close'] > prev['ma20'] and 
                  latest['close'] < latest['ma20'] and 
                  ts_code in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': '跌破 MA20'
                })
        
        return signals


# ==================== 策略 9: KDJ 策略 ====================
class KDJStrategy(Strategy):
    """
    KDJ 随机指标策略
    
    原理:
    - K: 最近N日收盘价的位置
    - D: K 的移动平均
    - J: 3*K - 2*D (敏感指标)
    
    买入信号:
    1. K < 20 且 J < 0 (超卖)
    2. K 上穿 D (金叉)
    3. KDJ 多头排列 (K > D > J 且上升)
    
    卖出信号:
    1. K > 80 且 J > 100 (超买)
    2. K 下穿 D (死叉)
    3. KDJ 空头排列
    """
    
    def __init__(self, n: int = 9, m1: int = 3, m2: int = 3):
        super().__init__("KDJ 策略")
        self.n = n  # RSV 周期
        self.m1 = m1  # K 平滑
        self.m2 = m2  # D 平滑
    
    def _calculate_kdj(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算 KDJ"""
        df = df.copy()
        
        # RSV = (C - L) / (H - L) * 100
        low_n = df['low'].rolling(self.n).min()
        high_n = df['high'].rolling(self.n).max()
        
        rsv = (df['close'] - low_n) / (high_n - low_n) * 100
        rsv = rsv.fillna(50)
        
        # K = 2/3 * prev_K + 1/3 * RSV
        # D = 2/3 * prev_D + 1/3 * K
        # J = 3*K - 2*D
        
        k = np.zeros(len(df))
        d = np.zeros(len(df))
        j = np.zeros(len(df))
        
        k[0] = 50
        d[0] = 50
        
        for i in range(1, len(df)):
            k[i] = (2/3) * k[i-1] + (1/3) * rsv.iloc[i]
            d[i] = (2/3) * d[i-1] + (1/3) * k[i]
        
        j = 3 * k - 2 * d
        
        df['kdj_k'] = k
        df['kdj_d'] = d
        df['kdj_j'] = j
        
        # 多头排列: K > D 且 K 上升
        df['kdj_gold'] = (df['kdj_k'] > df['kdj_d']) & (df['kdj_k'].diff() > 0)
        # 空头排列: K < D 且 K 下降
        df['kdj_dead'] = (df['kdj_k'] < df['kdj_d']) & (df['kdj_k'].diff() < 0)
        
        return df
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(60)
            if len(hist) < self.n + 5:
                continue
            
            df_kdj = self._calculate_kdj(hist)
            if len(df_kdj) < 2:
                continue
            
            latest = df_kdj.iloc[-1]
            prev = df_kdj.iloc[-2]
            
            # 买入: 金叉 + 超卖
            if (prev['kdj_k'] <= prev['kdj_d'] and 
                latest['kdj_k'] > latest['kdj_d'] and
                latest['kdj_k'] < 80 and
                ts_code not in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'KDJ 金叉 K={latest["kdj_k"]:.1f} D={latest["kdj_d"]:.1f}'
                })
            
            # 买入: KDJ 多头排列形成
            elif (not prev['kdj_gold'] and 
                  latest['kdj_gold'] and
                  ts_code not in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'KDJ 多头排列 J={latest["kdj_j"]:.1f}'
                })
            
            # 卖出: 死叉
            elif (prev['kdj_k'] >= prev['kdj_d'] and 
                  latest['kdj_k'] < latest['kdj_d'] and 
                  ts_code in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': f'KDJ 死叉 K={latest["kdj_k"]:.1f} D={latest["kdj_d"]:.1f}'
                })
            
            # 卖出: 超买
            elif (latest['kdj_j'] > 100 and 
                  ts_code in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': f'KDJ 超买 J={latest["kdj_j"]:.1f}'
                })
        
        return signals


# ==================== 策略 10: 趋势跟踪策略 ====================
class TrendFollowingStrategy(Strategy):
    """
    趋势跟踪策略 (Moving Average Crossover + ATR 止损)
    
    原理:
    - 使用 EMA 而非 SMA (更快反映趋势)
    - 多时间周期确认 (日线 + 4H)
    - ATR 动态止损
    
    买入信号:
    1. EMA5 > EMA20 > EMA60 (多头排列)
    2. 价格站上 EMA20
    3. ATR 突破 (波动率放大)
    
    卖出信号:
    1. EMA5 < EMA20 (空头排列)
    2. 价格跌破 EMA20
    3. ATR 止损触发
    """
    
    def __init__(self, fast: int = 5, mid: int = 20, slow: int = 60, atr_period: int = 14):
        super().__init__("趋势跟踪策略")
        self.fast = fast
        self.mid = mid
        self.slow = slow
        self.atr_period = atr_period
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算指标"""
        df = df.copy()
        
        # EMA
        df['ema_fast'] = df['close'].ewm(span=self.fast).mean()
        df['ema_mid'] = df['close'].ewm(span=self.mid).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(self.atr_period).mean()
        
        # 多头排列
        df['bullish'] = (df['ema_fast'] > df['ema_mid']) & (df['ema_mid'] > df['ema_slow'])
        
        return df
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(120)
            if len(hist) < self.slow + 10:
                continue
            
            df_ind = self._calculate_indicators(hist)
            if len(df_ind) < 2:
                continue
            
            latest = df_ind.iloc[-1]
            prev = df_ind.iloc[-2]
            
            # 买入: 多头排列 + 价格站上 EMA20
            if (latest['bullish'] and
                prev['close'] <= prev['ema_mid'] and
                latest['close'] > latest['ema_mid'] and
                ts_code not in positions):
                stop_loss = latest['close'] - 2 * latest['atr']
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'趋势跟踪买入 ATR止损={stop_loss:.2f}'
                })
            
            # 卖出: 空头排列
            elif (not latest['bullish'] and 
                  prev['ema_fast'] >= prev['ema_mid'] and
                  latest['ema_fast'] < latest['ema_mid'] and
                  ts_code in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'sell',
                    'reason': '趋势跟踪卖出 (EMA 死叉)'
                })
            
            # ATR 止损
            elif (ts_code in positions):
                entry_price = positions[ts_code].get('price', latest['close'])
                stop_loss = entry_price - 2 * latest['atr']
                if latest['close'] < stop_loss:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'sell',
                        'reason': f'ATR 止损'
                    })
        
        return signals


# ==================== 策略 11: 波动率突破策略 ====================
class VolatilityBreakoutStrategy(Strategy):
    """
    波动率突破策略
    
    原理:
    - 当价格突破 N 日最高价时买入
    - 使用 ATR 作为止损
    - 波动率收缩后突破往往有大行情
    
    买入信号:
    1. 价格突破 N 日最高价
    2. 成交量放大 (> 1.5 倍均量)
    
    卖出信号:
    1. 价格跌破入场价 - 2*ATR
    2. 价格跌破 N 日最低价
    """
    
    def __init__(self, period: int = 20, atr_period: int = 14, atr_multiplier: float = 2.0):
        super().__init__("波动率突破策略")
        self.period = period
        self.atr_period = atr_period
        self.atr_multiplier = atr_multiplier
    
    def _calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算指标"""
        df = df.copy()
        
        # 最高/最低价
        df['highest'] = df['high'].rolling(self.period).max()
        df['lowest'] = df['low'].rolling(self.period).min()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.rolling(self.atr_period).mean()
        
        # 成交量均量
        df['volume_ma'] = df['vol'].rolling(20).mean()
        
        return df
    
    def generate_signals(self, date_str: str, data_dict: Dict[str, pd.DataFrame], 
                        positions: Dict) -> List[Dict]:
        signals = []
        
        for ts_code, df in data_dict.items():
            hist = df[df['trade_date'] < date_str].tail(60)
            if len(hist) < self.period + 5:
                continue
            
            df_ind = self._calculate_indicators(hist)
            if len(df_ind) < 2:
                continue
            
            latest = df_ind.iloc[-1]
            prev = df_ind.iloc[-2]
            
            # 买入: 突破最高价 + 放量
            if (prev['close'] <= prev['highest'] and 
                latest['close'] > latest['highest'] and
                latest['vol'] > 1.5 * latest['volume_ma'] and
                ts_code not in positions):
                signals.append({
                    'ts_code': ts_code,
                    'direction': 'buy',
                    'volume': 100,
                    'reason': f'波动率突破 放量{latest["vol"]/latest["volume_ma"]:.1f}倍'
                })
            
            # 止损检查
            elif ts_code in positions:
                entry_price = positions[ts_code].get('price', latest['close'])
                stop_loss = entry_price - self.atr_multiplier * latest['atr']
                
                # ATR 止损
                if latest['close'] < stop_loss:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'sell',
                        'reason': '波动率止损'
                    })
                
                # 跌破最低价
                elif latest['close'] < latest['lowest']:
                    signals.append({
                        'ts_code': ts_code,
                        'direction': 'sell',
                        'reason': '跌破最低价'
                    })
        
        return signals


# ==================== 策略注册表 ====================
STRATEGY_REGISTRY = {
    'bollinger': BollingerBandStrategy,
    'rsi': RSIStrategy,
    'squeeze': SqueezeMomentumStrategy,
    'kdj': KDJStrategy,
    'trend': TrendFollowingStrategy,
    'volatility': VolatilityBreakoutStrategy,
}


if __name__ == '__main__':
    print("=" * 60)
    print("高级策略库")
    print("=" * 60)
    print("\n可用策略:")
    for name, cls in STRATEGY_REGISTRY.items():
        print(f"  - {name}: {cls.__name__}")
    print("\n使用示例:")
    print("  from strategies.advanced_strategies import STRATEGY_REGISTRY")
    print("  strategy = STRATEGY_REGISTRY['bollinger']()")
    print("  signals = strategy.generate_signals(date_str, data_dict, positions)")
