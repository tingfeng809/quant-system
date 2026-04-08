#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高胜率策略回测对比
⛏️ 超级龙虾 - 对比优化策略与原始KDJ策略
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime

from backtest.engine import BacktestEngine
from strategies.advanced_strategies import KDJStrategy
from strategies.high_win_rate_strategy import HighWinRateStrategy, ConservativeStrategy
from data.data_loader import DataLoader


def load_stock_pool():
    """加载股票池 (排除科创板/北证)"""
    stock_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'stocks', 'stock_list.csv')
    df = pd.read_csv(stock_file)
    
    # 排除科创板和北证
    exclude_codes = set()
    exclude_codes.update(df[df['ts_code'].str.startswith('688')]['ts_code'].tolist())
    exclude_codes.update(df[df['ts_code'].str.startswith('8')]['ts_code'].tolist())
    exclude_codes.update(df[df['market'] == '北交所']['ts_code'].tolist())
    
    df = df[~df['ts_code'].isin(exclude_codes)]
    return df


def run_strategy_test(strategy_name: str, strategy, stock_list: pd.DataFrame,
                      start_date: str, end_date: str, max_stocks: int = 500) -> dict:
    """运行策略测试"""
    loader = DataLoader()
    
    results = []
    
    print(f"\n{'='*50}")
    print(f"📊 策略: {strategy_name}")
    print(f"{'='*50}")
    
    test_stocks = stock_list.head(max_stocks)
    
    for idx, row in test_stocks.iterrows():
        ts_code = row['ts_code']
        
        try:
            df = loader.get_daily_data(ts_code, start_date=start_date, end_date=end_date)
            if df is None or len(df) < 30:
                continue
            
            df = df.copy()
            df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y%m%d')
            
            engine = BacktestEngine(initial_capital=100000)
            result = engine.run(strategy, {ts_code: df}, start_date, end_date)
            
            results.append({
                'ts_code': ts_code,
                'name': row['name'],
                'total_return': result.total_return,
                'annual_return': result.annual_return,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'total_trades': result.total_trades,
            })
            
        except Exception as e:
            continue
    
    if not results:
        return {'strategy': strategy_name, 'error': 'No results'}
    
    df_result = pd.DataFrame(results)
    
    # 统计
    total = len(df_result)
    positive = (df_result['total_return'] > 0).sum()
    win_rate = positive / total * 100 if total > 0 else 0
    
    # 高胜率筛选
    high_win = df_result[(df_result['total_return'] > 0) & 
                          (df_result['max_drawdown'] < 0.03) &
                          (df_result['total_trades'] >= 3)]
    
    summary = {
        'strategy': strategy_name,
        'total': total,
        'positive': positive,
        'win_rate': win_rate,
        'avg_return': df_result['total_return'].mean(),
        'avg_annual': df_result['annual_return'].mean(),
        'avg_drawdown': df_result['max_drawdown'].mean(),
        'avg_sharpe': df_result['sharpe_ratio'].mean(),
        'high_win_count': len(high_win),
        'high_win_rate': len(high_win) / total * 100 if total > 0 else 0,
        'results': df_result
    }
    
    print(f"\n📈 基础统计:")
    print(f"   总测试: {total} 只")
    print(f"   正收益: {positive} 只 ({win_rate:.1f}%)")
    print(f"   平均收益: {summary['avg_return']*100:+.2f}%")
    print(f"   平均年化: {summary['avg_annual']*100:+.2f}%")
    print(f"   平均最大回撤: {summary['avg_drawdown']*100:.2f}%")
    print(f"\n🎯 高胜率筛选 (收益>0 且 回撤<3% 且 交易>=3次):")
    print(f"   符合条件: {len(high_win)} 只 ({summary['high_win_rate']:.1f}%)")
    
    return summary


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 高胜率策略对比测试")
    print("⛏️ 超级龙虾 - 宁缺毋滥，出手必胜")
    print("=" * 60)
    
    # 参数
    start_date = '20250101'
    end_date = '20250408'
    max_stocks = 500  # 先测试500只
    
    # 加载股票池
    stock_list = load_stock_pool()
    print(f"\n📂 股票池: {len(stock_list)} 只 (排除科创板/北证)")
    
    # 测试策略
    strategies = [
        ('KDJ原始策略', KDJStrategy()),
        ('高胜率策略', HighWinRateStrategy()),
        ('保守高胜率策略', ConservativeStrategy()),
    ]
    
    summaries = []
    
    for name, strategy in strategies:
        summary = run_strategy_test(name, strategy, stock_list, start_date, end_date, max_stocks)
        summaries.append(summary)
    
    # 对比汇总
    print("\n" + "=" * 60)
    print("📊 策略对比汇总")
    print("=" * 60)
    
    print(f"\n{'策略':<20} {'测试数':>8} {'胜率':>8} {'平均收益':>10} {'高胜率比例':>12}")
    print("-" * 60)
    
    for s in summaries:
        print(f"{s['strategy']:<20} {s['total']:>8} {s['win_rate']:>7.1f}% "
              f"{s['avg_return']*100:>+9.2f}% {s['high_win_rate']:>11.1f}%")
    
    # 找出最优策略
    best = max(summaries, key=lambda x: x['high_win_rate'])
    print(f"\n🏆 最优策略: {best['strategy']}")
    print(f"   高胜率比例: {best['high_win_rate']:.1f}%")
    print(f"   胜率: {best['win_rate']:.1f}%")
    print(f"   平均收益: {best['avg_return']*100:.2f}%")
    
    print("\n" + "=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
