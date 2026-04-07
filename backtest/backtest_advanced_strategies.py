#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级策略回测脚本
⛏️ 超级龙虾 - 回测所有新增策略
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from datetime import datetime
import pandas as pd

# 回测引擎
from backtest.engine import BacktestEngine

# 高级策略
from strategies.advanced_strategies import (
    BollingerBandStrategy,
    RSIStrategy,
    SqueezeMomentumStrategy,
    KDJStrategy,
    TrendFollowingStrategy,
    VolatilityBreakoutStrategy
)

# 数据加载器
from data.data_loader import DataLoader


def load_test_data(start_date: str = '20250101', end_date: str = '20250408'):
    """加载测试数据"""
    loader = DataLoader()
    
    # 测试股票池: 沪深300成分股中的几只
    test_stocks = [
        '000001.SZ',  # 平安银行
        '600000.SH',  # 浦发银行
        '600036.SH',  # 招商银行
        '600519.SH',  # 贵州茅台
        '000002.SZ',  # 万科A
        '601318.SH',  # 中国平安
        '000858.SZ',  # 五粮液
        '002594.SZ',  # 比亚迪
    ]
    
    print("📡 加载测试数据...")
    data_dict = {}
    
    for ts_code in test_stocks:
        try:
            df = loader.get_daily_data(ts_code, start_date=start_date, end_date=end_date)
            if df is not None and len(df) > 30:  # 降低门槛到30条
                # 转换 trade_date 为字符串格式 YYYYMMDD
                df = df.copy()
                df['trade_date'] = pd.to_datetime(df['trade_date']).dt.strftime('%Y%m%d')
                data_dict[ts_code] = df
                print(f"  ✅ {ts_code}: {len(df)} 条数据")
            else:
                print(f"  ⚠️ {ts_code}: 数据不足 ({len(df) if df is not None else 0} 条)")
        except Exception as e:
            print(f"  ❌ {ts_code}: {e}")
    
    return data_dict


def run_strategy_backtest(strategy_name: str, strategy, data_dict: dict, 
                          start_date: str, end_date: str) -> dict:
    """运行单个策略回测"""
    print(f"\n{'='*50}")
    print(f"📊 策略: {strategy_name}")
    print(f"{'='*50}")
    
    try:
        # 创建回测引擎
        engine = BacktestEngine(initial_capital=100000)
        
        # 运行回测
        result = engine.run(strategy, data_dict, start_date, end_date)
        
        # 输出结果
        print(f"\n  📈 总收益率: {result.total_return*100:+.2f}%")
        print(f"  📈 年化收益率: {result.annual_return*100:+.2f}%")
        print(f"  📉 最大回撤: {result.max_drawdown*100:.2f}%")
        print(f"  📊 夏普比率: {result.sharpe_ratio:.2f}")
        print(f"  🎯 交易次数: {result.total_trades}")
        print(f"  ⏱️ 平均持仓: {result.avg_holding_days:.1f} 天")
        
        # 计算胜率
        if result.total_trades > 0:
            buy_trades = [t for t in engine.trades if t.direction == 'buy']
            sell_trades = [t for t in engine.trades if t.direction == 'sell']
            
            # 简化胜率计算
            profitable = 0
            for i, t in enumerate(sell_trades):
                if i < len(buy_trades) and buy_trades:
                    if t.amount > buy_trades[i].amount:
                        profitable += 1
            win_rate = profitable / len(sell_trades) * 100 if sell_trades else 0
            print(f"  🏆 胜率: {win_rate:.1f}%")
        
        return {
            'strategy': strategy_name,
            'total_return': result.total_return,
            'annual_return': result.annual_return,
            'max_drawdown': result.max_drawdown,
            'sharpe_ratio': result.sharpe_ratio,
            'total_trades': result.total_trades,
            'win_rate': win_rate if result.total_trades > 0 else 0,
            'success': True
        }
        
    except Exception as e:
        print(f"  ❌ 回测失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            'strategy': strategy_name,
            'success': False,
            'error': str(e)
        }


def main():
    """主函数"""
    print("=" * 60)
    print("🚀 高级策略回测系统")
    print("⛏️ 超级龙虾 - A股量化分析系统")
    print("=" * 60)
    
    # 回测参数
    start_date = '20250101'
    end_date = '20250408'
    
    # 加载数据
    data_dict = load_test_data(start_date, end_date)
    
    if len(data_dict) == 0:
        print("\n❌ 没有可用的测试数据，回测终止")
        return 1
    
    print(f"\n✅ 成功加载 {len(data_dict)} 只股票数据")
    
    # 定义策略
    strategies = [
        ('布林带策略', BollingerBandStrategy(period=20, std_dev=2.0)),
        ('RSI策略', RSIStrategy(period=14, oversold=30, overbought=70)),
        ('Squeeze动量策略', SqueezeMomentumStrategy()),
        ('KDJ策略', KDJStrategy(n=9, m1=3, m2=3)),
        ('趋势跟踪策略', TrendFollowingStrategy(fast=5, mid=20, slow=60)),
        ('波动率突破策略', VolatilityBreakoutStrategy(period=20)),
    ]
    
    # 存储结果
    results = []
    
    # 逐个策略回测
    for name, strategy in strategies:
        result = run_strategy_backtest(name, strategy, data_dict, start_date, end_date)
        results.append(result)
    
    # 汇总报告
    print("\n" + "=" * 60)
    print("📊 策略回测汇总")
    print("=" * 60)
    
    # 按年化收益率排序
    valid_results = [r for r in results if r.get('success', False)]
    valid_results.sort(key=lambda x: x.get('annual_return', 0), reverse=True)
    
    print(f"\n{'策略':<20} {'总收益':>10} {'年化':>10} {'最大回撤':>10} {'夏普':>8} {'交易次数':>10}")
    print("-" * 70)
    
    for r in valid_results:
        print(f"{r['strategy']:<20} {r['total_return']*100:>+9.2f}% {r['annual_return']*100:>+9.2f}% "
              f"{r['max_drawdown']*100:>9.2f}% {r['sharpe_ratio']:>7.2f} {r['total_trades']:>9}")
    
    # 输出最优策略
    if valid_results:
        best = valid_results[0]
        print(f"\n🏆 最优策略: {best['strategy']}")
        print(f"   年化收益率: {best['annual_return']*100:.2f}%")
        print(f"   夏普比率: {best['sharpe_ratio']:.2f}")
        print(f"   最大回撤: {best['max_drawdown']*100:.2f}%")
    
    print("\n" + "=" * 60)
    print("✅ 回测完成!")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
