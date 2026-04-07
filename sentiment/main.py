#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
A 股舆情监控系统 - 主程序
⛏️ 淘金者版 - 3 分钟黄金窗口
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from datetime import datetime
from typing import Dict
from nlp.sentiment_analyzer import SentimentAnalyzer
from crawler.news_collector import NewsCollector, ScheduledCollector
from alert.feishu_bot import FeishuAlertBot


class SentimentMonitor:
    """
    舆情监控系统
    
    整合:
    - 数据采集
    - NLP 分析
    - 预警推送
    """
    
    def __init__(self, feishu_webhook: str = None):
        """
        初始化
        
        Args:
            feishu_webhook: 飞书 Webhook URL
        """
        self.analyzer = SentimentAnalyzer()
        self.collector = NewsCollector()
        self.alert_bot = FeishuAlertBot(feishu_webhook)
        
        self.stats = {
            'total_news': 0,
            'alerts_sent': 0,
            'start_time': datetime.now()
        }
    
    def process_news(self, news: Dict) -> Dict:
        """
        处理单条新闻
        
        Args:
            news: 新闻 {
                'title': '...',
                'content': '...',
                'source': '...',
                'publish_time': '...',
                'url': '...'
            }
        
        Returns:
            Dict: 分析结果
        """
        # 1. 情感分析
        result = self.analyzer.analyze(
            text=news.get('content', ''),
            title=news.get('title', '')
        )
        
        # 2. 计算权重
        weight = self.collector.calculate_weight(news)
        result['weight'] = weight
        
        # 3. 调整预警级别 (考虑权重)
        if weight < 0.5:  # 低权重来源降级
            level_map = {
                '🔴 红色': '🟠 橙色',
                '🟠 橙色': '🟡 黄色',
                '🟡 黄色': '🔵 蓝色',
            }
            result['level'] = level_map.get(result['level'], result['level'])
        
        # 4. 添加新闻元数据
        result['news'] = news
        
        return result
    
    def check_and_alert(self, result: Dict) -> bool:
        """
        检查是否需要告警
        
        Args:
            result: 分析结果
        
        Returns:
            bool: 是否发送告警
        """
        # 告警阈值
        alert_thresholds = {
            '🔴 红色': True,    # 重大事件
            '🟠 橙色': True,    # 重要事件
            '🟡 黄色': True,    # 一般事件
            '🔵 蓝色': False,   # 关注事件 (不推送)
            '⚪ 关注': False,   # 仅记录
        }
        
        level = result.get('level', '⚪ 关注')
        
        if not alert_thresholds.get(level, False):
            return False
        
        # 构建告警
        entities = result.get('entities', [])
        if not entities:
            return False  # 无实体，不告警
        
        for entity in entities:
            if entity.get('type') != 'stock':
                continue
            
            alert = {
                'level': level,
                'stock': entity.get('name', ''),
                'code': entity.get('code', ''),
                'title': result['news'].get('title', ''),
                'source': result['news'].get('source', ''),
                'score': result.get('score', 0),
                'content': result['news'].get('content', '')[:200],
                'timestamp': result.get('timestamp', '')
            }
            
            # 发送告警
            if self.alert_bot.send_alert(alert):
                self.stats['alerts_sent'] += 1
        
        return True
    
    def run_once(self) -> Dict:
        """
        运行一次采集 - 分析 - 告警流程
        
        Returns:
            Dict: 运行结果统计
        """
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 开始采集...")
        
        # 1. 采集新闻
        news_list = self.collector.collect_from_api(limit=20)
        self.stats['total_news'] += len(news_list)
        
        if not news_list:
            print("   无新新闻")
            return self.stats
        
        print(f"   采集到 {len(news_list)} 条新闻")
        
        # 2. 处理每条新闻
        alerts_count = 0
        for news in news_list:
            result = self.process_news(news)
            
            # 检查是否需要告警
            if self.check_and_alert(result):
                alerts_count += 1
        
        print(f"   触发告警：{alerts_count} 条")
        
        return self.stats
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        running_time = (datetime.now() - self.stats['start_time']).total_seconds() / 60
        
        return {
            **self.stats,
            'running_time_minutes': round(running_time, 2),
            'news_per_minute': round(self.stats['total_news'] / max(running_time, 1), 2)
        }


# ==================== 命令行接口 ====================
def cmd_monitor(args):
    """启动监控"""
    print("=" * 70)
    print("A 股舆情监控系统 - 淘金者版")
    print("=" * 70)
    print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Webhook: {'已配置' if args.webhook else '未配置'}")
    print("=" * 70)
    
    monitor = SentimentMonitor(feishu_webhook=args.webhook)
    
    try:
        # 运行一次测试
        if args.test:
            print("\n【测试模式】运行一次...")
            stats = monitor.run_once()
            print(f"\n统计：{stats}")
            return
        
        # 持续监控
        print("\n【监控模式】开始实时监控...")
        print("按 Ctrl+C 停止\n")
        
        import time
        while True:
            monitor.run_once()
            
            # 等待 1 分钟
            time.sleep(60)
    
    except KeyboardInterrupt:
        print("\n\n停止监控...")
        stats = monitor.get_stats()
        print(f"\n运行统计:")
        print(f"  运行时间：{stats['running_time_minutes']:.1f} 分钟")
        print(f"  处理新闻：{stats['total_news']} 条")
        print(f"  发送告警：{stats['alerts_sent']} 条")
        print(f"  处理速度：{stats['news_per_minute']:.1f} 条/分钟")


def cmd_analyze(args):
    """分析单条新闻"""
    print("=" * 70)
    print("舆情分析工具")
    print("=" * 70)
    
    analyzer = SentimentAnalyzer()
    
    title = args.title
    content = args.content
    
    print(f"\n标题：{title}")
    print(f"内容：{content[:100]}...")
    
    result = analyzer.analyze(text=content, title=title)
    
    print(f"\n分析结果:")
    print(f"  情感分数：{result['score']:.3f}")
    print(f"  情感标签：{result['label']}")
    print(f"  预警级别：{result['level']}")
    print(f"  识别实体：{[e['name'] for e in result['entities']]}")
    print(f"  关键词：{result['keywords']}")
    print(f"  事件类型：{result['event_type']}")


# ==================== 主程序 ====================
if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='A 股舆情监控系统')
    subparsers = parser.add_subparsers(dest='command')
    
    # monitor 命令
    monitor_parser = subparsers.add_parser('monitor', help='启动监控')
    monitor_parser.add_argument('--webhook', '-w', help='飞书 Webhook URL')
    monitor_parser.add_argument('--test', '-t', action='store_true', help='测试模式')
    monitor_parser.set_defaults(func=cmd_monitor)
    
    # analyze 命令
    analyze_parser = subparsers.add_parser('analyze', help='分析新闻')
    analyze_parser.add_argument('--title', '-t', required=True, help='新闻标题')
    analyze_parser.add_argument('--content', '-c', required=True, help='新闻内容')
    analyze_parser.set_defaults(func=cmd_analyze)
    
    args = parser.parse_args()
    
    if args.command is None:
        parser.print_help()
    else:
        args.func(args)
