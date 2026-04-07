# -*- coding: utf-8 -*-
"""
资金流因子计算模块
基于 Tushare 真实资金流数据
"""

import pandas as pd
import numpy as np
from typing import List, Dict


class MoneyflowFactors:
    """资金流因子计算器"""
    
    def __init__(self):
        pass
    
    # ==================== 基础资金流因子 ====================
    def calculate_net_inflow(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算净流入指标
        
        Args:
            df: 包含资金流数据的 DataFrame (来自 Tushare moneyflow 接口)
        
        Returns:
            DataFrame: 添加净流入相关因子
        """
        df = df.copy()
        
        # 净流入额 (万元)
        if 'buy_sm_amount' in df.columns:
            df['net_inflow'] = (
                df['buy_sm_amount'] + df['buy_md_amount'] + 
                df['buy_lg_amount'] + df['buy_elg_amount'] -
                df['sell_sm_amount'] - df['sell_md_amount'] - 
                df['sell_lg_amount'] - df['sell_elg_amount']
            )
        
        # 净流入率 (净流入/成交额)
        if 'amount' in df.columns and 'net_inflow' in df.columns:
            df['net_inflow_rate'] = df['net_inflow'] * 10000 / df['amount'] * 100  # 百分比
        
        return df
    
    def calculate_main_force(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算主力资金指标
        
        主力 = 大单 + 超大单
        """
        df = df.copy()
        
        # 主力净流入
        if 'buy_lg_amount' in df.columns:
            df['main_inflow'] = (
                df['buy_lg_amount'] + df['buy_elg_amount'] -
                df['sell_lg_amount'] - df['sell_elg_amount']
            )
            
            # 主力净流入率
            if 'amount' in df.columns:
                df['main_inflow_rate'] = df['main_inflow'] * 10000 / df['amount'] * 100
        
        # 主力/散户比
        if 'buy_sm_amount' in df.columns and 'main_inflow' in df.columns:
            retail_inflow = df['buy_sm_amount'] - df['sell_sm_amount']
            df['main_retail_ratio'] = df['main_inflow'] / (retail_inflow.abs() + 1)
        
        return df
    
    # ==================== 资金流趋势因子 ====================
    def calculate_flow_trend(self, df: pd.DataFrame, windows: List[int] = [3, 5, 10]) -> pd.DataFrame:
        """
        计算资金流趋势
        
        Args:
            df: 包含 net_inflow 或 main_inflow 的 DataFrame
            windows: 统计周期
        """
        df = df.copy()
        
        flow_col = 'main_inflow' if 'main_inflow' in df.columns else 'net_inflow'
        
        if flow_col not in df.columns:
            return df
        
        for window in windows:
            # N 日累计净流入
            df[f'flow_sum_{window}d'] = df[flow_col].rolling(window).sum()
            
            # N 日净流入为正的天数
            df[f'flow_positive_{window}d'] = (df[flow_col] > 0).rolling(window).sum()
            
            # N 日净流入为正的比例
            df[f'flow_positive_ratio_{window}d'] = df[f'flow_positive_{window}d'] / window
            
            # 净流入均线
            df[f'flow_ma{window}'] = df[flow_col].rolling(window).mean()
        
        return df
    
    # ==================== 大单因子 ====================
    def calculate_large_order(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算大单相关因子
        """
        df = df.copy()
        
        # 大单买入占比
        if 'buy_sm_amount' in df.columns and 'amount' in df.columns:
            large_buy = df['buy_lg_amount'] + df['buy_elg_amount']
            df['large_buy_ratio'] = large_buy * 10000 / df['amount'] * 100
            
            large_sell = df['sell_lg_amount'] + df['sell_elg_amount']
            df['large_sell_ratio'] = large_sell * 10000 / df['amount'] * 100
            
            # 大单净买入占比
            df['large_net_ratio'] = df['large_buy_ratio'] - df['large_sell_ratio']
        
        # 超大单/大单比
        if 'buy_elg_amount' in df.columns and 'buy_lg_amount' in df.columns:
            df['elg_lg_ratio'] = df['buy_elg_amount'] / (df['buy_lg_amount'] + 0.01)
        
        return df
    
    # ==================== 资金流与价格背离因子 ====================
    def calculate_divergence(self, price_df: pd.DataFrame, flow_df: pd.DataFrame) -> pd.DataFrame:
        """
        计算资金流与价格背离
        
        Args:
            price_df: 价格数据 (包含 close)
            flow_df: 资金流数据 (包含 net_inflow 或 main_inflow)
        
        Returns:
            DataFrame: 背离信号
        """
        # 合并数据
        df = price_df.merge(flow_df[['trade_date', 'net_inflow', 'main_inflow']], 
                           on='trade_date', how='inner')
        df = df.sort_values('trade_date').reset_index(drop=True)
        
        # 价格创新高但资金流未创新高 = 顶背离
        df['price_high_5d'] = df['close'].rolling(5).max()
        df['price_low_5d'] = df['close'].rolling(5).min()
        
        flow_col = 'main_inflow' if 'main_inflow' in df.columns else 'net_inflow'
        df['flow_high_5d'] = df[flow_col].rolling(5).max()
        df['flow_low_5d'] = df[flow_col].rolling(5).min()
        
        # 顶背离：价格新高，资金流未新高
        df['top_divergence'] = (
            (df['close'] == df['price_high_5d']) & 
            (df[flow_col] < df['flow_high_5d'])
        ).astype(int)
        
        # 底背离：价格新低，资金流未新低
        df['bottom_divergence'] = (
            (df['close'] == df['price_low_5d']) & 
            (df[flow_col] > df['flow_low_5d'])
        ).astype(int)
        
        return df
    
    # ==================== 综合资金流评分 ====================
    def calculate_flow_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算综合资金流评分 (0-100)
        
        评分维度:
        - 当日净流入方向 (+20/-20)
        - 5 日累计净流入 (+20/-20)
        - 10 日累计净流入 (+20/-20)
        - 主力净流入率 (+20/-20)
        - 资金流趋势 (+20/-20)
        """
        df = df.copy()
        df['flow_score'] = 50  # 基准分
        
        flow_col = 'main_inflow' if 'main_inflow' in df.columns else 'net_inflow'
        
        if flow_col not in df.columns:
            return df
        
        # 当日净流入
        df.loc[df[flow_col] > 0, 'flow_score'] += 20
        df.loc[df[flow_col] <= 0, 'flow_score'] -= 20
        
        # 5 日累计
        if 'flow_sum_5d' in df.columns:
            df.loc[df['flow_sum_5d'] > 0, 'flow_score'] += 20
            df.loc[df['flow_sum_5d'] <= 0, 'flow_score'] -= 20
        
        # 10 日累计
        if 'flow_sum_10d' in df.columns:
            df.loc[df['flow_sum_10d'] > 0, 'flow_score'] += 20
            df.loc[df['flow_sum_10d'] <= 0, 'flow_score'] -= 20
        
        # 主力净流入率
        if 'main_inflow_rate' in df.columns:
            df.loc[df['main_inflow_rate'] > 5, 'flow_score'] += 20
            df.loc[df['main_inflow_rate'] < -5, 'flow_score'] -= 20
        
        # 资金流趋势
        if 'flow_positive_ratio_5d' in df.columns:
            df.loc[df['flow_positive_ratio_5d'] > 0.6, 'flow_score'] += 20
            df.loc[df['flow_positive_ratio_5d'] < 0.4, 'flow_score'] -= 20
        
        # 限制在 0-100
        df['flow_score'] = df['flow_score'].clip(0, 100)
        
        return df
    
    # ==================== 全部因子计算 ====================
    def calculate_all(self, flow_df: pd.DataFrame, price_df: pd.DataFrame = None) -> pd.DataFrame:
        """
        计算所有资金流因子
        
        Args:
            flow_df: 资金流数据 (来自 Tushare moneyflow)
            price_df: 可选的价格数据，用于计算背离
        
        Returns:
            DataFrame: 包含所有资金流因子
        """
        # 基础因子
        df = self.calculate_net_inflow(flow_df)
        df = self.calculate_main_force(df)
        df = self.calculate_flow_trend(df)
        df = self.calculate_large_order(df)
        df = self.calculate_flow_score(df)
        
        # 背离因子 (需要价格数据)
        if price_df is not None:
            df = self.calculate_divergence(price_df, df)
        
        return df


# ==================== 测试函数 ====================
def test_moneyflow_factors():
    """测试资金流因子计算"""
    import sys
    import os
    sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
    from data.data_loader import DataLoader
    
    print("=" * 60)
    print("资金流因子计算测试")
    print("=" * 60)
    
    # 加载数据
    loader = DataLoader()
    
    print("\n1. 加载资金流数据 (000001.SZ)...")
    flow_df = loader.get_moneyflow('000001.SZ')
    print(f"   数据条数：{len(flow_df)}")
    
    if len(flow_df) < 10:
        print("❌ 数据不足")
        return
    
    print("\n2. 加载价格数据...")
    price_df = loader.get_daily_data('000001.SZ')
    print(f"   数据条数：{len(price_df)}")
    
    # 计算因子
    print("\n3. 计算资金流因子...")
    calculator = MoneyflowFactors()
    df_with_factors = calculator.calculate_all(flow_df, price_df)
    
    # 检查因子列
    factor_cols = [col for col in df_with_factors.columns 
                   if col not in flow_df.columns and col not in price_df.columns]
    print(f"   计算因子数量：{len(factor_cols)}")
    
    # 显示最新数据
    print("\n4. 最新资金流指标:")
    latest = df_with_factors.iloc[-1]
    if 'net_inflow' in latest:
        print(f"   净流入：{latest['net_inflow']:.2f} 万元")
    if 'main_inflow' in latest:
        print(f"   主力净流入：{latest['main_inflow']:.2f} 万元")
    if 'main_inflow_rate' in latest:
        print(f"   主力净流入率：{latest['main_inflow_rate']:.2f}%")
    if 'flow_score' in latest:
        print(f"   资金流评分：{latest['flow_score']:.0f}")
    if 'flow_sum_5d' in latest:
        print(f"   5 日累计净流入：{latest['flow_sum_5d']:.2f} 万元")
    
    print("\n✅ 资金流因子计算测试完成！")


if __name__ == '__main__':
    test_moneyflow_factors()
