# -*- coding: utf-8 -*-
"""
数据加载模块
⚠️ 所有数据必须来自 Tushare 真实数据，禁止模拟/随机/测试数据
"""

import tushare as ts
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

# 导入配置
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from config.settings import TUSHARE_TOKEN, DATA_DIR, logger

class DataLoader:
    """数据加载器 - 基于 Tushare 真实数据"""
    
    def __init__(self, token=TUSHARE_TOKEN):
        ts.set_token(token)
        self.pro = ts.pro_api()
        self.cache_dir = os.path.join(DATA_DIR, 'cache')
        os.makedirs(self.cache_dir, exist_ok=True)
    
    # ==================== 股票列表 ====================
    def get_stock_list(self, exchange='', list_status='L'):
        """
        获取股票列表
        
        Args:
            exchange: 交易所 (SH/SZ/BJ)，空字符串表示全部
            list_status: 上市状态 (L 上市/D 退市/P 暂停)
        
        Returns:
            DataFrame: 股票列表
        """
        cache_file = os.path.join(self.cache_dir, f'stock_list_{exchange}_{list_status}.pkl')
        
        # 尝试读取缓存（缓存 7 天）
        if os.path.exists(cache_file):
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            if datetime.now() - cache_time < timedelta(days=7):
                logger.info(f"从缓存加载股票列表：{exchange}")
                return pd.read_pickle(cache_file)
        
        try:
            df = self.pro.stock_basic(
                exchange=exchange,
                list_status=list_status,
                fields='ts_code,symbol,name,area,industry,market,list_date,act_shares,total_shares'
            )
            df.to_pickle(cache_file)
            logger.info(f"获取股票列表成功：{len(df)} 只股票")
            return df
        except Exception as e:
            logger.error(f"获取股票列表失败：{e}")
            return pd.DataFrame()
    
    # ==================== 日线行情 ====================
    def get_daily_data(self, ts_code, start_date=None, end_date=None, adj='qfq'):
        """
        获取日线行情数据
        
        Args:
            ts_code: 股票代码 (000001.SZ)
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            adj: 复权类型 (None 不复权/qfq 前复权/hfq 后复权)
        
        Returns:
            DataFrame: 日线数据
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        cache_file = os.path.join(self.cache_dir, f'{ts_code}_{start_date}_{end_date}_{adj}.pkl')
        
        # 优化 1: 增强缓存策略 - 检查缓存有效性
        if os.path.exists(cache_file):
            cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
            # 缓存 1 小时（盘中）或 24 小时（盘后）
            cache_ttl = timedelta(hours=1) if datetime.now().hour < 15 else timedelta(days=1)
            if datetime.now() - cache_time < cache_ttl:
                logger.debug(f"从缓存加载 {ts_code} 日线数据")
                cached_df = pd.read_pickle(cache_file)
                # 验证缓存数据完整性
                if len(cached_df) > 0 and 'close' in cached_df.columns:
                    return cached_df
                logger.warning(f"缓存数据损坏，重新获取 {ts_code}")
        
        try:
            if adj is None:
                # 不复权
                df = self.pro.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date,
                    fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount'
                )
            else:
                # 获取复权因子
                adj_factor = self.pro.adj_factor(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # 获取日线
                df = self.pro.daily(
                    ts_code=ts_code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                # 应用复权
                if len(adj_factor) > 0 and len(df) > 0:
                    df = df.merge(adj_factor[['ts_code', 'trade_date', 'adj_factor']], 
                                  on=['ts_code', 'trade_date'], how='left')
                    df['open'] = df['open'] * df['adj_factor']
                    df['high'] = df['high'] * df['adj_factor']
                    df['low'] = df['low'] * df['adj_factor']
                    df['close'] = df['close'] * df['adj_factor']
                    df['pre_close'] = df['pre_close'] * df['adj_factor']
                    df = df.drop('adj_factor', axis=1)
            
            if len(df) > 0:
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
                df = df.sort_values('trade_date').reset_index(drop=True)
                
                # 增加数据验证：检查字段完整性
                required_cols = ['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol', 'amount']
                missing_cols = [c for c in required_cols if c not in df.columns]
                if missing_cols:
                    logger.error(f"{ts_code} 数据缺少字段：{missing_cols}")
                    return pd.DataFrame()
                
                # 验证数据质量：检查异常值
                if (df['close'] <= 0).any():
                    logger.error(f"{ts_code} 数据异常：存在零或负收盘价")
                    return pd.DataFrame()
                
                # 验证数据连续性
                if len(df) > 1:
                    date_gap = (df['trade_date'].diff().dropna().dt.days).max()
                    if date_gap > 10:
                        logger.warning(f"{ts_code} 数据存在超过 10 天的间隔")
                
                df.to_pickle(cache_file)
                logger.info(f"获取 {ts_code} 日线数据：{len(df)} 条，验证通过")
            
            return df
        except Exception as e:
            logger.error(f"获取 {ts_code} 日线数据失败：{e}")
            return pd.DataFrame()
    
    # ==================== 分钟级数据 ====================
    def get_min_bar(self, ts_code, trade_date=None, min_type='5min'):
        """
        获取分钟级数据
        
        Args:
            ts_code: 股票代码
            trade_date: 交易日期
            min_type: 分钟类型 (1min/5min/15min/30min/60min)
        
        Returns:
            DataFrame: 分钟数据
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.min_bar(
                ts_code=ts_code,
                trade_date=trade_date,
                min_type=min_type
            )
            logger.debug(f"获取 {ts_code} {min_type} 数据：{len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取分钟数据失败：{e}")
            return pd.DataFrame()
    
    # ==================== 财务数据 ====================
    def get_fina_indicator(self, ts_code, period=None):
        """
        获取财务指标
        
        Args:
            ts_code: 股票代码
            period: 报告期 (YYYYMMDD)
        
        Returns:
            DataFrame: 财务指标
        """
        try:
            if period is None:
                # 获取最近 4 个报告期
                df = self.pro.fina_indicator(ts_code=ts_code)
            else:
                df = self.pro.fina_indicator(ts_code=ts_code, period=period)
            
            logger.debug(f"获取 {ts_code} 财务指标：{len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取财务指标失败：{e}")
            return pd.DataFrame()
    
    def get_income(self, ts_code, period=None):
        """获取利润表"""
        try:
            df = self.pro.income(ts_code=ts_code, period=period)
            return df
        except Exception as e:
            logger.error(f"获取利润表失败：{e}")
            return pd.DataFrame()
    
    def get_balance(self, ts_code, period=None):
        """获取资产负债表"""
        try:
            df = self.pro.balance(ts_code=ts_code, period=period)
            return df
        except Exception as e:
            logger.error(f"获取资产负债表失败：{e}")
            return pd.DataFrame()
    
    def get_cashflow(self, ts_code, period=None):
        """获取现金流量表"""
        try:
            df = self.pro.cashflow(ts_code=ts_code, period=period)
            return df
        except Exception as e:
            logger.error(f"获取现金流量表失败：{e}")
            return pd.DataFrame()
    
    # ==================== 资金流数据 ====================
    def get_moneyflow(self, ts_code, start_date=None, end_date=None):
        """
        获取资金流数据
        
        Args:
            ts_code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            DataFrame: 资金流数据
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        
        try:
            df = self.pro.moneyflow(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            if len(df) > 0:
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            logger.debug(f"获取 {ts_code} 资金流数据：{len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取资金流数据失败：{e}")
            return pd.DataFrame()
    
    # ==================== 指数数据 ====================
    def get_index_daily(self, ts_code, start_date=None, end_date=None):
        """
        获取指数行情
        
        Args:
            ts_code: 指数代码 (000001.SH - 上证指数)
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            DataFrame: 指数行情
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        
        try:
            df = self.pro.index_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            if len(df) > 0:
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            logger.debug(f"获取 {ts_code} 指数数据：{len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取指数数据失败：{e}")
            return pd.DataFrame()
    
    # ==================== 涨跌停数据 ====================
    def get_limit_list(self, trade_date=None):
        """
        获取涨跌停列表
        
        Args:
            trade_date: 交易日期
        
        Returns:
            DataFrame: 涨跌停股票
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.limit_list(trade_date=trade_date)
            logger.info(f"获取 {trade_date} 涨跌停数据：{len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取涨跌停数据失败：{e}")
            return pd.DataFrame()
    
    # ==================== 龙虎榜数据 ====================
    def get_top_list(self, trade_date=None):
        """
        获取龙虎榜数据
        
        Args:
            trade_date: 交易日期
        
        Returns:
            DataFrame: 龙虎榜数据
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        try:
            df = self.pro.top_list(trade_date=trade_date)
            logger.info(f"获取 {trade_date} 龙虎榜数据：{len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败：{e}")
            return pd.DataFrame()
    
    # ==================== 沪深股通数据 ====================
    def get_hs_const(self, hs='H'):
        """
        获取沪深股通成分股
        
        Args:
            hs: H 沪股通/S 深股通
        
        Returns:
            DataFrame: 成分股列表
        """
        try:
            df = self.pro.hs_const(hs=hs)
            logger.info(f"获取{'沪' if hs == 'H' else '深'}股通成分股：{len(df)} 条")
            return df
        except Exception as e:
            logger.error(f"获取沪深股通数据失败：{e}")
            return pd.DataFrame()
    
    def get_hs_daily(self, ts_code, start_date=None, end_date=None):
        """获取沪深股通日线"""
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        
        try:
            df = self.pro.hs_daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date
            )
            if len(df) > 0:
                df['trade_date'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
            return df
        except Exception as e:
            logger.error(f"获取沪深股通日线失败：{e}")
            return pd.DataFrame()


# ==================== 测试函数 ====================
def test_data_loader():
    """测试数据加载器"""
    loader = DataLoader()
    
    print("=" * 60)
    print("数据加载器测试")
    print("=" * 60)
    
    # 测试股票列表
    print("\n1. 获取股票列表...")
    stocks = loader.get_stock_list()
    print(f"   股票总数：{len(stocks)}")
    if len(stocks) > 0:
        print(f"   示例：{stocks.iloc[0]['ts_code']} - {stocks.iloc[0]['name']}")
    
    # 测试日线数据
    print("\n2. 获取日线数据 (000001.SZ)...")
    daily = loader.get_daily_data('000001.SZ')
    print(f"   数据条数：{len(daily)}")
    if len(daily) > 0:
        print(f"   最新收盘价：{daily.iloc[-1]['close']:.2f}")
    
    # 测试财务数据
    print("\n3. 获取财务指标 (000001.SZ)...")
    fina = loader.get_fina_indicator('000001.SZ')
    print(f"   报告期数量：{len(fina)}")
    
    # 测试资金流
    print("\n4. 获取资金流数据 (000001.SZ)...")
    moneyflow = loader.get_moneyflow('000001.SZ')
    print(f"   数据条数：{len(moneyflow)}")
    
    # 测试指数
    print("\n5. 获取上证指数数据...")
    index = loader.get_index_daily('000001.SH')
    print(f"   数据条数：{len(index)}")
    
    print("\n✅ 数据加载器测试完成！")


if __name__ == '__main__':
    test_data_loader()
