#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""系统测试脚本"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from data.data_loader import DataLoader
from factors.technical_factors import TechnicalFactors
from backtest.engine import BacktestEngine
from strategies.example_strategies import DualMAStrategy

print("=" * 60)
print("A 股量化分析系统 - 测试")
print("=" * 60)

# 1. 测试数据加载
print("\n1. 测试数据加载...")
loader = DataLoader()
df = loader.get_daily_data('000001.SZ', start_date='20240101')
print(f"   加载 000001.SZ 数据：{len(df)} 条")
if len(df) > 0:
    print(f"   最新收盘价：{df.iloc[-1]['close']:.2f}")

# 2. 测试因子计算
print("\n2. 测试技术因子计算...")
tech = TechnicalFactors()
df_factors = tech.calculate_all(df.copy())
factor_cols = [c for c in df_factors.columns if c not in df.columns]
print(f"   计算因子数量：{len(factor_cols)}")

# 3. 测试回测
print("\n3. 测试回测引擎...")
strategy = DualMAStrategy()
engine = BacktestEngine(initial_capital=100000)
result = engine.run(strategy, {'000001.SZ': df}, '20240101', '20241231')
print(f"   总收益率：{result.total_return*100:.2f}%")
print(f"   交易次数：{result.total_trades}")

print("\n✅ 系统测试完成！")
