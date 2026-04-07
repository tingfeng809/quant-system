# -*- coding: utf-8 -*-
"""
量化系统配置
⚠️ 所有数据必须来自真实数据源，禁止模拟/随机/测试数据
"""

import os
from datetime import datetime, timedelta

# ==================== Tushare 配置 ====================
TUSHARE_TOKEN = '39a3955e10adc24a28b08b459d9ea092dcd737c3a8c0df386bc84bd8'

# ==================== 数据配置 ====================
DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')

# 确保目录存在
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ==================== 市场配置 ====================
# A 股市场
MARKETS = {
    'SH': '上海证券交易所',
    'SZ': '深圳证券交易所',
    'BJ': '北京证券交易所',
}

# 板块
BOARDS = {
    '主板': 'main',
    '创业板': 'chinext',
    '科创板': 'star',
    '北交所': 'bj',
}

# ==================== 回测配置 ====================
BACKTEST_CONFIG = {
    'initial_capital': 1000000,  # 初始资金 100 万
    'commission': 0.0003,  # 佣金万分之三
    'slippage': 0.001,  # 滑点 0.1%
    'stamp_tax': 0.001,  # 印花税 0.1%（仅卖出）
    'min_trade_amount': 100,  # 最小交易金额
}

# ==================== 因子配置 ====================
FACTOR_CONFIG = {
    # 技术因子
    'technical': {
        'enabled': True,
        'lookback_days': [5, 10, 20, 60],  # 回看周期
    },
    # 基本面因子
    'fundamental': {
        'enabled': True,
        'update_freq': 'quarterly',  # 季度更新
    },
    # 资金流因子
    'moneyflow': {
        'enabled': True,
        'lookback_days': [1, 5, 10, 20],
    },
}

# ==================== 交易日历 ====================
def get_trading_calendar(start_date=None, end_date=None):
    """获取交易日历"""
    import tushare as ts
    ts.set_token(TUSHARE_TOKEN)
    pro = ts.pro_api()
    
    if start_date is None:
        start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    
    try:
        df = pro.trade_cal(exchange='SSE', start_date=start_date, end_date=end_date, is_open='1')
        return df['cal_date'].tolist()
    except Exception as e:
        print(f"获取交易日历失败：{e}")
        return []

# ==================== 日志配置 ====================
import logging

def setup_logger(name, level=logging.INFO):
    """设置日志"""
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # 控制台输出
    ch = logging.StreamHandler()
    ch.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    return logger

logger = setup_logger('quant')
