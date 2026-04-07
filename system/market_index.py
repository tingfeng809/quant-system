# -*- coding: utf-8 -*-
"""
A股大中小盘自定义指数体系
⛏️ 淘金者版 - 基于市值分类的指数系统

分类标准:
- 大盘: >500亿 (机构主导，价值投资)
- 中盘: 100-500亿 (成长股，趋势跟随)
- 小盘: <100亿 (高波动，主题炒作)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass


@dataclass
class MarketIndex:
    """市场指数数据"""
    name: str           # 指数名称
    code: str           # 指数代码
    stocks: List[str]   # 成分股列表
    stock_weights: List[float]  # 成分股权重
    current_value: float  # 当前点位
    change_pct: float    # 涨跌幅 %
    market_cap_yi: float # 总市值(亿)
    stock_count: int     # 成分股数量


class MarketCapClassifier:
    """
    市值分类器
    
    将A股按市值分为大/中/小盘
    """
    
    # 市值阈值（亿元）
    LARGE_THRESHOLD = 500    # 大盘 >500亿
    MID_THRESHOLD = 100      # 中盘 100-500亿
    # 小盘 <100亿
    
    @classmethod
    def classify(cls, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        根据市值分类股票
        
        Args:
            df: 包含 total_mv (万元) 的行情数据
        
        Returns:
            Dict: {'large': 大盘, 'mid': 中盘, 'small': 小盘}
        """
        df = df.copy()
        df['market_cap_yi'] = df['total_mv'] / 10000  # 转为亿元
        
        large = df[df['market_cap_yi'] > cls.LARGE_THRESHOLD].copy()
        mid = df[(df['market_cap_yi'] >= cls.MID_THRESHOLD) & 
                 (df['market_cap_yi'] <= cls.LARGE_THRESHOLD)].copy()
        small = df[df['market_cap_yi'] < cls.MID_THRESHOLD].copy()
        
        return {
            'large': large.sort_values('market_cap_yi', ascending=False),
            'mid': mid.sort_values('market_cap_yi', ascending=False),
            'small': small.sort_values('market_cap_yi', ascending=False)
        }
    
    @classmethod
    def get_stats(cls, df: pd.DataFrame) -> Dict:
        """获取分类统计"""
        classified = cls.classify(df)
        
        stats = {}
        for category, data in classified.items():
            if len(data) > 0:
                stats[category] = {
                    'count': len(data),
                    'total_market_cap': data['market_cap_yi'].sum(),
                    'avg_market_cap': data['market_cap_yi'].mean(),
                    'median_market_cap': data['market_cap_yi'].median()
                }
            else:
                stats[category] = {
                    'count': 0, 'total_market_cap': 0, 
                    'avg_market_cap': 0, 'median_market_cap': 0
                }
        
        return stats


class CustomIndex:
    """
    自定义指数计算器
    
    基于成分股计算加权指数
    """
    
    def __init__(self, name: str, code: str, stocks: List[str], 
                 weights: Optional[List[float]] = None):
        """
        Args:
            name: 指数名称
            code: 指数代码
            stocks: 成分股列表
            weights: 权重列表（默认等权重）
        """
        self.name = name
        self.code = code
        self.stocks = stocks
        self.weights = weights if weights else ([1.0] if len(stocks) == 0 else [1.0/len(stocks)] * len(stocks))
        
        self.history = []  # 历史点位
    
    def calculate(self, price_data: pd.DataFrame) -> float:
        """
        计算当前指数点位
        
        Args:
            price_data: 包含 ts_code, close 的行情数据
        
        Returns:
            float: 指数点位
        """
        if len(price_data) == 0:
            return 0
        
        # 计算加权平均
        total_weight = 0
        weighted_sum = 0
        
        for _, row in price_data.iterrows():
            weight = self.weights[self.stocks.index(row['ts_code'])] \
                     if row['ts_code'] in self.stocks else 0
            weighted_sum += row['close'] * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0
        
        return weighted_sum / total_weight


class MarketIndexSystem:
    """
    A股大中小盘指数系统
    
    功能:
    - 每日自动分类股票
    - 计算自定义指数点位
    - 跟踪历史走势
    - 生成交易信号
    """
    
    def __init__(self):
        self.classifier = MarketCapClassifier()
        self.indices = {}
        self._init_indices()
    
    def _init_indices(self):
        """初始化指数结构"""
        # 预定义的指数代码
        self.indices = {
            'L': CustomIndex('大盘指数', 'INDEX_LARGE', []),      # 大盘
            'M': CustomIndex('中盘指数', 'INDEX_MID', []),       # 中盘
            'S': CustomIndex('小盘指数', 'INDEX_SMALL', []),     # 小盘
        }
    
    def update(self, trade_date: str) -> Dict[str, MarketIndex]:
        """
        更新指数数据
        
        Args:
            trade_date: 交易日期 YYYYMMDD
        
        Returns:
            Dict: 各指数数据
        """
        import tushare as ts
        ts.set_token('39a3955e10adc24a28b08b459d9ea092dcd737c3a8c0df386bc84bd8')
        pro = ts.pro_api()
        
        # 获取当日行情（含市值）
        df = pro.daily_basic(trade_date=trade_date)
        df = df[df['total_mv'] > 0].dropna()
        
        # 分类
        classified = self.classifier.classify(df)
        
        result = {}
        
        # 计算各指数
        for category, label in [('large', 'L'), ('mid', 'M'), ('small', 'S')]:
            stocks_data = classified[category]
            
            if len(stocks_data) == 0:
                continue
            
            stocks = stocks_data['ts_code'].tolist()
            
            # 市值加权
            market_caps = stocks_data['total_mv'].values
            weights = market_caps / market_caps.sum()
            
            # 更新指数
            index_obj = self.indices[label]
            index_obj.stocks = stocks
            index_obj.weights = weights.tolist()
            
            # 计算指数点位（使用平均股价 * 1000 作为初始基准）
            avg_price = (stocks_data['close'] * weights).sum()
            index_obj.current_value = avg_price * 1000  # 归一化
            
            result[label] = MarketIndex(
                name=index_obj.name,
                code=index_obj.code,
                stocks=stocks,
                stock_weights=weights.tolist(),
                current_value=index_obj.current_value,
                change_pct=0,  # 需历史数据计算
                market_cap_yi=stocks_data['market_cap_yi'].sum(),
                stock_count=len(stocks)
            )
        
        return result
    
    def get_index_data(self, trade_date: str) -> Dict:
        """
        获取指数数据（完整信息）
        
        Args:
            trade_date: 交易日期
        
        Returns:
            Dict: 指数详细信息
        """
        import tushare as ts
        ts.set_token('39a3955e10adc24a28b08b459d9ea092dcd737c3a8c0df386bc84bd8')
        pro = ts.pro_api()
        
        # 获取当日行情
        df = pro.daily_basic(trade_date=trade_date)
        df = df[df['total_mv'] > 0].dropna()
        df['market_cap_yi'] = df['total_mv'] / 10000
        
        # 分类
        classified = self.classifier.classify(df)
        
        # 计算各分类统计
        result = {}
        category_names = {'large': '大盘', 'mid': '中盘', 'small': '小盘'}
        
        for category, label in [('large', 'L'), ('mid', 'M'), ('small', 'S')]:
            data = classified[category]
            if len(data) == 0:
                continue
            
            # 加权平均涨跌
            if 'pct_change' in data.columns:
                weighted_change = (data['pct_change'] * data['total_mv']).sum() / data['total_mv'].sum()
            else:
                weighted_change = 0
            
            result[label] = {
                'name': category_names[category],
                'code': f'INDEX_{label}',
                'stock_count': len(data),
                'total_market_cap_yi': data['market_cap_yi'].sum(),
                'avg_market_cap_yi': data['market_cap_yi'].mean(),
                'median_market_cap_yi': data['market_cap_yi'].median(),
                'weighted_change_pct': weighted_change if 'pct_change' in data.columns else 0,
                'top_stocks': data.head(10)[['ts_code', 'close', 'market_cap_yi']].to_dict('records')
            }
        
        return result
    
    def calculate_index_history(self, days: int = 30) -> Dict[str, pd.Series]:
        """
        计算历史指数点位
        
        Args:
            days: 历史天数
        
        Returns:
            Dict: {'L': 大盘指数 series, 'M': 中盘指数 series, 'S': 小盘指数 series}
        """
        import tushare as ts
        ts.set_token('39a3955e10adc24a28b08b459d9ea092dcd737c3a8c0df386bc84bd8')
        pro = ts.pro_api()
        
        # 获取成分股
        df_base = pro.daily_basic(trade_date='20260407')
        df_base = df_base[df_base['total_mv'] > 0].dropna()
        df_base['market_cap_yi'] = df_base['total_mv'] / 10000
        
        classified = self.classifier.classify(df_base)
        
        # 计算日期范围
        from datetime import datetime, timedelta
        end_date = datetime.strptime('20260407', '%Y%m%d')
        start_date = end_date - timedelta(days=days)
        
        indices = {}
        
        for category, label in [('large', 'L'), ('mid', 'M'), ('small', 'S')]:
            stocks = classified[category]['ts_code'].tolist()
            
            if not stocks:
                continue
            
            # 分批获取日线数据
            all_data = []
            batch_size = 50
            
            for i in range(0, len(stocks), batch_size):
                batch = stocks[i:i+batch_size]
                try:
                    df = pro.daily(
                        ts_code=','.join(batch),
                        start_date=start_date.strftime('%Y%m%d'),
                        end_date='20260407'
                    )
                    if df is not None and len(df) > 0:
                        all_data.append(df)
                except Exception as e:
                    continue
            
            if not all_data:
                continue
            
            result = pd.concat(all_data)
            
            # 市值加权计算指数
            cap_dict = dict(zip(df_base['ts_code'], df_base['total_mv']))
            result['weight'] = result['ts_code'].map(cap_dict).fillna(1)
            result['weighted_price'] = result['close'] * result['weight']
            
            # 按日期汇总
            daily = result.groupby('trade_date').agg({
                'weighted_price': 'sum',
                'weight': 'sum'
            })
            daily['index'] = daily['weighted_price'] / daily['weight']
            
            # 归一化到1000点基准
            base_value = daily['index'].iloc[0]
            normalized = daily['index'] / base_value * 1000
            
            indices[label] = normalized.sort_index()
        
        return indices
    
    def get_trading_signals(self, trade_date: str) -> Dict:
        """
        生成交易信号
        
        基于大中小盘分化判断市场状态
        
        Returns:
            Dict: 信号 {
                'market_status': '单边/分化/轮动/震荡',
                'signal': '做多/做空/观望',
                'details': {...}
            }
        """
        data = self.get_index_data(trade_date)
        
        if len(data) < 3:
            return {'market_status': '数据不足', 'signal': '观望'}
        
        changes = {
            label: info.get('weighted_change_pct', 0) 
            for label, info in data.items()
        }
        
        large_change = changes.get('L', 0)
        mid_change = changes.get('M', 0)
        small_change = changes.get('S', 0)
        
        # 判断市场状态
        all_positive = all(v > 0 for v in changes.values())
        all_negative = all(v < 0 for v in changes.values())
        
        # 计算分化程度
        changes_list = list(changes.values())
        divergence = max(changes_list) - min(changes_list)
        
        # 生成信号
        if all_positive and divergence < 1:
            status = '普涨'
            signal = '做多'
        elif all_negative and divergence < 1:
            status = '普跌'
            signal = '做空'
        elif large_change > mid_change and large_change > small_change:
            status = '二八分化'
            signal = '做多大票'
        elif small_change > large_change and small_change > mid_change:
            status = '小票活跃'
            signal = '题材炒作'
        elif divergence > 3:
            status = '严重分化'
            signal = '观望'
        else:
            status = '震荡'
            signal = '观望'
        
        return {
            'trade_date': trade_date,
            'market_status': status,
            'signal': signal,
            'changes': changes,
            'divergence_pct': divergence,
            'details': data
        }


# ==================== 测试 ====================
def test_market_index():
    """测试市值指数系统"""
    print("=" * 70)
    print("A股大中小盘指数体系测试")
    print("=" * 70)
    
    system = MarketIndexSystem()
    
    # 更新今日数据
    print("\n【1】获取今日数据...")
    result = system.get_index_data('20260407')
    
    for label, info in result.items():
        print(f"\n  {info['name']} ({info['code']})")
        print(f"    股票数量: {info['stock_count']}")
        print(f"    总市值: {info['total_market_cap_yi']:.1f} 亿")
        print(f"    平均市值: {info['avg_market_cap_yi']:.1f} 亿")
        print(f"    中位市值: {info['median_market_cap_yi']:.1f} 亿")
    
    # 交易信号
    print("\n【2】交易信号...")
    signals = system.get_trading_signals('20260407')
    print(f"  市场状态: {signals['market_status']}")
    print(f"  交易信号: {signals['signal']}")
    print(f"  分化程度: {signals['divergence_pct']:.2f}%")
    print(f"  涨跌情况:")
    for label, change in signals['changes'].items():
        direction = '↑' if change > 0 else '↓'
        print(f"    {label}: {abs(change):.2f}% {direction}")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    test_market_index()