# -*- coding: utf-8 -*-
"""
舆情情感分析模块
⛏️ 淘金者版 - 基于真实新闻数据
"""

import jieba
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime
import re


class SentimentAnalyzer:
    """
    情感分析器
    
    功能:
    - 情感打分 [-1.0, 1.0]
    - 实体识别 (公司名/股票代码)
    - 事件分类
    """
    
    def __init__(self):
        # 情感词典 (简化版，实际应使用完整词典)
        self.positive_words = {
            '增长': 0.5, '上涨': 0.6, '突破': 0.7, '创新': 0.6,
            '利好': 0.7, '预增': 0.6, '扭亏': 0.8, '重组': 0.7,
            '并购': 0.6, '增持': 0.5, '回购': 0.5, '中标': 0.7,
            '分红': 0.4, '送转': 0.4, '合作': 0.4, '战略': 0.3,
        }
        
        self.negative_words = {
            '下跌': -0.6, '下滑': -0.5, '下降': -0.5, '亏损': -0.7,
            '利空': -0.7, '预亏': -0.6, '减持': -0.5, '解禁': -0.4,
            '诉讼': -0.5, '仲裁': -0.5, '处罚': -0.6, '调查': -0.7,
            'ST': -0.8, '*ST': -0.9, '退市': -1.0, '违约': -0.8,
            '警示函': -0.5, '监管函': -0.5, '问询函': -0.4,
        }
        
        # 程度副词
        self.degree_words = {
            '大幅': 1.5, '显著': 1.3, '明显': 1.2,
            '小幅': 0.7, '略有': 0.6, '轻微': 0.5,
            '非常': 1.5, '特别': 1.5, '极其': 1.8,
        }
        
        # 否定词
        self.negation_words = ['不', '未', '没', '无', '非', '否']
        
        # 加载股票池映射
        self.stock_map = self._load_stock_map()
    
    def _load_stock_map(self) -> Dict:
        """加载股票名称 - 代码映射"""
        # 简化版，实际应从配置文件加载
        return {
            '贵州茅台': '600519.SH',
            '茅台': '600519.SH',
            '五粮液': '000858.SZ',
            '宁德时代': '300750.SZ',
            '宁德': '300750.SZ',
            '比亚迪': '002594.SZ',
            '平安银行': '000001.SZ',
            '平安': '000001.SZ',  # 可能有歧义，需要上下文判断
            '招商银行': '600036.SH',
            '招行': '600036.SH',
        }
    
    def analyze(self, text: str, title: str = '') -> Dict:
        """
        情感分析
        
        Args:
            text: 新闻内容
            title: 新闻标题
        
        Returns:
            Dict: {
                'score': float,  # 情感分数 [-1.0, 1.0]
                'label': str,    # 情感标签
                'entities': List,  # 识别到的实体
                'keywords': List,  # 关键词
                'level': str     # 预警级别
            }
        """
        # 合并标题和正文 (标题权重更高)
        full_text = f"{title}。{text}" if title else text
        
        # 分词
        words = list(jieba.cut(full_text))
        
        # 情感打分
        score, keywords = self._calculate_score(words)
        
        # 实体识别
        entities = self._extract_entities(full_text)
        
        # 事件分类
        event_type = self._classify_event(words, keywords)
        
        # 确定预警级别
        level = self._determine_level(score)
        
        return {
            'score': round(score, 3),
            'label': self._score_to_label(score),
            'entities': entities,
            'keywords': keywords,
            'event_type': event_type,
            'level': level,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def _calculate_score(self, words: List[str]) -> Tuple[float, List[str]]:
        """
        计算情感分数
        
        Returns:
            (score, keywords)
        """
        score = 0.0
        keywords = []
        
        i = 0
        while i < len(words):
            word = words[i]
            
            # 检查程度副词
            degree = 1.0
            if i > 0 and words[i-1] in self.degree_words:
                degree = self.degree_words[words[i-1]]
            
            # 检查否定词
            negation = False
            if i > 0 and words[i-1] in self.negation_words:
                negation = True
            
            # 正向情感词
            if word in self.positive_words:
                word_score = self.positive_words[word] * degree
                if negation:
                    word_score = -word_score * 0.5  # 否定减弱
                score += word_score
                keywords.append(word)
            
            # 负向情感词
            elif word in self.negative_words:
                word_score = self.negative_words[word] * degree
                if negation:
                    word_score = -word_score * 0.5
                score += word_score
                keywords.append(word)
            
            i += 1
        
        # 归一化到 [-1.0, 1.0]
        if score > 1.0:
            score = 1.0
        elif score < -1.0:
            score = -1.0
        
        return score, keywords
    
    def _extract_entities(self, text: str) -> List[Dict]:
        """
        提取实体 (公司名、股票代码)
        
        Returns:
            List[Dict]: [
                {'name': '贵州茅台', 'code': '600519.SH', 'type': 'stock'},
                {'name': '白酒', 'type': 'industry'}
            ]
        """
        entities = []
        
        # 匹配股票代码
        stock_code_pattern = r'(\d{6})\.(SH|SZ|BJ)'
        codes = re.findall(stock_code_pattern, text)
        for code, exchange in codes:
            ts_code = f"{code}.{exchange}"
            entities.append({
                'name': ts_code,
                'code': ts_code,
                'type': 'stock'
            })
        
        # 匹配公司名/股票简称
        for name, code in self.stock_map.items():
            if name in text:
                entities.append({
                    'name': name,
                    'code': code,
                    'type': 'stock'
                })
        
        # 去重
        seen = set()
        unique_entities = []
        for entity in entities:
            key = entity['code']
            if key not in seen:
                seen.add(key)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _classify_event(self, words: List[str], keywords: List[str]) -> str:
        """
        事件分类
        
        Returns:
            str: 事件类型
        """
        # 经营类
        if any(w in keywords for w in ['业绩', '预增', '预亏', '中标', '合同']):
            return '经营'
        
        # 资本类
        if any(w in keywords for w in ['重组', '并购', '定增', '配股']):
            return '资本'
        
        # 股东类
        if any(w in keywords for w in ['增持', '减持', '解禁', '回购']):
            return '股东'
        
        # 风险类
        if any(w in keywords for w in ['ST', '退市', '调查', '诉讼', '处罚']):
            return '风险'
        
        # 政策类
        if any(w in keywords for w in ['政策', '监管', '补贴', '税收']):
            return '政策'
        
        # 市场类
        if any(w in keywords for w in ['价格', '涨价', '降价', '竞争']):
            return '市场'
        
        return '其他'
    
    def _score_to_label(self, score: float) -> str:
        """分数转标签"""
        if score >= 0.7:
            return '重大利好'
        elif score >= 0.3:
            return '利好'
        elif score >= -0.3:
            return '中性'
        elif score >= -0.7:
            return '利空'
        else:
            return '重大利空'
    
    def _determine_level(self, score: float) -> str:
        """确定预警级别"""
        if abs(score) >= 0.8:
            return '🔴 红色'
        elif abs(score) >= 0.6:
            return '🟠 橙色'
        elif abs(score) >= 0.4:
            return '🟡 黄色'
        elif abs(score) >= 0.2:
            return '🔵 蓝色'
        else:
            return '⚪ 关注'


# ==================== 测试 ====================
def test_sentiment_analyzer():
    """测试情感分析器"""
    print("=" * 70)
    print("舆情情感分析测试")
    print("=" * 70)
    
    analyzer = SentimentAnalyzer()
    
    # 测试用例
    test_cases = [
        {
            'title': '贵州茅台业绩预增 50%',
            'text': '公司发布业绩预告，预计净利润同比增长 50%',
            'expected': '利好'
        },
        {
            'title': '宁德时代中标 50 亿订单',
            'text': '公司中标某大型电池采购项目，金额约 50 亿元',
            'expected': '利好'
        },
        {
            'title': '某公司大股东减持 1%',
            'text': '控股股东通过集中竞价减持公司股份 1%',
            'expected': '利空'
        },
        {
            'title': '*ST 公司收到退市风险警示',
            'text': '因连续三年亏损，公司股票将被实施退市风险警示',
            'expected': '重大利空'
        },
    ]
    
    for i, case in enumerate(test_cases, 1):
        result = analyzer.analyze(case['title'], case['text'])
        print(f"\n测试 {i}: {case['title']}")
        print(f"  情感分数：{result['score']:.3f}")
        print(f"  情感标签：{result['label']}")
        print(f"  预警级别：{result['level']}")
        print(f"  识别实体：{[e['name'] for e in result['entities']]}")
        print(f"  关键词：{result['keywords']}")
        print(f"  事件类型：{result['event_type']}")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    test_sentiment_analyzer()
