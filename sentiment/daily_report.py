#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日市场报告生成与推送
⛏️ 超级龙虾 - A股量化分析系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import yaml
import requests
from datetime import datetime
from sentiment.market_index_integration import IndexSentimentIntegration


def load_config():
    """加载配置"""
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'webhook.yaml')
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def get_market_data():
    """获取市场数据"""
    try:
        integration = IndexSentimentIntegration()
        sentiment = integration.get_market_sentiment()
        # 转换为字典
        return {
            "market_status": sentiment.market_status,
            "sentiment_score": sentiment.sentiment_score,
            "sentiment_label": sentiment.sentiment_label,
            "index_signals": sentiment.index_signals,
            "news_count": sentiment.news_count,
            "alert_level": sentiment.alert_level,
            "trading_suggestion": sentiment.trading_suggestion
        }
    except Exception as e:
        return {"error": str(e)}


def format_report(sentiment_data):
    """格式化报告"""
    now = datetime.now().strftime('%Y-%m-%d %H:%M')
    
    if "error" in sentiment_data:
        return f"📊 **每日市场报告**\n⏰ {now}\n\n⚠️ 数据获取失败: {sentiment_data['error']}"
    
    # 构建报告内容
    market_emoji = {
        "普涨": "🟢",
        "普跌": "🔴",
        "分化": "🟡",
        "震荡": "⚪"
    }.get(sentiment_data.get("market_status", "未知"), "⚪")
    
    sentiment_emoji = {
        "乐观": "😄",
        "中性": "😐",
        "悲观": "😟"
    }.get(sentiment_data.get("sentiment_label", "中性"), "😐")
    
    alert_emoji = {
        "🔴 红色预警": "🚨",
        "🟠 橙色预警": "⚠️",
        "🟡 黄色预警": "📢",
        "🔵 蓝色预警": "💬",
        "⚪ 关注": "➡️"
    }.get(sentiment_data.get("alert_level", "⚪ 关注"), "➡️")
    
    report = f"""📊 **每日市场报告**
⏰ {now}

🏛️ 市场状态: {market_emoji} {sentiment_data.get('market_status', '未知')}
😊 市场情绪: {sentiment_emoji} {sentiment_data.get('sentiment_label', '未知')} ({sentiment_data.get('sentiment_score', 0):.2%})
{alert_emoji} 预警级别: {sentiment_data.get('alert_level', '⚪ 关注')}
📰 新闻数量: {sentiment_data.get('news_count', 0)}
💡 交易建议: {sentiment_data.get('trading_suggestion', '观望')}

---
*超级龙虾每日自动生成*"""
    
    return report


def push_to_feishu(content: str, webhook_url: str) -> bool:
    """推送到飞书"""
    try:
        payload = {
            "msg_type": "text",
            "content": {"text": content}
        }
        response = requests.post(webhook_url, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"推送失败: {e}")
        return False


def main():
    """主函数"""
    print("=" * 50)
    print("📊 每日市场报告生成器")
    print("=" * 50)
    
    # 加载配置
    config = load_config()
    webhook_url = config['alert']['webhook_url']
    
    # 获取市场数据
    print("\n📡 获取市场数据...")
    sentiment_data = get_market_data()
    
    # 格式化报告
    print("\n📝 生成报告...")
    report = format_report(sentiment_data)
    print(report)
    
    # 推送
    print("\n📤 推送到飞书...")
    if push_to_feishu(report, webhook_url):
        print("✅ 推送成功!")
    else:
        print("❌ 推送失败")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
