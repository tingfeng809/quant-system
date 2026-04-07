#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
雪球 API 测试脚本
⛏️ 淘金者舆情监控系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from crawler.datasource_manager import XueqiuSource
from datetime import datetime

# 雪球 Cookie 配置
XUEQIU_U = "7670593540"
XUEQIU_TOKEN = "140926cd1a48534920e718f5f74c857ef0307437"


def test_xueqiu():
    """测试雪球采集"""
    print("=" * 70)
    print("雪球 API 测试")
    print("=" * 70)
    print(f"Cookie U: {XUEQIU_U}")
    print(f"Token: {XUEQIU_TOKEN[:20]}...")
    print("=" * 70)
    
    # 创建雪球数据源
    source = XueqiuSource(
        cookie_u=XUEQIU_U,
        cookie_token=XUEQIU_TOKEN
    )
    
    # 测试 1: 采集热门讨论
    print("\n1. 测试采集热门讨论...")
    news_list = source.collect(limit=5)
    
    if news_list:
        print(f"   采集到 {len(news_list)} 条讨论")
        
        for i, news in enumerate(news_list[:3], 1):
            print(f"\n   [{i}] {news['title']}")
            print(f"       用户：{news.get('user', '未知')}")
            print(f"       时间：{news.get('publish_time', '未知')}")
            print(f"       互动：❤️{news.get('likes', 0)} 💬{news.get('comments', 0)} 🔁{news.get('retweets', 0)}")
    else:
        print("   ❌ 未采集到数据 (可能 Cookie 失效或网络问题)")
    
    # 测试 2: 采集个股讨论
    print("\n2. 测试采集贵州茅台讨论...")
    news_list = source.collect(stock_code="600519", limit=5)
    
    if news_list:
        print(f"   采集到 {len(news_list)} 条讨论")
        
        for i, news in enumerate(news_list[:2], 1):
            print(f"\n   [{i}] {news['title'][:60]}...")
            print(f"       互动：❤️{news.get('likes', 0)} 💬{news.get('comments', 0)}")
    else:
        print("   ❌ 未采集到数据")
    
    # 统计信息
    print("\n3. 采集统计:")
    stats = source.get_stats()
    print(f"   总采集：{stats['total']} 次")
    print(f"   成功：{stats['success']} 次")
    print(f"   失败：{stats['failed']} 次")
    print(f"   最后更新：{stats.get('last_update', '未知')}")
    
    print("\n" + "=" * 70)
    if news_list:
        print("✅ 雪球 API 测试成功！")
    else:
        print("⚠️ 雪球 API 测试失败，请检查:")
        print("  1. Cookie 是否有效")
        print("  2. 网络连接是否正常")
        print("  3. 雪球是否有反爬限制")
    print("=" * 70)


if __name__ == '__main__':
    test_xueqiu()
