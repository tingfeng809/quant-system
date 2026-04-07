#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 Tushare 批量拉取 A 股数据到本地
⚠️ 所有数据来自真实市场数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from data.data_loader import DataLoader
from config.settings import DATA_DIR, logger
import pandas as pd
from datetime import datetime, timedelta

# ==================== 配置 ====================
# 数据保存目录
DATA_BASE = os.path.join(DATA_DIR, 'stocks')
os.makedirs(DATA_BASE, exist_ok=True)

# 默认拉取参数
DEFAULT_START_DATE = (datetime.now() - timedelta(days=365*3)).strftime('%Y%m%d')  # 3 年数据
DEFAULT_END_DATE = datetime.now().strftime('%Y%m%d')

# 股票池配置
STOCK_POOL_CONFIG = {
    'all': True,  # 拉取全部股票
    'codes': [],  # 自定义股票列表，如 ['000001.SZ', '600519.SH']
    'exclude_st': True,  # 排除 ST 股票
    'exclude_kcb': False,  # 排除科创板
    'exclude_cyb': False,  # 排除创业板
}


# ==================== 数据拉取函数 ====================

def fetch_stock_list():
    """获取股票列表"""
    print("=" * 60)
    print("1. 获取股票列表...")
    print("=" * 60)
    
    loader = DataLoader()
    stocks = loader.get_stock_list()
    
    # 筛选
    if STOCK_POOL_CONFIG['exclude_st']:
        stocks = stocks[~stocks['name'].str.contains('ST', na=False)]
        print(f"   排除 ST 股票，剩余：{len(stocks)} 只")
    
    if STOCK_POOL_CONFIG['exclude_kcb']:
        stocks = stocks[stocks['market'] != 'STAR']
        print(f"   排除科创板，剩余：{len(stocks)} 只")
    
    if STOCK_POOL_CONFIG['exclude_cyb']:
        stocks = stocks[stocks['market'] != 'ChiNext']
        print(f"   排除创业板，剩余：{len(stocks)} 只")
    
    # 保存股票列表
    stocks_file = os.path.join(DATA_BASE, 'stock_list.csv')
    stocks.to_csv(stocks_file, index=False, encoding='utf-8-sig')
    print(f"   ✅ 股票列表已保存：{stocks_file}")
    print(f"   总计：{len(stocks)} 只股票")
    
    return stocks


def fetch_daily_data(stocks, start_date=DEFAULT_START_DATE, end_date=DEFAULT_END_DATE):
    """批量获取日线数据"""
    print("\n" + "=" * 60)
    print("2. 批量获取日线数据...")
    print("=" * 60)
    print(f"   时间范围：{start_date} - {end_date}")
    
    loader = DataLoader()
    
    # 确定股票池
    if STOCK_POOL_CONFIG['all']:
        codes = stocks['ts_code'].tolist()
    elif STOCK_POOL_CONFIG['codes']:
        codes = STOCK_POOL_CONFIG['codes']
    else:
        codes = stocks['ts_code'].head(100).tolist()  # 默认前 100 只
    
    print(f"   股票数量：{len(codes)}")
    
    # 批量拉取
    success_count = 0
    error_count = 0
    
    for i, code in enumerate(codes):
        try:
            # 进度显示
            if (i + 1) % 100 == 0 or i == 0:
                print(f"   进度：{i+1}/{len(codes)} ({(i+1)/len(codes)*100:.1f}%)")
            
            # 获取数据
            df = loader.get_daily_data(code, start_date=start_date, end_date=end_date, adj='qfq')
            
            if len(df) > 0:
                # 保存为 CSV
                code_safe = code.replace('.', '_')
                code_dir = os.path.join(DATA_BASE, 'daily')
                os.makedirs(code_dir, exist_ok=True)
                
                file_path = os.path.join(code_dir, f'{code_safe}.csv')
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                success_count += 1
            else:
                error_count += 1
                
        except Exception as e:
            logger.error(f"获取 {code} 失败：{e}")
            error_count += 1
    
    print(f"\n   ✅ 完成：成功 {success_count} 只，失败 {error_count} 只")
    print(f"   数据目录：{DATA_BASE}/daily/")


def fetch_index_data(start_date=DEFAULT_START_DATE, end_date=DEFAULT_END_DATE):
    """获取指数数据"""
    print("\n" + "=" * 60)
    print("3. 获取指数数据...")
    print("=" * 60)
    
    loader = DataLoader()
    
    # 主要指数
    indices = {
        '000001.SH': '上证指数',
        '399001.SZ': '深证成指',
        '399006.SZ': '创业板指',
        '000300.SH': '沪深 300',
        '000016.SH': '上证 50',
        '000905.SH': '中证 500',
    }
    
    index_dir = os.path.join(DATA_BASE, 'index')
    os.makedirs(index_dir, exist_ok=True)
    
    for ts_code, name in indices.items():
        try:
            print(f"   获取 {name} ({ts_code})...")
            df = loader.get_index_daily(ts_code, start_date=start_date, end_date=end_date)
            
            if len(df) > 0:
                file_path = os.path.join(index_dir, f'{ts_code.replace(".", "_")}.csv')
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                print(f"   ✅ {name}: {len(df)} 条")
        except Exception as e:
            logger.error(f"获取 {ts_code} 失败：{e}")
    
    print(f"   指数目录：{index_dir}/")


def fetch_moneyflow_data(stocks, start_date=DEFAULT_START_DATE, end_date=DEFAULT_END_DATE):
    """获取资金流数据"""
    print("\n" + "=" * 60)
    print("4. 获取资金流数据...")
    print("=" * 60)
    
    loader = DataLoader()
    
    # 默认拉取前 500 只股票
    codes = stocks['ts_code'].head(500).tolist()
    
    moneyflow_dir = os.path.join(DATA_BASE, 'moneyflow')
    os.makedirs(moneyflow_dir, exist_ok=True)
    
    success_count = 0
    for i, code in enumerate(codes):
        try:
            if (i + 1) % 100 == 0 or i == 0:
                print(f"   进度：{i+1}/{len(codes)}")
            
            df = loader.get_moneyflow(code, start_date=start_date, end_date=end_date)
            
            if len(df) > 0:
                code_safe = code.replace('.', '_')
                file_path = os.path.join(moneyflow_dir, f'{code_safe}.csv')
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                success_count += 1
        except Exception as e:
            logger.error(f"获取 {code} 资金流失败：{e}")
    
    print(f"   ✅ 完成：{success_count}/{len(codes)}")
    print(f"   资金流目录：{moneyflow_dir}/")


def fetch_fina_data(stocks):
    """获取财务数据"""
    print("\n" + "=" * 60)
    print("5. 获取财务数据...")
    print("=" * 60)
    
    loader = DataLoader()
    
    # 默认拉取前 200 只股票
    codes = stocks['ts_code'].head(200).tolist()
    
    fina_dir = os.path.join(DATA_BASE, 'fina')
    os.makedirs(fina_dir, exist_ok=True)
    
    success_count = 0
    for i, code in enumerate(codes):
        try:
            if (i + 1) % 50 == 0 or i == 0:
                print(f"   进度：{i+1}/{len(codes)}")
            
            df = loader.get_fina_indicator(code)
            
            if len(df) > 0:
                code_safe = code.replace('.', '_')
                file_path = os.path.join(fina_dir, f'{code_safe}.csv')
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
                success_count += 1
        except Exception as e:
            logger.error(f"获取 {code} 财务数据失败：{e}")
    
    print(f"   ✅ 完成：{success_count}/{len(codes)}")
    print(f"   财务目录：{fina_dir}/")


# ==================== 主程序 ====================

def main():
    print("\n" + "=" * 70)
    print("📊 A 股数据批量拉取工具 - 淘金者版")
    print("=" * 70)
    print(f"数据源：Tushare (8000+ 积分)")
    print(f"数据目录：{DATA_BASE}")
    print(f"时间范围：{DEFAULT_START_DATE} - {DEFAULT_END_DATE}")
    print("=" * 70)
    
    # 1. 获取股票列表
    stocks = fetch_stock_list()
    
    # 2. 获取日线数据
    fetch_daily_data(stocks)
    
    # 3. 获取指数数据
    fetch_index_data()
    
    # 4. 获取资金流数据 (可选，耗时较长)
    # fetch_moneyflow_data(stocks)
    
    # 5. 获取财务数据 (可选，耗时较长)
    # fetch_fina_data(stocks)
    
    print("\n" + "=" * 70)
    print("✅ 数据拉取完成！")
    print("=" * 70)
    print(f"\n数据目录结构:")
    print(f"  {DATA_BASE}/")
    print(f"  ├── stock_list.csv      # 股票列表")
    print(f"  ├── daily/              # 日线数据")
    print(f"  ├── index/              # 指数数据")
    print(f"  ├── moneyflow/          # 资金流数据 (可选)")
    print(f"  └── fina/               # 财务数据 (可选)")
    print("\n💡 提示：")
    print("  - 数据已缓存，后续分析会自动使用")
    print("  - 可修改 STOCK_POOL_CONFIG 自定义股票池")
    print("  - 取消注释可拉取资金流和财务数据")
    print("=" * 70)


if __name__ == '__main__':
    main()
