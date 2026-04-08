#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RSI-EMA14策略全量回测
⛏️ 超级龙虾
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime

from backtest.engine import BacktestEngine
from backtest.rsi_ema14_strategy import RSIEma14Strategy
from data.data_loader import DataLoader


def load_stock_list():
    """加载股票列表 (排除科创板688和北证8xx)"""
    stock_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'stocks', 'stock_list.csv')
    df = pd.read_csv(stock_file)
    
    # 排除科创板和北证
    exclude_codes = set()
    exclude_codes.update(df[df['ts_code'].str.startswith('688')]['ts_code'].tolist())
    exclude_codes.update(df[df['ts_code'].str.startswith('8')]['ts_code'].tolist())
    exclude_codes.update(df[df['market'] == '北交所']['ts_code'].tolist())
    
    df = df[~df['ts_code'].isin(exclude_codes)]
    return df


def run_backtest(stock_list, strategy, start_date, end_date):
    """运行回测"""
    loader = DataLoader()
    
    results = []
    total = len(stock_list)
    
    print(f"\n{'='*60}")
    print(f"📊 RSI-EMA14策略回测")
    print(f"{'='*60}")
    print(f"总股票数: {total}")
    print(f"回测区间: {start_date} - {end_date}")
    print(f"{'='*60}")
    
    for idx, (_, row) in enumerate(stock_list.iterrows()):
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
            
            if (idx + 1) % 500 == 0:
                print(f"进度: {idx+1}/{total} ({(idx+1)*100//total}%)")
            
        except Exception as e:
            continue
    
    return pd.DataFrame(results)


def print_summary(df: pd.DataFrame, strategy=None):
    """打印回测汇总"""
    if len(df) == 0:
        print("无回测结果")
        return df
    
    total = len(df)
    positive = (df['total_return'] > 0).sum()
    win_rate = positive / total * 100
    
    print(f"\n{'='*60}")
    print(f"📊 回测汇总 - RSI-EMA14策略")
    print(f"{'='*60}")
    print(f"策略参数:")
    if strategy:
        print(f"  - RSI(EMA14) < {strategy.rsi_threshold}")
        print(f"  - 持股{strategy.hold_days}天")
        print(f"  - 盈利>{int(strategy.profit_target*100)}%浮动止盈")
        print(f"  - 亏损{int(strategy.stop_loss*100)}%止损")
    print(f"\n总测试: {total} 只")
    print(f"正收益: {positive} 只 ({win_rate:.1f}%)")
    print(f"负收益: {total - positive} 只 ({100-win_rate:.1f}%)")
    print(f"\n平均收益率: {df['total_return'].mean()*100:+.2f}%")
    print(f"平均年化: {df['annual_return'].mean()*100:+.2f}%")
    print(f"平均最大回撤: {df['max_drawdown'].mean()*100:.2f}%")
    print(f"平均交易次数: {df['total_trades'].mean():.1f}")
    
    # 10万本金计算
    initial_capital = 100000
    avg_return = df['total_return'].mean()
    final_value = initial_capital * (1 + avg_return)
    print(f"\n💰 10万本金:")
    print(f"   平均收益: {final_value - initial_capital:+,.0f} 元")
    print(f"   最终价值: {final_value:,.0f} 元")
    
    # Top 10 正收益
    print(f"\n🏆 Top 10 正收益:")
    top10 = df.nlargest(10, 'total_return')
    print(f"{'代码':<12} {'名称':<10} {'总收益':>10} {'10万收益':>12}")
    print("-" * 50)
    for _, row in top10.iterrows():
        profit = 100000 * row['total_return']
        print(f"{row['ts_code']:<12} {row['name']:<10} {row['total_return']*100:>+9.2f}% {profit:>+11,.0f}元")
    
    # Top 10 负收益
    print(f"\n⚠️ Top 10 负收益:")
    bottom10 = df.nsmallest(10, 'total_return')
    print(f"{'代码':<12} {'名称':<10} {'总收益':>10} {'10万亏损':>12}")
    print("-" * 50)
    for _, row in bottom10.iterrows():
        loss = 100000 * row['total_return']
        print(f"{row['ts_code']:<12} {row['name']:<10} {row['total_return']*100:>+9.2f}% {loss:>+11,.0f}元")
    
    # 高胜率筛选
    high_quality = df[(df['total_return'] > 0) & (df['max_drawdown'] < 0.06)]
    print(f"\n🎯 高胜率筛选 (收益>0 且 回撤<6%):")
    print(f"符合条件: {len(high_quality)} 只 ({len(high_quality)*100//total}%)")
    
    if len(high_quality) > 0:
        avg_hq = high_quality['total_return'].mean()
        print(f"平均收益: {avg_hq*100:+.2f}%")
        print(f"10万本金 → {100000 * (1 + avg_hq):,.0f} 元")
    
    return df


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 RSI-EMA14策略全量回测")
    print("⛏️ 超级龙虾")
    print("=" * 60)
    
    # 参数
    start_date = '20250101'
    end_date = '20250408'
    
    # 加载股票列表
    stock_list = load_stock_list()
    print(f"\n📂 股票池: {len(stock_list)} 只 (排除科创板/北证)")
    
    # 创建策略
    strategy = RSIEma14Strategy(
        rsi_period=14,
        rsi_ema_period=14,
        rsi_threshold=25,
        hold_days=10,
        profit_target=0.10,
        stop_loss=0.06,
        trailing_stop=0.05
    )
    
    # 运行回测
    start_time = datetime.now()
    df = run_backtest(stock_list, strategy, start_date, end_date)
    end_time = datetime.now()
    
    # 打印结果
    print_summary(df, strategy)
    
    # 耗时
    duration = (end_time - start_time).total_seconds()
    print(f"\n⏱️ 耗时: {duration:.1f} 秒 ({duration/60:.1f} 分钟)")
    
    # 保存结果
    output_file = os.path.join(os.path.dirname(__file__), '..', 'output', 
                              f'rsi_ema14_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 结果已保存: {output_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
