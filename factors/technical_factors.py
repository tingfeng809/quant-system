# -*- coding: utf-8 -*-
"""
技术因子计算模块
⚠️ 所有计算基于真实行情数据
"""

import pandas as pd
import numpy as np
import talib
from typing import List, Dict


class TechnicalFactors:
    """技术因子计算器"""
    
    def __init__(self):
        pass
    
    # ==================== 趋势类因子 ====================
    def calculate_ma(self, df: pd.DataFrame, windows: List[int] = [5, 10, 20, 60]) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: 包含 close 列的 DataFrame
            windows: 均线周期列表
        
        Returns:
            DataFrame: 添加均线列
        """
        df = df.copy()
        for window in windows:
            df[f'ma{window}'] = talib.SMA(df['close'].values, timeperiod=window)
        return df
    
    def calculate_ema(self, df: pd.DataFrame, windows: List[int] = [12, 26]) -> pd.DataFrame:
        """计算指数移动平均"""
        df = df.copy()
        for window in windows:
            df[f'ema{window}'] = talib.EMA(df['close'].values, timeperiod=window)
        return df
    
    def calculate_macd(self, df: pd.DataFrame, fast=12, slow=26, signal=9) -> pd.DataFrame:
        """
        计算 MACD
        
        Returns:
            DataFrame: 添加 MACD 相关列
        """
        df = df.copy()
        df['macd_dif'], df['macd_dea'], df['macd'] = talib.MACD(
            df['close'].values, fastperiod=fast, slowperiod=slow, signalperiod=signal
        )
        return df
    
    def calculate_bollinger(self, df: pd.DataFrame, period=20, std_dev=2) -> pd.DataFrame:
        """
        计算布林带
        
        Returns:
            DataFrame: 添加布林带列
        """
        df = df.copy()
        df['boll_upper'], df['boll_middle'], df['boll_lower'] = talib.BBANDS(
            df['close'].values, timeperiod=period, nbdevup=std_dev, nbdevdn=std_dev
        )
        # 布林带宽度
        df['boll_width'] = (df['boll_upper'] - df['boll_lower']) / df['boll_middle']
        # 价格位置
        df['boll_position'] = (df['close'] - df['boll_lower']) / (df['boll_upper'] - df['boll_lower'])
        return df
    
    # ==================== 动量类因子 ====================
    def calculate_rsi(self, df: pd.DataFrame, windows: List[int] = [6, 12, 24]) -> pd.DataFrame:
        """计算 RSI"""
        df = df.copy()
        for window in windows:
            df[f'rsi{window}'] = talib.RSI(df['close'].values, timeperiod=window)
        return df
    
    def calculate_kdj(self, df: pd.DataFrame, n=9, m1=3, m2=3) -> pd.DataFrame:
        """
        计算 KDJ
        
        Returns:
            DataFrame: 添加 KDJ 列
        """
        df = df.copy()
        df['kdj_k'], df['kdj_d'] = talib.STOCH(
            df['high'].values, df['low'].values, df['close'].values,
            fastk_period=n, slowk_period=m1, slowk_matype=0,
            slowd_period=m2, slowd_matype=0
        )
        df['kdj_j'] = 3 * df['kdj_k'] - 2 * df['kdj_d']
        return df
    
    def calculate_wmr(self, df: pd.DataFrame, windows: List[int] = [10, 20]) -> pd.DataFrame:
        """计算威廉指标"""
        df = df.copy()
        for window in windows:
            df[f'wmr{window}'] = talib.WILLR(
                df['high'].values, df['low'].values, df['close'].values, timeperiod=window
            )
        return df
    
    def calculate_momentum(self, df: pd.DataFrame, windows: List[int] = [5, 10, 20]) -> pd.DataFrame:
        """
        计算动量因子
        
        Momentum = (当前价格 - N 日前价格) / N 日前价格
        """
        df = df.copy()
        for window in windows:
            df[f'momentum_{window}d'] = (df['close'] - df['close'].shift(window)) / df['close'].shift(window)
        return df
    
    # ==================== 波动率类因子 ====================
    def calculate_atr(self, df: pd.DataFrame, windows: List[int] = [14, 20]) -> pd.DataFrame:
        """计算 ATR (平均真实波幅)"""
        df = df.copy()
        for window in windows:
            df[f'atr{window}'] = talib.ATR(df['high'].values, df['low'].values, df['close'].values, timeperiod=window)
        return df
    
    def calculate_volatility(self, df: pd.DataFrame, windows: List[int] = [20, 60]) -> pd.DataFrame:
        """
        计算波动率 (收益率标准差)
        """
        df = df.copy()
        df['returns'] = df['close'].pct_change()
        for window in windows:
            df[f'volatility_{window}d'] = df['returns'].rolling(window).std()
        return df
    
    # ==================== 成交量类因子 ====================
    def calculate_volume_ma(self, df: pd.DataFrame, windows: List[int] = [5, 10, 20]) -> pd.DataFrame:
        """计算成交量均线"""
        df = df.copy()
        for window in windows:
            df[f'vol_ma{window}'] = talib.SMA(df['vol'].values, timeperiod=window)
        return df
    
    def calculate_obv(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算 OBV (能量潮)"""
        df = df.copy()
        df['obv'] = talib.OBV(df['close'].values, df['vol'].values)
        return df
    
    def calculate_vr(self, df: pd.DataFrame, period=26) -> pd.DataFrame:
        """计算 VR (成交量比率) - 手动实现"""
        df = df.copy()
        # VR = (上涨日成交量之和 + 0.5*平盘日成交量之和) / (下跌日成交量之和 + 0.5*平盘日成交量之和) * 100
        df['returns'] = df['close'].pct_change()
        up_vol = df.loc[df['returns'] > 0, 'vol'].rolling(period).sum()
        down_vol = df.loc[df['returns'] < 0, 'vol'].rolling(period).sum()
        flat_vol = df.loc[df['returns'] == 0, 'vol'].rolling(period).sum()
        df['vr'] = (up_vol + 0.5 * flat_vol) / (down_vol + 0.5 * flat_vol + 1) * 100
        return df
    
    # ==================== 综合因子计算 ====================
    def calculate_all(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有技术因子
        
        Args:
            df: 包含 OHLCV 数据的 DataFrame
        
        Returns:
            DataFrame: 添加所有技术因子
        """
        # 确保数据按日期排序
        df = df.sort_values('trade_date').reset_index(drop=True)
        
        # 趋势类
        df = self.calculate_ma(df, [5, 10, 20, 60])
        df = self.calculate_ema(df, [12, 26])
        df = self.calculate_macd(df)
        df = self.calculate_bollinger(df)
        
        # 动量类
        df = self.calculate_rsi(df, [6, 12, 24])
        df = self.calculate_kdj(df)
        df = self.calculate_wmr(df, [10, 20])
        df = self.calculate_momentum(df, [5, 10, 20])
        
        # 波动率类
        df = self.calculate_atr(df, [14, 20])
        df = self.calculate_volatility(df, [20, 60])
        
        # 成交量类
        df = self.calculate_volume_ma(df, [5, 10, 20])
        df = self.calculate_obv(df)
        df = self.calculate_vr(df)
        
        return df
    
    # ==================== 因子标准化 ====================
    def normalize_factors(self, df: pd.DataFrame, factor_columns: List[str], 
                          window: int = 252) -> pd.DataFrame:
        """
        因子标准化 (Z-Score)
        
        Args:
            df: 包含因子值的 DataFrame
            factor_columns: 需要标准化的因子列
            window: 滚动窗口 (默认 252 交易日)
        
        Returns:
            DataFrame: 标准化后的因子
        """
        df = df.copy()
        for col in factor_columns:
            if col in df.columns:
                rolling_mean = df[col].rolling(window=window).mean()
                rolling_std = df[col].rolling(window=window).std()
                df[f'{col}_zscore'] = (df[col] - rolling_mean) / rolling_std
        return df
    
    # ==================== 因子 IC 计算 ====================
    def calculate_ic(self, factor_df: pd.DataFrame, return_df: pd.DataFrame, 
                     method: str = 'rank') -> float:
        """
        计算因子 IC (信息系数)
        
        Args:
            factor_df: 因子值 (index=日期)
            return_df: 未来收益率 (index=日期)
            method: 'rank' 或 'normal'
        
        Returns:
            float: IC 值
        """
        # 对齐日期
        common_idx = factor_df.index.intersection(return_df.index)
        factors = factor_df.loc[common_idx].values.flatten()
        returns = return_df.loc[common_idx].values.flatten()
        
        # 去除 NaN
        mask = ~(np.isnan(factors) | np.isnan(returns))
        factors = factors[mask]
        returns = returns[mask]
        
        if len(factors) < 10:
            return np.nan
        
        if method == 'rank':
            # Rank IC
            from scipy.stats import spearmanr
            ic, _ = spearmanr(factors, returns)
        else:
            # Normal IC
            from scipy.stats import pearsonr
            ic, _ = pearsonr(factors, returns)
        
        return ic


# ==================== 测试函数 ====================
def test_technical_factors():
    """测试技术因子计算"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from data.data_loader import DataLoader
    
    print("=" * 60)
    print("技术因子计算测试")
    print("=" * 60)
    
    # 加载数据
    loader = DataLoader()
    df = loader.get_daily_data('000001.SZ', start_date='20240101')
    print(f"\n加载数据：{len(df)} 条")
    
    if len(df) < 60:
        print("❌ 数据不足，无法计算因子")
        return
    
    # 计算因子
    calculator = TechnicalFactors()
    df_with_factors = calculator.calculate_all(df)
    
    # 检查因子列
    factor_cols = [col for col in df_with_factors.columns if col not in df.columns]
    print(f"\n计算因子数量：{len(factor_cols)}")
    print(f"因子列表：{factor_cols[:10]}...")
    
    # 显示最新数据
    print("\n最新因子值:")
    latest = df_with_factors.iloc[-1]
    print(f"  MA5: {latest['ma5']:.2f}, MA20: {latest['ma20']:.2f}")
    print(f"  MACD: {latest['macd']:.4f}")
    print(f"  RSI12: {latest['rsi12']:.2f}")
    print(f"  KDJ_K: {latest['kdj_k']:.2f}, KDJ_D: {latest['kdj_d']:.2f}")
    
    print("\n✅ 技术因子计算测试完成！")


if __name__ == '__main__':
    test_technical_factors()
