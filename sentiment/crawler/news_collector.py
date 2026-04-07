# -*- coding: utf-8 -*-
"""
新闻采集器
⛏️ 淘金者版 - 合规采集，多源验证
"""

import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict
import hashlib


class NewsCollector:
    """
    新闻采集器
    
    功能:
    - API 调用 (优先)
    - RSS 订阅
    - 爬虫采集 (合规)
    - 去重过滤
    """
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (compatible; OpenClaw Sentiment Bot/1.0)'
        })
        
        # 采集历史 (用于去重)
        self.collected_hashes = set()
        
        # 来源权重
        self.source_weights = {
            '巨潮资讯': 1.0,
            '上交所': 1.0,
            '深交所': 1.0,
            '财联社': 0.8,
            '东方财富': 0.6,
            '新浪财经': 0.6,
        }
        
        # Tushare API 限流追踪
        self._last_api_call = 0
        self._api_call_interval = 65  # 65秒间隔 (略多于1分钟)
        self._api_cooldown = False
        self._cooldown_until = 0
    
    def collect_from_api(self, stock_code: str = None, 
                         limit: int = 10) -> List[Dict]:
        """
        从 API 采集新闻（多源）
        
        Args:
            stock_code: 股票代码 (可选，不传则采集全市场)
            limit: 数量限制
        
        Returns:
            List[Dict]: 新闻列表
        """
        news_list = []
        
        # 1. 东方财富公告（主要来源，防反爬）
        news_list.extend(self.collect_from_eastmoney(limit))
        
        # 2. Tushare 新闻（备用，但限制每分钟1次）
        # 检查限流冷却期
        now = time.time()
        if self._api_cooldown and now < self._cooldown_until:
            remaining = int(self._cooldown_until - now)
            print(f"[限流] Tushare API 冷却中，还需等待 {remaining} 秒")
        else:
            tushare_news = self._collect_from_tushare(stock_code, limit)
            news_list.extend(tushare_news)
        
        return news_list
    
    def _collect_from_tushare(self, stock_code: str = None, 
                              limit: int = 10) -> List[Dict]:
        """
        从 Tushare 采集新闻
        
        Args:
            stock_code: 股票代码
            limit: 数量限制
        
        Returns:
            List[Dict]: 新闻列表
        """
        news_list = []
        
        # Tushare 新闻接口
        try:
            import tushare as ts
            ts.set_token('39a3955e10adc24a28b08b459d9ea092dcd737c3a8c0df386bc84bd8')
            pro = ts.pro_api()
            
            # 获取财经新闻
            df = pro.news(src='sina', start_date=(datetime.now()-timedelta(days=1)).strftime('%Y%m%d'), 
                         end_date=datetime.now().strftime('%Y%m%d'))
            
            for _, row in df.head(limit).iterrows():
                news = {
                    'title': row.get('content', ''),
                    'content': row.get('content', ''),
                    'source': '新浪财经',
                    'publish_time': row.get('pub_date', ''),
                    'url': row.get('url', ''),
                    'stock_code': stock_code
                }
                
                # 去重
                if self._is_duplicate(news):
                    continue
                
                news_list.append(news)
            
            # 成功调用，更新状态
            self._last_api_call = time.time()
            self._api_cooldown = False
        
        except Exception as e:
            error_msg = str(e)
            print(f"Tushare 新闻接口失败：{e}")
            
            # 检测限流错误
            if '每分钟最多' in error_msg or '频率' in error_msg:
                print(f"[限流] 检测到 API 限流，设置 60 秒冷却期")
                self._api_cooldown = True
                self._cooldown_until = time.time() + 60
            
            # 更新最后调用时间
            self._last_api_call = time.time()
        
        return news_list
    
    def collect_from_eastmoney(self, limit: int = 20) -> List[Dict]:
        """
        从东方财富采集公告新闻（带防反爬）
        
        Args:
            limit: 数量限制
        
        Returns:
            List[Dict]: 新闻列表
        """
        try:
            from crawler.eastmoney_source import EastMoneySource
            
            source = EastMoneySource()
            news_items = source.get_announcements(page_size=limit)
            
            news_list = []
            for item in news_items:
                news = {
                    'title': item.title,
                    'content': item.content,
                    'source': item.source,
                    'publish_time': item.publish_time,
                    'url': item.url,
                    'stock_code': item.stock_code,
                    'stock_name': item.stock_name,
                    'category': item.category,
                }
                
                # 去重
                if self._is_duplicate(news):
                    continue
                
                news_list.append(news)
            
            if news_list:
                print(f"[东方财富] 获取到 {len(news_list)} 条公告")
            
            return news_list
        
        except ImportError:
            print("[东方财富] 模块未找到，跳过")
        except Exception as e:
            print(f"[东方财富] 采集失败：{str(e)[:50]}")
        
        return []
    
    def collect_from_rss(self, feed_url: str) -> List[Dict]:
        """
        从 RSS Feed 采集
        
        Args:
            feed_url: RSS Feed 地址
        
        Returns:
            List[Dict]: 新闻列表
        """
        news_list = []
        
        try:
            import feedparser
            feed = feedparser.parse(feed_url)
            
            for entry in feed.entries[:10]:
                news = {
                    'title': entry.title,
                    'content': entry.summary if hasattr(entry, 'summary') else entry.title,
                    'source': feed.feed.title if hasattr(feed, 'feed') else 'RSS',
                    'publish_time': entry.published if hasattr(entry, 'published') else '',
                    'url': entry.link,
                }
                
                # 去重
                if self._is_duplicate(news):
                    continue
                
                news_list.append(news)
        
        except Exception as e:
            print(f"RSS 采集失败：{e}")
        
        return news_list
    
    def collect_from_web(self, url: str, source: str) -> List[Dict]:
        """
        从网页采集 (合规方式)
        
        Args:
            url: 网页地址
            source: 来源名称
        
        Returns:
            List[Dict]: 新闻列表
        """
        news_list = []
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # 简单解析 (实际应使用 BeautifulSoup 等)
            # 这里仅作示例
            
        except Exception as e:
            print(f"网页采集失败：{e}")
        
        return news_list
    
    def _is_duplicate(self, news: Dict) -> bool:
        """
        检查是否重复
        
        使用 SimHash 算法简化版
        """
        # 生成内容哈希
        content = f"{news['title']}{news.get('content', '')}"
        content_hash = hashlib.md5(content.encode()).hexdigest()
        
        if content_hash in self.collected_hashes:
            return True
        
        self.collected_hashes.add(content_hash)
        
        # 限制缓存大小
        if len(self.collected_hashes) > 10000:
            # 移除一半旧数据
            self.collected_hashes = set(list(self.collected_hashes)[:5000])
        
        return False
    
    def deduplicate(self, news_list: List[Dict]) -> List[Dict]:
        """
        批量去重
        
        Args:
            news_list: 新闻列表
        
        Returns:
            List[Dict]: 去重后的新闻
        """
        unique_news = []
        
        for news in news_list:
            if not self._is_duplicate(news):
                unique_news.append(news)
        
        return unique_news
    
    def calculate_weight(self, news: Dict) -> float:
        """
        计算新闻权重
        
        Args:
            news: 新闻
        
        Returns:
            float: 权重 [0, 1]
        """
        source = news.get('source', '')
        base_weight = self.source_weights.get(source, 0.5)
        
        # 时效性权重 (越新越高)
        publish_time = news.get('publish_time', '')
        if publish_time:
            try:
                pub_datetime = datetime.strptime(publish_time, '%Y-%m-%d %H:%M:%S')
                hours_old = (datetime.now() - pub_datetime).total_seconds() / 3600
                time_weight = max(0.5, 1.0 - hours_old / 24)  # 24 小时内有效
            except:
                time_weight = 0.8
        else:
            time_weight = 0.8
        
        return base_weight * time_weight


# ==================== 定时采集任务 ====================
class ScheduledCollector:
    """
    定时采集器
    
    功能:
    - 按计划执行采集
    - 增量更新
    - 异常重试
    """
    
    def __init__(self):
        self.collector = NewsCollector()
        self.running = False
    
    def start(self):
        """启动采集任务"""
        self.running = True
        print("开始定时采集任务...")
        
        while self.running:
            try:
                # 采集全市场新闻
                news_list = self.collector.collect_from_api(limit=50)
                
                if news_list:
                    print(f"采集到 {len(news_list)} 条新闻")
                    
                    # 发送到处理队列
                    # self.send_to_processor(news_list)
                
                # 等待 1 分钟
                time.sleep(60)
            
            except Exception as e:
                print(f"采集任务异常：{e}")
                time.sleep(10)  # 异常后短暂等待
    
    def stop(self):
        """停止采集任务"""
        self.running = False
        print("停止采集任务")


# ==================== 测试 ====================
def test_collector():
    """测试采集器"""
    print("=" * 70)
    print("新闻采集器测试")
    print("=" * 70)
    
    collector = NewsCollector()
    
    # 测试 API 采集
    print("\n1. 测试 API 采集...")
    news_list = collector.collect_from_api(limit=5)
    print(f"   采集到 {len(news_list)} 条新闻")
    
    for news in news_list[:3]:
        print(f"   - {news['title'][:50]}...")
        print(f"     来源：{news['source']}, 权重：{collector.calculate_weight(news):.2f}")
    
    # 测试去重
    print("\n2. 测试去重...")
    initial_count = len(collector.collected_hashes)
    news_list = collector.collect_from_api(limit=5)
    final_count = len(collector.collected_hashes)
    print(f"   新增哈希：{final_count - initial_count}")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    test_collector()
