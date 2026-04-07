# -*- coding: utf-8 -*-
"""
RSS 采集器 - 财联社等财经媒体
⛏️ 淘金者舆情监控系统
"""

import feedparser
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import hashlib
import yaml
import os


class RSSCollector:
    """
    RSS 采集器
    
    功能:
    - 多 RSS 源采集
    - 增量更新
    - 内容解析
    - 去重过滤
    """
    
    def __init__(self, config_file: str = None):
        """
        初始化
        
        Args:
            config_file: 配置文件路径
        """
        self.config = self._load_config(config_file)
        self.session_hashes = {}  # 每个 RSS 源的采集历史
        self.last_update = {}  # 最后更新时间
        
        # 设置 User-Agent (更真实的浏览器标识)
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/rss+xml, application/xml, text/xml, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
    
    def _load_config(self, config_file: str) -> Dict:
        """加载配置文件"""
        if config_file is None:
            # 默认配置路径
            config_file = os.path.join(
                os.path.dirname(__file__),
                '..',
                'config',
                'rss_feeds.yaml'
            )
        
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"加载配置文件失败：{e}")
            return {}
    
    def collect_from_feed(self, feed_name: str, limit: int = 20) -> List[Dict]:
        """
        从指定 RSS 源采集
        
        Args:
            feed_name: RSS 源名称 (如 'telegraph', 'stock', 'news')
            limit: 数量限制
        
        Returns:
            List[Dict]: 新闻列表
        """
        # 获取 RSS 配置
        rss_config = self.config.get('cls_rss', {}).get(feed_name)
        if not rss_config:
            # 尝试从 other_rss 查找
            rss_config = self.config.get('other_rss', {}).get(feed_name)
        
        if not rss_config:
            print(f"未找到 RSS 源配置：{feed_name}")
            return []
        
        feed_url = rss_config.get('url')
        weight = rss_config.get('weight', 0.5)
        category = rss_config.get('category', '未知')
        
        print(f"采集 {rss_config.get('name', feed_name)}: {feed_url}")
        
        try:
            # 解析 RSS Feed
            feed = feedparser.parse(feed_url, request_headers=self.headers)
            
            news_list = []
            
            for entry in feed.entries[:limit]:
                news = self._parse_entry(entry, rss_config)
                
                if news:
                    # 去重
                    if self._is_duplicate(feed_name, news):
                        continue
                    
                    # 添加元数据
                    news['source_weight'] = weight
                    news['category'] = category
                    news['feed_name'] = feed_name
                    
                    news_list.append(news)
            
            # 更新采集历史
            self._update_hashes(feed_name, news_list)
            self.last_update[feed_name] = datetime.now()
            
            print(f"   采集到 {len(news_list)} 条新闻")
            return news_list
        
        except Exception as e:
            print(f"RSS 采集失败：{e}")
            return []
    
    def _parse_entry(self, entry, rss_config: Dict) -> Optional[Dict]:
        """
        解析 RSS 条目
        
        Args:
            entry: RSS 条目
            rss_config: RSS 配置
        
        Returns:
            Dict: 新闻字典
        """
        try:
            # 提取标题
            title = getattr(entry, 'title', '')
            if not title:
                return None
            
            # 提取内容
            content = ''
            if hasattr(entry, 'summary'):
                content = entry.summary
            elif hasattr(entry, 'description'):
                content = entry.description
            elif hasattr(entry, 'content') and len(entry.content) > 0:
                content = entry.content[0].value
            
            # 提取发布时间
            publish_time = ''
            if hasattr(entry, 'published'):
                publish_time = entry.published
            elif hasattr(entry, 'updated'):
                publish_time = entry.updated
            
            # 提取链接
            url = getattr(entry, 'link', '')
            
            # 内容过滤
            if self._should_filter(title, content):
                return None
            
            news = {
                'title': title,
                'content': content[:500] if content else title,  # 限制长度
                'source': rss_config.get('name', 'RSS'),
                'publish_time': publish_time,
                'url': url,
                'feed_url': rss_config.get('url', ''),
            }
            
            return news
        
        except Exception as e:
            print(f"解析 RSS 条目失败：{e}")
            return None
    
    def _should_filter(self, title: str, content: str) -> bool:
        """
        检查是否应该过滤
        
        Args:
            title: 标题
            content: 内容
        
        Returns:
            bool: 是否过滤
        """
        # 最小长度检查
        min_length = self.config.get('rss_settings', {}).get('content_filter', {}).get('min_length', 20)
        if len(title) < min_length:
            return True
        
        # 关键词过滤
        filter_keywords = self.config.get('rss_settings', {}).get('content_filter', {}).get('filter_keywords', [])
        text = f"{title} {content}".lower()
        
        for keyword in filter_keywords:
            if keyword.lower() in text:
                return True
        
        return False
    
    def _is_duplicate(self, feed_name: str, news: Dict) -> bool:
        """检查是否重复"""
        content = f"{news['title']}{news.get('content', '')}"
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        if feed_name not in self.session_hashes:
            self.session_hashes[feed_name] = set()
        
        if content_hash in self.session_hashes[feed_name]:
            return True
        
        self.session_hashes[feed_name].add(content_hash)
        
        # 限制缓存大小
        if len(self.session_hashes[feed_name]) > 5000:
            self.session_hashes[feed_name] = set(
                list(self.session_hashes[feed_name])[:2000]
            )
        
        return False
    
    def _update_hashes(self, feed_name: str, news_list: List[Dict]):
        """更新采集历史"""
        if feed_name not in self.session_hashes:
            self.session_hashes[feed_name] = set()
        
        for news in news_list:
            content = f"{news['title']}{news.get('content', '')}"
            content_hash = hashlib.md5(content.encode()).hexdigest()
            self.session_hashes[feed_name].add(content_hash)
    
    def collect_all(self, limit_per_feed: int = 10) -> List[Dict]:
        """
        采集所有 RSS 源
        
        Args:
            limit_per_feed: 每个源的数量限制
        
        Returns:
            List[Dict]: 新闻列表
        """
        all_news = []
        
        # 采集财联社 RSS
        for feed_name in ['telegraph', 'stock', 'news']:
            news_list = self.collect_from_feed(feed_name, limit_per_feed)
            all_news.extend(news_list)
        
        # 采集其他 RSS
        for feed_name in self.config.get('other_rss', {}).keys():
            news_list = self.collect_from_feed(feed_name, limit_per_feed)
            all_news.extend(news_list)
        
        # 按发布时间排序
        all_news.sort(
            key=lambda x: x.get('publish_time', ''),
            reverse=True
        )
        
        return all_news
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            'total_feeds': 0,
            'total_hashes': 0,
            'last_update': {}
        }
        
        for feed_name in list(self.config.get('cls_rss', {}).keys()) + \
                         list(self.config.get('other_rss', {}).keys()):
            stats['total_feeds'] += 1
            
            if feed_name in self.session_hashes:
                stats['total_hashes'] += len(self.session_hashes[feed_name])
            
            if feed_name in self.last_update:
                stats['last_update'][feed_name] = self.last_update[feed_name].strftime('%Y-%m-%d %H:%M:%S')
        
        return stats


# ==================== 测试 ====================
def test_rss_collector():
    """测试 RSS 采集器"""
    print("=" * 70)
    print("RSS 采集器测试 - 财联社")
    print("=" * 70)
    
    collector = RSSCollector()
    
    # 测试财联社电报
    print("\n1. 测试财联社电报...")
    news_list = collector.collect_from_feed('telegraph', limit=5)
    
    for i, news in enumerate(news_list[:3], 1):
        print(f"\n   [{i}] {news['title']}")
        print(f"       来源：{news['source']}")
        print(f"       时间：{news.get('publish_time', '未知')}")
        print(f"       链接：{news.get('url', 'N/A')[:80]}...")
    
    # 测试财联社 A 股
    print("\n2. 测试财联社 A 股...")
    news_list = collector.collect_from_feed('stock', limit=5)
    print(f"   采集到 {len(news_list)} 条新闻")
    
    # 测试财联社要闻
    print("\n3. 测试财联社要闻...")
    news_list = collector.collect_from_feed('news', limit=5)
    print(f"   采集到 {len(news_list)} 条新闻")
    
    # 统计信息
    print("\n4. 采集统计:")
    stats = collector.get_stats()
    print(f"   RSS 源数量：{stats['total_feeds']}")
    print(f"   去重缓存：{stats['total_hashes']} 条")
    print(f"   最后更新：{stats['last_update']}")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    test_rss_collector()
