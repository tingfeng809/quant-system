#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股量化分析系统 - 演示脚本
⛏️ 淘金者版 - 基于真实数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from data.data_loader import DataLoader
from factors.technical_factors import TechnicalFactors
from factors.moneyflow_factors import MoneyflowFactors

print("=" * 70)
print("A 股量化分析系统 - 演示")
print("⛏️ 淘金者版 - 基于真实市场数据")
print("=" * 70)

# ==================== 1. 数据加载 ====================
print("\n【1】数据加载测试")
print("-" * 70)

loader = DataLoader()

# 获取股票列表
stocks = loader.get_stock_list()
print(f"A 股上市公司总数：{len(stocks)} 只")

# 获取示例股票数据
sample_codes = ['000001.SZ', '600519.SH', '300750.SZ']  # 平安银行，贵州茅台，宁德时代
sample_names = ['平安银行', '贵州茅台', '宁德时代']

for code, name in zip(sample_codes, sample_names):
    df = loader.get_daily_data(code, start_date='20251201')
    if len(df) > 0:
        latest = df.iloc[-1]
        print(f"{code} ({name}): 最新价 {latest['close']:.2f}, "
              f"日期 {latest['trade_date'].strftime('%Y-%m-%d')}")

# ==================== 2. 技术分析 ====================
print("\n【2】技术分析 - 以 000001.SZ (平安银行) 为例")
print("-" * 70)

df = loader.get_daily_data('000001.SZ', start_date='20250101')
tech = TechnicalFactors()
df_factors = tech.calculate_all(df.copy())

latest = df_factors.iloc[-1]
prev = df_factors.iloc[-2]

print(f"\n当前价格：{latest['close']:.2f}")

# 均线分析
print(f"\n均线系统:")
print(f"  MA5:  {latest['ma5']:.2f}  {'↑' if latest['ma5'] > prev['ma5'] else '↓'}")
print(f"  MA10: {latest['ma10']:.2f}  {'↑' if latest['ma10'] > prev['ma10'] else '↓'}")
print(f"  MA20: {latest['ma20']:.2f}  {'↑' if latest['ma20'] > prev['ma20'] else '↓'}")
print(f"  MA60: {latest['ma60']:.2f}")

ma_signal = "多头排列 ✅" if (latest['ma5'] > latest['ma10'] > latest['ma20']) else "空头排列 ❌"
print(f"  排列：{ma_signal}")

# MACD
print(f"\nMACD 指标:")
print(f"  DIF:  {latest['macd_dif']:.4f}  {'↑' if latest['macd_dif'] > prev['macd_dif'] else '↓'}")
print(f"  DEA:  {latest['macd_dea']:.4f}")
print(f"  MACD: {latest['macd']:.4f}")
macd_signal = "金叉 ✅" if (latest['macd_dif'] > latest['macd_dea']) else "死叉 ❌"
print(f"  信号：{macd_signal}")

# RSI
print(f"\nRSI 指标:")
print(f"  RSI6:  {latest['rsi6']:.2f}")
print(f"  RSI12: {latest['rsi12']:.2f}")
print(f"  RSI24: {latest['rsi24']:.2f}")
if latest['rsi12'] > 70:
    print(f"  状态：超买区 ⚠️")
elif latest['rsi12'] < 30:
    print(f"  状态：超卖区 ✅")
else:
    print(f"  状态：中性区")

# KDJ
print(f"\nKDJ 指标:")
print(f"  K: {latest['kdj_k']:.2f}, D: {latest['kdj_d']:.2f}, J: {latest['kdj_j']:.2f}")
kdj_signal = "金叉 ✅" if (latest['kdj_k'] > latest['kdj_d']) else "死叉 ❌"
print(f"  信号：{kdj_signal}")

# ==================== 3. 资金流分析 ====================
print("\n【3】资金流分析 - 以 000001.SZ (平安银行) 为例")
print("-" * 70)

moneyflow_df = loader.get_moneyflow('000001.SZ', start_date='20251201')
if len(moneyflow_df) > 0:
    mf = MoneyflowFactors()
    flow_factors = mf.calculate_all(moneyflow_df.copy())
    
    flow_latest = flow_factors.iloc[-1]
    
    print(f"\n当日资金流:")
    if 'net_inflow' in flow_latest:
        print(f"  净流入：{flow_latest['net_inflow']:.2f} 万元")
    if 'main_inflow' in flow_latest:
        print(f"  主力净流入：{flow_latest['main_inflow']:.2f} 万元")
    if 'main_inflow_rate' in flow_latest:
        rate = flow_latest['main_inflow_rate']
        print(f"  主力净流入率：{rate:.2f}% {'✅' if rate > 0 else '❌'}")
    
    print(f"\n资金流趋势:")
    if 'flow_sum_5d' in flow_latest:
        print(f"  5 日累计净流入：{flow_latest['flow_sum_5d']:.2f} 万元")
    if 'flow_sum_10d' in flow_latest:
        print(f"  10 日累计净流入：{flow_latest['flow_sum_10d']:.2f} 万元")
    
    if 'flow_score' in flow_latest:
        score = flow_latest['flow_score']
        print(f"\n资金流评分：{score:.0f}/100")
        if score >= 70:
            print(f"  评价：强势 ✅")
        elif score >= 50:
            print(f"  评价：中性")
        else:
            print(f"  评价：弱势 ❌")
else:
    print("暂无资金流数据")

# ==================== 4. 综合判断 ====================
print("\n【4】综合判断 - 000001.SZ (平安银行)")
print("-" * 70)

buy_signals = 0
sell_signals = 0

# 技术面
if latest['ma5'] > latest['ma10'] > latest['ma20']:
    buy_signals += 1
    print("✅ 均线多头排列")
else:
    sell_signals += 1
    print("❌ 均线空头排列")

if latest['macd_dif'] > latest['macd_dea']:
    buy_signals += 1
    print("✅ MACD 金叉")
else:
    sell_signals += 1
    print("❌ MACD 死叉")

if 50 <= latest['rsi12'] <= 70:
    buy_signals += 1
    print("✅ RSI 中性偏强")
elif latest['rsi12'] > 70 or latest['rsi12'] < 30:
    sell_signals += 1
    print("⚠️ RSI 极端区域")

# 资金流
if len(moneyflow_df) > 0 and 'flow_score' in flow_latest:
    if flow_latest['flow_score'] >= 60:
        buy_signals += 1
        print("✅ 资金流强势")
    elif flow_latest['flow_score'] <= 40:
        sell_signals += 1
        print("❌ 资金流弱势")

print(f"\n信号统计:")
print(f"  买入信号：{buy_signals} 个")
print(f"  卖出信号：{sell_signals} 个")

if buy_signals > sell_signals and buy_signals >= 2:
    print(f"\n👉 综合建议：谨慎看多")
elif sell_signals > buy_signals and sell_signals >= 2:
    print(f"\n👉 综合建议：谨慎看空")
else:
    print(f"\n👉 综合建议：观望")

# ==================== 5. 回测演示 ====================
print("\n\n【5】策略回测演示")
print("-" * 70)

from backtest.engine import BacktestEngine
from strategies.example_strategies import DualMAStrategy, MultiFactorStrategy

# 准备数据池
data_pool = {}
for code in sample_codes:
    df = loader.get_daily_data(code, start_date='20240101', end_date='20241231')
    if len(df) > 0:
        data_pool[code] = df
        print(f"加载 {code} 数据：{len(df)} 条")

if data_pool:
    # 双均线策略回测
    print("\n策略：双均线策略 (MA5/MA20)")
    strategy = DualMAStrategy(fast_period=5, slow_period=20)
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(strategy, data_pool, '20240101', '20241231')
    
    print(f"  初始资金：100,000")
    print(f"  最终资金：{engine.daily_values[-1]:,.0f}")
    print(f"  总收益率：{result.total_return*100:.2f}%")
    print(f"  年化收益率：{result.annual_return*100:.2f}%")
    print(f"  最大回撤：{result.max_drawdown*100:.2f}%")
    print(f"  夏普比率：{result.sharpe_ratio:.2f}")
    print(f"  交易次数：{result.total_trades}")
    
    # 多因子策略回测
    print("\n策略：多因子综合策略")
    strategy = MultiFactorStrategy()
    engine = BacktestEngine(initial_capital=100000)
    result = engine.run(strategy, data_pool, '20240101', '20241231')
    
    print(f"  初始资金：100,000")
    print(f"  最终资金：{engine.daily_values[-1]:,.0f}")
    print(f"  总收益率：{result.total_return*100:.2f}%")
    print(f"  年化收益率：{result.annual_return*100:.2f}%")
    print(f"  最大回撤：{result.max_drawdown*100:.2f}%")
    print(f"  夏普比率：{result.sharpe_ratio:.2f}")
    print(f"  交易次数：{result.total_trades}")

print("\n" + "=" * 70)
print("演示完成！⛏️")
print("=" * 70)
