# -*- coding: utf-8 -*-
"""
数据源管理器 - 统一多源采集
⛏️ 淘金者舆情监控系统 v2.0
"""

import time
from datetime import datetime
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import hashlib


class DataSource(ABC):
    """数据源基类"""
    
    def __init__(self, name: str, weight: float = 0.5):
        self.name = name
        self.weight = weight
        self.last_update = None
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'duplicate': 0
        }
    
    @abstractmethod
    def collect(self, **kwargs) -> List[Dict]:
        """采集数据"""
        pass
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'name': self.name,
            'weight': self.weight,
            'last_update': self.last_update,
            **self.stats
        }


class CLSTelegraphSource(DataSource):
    """财联社电报 - 最快快讯渠道"""
    
    def __init__(self):
        super().__init__('财联社电报', weight=0.9)
        self.api_url = 'https://www.cls.cn/v3/roll/get_roll_list'
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://www.cls.cn/',
        }
    
    def collect(self, limit: int = 20, **kwargs) -> List[Dict]:
        """
        采集财联社电报
        
        注意：需要解决反爬问题
        """
        import requests
        
        news_list = []
        try:
            # 尝试 API 调用
            response = requests.get(
                self.api_url,
                headers=self.headers,
                params={
                    'app': 'CailianpressWeb',
                    'category_id': '1',
                    'last_time': int(time.time())
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('code') == 200:
                    for item in data.get('data', {}).get('roll_data', [])[:limit]:
                        news = {
                            'title': item.get('title', ''),
                            'content': item.get('content', ''),
                            'source': '财联社电报',
                            'publish_time': datetime.fromtimestamp(
                                item.get('ctime', 0)
                            ).strftime('%Y-%m-%d %H:%M:%S'),
                            'url': f"https://www.cls.cn/detail/{item.get('id', '')}",
                            'source_weight': self.weight
                        }
                        news_list.append(news)
                        self.stats['success'] += 1
            
            self.stats['total'] += 1
            self.last_update = datetime.now()
            
        except Exception as e:
            print(f"财联社采集失败：{e}")
            self.stats['failed'] += 1
        
        return news_list


class CninfoSource(DataSource):
    """巨潮资讯 - 官方公告"""
    
    def __init__(self):
        super().__init__('巨潮资讯', weight=1.0)
        self.api_url = 'http://www.cninfo.com.cn/new/hisAnnouncement/query'
    
    def collect(self, stock_code: str = None, limit: int = 10, **kwargs) -> List[Dict]:
        """
        采集巨潮资讯公告
        
        Args:
            stock_code: 股票代码 (可选)
            limit: 数量限制
        """
        import requests
        
        news_list = []
        try:
            # 查询公告
            params = {
                'tabName': 'fulltext',
                'plate': 'sse',
                'stock': stock_code if stock_code else '',
                'searchkey': '',
                'secid': '',
                'category': 'category_ngsl',
                'sortName': 'time',
                'sortType': 'time',
                'isHL': 'true',
                'isfulltext': 'true',
                'pageNum': '1',
                'pageSize': str(limit)
            }
            
            response = requests.get(self.api_url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                for announcement in data.get('announcements', [])[:limit]:
                    news = {
                        'title': announcement.get('title', ''),
                        'content': announcement.get('announcementTitle', ''),
                        'source': '巨潮资讯',
                        'publish_time': datetime.fromtimestamp(
                            announcement.get('announcementTime', 0) / 1000
                        ).strftime('%Y-%m-%d %H:%M:%S'),
                        'url': f"http://www.cninfo.com.cn/new/disclosure/detail?plate=sse&stockCode={announcement.get('code', '')}&announcementId={announcement.get('id', '')}",
                        'source_weight': self.weight,
                        'stock_code': announcement.get('code', '')
                    }
                    news_list.append(news)
                    self.stats['success'] += 1
            
            self.stats['total'] += 1
            self.last_update = datetime.now()
            
        except Exception as e:
            print(f"巨潮资讯采集失败：{e}")
            self.stats['failed'] += 1
        
        return news_list


class XueqiuSource(DataSource):
    """雪球 - 投资者情绪"""
    
    def __init__(self, cookie_u: str = None, cookie_token: str = None):
        super().__init__('雪球', weight=0.3)
        self.base_url = 'https://xueqiu.com'
        
        # 配置 Cookie
        self.cookies = {}
        if cookie_u and cookie_token:
            self.cookies = {
                'u': cookie_u,
                'xq_a_token': cookie_token,
            }
        
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Referer': 'https://xueqiu.com/',
        }
    
    def collect(self, stock_code: str = None, limit: int = 10, **kwargs) -> List[Dict]:
        """
        采集雪球讨论
        
        Args:
            stock_code: 股票代码
            limit: 数量限制
        """
        import requests
        
        news_list = []
        
        if not self.cookies:
            print("雪球 API 需要配置 Cookie")
            self.stats['total'] += 1
            self.stats['failed'] += 1
            return news_list
        
        try:
            # 1. 获取股票信息
            if stock_code:
                # 个股页面
                url = f"{self.base_url}/S/{stock_code}"
            else:
                # 热门讨论
                url = f"{self.base_url}/hot"
            
            # 2. 获取讨论列表
            session = requests.Session()
            session.cookies.update(self.cookies)
            session.headers.update(self.headers)
            
            # API: 获取股票动态
            if stock_code:
                api_url = f"{self.base_url}/statuses/hot/list.json?symbol={stock_code}"
            else:
                api_url = f"{self.base_url}/v4/statuses/hot_list.json"
            
            response = session.get(api_url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                items = data.get('list', [])
                
                for item in items[:limit]:
                    title = item.get('title', '')
                    text = item.get('text', '')
                    
                    news = {
                        'title': title[:100] if title else text[:100],
                        'content': text,
                        'source': '雪球',
                        'publish_time': datetime.fromtimestamp(
                            item.get('created_at', 0) / 1000
                        ).strftime('%Y-%m-%d %H:%M:%S') if item.get('created_at') else '',
                        'url': f"{self.base_url}{item.get('target', '')}",
                        'source_weight': self.weight,
                        'user': item.get('user', {}).get('screen_name', ''),
                        'likes': item.get('likes_count', 0),
                        'comments': item.get('comments_count', 0),
                        'retweets': item.get('retweets_count', 0),
                    }
                    news_list.append(news)
                    self.stats['success'] += 1
            
            self.stats['total'] += 1
            self.last_update = datetime.now()
            
        except Exception as e:
            print(f"雪球采集失败：{e}")
            self.stats['failed'] += 1
        
        return news_list


class BaiduNewsSource(DataSource):
    """百度新闻 API - 新闻聚合"""
    
    def __init__(self, api_key: str = None):
        super().__init__('百度新闻', weight=0.6)
        self.api_key = api_key
    
    def collect(self, keyword: str = 'A 股', limit: int = 10, **kwargs) -> List[Dict]:
        """
        采集百度新闻
        
        需要百度 API Key
        """
        news_list = []
        
        if not self.api_key:
            print("百度新闻 API 需要 API Key")
            self.stats['total'] += 1
            self.stats['failed'] += 1
            return news_list
        
        # TODO: 实现百度新闻 API 调用
        print("百度新闻 API 待实现")
        return news_list


class ExchangeSource(DataSource):
    """交易所 API - 监管信息"""
    
    def __init__(self, exchange: str = 'SSE'):
        """
        Args:
            exchange: SSE(上交所) / SZSE(深交所)
        """
        super().__init__(f'{exchange}交易所', weight=0.8)
        self.exchange = exchange
    
    def collect(self, limit: int = 10, **kwargs) -> List[Dict]:
        """采集交易所监管信息"""
        news_list = []
        
        if self.exchange == 'SSE':
            # 上交所
            url = 'http://www.sse.com.cn/disclosure/listed/announcement/'
        else:
            # 深交所
            url = 'http://www.szse.cn/disclosure/listed/notice/'
        
        # TODO: 实现交易所 API
        print(f"{self.exchange}交易所 API 待实现")
        return news_list


class DataSourceManager:
    """
    数据源管理器
    
    功能:
    - 多源采集
    - 去重合并
    - 可信度评分
    - 交叉验证
    """
    
    def __init__(self):
        self.sources: Dict[str, DataSource] = {}
        self.collected_hashes = set()
        
        # 注册数据源
        self._register_default_sources()
    
    def _register_default_sources(self):
        """注册默认数据源"""
        # 优先级 1 - 提升速度
        self.sources['cls_telegraph'] = CLSTelegraphSource()
        self.sources['cninfo'] = CninfoSource()
        
        # 优先级 2 - 提升覆盖率
        self.sources['xueqiu'] = XueqiuSource()
        self.sources['baidu_news'] = BaiduNewsSource()
        self.sources['exchange'] = ExchangeSource()
        
        # Tushare (已有)
        # 从 news_collector.py 导入
    
    def add_source(self, name: str, source: DataSource):
        """添加数据源"""
        self.sources[name] = source
    
    def collect_all(self, **kwargs) -> List[Dict]:
        """
        从所有数据源采集
        
        Returns:
            List[Dict]: 新闻列表 (已去重)
        """
        all_news = []
        
        for name, source in self.sources.items():
            print(f"\n采集 {name}...")
            try:
                news_list = source.collect(**kwargs)
                all_news.extend(news_list)
            except Exception as e:
                print(f"{name} 采集失败：{e}")
        
        # 去重
        unique_news = self._deduplicate(all_news)
        
        # 计算可信度评分
        self._calculate_credibility(unique_news)
        
        return unique_news
    
    def _deduplicate(self, news_list: List[Dict]) -> List[Dict]:
        """去重"""
        unique_news = []
        
        for news in news_list:
            content = f"{news['title']}{news.get('content', '')}"
            content_hash = hashlib.md5(content.encode()).hexdigest()
            
            if content_hash not in self.collected_hashes:
                self.collected_hashes.add(content_hash)
                unique_news.append(news)
            else:
                # 重复新闻，累加来源
                for existing in unique_news:
                    if hashlib.md5(f"{existing['title']}{existing.get('content', '')}".encode()).hexdigest() == content_hash:
                        if 'duplicate_sources' not in existing:
                            existing['duplicate_sources'] = []
                        existing['duplicate_sources'].append(news['source'])
                        break
        
        # 限制缓存大小
        if len(self.collected_hashes) > 10000:
            self.collected_hashes = set(list(self.collected_hashes)[:5000])
        
        return unique_news
    
    def _calculate_credibility(self, news_list: List[Dict]):
        """
        计算可信度评分
        
        因素:
        - 来源权重
        - 多源交叉验证
        - 时效性
        """
        for news in news_list:
            score = 0.0
            
            # 1. 来源权重
            score += news.get('source_weight', 0.5)
            
            # 2. 多源交叉验证
            duplicate_count = len(news.get('duplicate_sources', []))
            if duplicate_count > 0:
                score += min(duplicate_count * 0.2, 0.6)  # 最多加 0.6
            
            # 3. 时效性
            publish_time = news.get('publish_time', '')
            if publish_time:
                try:
                    pub_datetime = datetime.strptime(publish_time, '%Y-%m-%d %H:%M:%S')
                    hours_old = (datetime.now() - pub_datetime).total_seconds() / 3600
                    time_score = max(0.5, 1.0 - hours_old / 24)
                    score *= time_score
                except:
                    pass
            
            # 归一化到 [0, 1]
            news['credibility_score'] = min(score, 1.0)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            'total_sources': len(self.sources),
            'sources': {name: source.get_stats() for name, source in self.sources.items()},
            'cache_size': len(self.collected_hashes)
        }


# ==================== 测试 ====================
def test_datasource_manager():
    """测试数据源管理器"""
    print("=" * 70)
    print("数据源管理器测试")
    print("=" * 70)
    
    manager = DataSourceManager()
    
    print("\n已注册数据源:")
    for name, source in manager.sources.items():
        print(f"  - {name}: 权重 {source.weight}")
    
    print("\n开始采集...")
    news_list = manager.collect_all(limit=5)
    
    print(f"\n采集结果:")
    print(f"  总新闻数：{len(news_list)}")
    
    # 显示前 3 条
    for i, news in enumerate(news_list[:3], 1):
        print(f"\n  [{i}] {news['title'][:50]}...")
        print(f"      来源：{news['source']}")
        print(f"      可信度：{news.get('credibility_score', 0):.2f}")
    
    # 统计信息
    print("\n数据统计:")
    stats = manager.get_stats()
    print(f"  数据源数量：{stats['total_sources']}")
    print(f"  去重缓存：{stats['cache_size']} 条")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    test_datasource_manager()
