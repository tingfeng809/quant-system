#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股量化分析系统 - 淘金者版
⛏️ 基于真实数据，禁止模拟/随机/测试数据

作者：淘金者 (Gold Rush)
用户：听风
"""

import argparse
import sys
import os
from datetime import datetime, timedelta

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

from config.settings import logger
from data.data_loader import DataLoader
from factors.technical_factors import TechnicalFactors
from factors.moneyflow_factors import MoneyflowFactors
from backtest.engine import BacktestEngine
from strategies.example_strategies import (
    DualMAStrategy, 
    MACDStrategy, 
    MultiFactorStrategy
)


# ==================== 命令行功能 ====================

def cmd_fetch(args):
    """获取数据"""
    loader = DataLoader()
    
    if args.type == 'stock_list':
        print("获取股票列表...")
        df = loader.get_stock_list()
        print(f"共 {len(df)} 只股票")
        print(df.head())
    
    elif args.type == 'daily':
        print(f"获取 {args.code} 日线数据...")
        df = loader.get_daily_data(args.code, start_date=args.start, end_date=args.end)
        print(f"共 {len(df)} 条记录")
        print(df.tail())
    
    elif args.type == 'moneyflow':
        print(f"获取 {args.code} 资金流数据...")
        df = loader.get_moneyflow(args.code, start_date=args.start, end_date=args.end)
        print(f"共 {len(df)} 条记录")
        print(df.tail())
    
    elif args.type == 'fina':
        print(f"获取 {args.code} 财务数据...")
        df = loader.get_fina_indicator(args.code)
        print(f"共 {len(df)} 个报告期")
        print(df.head())


def cmd_analyze(args):
    """分析股票"""
    loader = DataLoader()
    tech_factor = TechnicalFactors()
    moneyflow_factor = MoneyflowFactors()
    
    print(f"\n分析股票：{args.code}")
    print("=" * 60)
    
    # 加载数据
    daily_df = loader.get_daily_data(args.code, start_date=args.start)
    moneyflow_df = loader.get_moneyflow(args.code, start_date=args.start)
    
    if len(daily_df) < 60:
        print("❌ 数据不足")
        return
    
    # 计算技术因子
    print("\n1. 计算技术因子...")
    df_with_factors = tech_factor.calculate_all(daily_df.copy())
    
    # 显示最新指标
    latest = df_with_factors.iloc[-1]
    print(f"\n最新收盘价：{latest['close']:.2f}")
    print(f"均线：MA5={latest['ma5']:.2f}, MA10={latest['ma10']:.2f}, MA20={latest['ma20']:.2f}")
    print(f"MACD: DIF={latest['macd_dif']:.4f}, DEA={latest['macd_dea']:.4f}")
    print(f"RSI: RSI6={latest['rsi6']:.2f}, RSI12={latest['rsi12']:.2f}")
    print(f"KDJ: K={latest['kdj_k']:.2f}, D={latest['kdj_d']:.2f}, J={latest['kdj_j']:.2f}")
    
    # 资金流分析
    if len(moneyflow_df) > 0:
        print("\n2. 资金流分析...")
        flow_df = moneyflow_factor.calculate_all(moneyflow_df.copy())
        flow_latest = flow_df.iloc[-1]
        
        if 'net_inflow' in flow_latest:
            print(f"当日净流入：{flow_latest['net_inflow']:.2f} 万元")
        if 'main_inflow' in flow_latest:
            print(f"主力净流入：{flow_latest['main_inflow']:.2f} 万元")
        if 'main_inflow_rate' in flow_latest:
            print(f"主力净流入率：{flow_latest['main_inflow_rate']:.2f}%")
        if 'flow_score' in flow_latest:
            print(f"资金流评分：{flow_latest['flow_score']:.0f}/100")
    
    # 买卖信号
    print("\n3. 技术信号:")
    signals = []
    
    # 均线信号
    if latest['ma5'] > latest['ma10'] > latest['ma20']:
        signals.append("✅ 均线多头排列")
    elif latest['ma5'] < latest['ma10'] < latest['ma20']:
        signals.append("❌ 均线空头排列")
    
    # MACD 信号
    if latest['macd_dif'] > latest['macd_dea']:
        signals.append("✅ MACD 金叉")
    else:
        signals.append("❌ MACD 死叉")
    
    # RSI 信号
    if latest['rsi12'] > 70:
        signals.append("⚠️ RSI 超买")
    elif latest['rsi12'] < 30:
        signals.append("✅ RSI 超卖")
    
    # KDJ 信号
    if latest['kdj_j'] > 100:
        signals.append("⚠️ KDJ 超买")
    elif latest['kdj_j'] < 0:
        signals.append("✅ KDJ 超卖")
    
    for signal in signals:
        print(f"   {signal}")
    
    # 综合判断
    buy_signals = sum(1 for s in signals if s.startswith('✅') and '超买' not in s)
    sell_signals = sum(1 for s in signals if s.startswith('❌') or '超买' in s)
    
    print(f"\n4. 综合判断:")
    print(f"   买入信号：{buy_signals} 个")
    print(f"   卖出信号：{sell_signals} 个")
    
    if buy_signals > sell_signals and buy_signals >= 2:
        print(f"   👉 建议：谨慎看多")
    elif sell_signals > buy_signals and sell_signals >= 2:
        print(f"   👉 建议：谨慎看空")
    else:
        print(f"   👉 建议：观望")


def cmd_backtest(args):
    """回测策略"""
    loader = DataLoader()
    
    print(f"\n回测策略：{args.strategy}")
    print(f"回测区间：{args.start} - {args.end}")
    print("=" * 60)
    
    # 获取股票池
    if args.codes:
        codes = args.codes.split(',')
    else:
        # 默认测试几只股票
        codes = ['000001.SZ', '600000.SH', '000002.SZ']
    
    print(f"股票池：{codes}")
    
    # 加载数据
    print("\n加载数据...")
    data = {}
    for code in codes:
        df = loader.get_daily_data(code, start_date=args.start, end_date=args.end)
        if len(df) > 0:
            data[code] = df
            print(f"  {code}: {len(df)} 条")
    
    if not data:
        print("❌ 无数据")
        return
    
    # 选择策略
    if args.strategy == 'ma':
        strategy = DualMAStrategy()
    elif args.strategy == 'macd':
        strategy = MACDStrategy()
    elif args.strategy == 'multi':
        strategy = MultiFactorStrategy()
    else:
        print(f"❌ 未知策略：{args.strategy}")
        return
    
    # 运行回测
    print(f"\n运行回测...")
    engine = BacktestEngine(initial_capital=args.capital)
    result = engine.run(strategy, data, args.start, args.end)
    
    # 输出结果
    print("\n" + "=" * 60)
    print("回测结果")
    print("=" * 60)
    print(f"初始资金：{args.capital:,.0f}")
    print(f"最终资金：{engine.daily_values[-1]:,.0f}")
    print(f"总收益率：{result.total_return*100:.2f}%")
    print(f"年化收益率：{result.annual_return*100:.2f}%")
    print(f"最大回撤：{result.max_drawdown*100:.2f}%")
    print(f"夏普比率：{result.sharpe_ratio:.2f}")
    print(f"交易次数：{result.total_trades}")
    print(f"胜率：{result.win_rate*100:.1f}%")
    print(f"盈亏比：{result.profit_factor:.2f}")


def cmd_list(args):
    """列出股票"""
    loader = DataLoader()
    
    print("获取股票列表...")
    df = loader.get_stock_list()
    
    # 筛选
    if args.market:
        df = df[df['market'] == args.market]
    if args.industry:
        df = df[df['industry'].str.contains(args.industry, na=False)]
    if args.area:
        df = df[df['area'] == args.area]
    
    print(f"\n共 {len(df)} 只股票")
    print(df[['ts_code', 'name', 'industry', 'market', 'area']].head(20))


# ==================== 主程序 ====================

def main():
    parser = argparse.ArgumentParser(description='A 股量化分析系统 - 淘金者版 ⛏️')
    subparsers = parser.add_subparsers(dest='command', help='命令')
    
    # fetch 命令
    fetch_parser = subparsers.add_parser('fetch', help='获取数据')
    fetch_parser.add_argument('type', choices=['stock_list', 'daily', 'moneyflow', 'fina'])
    fetch_parser.add_argument('--code', default='000001.SZ')
    fetch_parser.add_argument('--start', default=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'))
    fetch_parser.add_argument('--end', default=datetime.now().strftime('%Y%m%d'))
    fetch_parser.set_defaults(func=cmd_fetch)
    
    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析股票')
    analyze_parser.add_argument('code')
    analyze_parser.add_argument('--start', default=(datetime.now() - timedelta(days=365)).strftime('%Y%m%d'))
    analyze_parser.set_defaults(func=cmd_analyze)
    
    # backtest 命令
    backtest_parser = subparsers.add_parser('backtest', help='回测策略')
    backtest_parser.add_argument('strategy', choices=['ma', 'macd', 'multi'])
    backtest_parser.add_argument('--codes', default='')
    backtest_parser.add_argument('--start', default='20240101')
    backtest_parser.add_argument('--end', default='20241231')
    backtest_parser.add_argument('--capital', type=int, default=100000)
    backtest_parser.set_defaults(func=cmd_backtest)
    
    # list 命令
    list_parser = subparsers.add_parser('list', help='列出股票')
    list_parser.add_argument('--market', choices=['main', 'chinext', 'star'])
    list_parser.add_argument('--industry')
    list_parser.add_argument('--area')
    list_parser.set_defaults(func=cmd_list)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
        return
    
    args.func(args)


if __name__ == '__main__':
    main()
