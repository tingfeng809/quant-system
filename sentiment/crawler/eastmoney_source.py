# -*- coding: utf-8 -*-
"""
东方财富数据源
⛏️ 淘金者版 - 防反爬采集
"""

import requests
import random
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class NewsItem:
    """新闻条目"""
    title: str
    content: str
    source: str
    publish_time: str
    url: str
    stock_code: str = ""
    stock_name: str = ""
    category: str = ""


class AntiCrawlHeaders:
    """防反爬请求头管理器"""
    
    # 轮换 User-Agent 列表
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    ]
    
    # 推荐的 Referer
    REFERERS = [
        "https://finance.eastmoney.com/",
        "https://www.eastmoney.com/",
        "https://stock.eastmoney.com/",
        "https://news.eastmoney.com/",
    ]
    
    @classmethod
    def get_random(cls) -> Dict[str, str]:
        """获取随机请求头"""
        return {
            'User-Agent': random.choice(cls.USER_AGENTS),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Cache-Control': 'max-age=0',
            'Referer': random.choice(cls.REFERERS),
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
        }


class RateLimiter:
    """请求频率限制器"""
    
    def __init__(self, min_interval: float = 1.0, max_interval: float = 3.0):
        """
        Args:
            min_interval: 最小请求间隔（秒）
            max_interval: 最大请求间隔（秒）
        """
        self.min_interval = min_interval
        self.max_interval = max_interval
        self._last_request = 0
        self._request_count = 0
        self._window_start = time.time()
    
    def wait(self):
        """等待合适的间隔"""
        now = time.time()
        
        # 计算窗口内请求数
        if now - self._window_start > 60:
            self._request_count = 0
            self._window_start = now
        
        # 如果 60 秒内请求超过 30 次，等待更久
        if self._request_count > 30:
            wait_time = 60 - (now - self._window_start)
            if wait_time > 0:
                time.sleep(wait_time)
                self._request_count = 0
                self._window_start = time.time()
        
        # 基础间隔
        elapsed = now - self._last_request
        if elapsed < self.min_interval:
            sleep_time = random.uniform(self.min_interval, self.max_interval)
            time.sleep(sleep_time)
        
        self._last_request = time.time()
        self._request_count += 1
    
    def random_delay(self):
        """随机延迟"""
        time.sleep(random.uniform(0.5, 2.0))


class EastMoneySource:
    """
    东方财富数据源
    
    防反爬措施：
    1. 轮换 User-Agent
    2. 随机请求间隔
    3. 随机 Referer
    4. 60 秒内请求数限制
    5. 渐进式等待
    """
    
    BASE_URL = "https://np-anotice-stock.eastmoney.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(min_interval=1.5, max_interval=3.0)
        self._last_news_check = 0
        
        # 来源标识
        self.source_name = "东方财富"
        self.source_weight = 0.8
    
    def _get_headers(self) -> Dict[str, str]:
        """获取随机请求头"""
        return AntiCrawlHeaders.get_random()
    
    def _make_request(self, url: str, params: Dict = None, max_retries: int = 3) -> Optional[Dict]:
        """
        发起请求（带防反爬）
        
        Args:
            url: 请求 URL
            params: 请求参数
            max_retries: 最大重试次数
        
        Returns:
            响应 JSON 或 None
        """
        self.rate_limiter.wait()
        
        for attempt in range(max_retries):
            try:
                headers = self._get_headers()
                
                response = self.session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=15,
                    allow_redirects=True
                )
                
                # 检查响应状态
                if response.status_code == 200:
                    return response.json()
                
                # 403/418 表示被拦截
                elif response.status_code in [403, 418]:
                    print(f"[东方财富] 请求被拦截 (状态码: {response.status_code})，等待后重试...")
                    self.rate_limiter.random_delay()
                    continue
                
                # 其他错误
                else:
                    print(f"[东方财富] 请求失败 (状态码: {response.status_code})")
                    return None
            
            except requests.exceptions.Timeout:
                print(f"[东方财富] 请求超时，重试 ({attempt + 1}/{max_retries})...")
                time.sleep(2)
            
            except requests.exceptions.RequestException as e:
                print(f"[东方财富] 请求异常: {str(e)[:50]}，重试 ({attempt + 1}/{max_retries})...")
                time.sleep(2)
        
        return None
    
    def get_announcements(self, page_size: int = 20, page_index: int = 1) -> List[NewsItem]:
        """
        获取最新公告
        
        Args:
            page_size: 每页数量
            page_index: 页码
        
        Returns:
            公告列表
        """
        url = f"{self.BASE_URL}/api/security/ann"
        params = {
            "sr": -1,  # 按时间倒序
            "page_size": page_size,
            "page_index": page_index,
            "ann_type": "SHA,SZA",  # 上海A股+深圳A股
        }
        
        result = self._make_request(url, params)
        
        news_list = []
        if result and result.get("success") == 1:
            data = result.get("data", {})
            items = data.get("list", [])
            
            for item in items:
                # 解析股票信息
                codes = item.get("codes", [{}])[0] if item.get("codes") else {}
                
                # 解析公告类型
                columns = item.get("columns", [{}])[0] if item.get("columns") else {}
                
                news = NewsItem(
                    title=item.get("title_ch", ""),
                    content=item.get("title_ch", ""),  # 公告标题作为内容摘要
                    source=self.source_name,
                    publish_time=item.get("notice_date", ""),
                    url=f"https://np-anotice-stock.eastmoney.com/api/security/ann?art_code={item.get('art_code', '')}",
                    stock_code=codes.get("stock_code", ""),
                    stock_name=codes.get("short_name", ""),
                    category=columns.get("column_name", ""),
                )
                news_list.append(news)
        
        return news_list
    
    def get_stock_news(self, limit: int = 20) -> List[NewsItem]:
        """
        获取个股新闻（从公告接口）
        
        Args:
            limit: 数量限制
        
        Returns:
            新闻列表
        """
        news_list = self.get_announcements(page_size=limit)
        
        # 过滤，只保留有股票代码的
        return [n for n in news_list if n.stock_code]
    
    def search_news(self, keyword: str, limit: int = 10) -> List[NewsItem]:
        """
        搜索新闻（通过公告标题）
        
        Args:
            keyword: 搜索关键词
            limit: 数量限制
        
        Returns:
            新闻列表
        """
        all_news = self.get_announcements(page_size=50)
        
        # 简单关键词匹配
        matched = [n for n in all_news if keyword in n.title]
        
        return matched[:limit]


class EastMoneyNewsAPI:
    """
    东方财富新闻 API（另一接口）
    """
    
    # 快讯 API
    FAST_NEWS_URL = "https://newsapi.eastmoney.com/kuaixun/v1/getlist_101_ajaxResult_50_1_.html"
    
    def __init__(self):
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(min_interval=2.0, max_interval=4.0)
    
    def get_fast_news(self, limit: int = 20) -> List[Dict]:
        """
        获取快讯
        
        Args:
            limit: 数量限制
        
        Returns:
            快讯列表
        """
        self.rate_limiter.wait()
        
        try:
            headers = AntiCrawlHeaders.get_random()
            headers['Referer'] = 'https://www.eastmoney.com/'
            
            response = self.session.get(
                self.FAST_NEWS_URL,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                items = data.get("data", {}).get("list", [])[:limit]
                
                result = []
                for item in items:
                    result.append({
                        'title': item.get('title', ''),
                        'content': item.get('digest', ''),
                        'source': '东方财富快讯',
                        'publish_time': item.get('showtime', ''),
                        'url': item.get('url', ''),
                    })
                
                return result
            
        except Exception as e:
            print(f"[东方财富快讯] 获取失败: {str(e)[:50]}")
        
        return []


# ==================== 测试 ====================
def test_eastmoney():
    """测试东方财富数据源"""
    print("=" * 70)
    print("东方财富数据源测试")
    print("=" * 70)
    
    # 测试公告接口
    print("\n【1】测试公告接口...")
    source = EastMoneySource()
    news = source.get_announcements(page_size=5)
    print(f"   获取到 {len(news)} 条公告")
    
    for n in news[:3]:
        print(f"   - [{n.stock_code}] {n.stock_name}: {n.title[:40]}...")
        print(f"     类型: {n.category}, 时间: {n.publish_time}")
    
    # 测试快讯接口
    print("\n【2】测试快讯接口...")
    news_api = EastMoneyNewsAPI()
    fast_news = news_api.get_fast_news(limit=5)
    print(f"   获取到 {len(fast_news)} 条快讯")
    
    for n in fast_news[:3]:
        print(f"   - {n.get('title', '')[:50]}...")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    test_eastmoney()