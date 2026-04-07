# -*- coding: utf-8 -*-
"""
高级因子库
⛏️ 超级龙虾 - A股量化分析系统

包含:
1. 波动率因子 (Volatility Factors)
2. 动量因子 (Momentum Factors)
3. 趋势强度因子 (Trend Strength Factors)
4. 成交量因子 (Volume Factors)
5. 支撑压力因子 (Support Resistance Factors)
6. 背离因子 (Divergence Factors)
"""

import pandas as pd
import numpy as np
from typing import Dict, Optional
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


class VolatilityFactors:
    """波动率因子"""
    
    @staticmethod
    def atr(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        ATR (Average True Range) - 平均真实波幅
        
        用途: 衡量市场波动程度, 用于止损/仓位管理
        """
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()
    
    @staticmethod
    def historical_volatility(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        历史波动率
        
        计算: N日收益的标准差年化
        """
        returns = df['close'].pct_change()
        return returns.rolling(period).std() * np.sqrt(252)
    
    @staticmethod
    def keltner_channels(df: pd.DataFrame, ema_period: int = 20, atr_period: int = 10, multiplier: float = 2.0):
        """
        肯特纳通道
        
        - 中轨: EMA
        - 上轨: EMA + 2 * ATR
        - 下轨: EMA - 2 * ATR
        """
        ema = df['close'].ewm(span=ema_period).mean()
        atr = VolatilityFactors.atr(df, atr_period)
        
        return {
            'kc_mid': ema,
            'kc_upper': ema + multiplier * atr,
            'kc_lower': ema - multiplier * atr
        }
    
    @staticmethod
    def donchian_channels(df: pd.DataFrame, period: int = 20):
        """
        唐奇安通道 (布林带的趋势版本)
        
        - 上轨: N日最高价
        - 下轨: N日最低价
        - 中轨: (上轨 + 下轨) / 2
        """
        return {
            'dc_upper': df['high'].rolling(period).max(),
            'dc_lower': df['low'].rolling(period).min(),
            'dc_mid': (df['high'].rolling(period).max() + df['low'].rolling(period).min()) / 2
        }


class MomentumFactors:
    """动量因子"""
    
    @staticmethod
    def rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        RSI (Relative Strength Index) - 相对强弱指数
        """
        delta = df['close'].diff()
        gain = delta.where(delta > 0, 0).rolling(period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    @staticmethod
    def stochastic(df: pd.DataFrame, k_period: int = 14, d_period: int = 3) -> Dict[str, pd.Series]:
        """
        随机指标 (KD)
        
        - K: RSV 的 M1 日平滑
        - D: K 的 M2 日平滑
        """
        low_min = df['low'].rolling(k_period).min()
        high_max = df['high'].rolling(k_period).max()
        
        rsv = (df['close'] - low_min) / (high_max - low_min) * 100
        rsv = rsv.fillna(50)
        
        k = rsv.rolling(d_period).mean()
        d = k.rolling(d_period).mean()
        
        return {'stoch_k': k, 'stoch_d': d}
    
    @staticmethod
    def cci(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        CCI (Commodity Channel Index) - 商品通道指数
        
        用途: 超买超卖研判, 趋势确认
        """
        tp = (df['high'] + df['low'] + df['close']) / 3
        sma = tp.rolling(period).mean()
        mad = tp.rolling(period).apply(lambda x: np.abs(x - x.mean()).mean())
        
        return (tp - sma) / (0.015 * mad)
    
    @staticmethod
    def mfi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """
        MFI (Money Flow Index) - 资金流量指数
        
        原理: 类似 RSI 但使用成交量加权
        """
        tp = (df['high'] + df['low'] + df['close']) / 3
        raw_money_flow = tp * df['vol']
        
        positive_flow = raw_money_flow.where(tp > tp.shift(1), 0).rolling(period).sum()
        negative_flow = raw_money_flow.where(tp < tp.shift(1), 0).rolling(period).sum()
        
        money_ratio = positive_flow / negative_flow
        return 100 - (100 / (1 + money_ratio))
    
    @staticmethod
    def momentum(df: pd.DataFrame, period: int = 10) -> pd.Series:
        """
        动量指标
        
        计算: 今日收盘价 - N日前收盘价
        """
        return df['close'] - df['close'].shift(period)
    
    @staticmethod
    def roc(df: pd.DataFrame, period: int = 12) -> pd.Series:
        """
        ROC (Rate of Change) - 变动率指标
        """
        return (df['close'] - df['close'].shift(period)) / df['close'].shift(period) * 100


class TrendStrengthFactors:
    """趋势强度因子"""
    
    @staticmethod
    def adx(df: pd.DataFrame, period: int = 14) -> Dict[str, pd.Series]:
        """
        ADX (Average Directional Index) - 平均趋向指数
        
        - ADX: 趋势强度 (0-100, 越高趋势越强)
        - +DI: 上升趋向指标
        - -DI: 下降趋向指标
        """
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        
        plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
        minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)
        
        atr = VolatilityFactors.atr(df, period)
        
        plus_di = 100 * (plus_dm.rolling(period).mean() / atr)
        minus_di = 100 * (minus_dm.rolling(period).mean() / atr)
        
        dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
        adx = dx.rolling(period).mean()
        
        return {'adx': adx, 'plus_di': plus_di, 'minus_di': minus_di}
    
    @staticmethod
    def trend_intensity(df: pd.DataFrame, period: int = 30) -> pd.Series:
        """
        趋势强度指数
        
        计算: 收盘价在 N 日高低点区间的位置
        """
        highest = df['close'].rolling(period).max()
        lowest = df['close'].rolling(period).min()
        
        return (df['close'] - lowest) / (highest - lowest) * 100
    
    @staticmethod
    def supertrend(df: pd.DataFrame, period: int = 10, multiplier: float = 3.0) -> Dict[str, pd.Series]:
        """
        SuperTrend 超级趋势
        
        - 上轨/下轨基于 ATR
        - 趋势反转条件: 收盘价上穿/下穿轨道
        """
        atr = VolatilityFactors.atr(df, period)
        
        hl2 = (df['high'] + df['low']) / 2
        upper_band = hl2 + multiplier * atr
        lower_band = hl2 - multiplier * atr
        
        supertrend = pd.Series(index=df.index, dtype=float)
        direction = pd.Series(1, index=df.index)  # 1=上涨, -1=下跌
        
        for i in range(period, len(df)):
            if i == period:
                supertrend.iloc[i] = lower_band.iloc[i]
            else:
                if df['close'].iloc[i] > upper_band.iloc[i-1]:
                    direction.iloc[i] = 1
                    supertrend.iloc[i] = lower_band.iloc[i]
                elif df['close'].iloc[i] < upper_band.iloc[i-1]:
                    direction.iloc[i] = -1
                    supertrend.iloc[i] = upper_band.iloc[i]
                else:
                    direction.iloc[i] = direction.iloc[i-1]
                    supertrend.iloc[i] = supertrend.iloc[i-1]
        
        return {'supertrend': supertrend, 'direction': direction}


class VolumeFactors:
    """成交量因子"""
    
    @staticmethod
    def obv(df: pd.DataFrame) -> pd.Series:
        """
        OBV (On-Balance Volume) - 能量潮
        
        原理: 上涨日成交量累加, 下跌日成交量累减
        """
        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = df['vol'].iloc[0]
        
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['vol'].iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['vol'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def vwap(df: pd.DataFrame) -> pd.Series:
        """
        VWAP (Volume Weighted Average Price) - 成交量加权平均价
        
        用途: 机构入场/出场成本参考
        """
        tp = (df['high'] + df['low'] + df['close']) / 3
        return (tp * df['vol']).cumsum() / df['vol'].cumsum()
    
    @staticmethod
    def volume_ratio(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        量比 (Volume Ratio)
        
        计算: 今日成交量 / N日平均成交量
        """
        return df['vol'] / df['vol'].rolling(period).mean()
    
    @staticmethod
    def money_flow(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        资金流
    
        计算: (收盘价 - 最低价) / (最高价 - 最低价) * 成交量
        """
        mf = (df['close'] - df['low']) / (df['high'] - df['low'] + 1e-10) * df['vol']
        return mf.rolling(period).sum()


class SupportResistanceFactors:
    """支撑压力因子"""
    
    @staticmethod
    def pivot_points(df: pd.DataFrame) -> Dict[str, float]:
        """
        枢轴点 (Pivot Points)
        
        - R1, R2, R3: 阻力位
        - S1, S2, S3: 支撑位
        """
        pivot = (df['high'].iloc[-1] + df['low'].iloc[-1] + df['close'].iloc[-1]) / 3
        
        r1 = 2 * pivot - df['low'].iloc[-1]
        r2 = pivot + (df['high'].iloc[-1] - df['low'].iloc[-1])
        r3 = r2 + (df['high'].iloc[-1] - df['low'].iloc[-1])
        
        s1 = 2 * pivot - df['high'].iloc[-1]
        s2 = pivot - (df['high'].iloc[-1] - df['low'].iloc[-1])
        s3 = s2 - (df['high'].iloc[-1] - df['low'].iloc[-1])
        
        return {
            'pivot': pivot,
            'r1': r1, 'r2': r2, 'r3': r3,
            's1': s1, 's2': s2, 's3': s3
        }
    
    @staticmethod
    def fibonacci_retracement(df: pd.DataFrame, period: int = 50) -> Dict[str, float]:
        """
        斐波那契回撤位
        
        关键位: 23.6%, 38.2%, 50%, 61.8%, 78.6%
        """
        high = df['high'].rolling(period).max().iloc[-1]
        low = df['low'].rolling(period).min().iloc[-1]
        diff = high - low
        
        return {
            'fib_236': high - diff * 0.236,
            'fib_382': high - diff * 0.382,
            'fib_500': high - diff * 0.500,
            'fib_618': high - diff * 0.618,
            'fib_786': high - diff * 0.786
        }
    
    @staticmethod
    def distance_to_support(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        到支撑位的距离
        
        计算: (收盘价 - N日最低价) / N日最低价
        """
        lowest = df['low'].rolling(period).min()
        return (df['close'] - lowest) / lowest * 100
    
    @staticmethod
    def distance_to_resistance(df: pd.DataFrame, period: int = 20) -> pd.Series:
        """
        到压力位的距离
        
        计算: (N日最高价 - 收盘价) / 收盘价
        """
        highest = df['high'].rolling(period).max()
        return (highest - df['close']) / df['close'] * 100


class DivergenceFactors:
    """背离因子"""
    
    @staticmethod
    def price_volume_divergence(df: pd.DataFrame, period: int = 20) -> str:
        """
        量价背离
        
        - 上涨缩量: 可能见顶
        - 下跌放量: 可能见底
        """
        price_trend = df['close'].iloc[-1] - df['close'].iloc[-period]
        volume_trend = df['vol'].iloc[-1] - df['vol'].rolling(period).mean().iloc[-1]
        
        if price_trend > 0 and volume_trend < 0:
            return "顶背离(上涨缩量)"
        elif price_trend < 0 and volume_trend > 0:
            return "底背离(下跌放量)"
        elif price_trend > 0 and volume_trend > 0:
            return "量价同增"
        elif price_trend < 0 and volume_trend < 0:
            return "量价同减"
        else:
            return "无明显背离"
    
    @staticmethod
    def rsi_divergence(df: pd.DataFrame, period: int = 14) -> str:
        """
        RSI 背离
        
        - 价格创高, RSI 未创新高: 顶背离
        - 价格创低, RSI 未创新低: 底背离
        """
        price = df['close']
        rsi = MomentumFactors.rsi(df, period)
        
        # 简化判断: 最近 N 天价格与 RSI 的相关性
        recent_price = price.iloc[-period:]
        recent_rsi = rsi.iloc[-period:]
        
        price_high_idx = recent_price.idxmax()
        rsi_high_idx = recent_rsi.idxmax()
        
        price_low_idx = recent_price.idxmin()
        rsi_low_idx = recent_rsi.idxmin()
        
        # 顶背离: 价格创新高但 RSI 没有
        if price.iloc[-1] > recent_price.iloc[0] and rsi.iloc[-1] < recent_rsi.loc[price_high_idx]:
            return "顶背离"
        # 底背离: 价格创新低但 RSI 没有
        elif price.iloc[-1] < recent_price.iloc[0] and rsi.iloc[-1] > recent_rsi.loc[price_low_idx]:
            return "底背离"
        else:
            return "无背离"


class AdvancedFactorCalculator:
    """高级因子计算器 - 整合所有因子"""
    
    def __init__(self):
        self.volatility = VolatilityFactors()
        self.momentum = MomentumFactors()
        self.trend = TrendStrengthFactors()
        self.volume = VolumeFactors()
        self.support_resistance = SupportResistanceFactors()
        self.divergence = DivergenceFactors()
    
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有高级因子
        
        Returns:
            添加了以下列的 DataFrame:
            - atr_14, atr_28
            - hv_20 (历史波动率)
            - rsi_14, rsi_28
            - stoch_k, stoch_d
            - cci_20
            - mfi_14
            - momentum_10
            - roc_12
            - adx_14, plus_di, minus_di
            - trend_intensity_30
            - obv
            - vwap
            - volume_ratio_20
            - money_flow_20
        """
        result = df.copy()
        
        # 波动率因子
        result['atr_14'] = self.volatility.atr(df, 14)
        result['atr_28'] = self.volatility.atr(df, 28)
        result['hv_20'] = self.volatility.historical_volatility(df, 20)
        
        # 动量因子
        result['rsi_14'] = self.momentum.rsi(df, 14)
        result['rsi_28'] = self.momentum.rsi(df, 28)
        
        stoch = self.momentum.stochastic(df)
        result['stoch_k'] = stoch['stoch_k']
        result['stoch_d'] = stoch['stoch_d']
        
        result['cci_20'] = self.momentum.cci(df, 20)
        result['mfi_14'] = self.momentum.mfi(df, 14)
        result['momentum_10'] = self.momentum.momentum(df, 10)
        result['roc_12'] = self.momentum.roc(df, 12)
        
        # 趋势因子
        adx_data = self.trend.adx(df)
        result['adx_14'] = adx_data['adx']
        result['plus_di'] = adx_data['plus_di']
        result['minus_di'] = adx_data['minus_di']
        result['trend_intensity_30'] = self.trend.trend_intensity(df, 30)
        
        # 成交量因子
        result['obv'] = self.volume.obv(df)
        result['vwap'] = self.volume.vwap(df)
        result['volume_ratio_20'] = self.volume.volume_ratio(df, 20)
        result['money_flow_20'] = self.volume.money_flow(df, 20)
        
        return result


# ==================== 因子注册表 ====================
FACTOR_CALCULATORS = {
    'volatility': VolatilityFactors,
    'momentum': MomentumFactors,
    'trend': TrendStrengthFactors,
    'volume': VolumeFactors,
    'support_resistance': SupportResistanceFactors,
    'divergence': DivergenceFactors,
    'advanced': AdvancedFactorCalculator,
}


if __name__ == '__main__':
    print("=" * 60)
    print("高级因子库")
    print("=" * 60)
    print("\n因子类别:")
    for name, cls in FACTOR_CALCULATORS.items():
        print(f"  - {name}: {cls.__name__}")
    print("\n使用示例:")
    print("  from factors.advanced_factors import AdvancedFactorCalculator")
    print("  calc = AdvancedFactorCalculator()")
    print("  df_with_factors = calc.calculate_all(df)")
