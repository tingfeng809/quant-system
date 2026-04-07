#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
全量A股回测脚本
⛏️ 超级龙虾 - 对全量A股(除科创板/北证)进行回测
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import pandas as pd
import numpy as np
from datetime import datetime
from collections import defaultdict

# 回测引擎
from backtest.engine import BacktestEngine

# 策略
from strategies.advanced_strategies import KDJStrategy

# 数据加载器
from data.data_loader import DataLoader


def load_stock_list():
    """加载股票列表 (排除科创板688和北证8xx)"""
    stock_file = os.path.join(os.path.dirname(__file__), '..', 'data', 'stocks', 'stock_list.csv')
    df = pd.read_csv(stock_file)
    
    # 排除条件:
    # 1. 科创板: 688xxx.SH
    # 2. 北证: 8xxxxx.SH/BJ
    # 3. ST股票 (可选,暂时保留)
    
    exclude_codes = []
    
    # 排除科创板 (688xxx.SH)
    exclude_codes.extend(df[df['ts_code'].str.startswith('688')]['ts_code'].tolist())
    
    # 排除北证 (8开头, 或市场为北交所)
    exclude_codes.extend(df[df['ts_code'].str.startswith('8')]['ts_code'].tolist())
    exclude_codes.extend(df[df['market'] == '北交所']['ts_code'].tolist())
    
    # 过滤
    df = df[~df['ts_code'].isin(exclude_codes)]
    
    return df


def batch_backtest(stock_list: pd.DataFrame, strategy, start_date: str, end_date: str,
                   batch_size: int = 50, max_workers: int = 4) -> dict:
    """
    批量回测
    
    Args:
        stock_list: 股票列表 DataFrame
        strategy: 策略对象
        start_date: 开始日期
        end_date: 结束日期
        batch_size: 每批处理股票数
        max_workers: 最大并行数 (实际未使用多进程,顺序执行)
    
    Returns:
        dict: 回测结果汇总
    """
    loader = DataLoader()
    
    total = len(stock_list)
    processed = 0
    success = 0
    failed = 0
    
    # 汇总统计
    total_return_sum = 0
    positive_count = 0
    negative_count = 0
    total_trades = 0
    
    # 详细结果
    results_detail = []
    
    strategy_name = strategy.name
    
    print(f"\n{'='*60}")
    print(f"📊 全量A股回测: {strategy_name}")
    print(f"{'='*60}")
    print(f"总股票数: {total}")
    print(f"回测区间: {start_date} - {end_date}")
    print(f"每批数量: {batch_size}")
    print(f"{'='*60}")
    
    engine = BacktestEngine(initial_capital=100000)
    
    # 分批处理
    for batch_start in range(0, total, batch_size):
        batch_end = min(batch_start + batch_size, total)
        batch = stock_list.iloc[batch_start:batch_end]
        
        print(f"\n处理批次: {batch_start//batch_size + 1}/{(total-1)//batch_size + 1} "
              f"({batch_start}-{batch_end})")
        
        for idx, row in batch.iterrows():
            ts_code = row['ts_code']
            name = row['name']
            
            try:
                # 加载数据
                df = loader.get_daily_data(ts_code, start_date=start_date, end_date=end_date)
                
                if df is None or len(df) < 30:
                    failed += 1
                    continue
                
                # 转换日期格式
                df = df.copy()
                df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y%m%d')
                
                # 构建 data_dict
                data_dict = {ts_code: df}
                
                # 运行回测
                engine.reset()
                result = engine.run(strategy, data_dict, start_date, end_date)
                
                processed += 1
                success += 1
                
                total_return_sum += result.total_return
                total_trades += result.total_trades
                
                if result.total_return > 0:
                    positive_count += 1
                elif result.total_return < 0:
                    negative_count += 1
                
                # 记录详细结果
                if result.total_trades > 0:
                    results_detail.append({
                        'ts_code': ts_code,
                        'name': name,
                        'total_return': result.total_return,
                        'annual_return': result.annual_return,
                        'max_drawdown': result.max_drawdown,
                        'sharpe_ratio': result.sharpe_ratio,
                        'total_trades': result.total_trades,
                    })
                
                if processed % 100 == 0:
                    avg_return = total_return_sum / success if success > 0 else 0
                    print(f"  进度: {processed}/{total} | "
                          f"成功: {success} | "
                          f"正收益: {positive_count} | "
                          f"平均收益: {avg_return*100:.2f}%")
                
            except Exception as e:
                failed += 1
                continue
    
    # 计算汇总统计
    avg_return = total_return_sum / success if success > 0 else 0
    win_rate = positive_count / success * 100 if success > 0 else 0
    
    summary = {
        'strategy': strategy_name,
        'total_stocks': total,
        'processed': processed,
        'success': success,
        'failed': failed,
        'avg_return': avg_return,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'win_rate': win_rate,
        'total_trades': total_trades,
        'detail': results_detail
    }
    
    return summary


def print_summary(summary: dict):
    """打印回测汇总"""
    print(f"\n{'='*60}")
    print(f"📊 回测汇总")
    print(f"{'='*60}")
    print(f"策略: {summary['strategy']}")
    print(f"总股票数: {summary['total_stocks']}")
    print(f"成功回测: {summary['success']}")
    print(f"失败/数据不足: {summary['failed']}")
    print(f"正收益股票: {summary['positive_count']} ({summary['win_rate']:.1f}%)")
    print(f"负收益股票: {summary['negative_count']}")
    print(f"平均收益: {summary['avg_return']*100:+.2f}%")
    print(f"总交易次数: {summary['total_trades']}")
    
    # Top 10 最佳
    if summary['detail']:
        print(f"\n🏆 Top 10 正收益股票:")
        sorted_pos = sorted(summary['detail'], key=lambda x: x['total_return'], reverse=True)[:10]
        print(f"{'代码':<12} {'名称':<10} {'总收益':>10} {'年化':>10} {'最大回撤':>10} {'交易次数':>8}")
        print("-" * 65)
        for r in sorted_pos:
            print(f"{r['ts_code']:<12} {r['name']:<10} {r['total_return']*100:>+9.2f}% "
                  f"{r['annual_return']*100:>+9.2f}% {r['max_drawdown']*100:>9.2f}% {r['total_trades']:>7}")
    
    # Top 10 最差
    if summary['detail']:
        print(f"\n⚠️ Top 10 负收益股票:")
        sorted_neg = sorted(summary['detail'], key=lambda x: x['total_return'])[:10]
        print(f"{'代码':<12} {'名称':<10} {'总收益':>10} {'年化':>10} {'最大回撤':>10} {'交易次数':>8}")
        print("-" * 65)
        for r in sorted_neg:
            print(f"{r['ts_code']:<12} {r['name']:<10} {r['total_return']*100:>+9.2f}% "
                  f"{r['annual_return']*100:>+9.2f}% {r['max_drawdown']*100:>9.2f}% {r['total_trades']:>7}")
    
    print(f"\n{'='*60}")


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 全量A股回测系统")
    print("⛏️ 超级龙虾 - KDJ策略全量回测")
    print("=" * 60)
    
    # 回测参数
    start_date = '20250101'
    end_date = '20250408'
    
    # 加载股票列表
    print("\n📂 加载股票列表...")
    stock_list = load_stock_list()
    print(f"✅ 排除科创板/北证后: {len(stock_list)} 只股票")
    
    # 使用 KDJ 策略 (回测表现最佳)
    strategy = KDJStrategy(n=9, m1=3, m2=3)
    
    # 运行回测
    start_time = datetime.now()
    summary = batch_backtest(stock_list, strategy, start_date, end_date, batch_size=50)
    end_time = datetime.now()
    
    # 打印结果
    print_summary(summary)
    
    # 耗时
    duration = (end_time - start_time).total_seconds()
    print(f"\n⏱️ 总耗时: {duration:.1f} 秒")
    print(f"📊 平均每只: {duration/summary['success']:.2f} 秒")
    
    # 保存结果
    output_file = os.path.join(os.path.dirname(__file__), '..', 'output', 
                              f'full_backtest_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv')
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    if summary['detail']:
        df_result = pd.DataFrame(summary['detail'])
        df_result.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 结果已保存: {output_file}")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
