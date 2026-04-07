# -*- coding: utf-8 -*-
"""
情绪指数与自定义指数集成模块
淘金者版 - 结合市场指数的情绪监控系统

功能:
- 基于大中小盘指数生成市场情绪信号
- 结合舆情分析判断市场情绪
- 生成综合交易建议
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class MarketSentiment:
    """市场情绪数据"""
    timestamp: str
    market_status: str          # 普涨/普跌/分化/震荡
    sentiment_score: float       # -1 to 1, 负面到正面
    sentiment_label: str          # 乐观/中性/悲观
    index_signals: Dict          # 各指数信号
    news_count: int              # 相关新闻数
    alert_level: str             # 预警级别
    trading_suggestion: str        # 交易建议


class IndexSentimentIntegration:
    """
    指数与情绪集成器
    
    结合:
    - 大中小盘指数信号
    - 舆情情绪分析
    - 涨跌家数统计
    """
    
    def __init__(self):
        self.market_index_system = None
        self.news_collector = None
        self.sentiment_analyzer = None
        
        # 情绪阈值
        self.sentiment_thresholds = {
            'bullish': 0.3,      # >0.3 乐观
            'bearish': -0.3,     # <-0.3 悲观
        }
        
        # 指数权重
        self.index_weights = {
            'L': 0.5,   # 大盘权重最高
            'M': 0.3,
            'S': 0.2
        }
    
    def _get_market_index_system(self):
        """懒加载市场指数系统"""
        if self.market_index_system is None:
            from system.market_index import MarketIndexSystem
            self.market_index_system = MarketIndexSystem()
        return self.market_index_system
    
    def _get_news_collector(self):
        """懒加载新闻采集器"""
        if self.news_collector is None:
            from crawler.news_collector import NewsCollector
            self.news_collector = NewsCollector()
        return self.news_collector
    
    def _get_sentiment_analyzer(self):
        """懒加载情感分析器"""
        if self.sentiment_analyzer is None:
            from nlp.sentiment_analyzer import SentimentAnalyzer
            self.sentiment_analyzer = SentimentAnalyzer()
        return self.sentiment_analyzer
    
    def get_market_sentiment(self, trade_date: str = None) -> MarketSentiment:
        """
        获取市场情绪
        
        Args:
            trade_date: 交易日期 YYYYMMDD
        
        Returns:
            MarketSentiment: 市场情绪数据
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        system = self._get_market_index_system()
        
        # 获取指数历史数据计算实际涨跌
        indices = system.calculate_index_history(days=30)
        
        # 计算各指数涨跌
        index_changes = {}
        index_daily_changes = {}
        for label, series in indices.items():
            change = (series.iloc[-1] / series.iloc[0] - 1) * 100
            index_changes[label] = change
            # 当日涨跌
            if len(series) >= 2:
                daily = (series.iloc[-1] / series.iloc[-2] - 1) * 100
            else:
                daily = 0
            index_daily_changes[label] = daily
        
        # 获取涨跌家数
        index_adv_dec = self._get_advance_decline()
        
        # 获取创业板数据
        cyb_data = self._get_cyb_data()
        
        # 计算指数综合信号
        index_signals = self._calculate_index_signals(index_changes, index_daily_changes, index_adv_dec, cyb_data)
        
        # 获取舆情情绪
        news_sentiment = self._analyze_news_sentiment()
        
        # 综合情绪评分
        sentiment_score = self._calculate_sentiment_score(index_signals, news_sentiment)
        
        # 判断市场状态
        market_status = self._determine_market_status_v2(index_changes)
        
        # 生成预警级别
        alert_level = self._determine_alert_level(sentiment_score, index_changes)
        
        # 生成交易建议
        trading_suggestion = self._generate_trading_suggestion(
            market_status, sentiment_score, index_signals
        )
        
        return MarketSentiment(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            market_status=market_status,
            sentiment_score=sentiment_score,
            sentiment_label=self._get_sentiment_label(sentiment_score),
            index_signals=index_signals,
            news_count=news_sentiment.get('count', 0),
            alert_level=alert_level,
            trading_suggestion=trading_suggestion
        )
    
    def _calculate_index_signals(self, changes: Dict, daily_changes: Dict, adv_dec_data: Dict, cyb_data: Dict) -> Dict:
        """计算指数信号"""
        result = {}
        for label, change in changes.items():
            # 归一化评分 (-1 to 1)
            score = max(-1, min(1, change / 10))
            
            # 涨跌家数
            adv_dec = adv_dec_data.get(label, {'advance': 0, 'decline': 0})
            
            result[label] = {
                'change_30d': change,           # 30日涨跌
                'change_daily': daily_changes.get(label, 0),  # 当日涨跌
                'advance': adv_dec.get('advance', 0),   # 上涨家数
                'decline': adv_dec.get('decline', 0),     # 下跌家数
                'score': score,
                'weight': self.index_weights.get(label, 0.2)
            }
        
        # 添加创业板信号
        if cyb_data:
            result['CYB'] = {
                'change_30d': cyb_data.get('change_30d', 0),
                'change_daily': cyb_data.get('change_daily', 0),
                'advance': cyb_data.get('advance', 0),
                'decline': cyb_data.get('decline', 0),
                'score': cyb_data.get('score', 0),
                'weight': 0.25
            }
        
        return result
    
    def _get_cyb_data(self) -> Dict:
        """获取创业板数据"""
        import tushare as ts
        try:
            ts.set_token('39a3955e10adc24a28b08b459d9ea092dcd737c3a8c0df386bc84bd8')
            pro = ts.pro_api()
            
            # 获取创业板指数数据
            df = pro.index_daily(ts_code='399006.SZ', start_date='20260201', end_date='20260407')
            if df is None or len(df) == 0:
                return {}
            
            df = df.sort_values('trade_date')
            
            # 30日涨跌
            change_30d = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
            
            # 当日涨跌
            if len(df) >= 2:
                change_daily = (df['close'].iloc[-1] / df['close'].iloc[-2] - 1) * 100
            else:
                change_daily = 0
            
            # 获取创业板成分股涨跌家数
            # 创业板股票以300开头
            stocks = pro.stock_basic(ts_code='', list_status='L', exchange='SZSE')
            cyb_codes = stocks[stocks['ts_code'].str.startswith('300')]['ts_code'].tolist()
            
            # 获取今日涨跌（需要从日线数据计算）
            latest_date = df['trade_date'].iloc[-1]
            daily_df = pro.daily(trade_date=latest_date, fields='ts_code,close')
            
            # 计算前一交易日收盘价来获取涨跌
            if len(df) >= 2:
                prev_date = df['trade_date'].iloc[-2]
                prev_df = pro.daily(trade_date=prev_date, fields='ts_code,close')
                
                # 合并计算涨跌幅
                merged = daily_df.merge(prev_df, on='ts_code', suffixes=('_today', '_prev'))
                merged = merged[merged['ts_code'].isin(cyb_codes)]
                merged['pct_change'] = (merged['close_today'] - merged['close_prev']) / merged['close_prev'] * 100
                
                advance = len(merged[merged['pct_change'] > 0])
                decline = len(merged[merged['pct_change'] < 0])
            else:
                advance = 0
                decline = 0
            
            return {
                'change_30d': change_30d,
                'change_daily': change_daily,
                'advance': advance,
                'decline': decline,
                'score': max(-1, min(1, change_30d / 10))
            }
        except Exception as e:
            print(f"获取创业板数据失败: {e}")
            return {}
    
    def _get_advance_decline(self) -> Dict:
        """获取涨跌家数"""
        import pandas as pd
        try:
            adv_dec = pd.read_pickle('/tmp/advance_decline.pkl')
            latest = '20260407'
            
            # 映射: L->large, M->mid, S->small
            return {
                'L': adv_dec[latest]['large'],
                'M': adv_dec[latest]['mid'],
                'S': adv_dec[latest]['small']
            }
        except Exception as e:
            print(f"获取涨跌家数失败: {e}")
            return {'L': {'advance': 0, 'decline': 0},
                    'M': {'advance': 0, 'decline': 0},
                    'S': {'advance': 0, 'decline': 0}}
    
    def _analyze_news_sentiment(self) -> Dict:
        """分析舆情情绪"""
        try:
            collector = self._get_news_collector()
            news = collector.collect_from_api(limit=20)
            
            if not news:
                return {'count': 0, 'avg_score': 0}
            
            analyzer = self._get_sentiment_analyzer()
            scores = []
            
            for n in news:
                result = analyzer.analyze(
                    text=n.get('content', ''),
                    title=n.get('title', '')
                )
                scores.append(result.get('score', 0))
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            return {
                'count': len(news),
                'avg_score': avg_score,
                'scores': scores
            }
        except Exception as e:
            print(f"舆情分析失败: {e}")
            return {'count': 0, 'avg_score': 0}
    
    def _calculate_sentiment_score(self, index_signals: Dict, 
                                   news_sentiment: Dict) -> float:
        """计算综合情绪评分"""
        # 指数信号评分
        index_score = 0
        total_weight = 0
        
        for label, signal in index_signals.items():
            weight = signal['weight']
            score = signal['score']
            index_score += score * weight
            total_weight += weight
        
        if total_weight > 0:
            index_score /= total_weight
        
        # 舆情评分
        news_score = news_sentiment.get('avg_score', 0)
        
        # 综合评分 (指数60% + 舆情40%)
        combined = index_score * 0.6 + news_score * 0.4
        
        return combined
    
    def _determine_market_status_v2(self, changes: Dict) -> str:
        """判断市场状态(v2)"""
        if not changes:
            return "震荡"
        
        sorted_changes = sorted(changes.items(), key=lambda x: x[1], reverse=True)
        strongest = sorted_changes[0]
        weakest = sorted_changes[-1]
        divergence = strongest[1] - weakest[1]
        
        name_map = {'L': '大盘', 'M': '中盘', 'S': '小盘'}
        
        # 全部上涨
        if all(c > 0 for c in changes.values()):
            return "普涨"
        
        # 全部下跌
        if all(c < 0 for c in changes.values()):
            return "普跌"
        
        # 分化判断
        if divergence > 10:
            if strongest[0] == 'L' and weakest[0] == 'S':
                return "二八分化(大盘强/小盘弱)"
            elif strongest[0] == 'S' and weakest[0] == 'L':
                return "小盘活跃(小盘强/大盘弱)"
        
        if divergence > 5:
            return f"分化({name_map.get(strongest[0], strongest[0])}强/{name_map.get(weakest[0], weakest[0])}弱)"
        
        return "震荡"
    
    def _get_sentiment_label(self, score: float) -> str:
        """获取情绪标签"""
        if score > 0.3:
            return "乐观"
        elif score < -0.3:
            return "悲观"
        else:
            return "中性"
    
    def _determine_alert_level(self, sentiment_score: float, 
                                changes: Dict) -> str:
        """确定预警级别"""
        # 检查是否有异常涨跌
        extreme_change = any(abs(c) > 3 for c in changes.values()) if changes else False
        
        # 计算分化程度
        divergence = 0
        if changes and len(changes) > 1:
            divergence = max(changes.values()) - min(changes.values())
        
        if extreme_change or abs(sentiment_score) > 0.5:
            return "🔴 红色"
        elif abs(sentiment_score) > 0.3 or divergence > 3:
            return "🟠 橙色"
        elif abs(sentiment_score) > 0.1:
            return "🟡 黄色"
        else:
            return "⚪ 关注"
    
    def _generate_trading_suggestion(self, market_status: str,
                                      sentiment_score: float,
                                      index_signals: Dict) -> str:
        """生成交易建议"""
        suggestions = []
        
        # 基于情绪评分
        if sentiment_score > 0.3:
            suggestions.append("情绪偏多，可适当持仓")
        elif sentiment_score < -0.3:
            suggestions.append("情绪偏空，建议减仓观望")
        else:
            suggestions.append("情绪中性，保持仓位")
        
        # 基于市场状态
        if "二八" in market_status or "大盘主导" in market_status:
            suggestions.append("配置大盘蓝筹")
        elif "小盘弱势" in market_status:
            suggestions.append("回避小盘股")
        
        # 基于指数信号
        for label, signal in index_signals.items():
            name = {'L': '大盘', 'M': '中盘', 'S': '小盘'}.get(label, label)
            daily = signal.get('change_daily', 0)
            change_30d = signal.get('change_30d', 0)
            
            if daily > 1:
                suggestions.append(f"{name}当日强势")
            elif daily < -1:
                suggestions.append(f"{name}当日走弱")
            
            if change_30d > 3:
                suggestions.append(f"{name}月线强势")
            elif change_30d < -3:
                suggestions.append(f"{name}月线弱势")
        
        return "; ".join(suggestions) if suggestions else "观望"
    
    def get_daily_sentiment_report(self, trade_date: str = None) -> Dict:
        """
        获取每日情绪报告
        
        Args:
            trade_date: 交易日期
        
        Returns:
            Dict: 完整报告
        """
        sentiment = self.get_market_sentiment(trade_date)
        
        report = {
            'report_time': sentiment.timestamp,
            'trade_date': trade_date,
            'market_status': sentiment.market_status,
            'sentiment': {
                'score': sentiment.sentiment_score,
                'label': sentiment.sentiment_label
            },
            'index_details': {},
            'alert_level': sentiment.alert_level,
            'trading_suggestion': sentiment.trading_suggestion,
            'news_count': sentiment.news_count
        }
        
        # 添加各指数详情
        name_map = {'L': '大盘', 'M': '中盘', 'S': '小盘'}
        for label, data in sentiment.index_signals.items():
            report['index_details'][name_map.get(label, label)] = {
                'change_daily_pct': data['change_daily'],
                'change_30d_pct': data['change_30d'],
                'signal_score': data['score'],
                'weight': data['weight']
            }
        
        return report


# ==================== 测试 ====================
def test_integration():
    """测试集成系统"""
    print("=" * 70)
    print("情绪指数与自定义指数集成测试")
    print("=" * 70)
    
    integrator = IndexSentimentIntegration()
    
    print("\n【市场情绪分析】")
    sentiment = integrator.get_market_sentiment('20260407')
    
    print(f"  时间: {sentiment.timestamp}")
    print(f"  市场状态: {sentiment.market_status}")
    print(f"  情绪评分: {sentiment.sentiment_score:.3f} ({sentiment.sentiment_label})")
    print(f"  预警级别: {sentiment.alert_level}")
    print(f"  新闻数量: {sentiment.news_count}")
    
    print(f"\n  指数信号:")
    for label, data in sentiment.index_signals.items():
        name = {'L': '大盘', 'M': '中盘', 'S': '小盘'}.get(label, label)
        daily = data['change_daily']
        change_30d = data['change_30d']
        daily_str = f"{daily:+.2f}%" if daily else "N/A"
        change_str = f"{change_30d:+.2f}%" if change_30d else "N/A"
        print(f"    {name}: 当日{daily_str}, 30日{change_str}")
    
    print(f"\n  交易建议: {sentiment.trading_suggestion}")
    
    print("\n✅ 测试完成!")


if __name__ == '__main__':
    test_integration()