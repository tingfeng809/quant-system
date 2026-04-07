# -*- coding: utf-8 -*-
"""
可信度评分与谣言识别
⛏️ 淘金者舆情监控系统 v2.0
"""

from typing import Dict, List
from datetime import datetime
import re


class CredibilityScorer:
    """
    可信度评分器
    
    评估新闻可信度:
    - 来源权威性
    - 多源交叉验证
    - 内容质量
    - 时效性
    """
    
    def __init__(self):
        # 来源权威性评分
        self.source_authority = {
            # 官方渠道 (1.0)
            '巨潮资讯': 1.0,
            '上交所': 1.0,
            '深交所': 1.0,
            '证监会': 1.0,
            
            # 权威媒体 (0.8-0.9)
            '财联社': 0.9,
            '证券时报': 0.85,
            '上海证券报': 0.85,
            '中国证券报': 0.85,
            '财新网': 0.8,
            
            # 财经媒体 (0.6-0.7)
            '东方财富': 0.65,
            '同花顺': 0.65,
            '新浪财经': 0.6,
            '搜狐财经': 0.6,
            '腾讯财经': 0.6,
            
            # 社交平台 (0.3-0.4)
            '雪球': 0.35,
            '淘股吧': 0.3,
            '微博': 0.3,
        }
        
        # 谣言特征词
        self.rumor_keywords = [
            '内幕消息',
            '稳赚不赔',
            '推荐牛股',
            '加 QQ 群',
            '加微信',
            '收费',
            '保本',
            '翻倍',
            '庄家',
            '主力爆料',
        ]
        
        # 可信度关键词
        self.credible_keywords = [
            '公告',
            '披露',
            '证监会批准',
            '交易所',
            '董事会决议',
            '股东大会',
            '审计',
            '律师',
        ]
    
    def calculate(self, news: Dict, cross_sources: int = 0) -> Dict:
        """
        计算可信度评分
        
        Args:
            news: 新闻字典
            cross_sources: 交叉验证来源数
        
        Returns:
            Dict: 评分详情
        """
        score = 0.0
        details = {}
        
        # 1. 来源权威性 (40%)
        source = news.get('source', '')
        authority_score = self.source_authority.get(source, 0.5)
        score += authority_score * 0.4
        details['authority'] = authority_score
        
        # 2. 多源交叉验证 (30%)
        cross_score = min(cross_sources * 0.15, 0.45)
        score += cross_score * 0.3
        details['cross_validation'] = cross_score
        
        # 3. 内容质量 (20%)
        content_score = self._evaluate_content(news)
        score += content_score * 0.2
        details['content_quality'] = content_score
        
        # 4. 时效性 (10%)
        time_score = self._evaluate_timeliness(news)
        score += time_score * 0.1
        details['timeliness'] = time_score
        
        # 5. 谣言检测 (扣分项)
        rumor_score = self._detect_rumor(news)
        score -= rumor_score * 0.3
        details['rumor_risk'] = rumor_score
        
        # 归一化到 [0, 1]
        final_score = max(0, min(score, 1.0))
        
        return {
            'total_score': round(final_score, 3),
            'level': self._score_to_level(final_score),
            'details': details,
            'is_rumor': rumor_score > 0.5
        }
    
    def _evaluate_content(self, news: Dict) -> float:
        """评估内容质量"""
        score = 0.5  # 基础分
        
        title = news.get('title', '')
        content = news.get('content', '')
        text = f"{title} {content}"
        
        # 有具体数据加分
        if re.search(r'\d+%', text) or re.search(r'\d+ 亿元', text):
            score += 0.2
        
        # 有公司名称/代码加分
        if re.search(r'\d{6}\.\w{2}', text):
            score += 0.1
        
        # 有可信度关键词加分
        for keyword in self.credible_keywords:
            if keyword in text:
                score += 0.1
                break
        
        # 内容过短减分
        if len(text) < 50:
            score -= 0.2
        
        return max(0, min(score, 1.0))
    
    def _evaluate_timeliness(self, news: Dict) -> float:
        """评估时效性"""
        publish_time = news.get('publish_time', '')
        
        if not publish_time:
            return 0.5
        
        try:
            pub_datetime = datetime.strptime(publish_time, '%Y-%m-%d %H:%M:%S')
            hours_old = (datetime.now() - pub_datetime).total_seconds() / 3600
            
            if hours_old < 1:
                return 1.0
            elif hours_old < 6:
                return 0.9
            elif hours_old < 24:
                return 0.7
            elif hours_old < 72:
                return 0.5
            else:
                return 0.3
        except:
            return 0.5
    
    def _detect_rumor(self, news: Dict) -> float:
        """
        检测谣言风险
        
        Returns:
            float: 谣言概率 [0, 1]
        """
        risk_score = 0.0
        
        title = news.get('title', '')
        content = news.get('content', '')
        text = f"{title} {content}".lower()
        
        # 检查谣言关键词
        for keyword in self.rumor_keywords:
            if keyword.lower() in text:
                risk_score += 0.3
        
        # 来源是社交平台加分
        source = news.get('source', '')
        if source in ['雪球', '淘股吧', '微博']:
            risk_score += 0.2
        
        # 没有明确来源加分
        if not source or source == '未知':
            risk_score += 0.3
        
        return min(risk_score, 1.0)
    
    def _score_to_level(self, score: float) -> str:
        """分数转等级"""
        if score >= 0.8:
            return '可信'
        elif score >= 0.6:
            return '较可信'
        elif score >= 0.4:
            return '一般'
        elif score >= 0.2:
            return '存疑'
        else:
            return '不可信'


class CrossValidator:
    """
    交叉验证器
    
    功能:
    - 多源比对
    - 一致性检查
    - 冲突检测
    """
    
    def __init__(self):
        self.news_groups = {}  # 按事件分组
    
    def group_news(self, news_list: List[Dict]) -> Dict:
        """
        将新闻按事件分组
        
        Args:
            news_list: 新闻列表
        
        Returns:
            Dict: 分组结果
        """
        groups = {}
        
        for news in news_list:
            # 提取关键信息用于分组
            title = news.get('title', '')
            stock_code = self._extract_stock_code(title)
            event_type = self._extract_event_type(title)
            
            # 分组 key
            key = f"{stock_code}_{event_type}"
            
            if key not in groups:
                groups[key] = []
            
            groups[key].append(news)
        
        self.news_groups = groups
        return groups
    
    def validate(self, group_key: str) -> Dict:
        """
        验证某组新闻的一致性
        
        Args:
            group_key: 分组 key
        
        Returns:
            Dict: 验证结果
        """
        if group_key not in self.news_groups:
            return {'valid': False, 'reason': '分组不存在'}
        
        news_list = self.news_groups[group_key]
        
        if len(news_list) < 2:
            return {
                'valid': True,
                'confidence': 'low',
                'reason': '单一来源，无法交叉验证'
            }
        
        # 检查一致性
        sources = set(n.get('source', '') for n in news_list)
        sentiments = []
        
        for news in news_list:
            # TODO: 调用情感分析
            sentiments.append(news.get('sentiment', 0))
        
        # 多源一致
        if len(sources) >= 3:
            return {
                'valid': True,
                'confidence': 'high',
                'reason': f'{len(sources)} 个独立来源交叉验证',
                'sources': list(sources)
            }
        
        # 双源验证
        if len(sources) == 2:
            return {
                'valid': True,
                'confidence': 'medium',
                'reason': '双源验证',
                'sources': list(sources)
            }
        
        return {
            'valid': True,
            'confidence': 'low',
            'reason': '单一来源'
        }
    
    def _extract_stock_code(self, text: str) -> str:
        """提取股票代码"""
        import re
        match = re.search(r'(\d{6})\.(SH|SZ|BJ)', text)
        if match:
            return match.group(1)
        return 'unknown'
    
    def _extract_event_type(self, text: str) -> str:
        """提取事件类型"""
        event_keywords = {
            '业绩': ['业绩', '预增', '预亏', '利润'],
            '并购': ['并购', '重组', '收购'],
            '减持': ['减持', '套现'],
            '中标': ['中标', '合同'],
            '处罚': ['处罚', '调查', '问询'],
        }
        
        for event_type, keywords in event_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    return event_type
        
        return 'other'


# ==================== 测试 ====================
def test_credibility():
    """测试可信度评分"""
    print("=" * 70)
    print("可信度评分与谣言识别测试")
    print("=" * 70)
    
    scorer = CredibilityScorer()
    
    # 测试用例
    test_cases = [
        {
            'title': '贵州茅台发布业绩预告 预计净利润增长 50%',
            'content': '公司披露 2026 年上半年业绩预告...',
            'source': '巨潮资讯',
            'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'title': '内幕消息！这只股票明天涨停！加 QQ 群领取',
            'content': '稳赚不赔，保本翻倍...',
            'source': '微博',
            'publish_time': ''
        },
        {
            'title': '宁德时代中标 50 亿订单',
            'content': '公司收到中标通知书...',
            'source': '财联社',
            'publish_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
    ]
    
    for i, news in enumerate(test_cases, 1):
        result = scorer.calculate(news, cross_sources=i)
        
        print(f"\n测试 {i}: {news['title'][:40]}...")
        print(f"  可信度分数：{result['total_score']:.3f}")
        print(f"  可信度等级：{result['level']}")
        print(f"  谣言风险：{'⚠️ 高' if result['is_rumor'] else '✅ 低'}")
        print(f"  评分详情:")
        for key, value in result['details'].items():
            print(f"    {key}: {value:.2f}")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    test_credibility()
