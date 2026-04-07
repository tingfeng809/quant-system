#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
飞书 Webhook 测试脚本
⛏️ 淘金者舆情监控系统
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from alert.feishu_bot import FeishuAlertBot
from datetime import datetime

# 飞书 Webhook URL
WEBHOOK_URL = "https://open.feishu.cn/open-apis/bot/v2/hook/aa04be2c-9535-40a6-b1c0-cdeab1cd73a7"


def test_webhook():
    """测试飞书 Webhook 推送"""
    print("=" * 70)
    print("飞书 Webhook 测试")
    print("=" * 70)
    print(f"Webhook URL: {WEBHOOK_URL}")
    print("=" * 70)
    
    bot = FeishuAlertBot(webhook_url=WEBHOOK_URL)
    
    # 测试告警
    test_alerts = [
        {
            'level': '🔴 红色',
            'stock': '贵州茅台',
            'code': '600519.SH',
            'title': '业绩预增 50%',
            'source': '巨潮资讯',
            'score': 0.85,
            'content': '公司发布业绩预告，预计 2026 年上半年净利润同比增长 50%，主要得益于高端产品销量增长。',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'level': '🟠 橙色',
            'stock': '宁德时代',
            'code': '300750.SZ',
            'title': '中标 50 亿订单',
            'source': '财联社',
            'score': 0.72,
            'content': '公司中标某大型电池采购项目，金额约 50 亿元，预计对未来业绩产生积极影响。',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
        {
            'level': '🟡 黄色',
            'stock': '平安银行',
            'code': '000001.SZ',
            'title': '股东减持 0.5%',
            'source': '东方财富',
            'score': -0.45,
            'content': '公司股东通过集中竞价方式减持公司股份 0.5%，套现约 X 亿元。',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        },
    ]
    
    print(f"\n准备发送 {len(test_alerts)} 条测试告警...\n")
    
    success_count = 0
    for i, alert in enumerate(test_alerts, 1):
        print(f"[{i}/{len(test_alerts)}] 发送：{alert['title']}")
        if bot.send_alert(alert):
            success_count += 1
            print(f"   ✅ 推送成功")
        else:
            print(f"   ❌ 推送失败")
        
        # 间隔 1 秒
        import time
        time.sleep(1)
    
    print(f"\n{'=' * 70}")
    print(f"测试结果：成功 {success_count}/{len(test_alerts)} 条")
    print(f"{'=' * 70}")
    
    if success_count == len(test_alerts):
        print("\n✅ 所有告警推送成功！")
        print("\n请检查飞书是否收到 3 条消息:")
        print("  1. 🔴 红色预警 - 贵州茅台 业绩预增 50%")
        print("  2. 🟠 橙色预警 - 宁德时代 中标 50 亿订单")
        print("  3. 🟡 黄色预警 - 平安银行 股东减持 0.5%")
    else:
        print("\n⚠️ 部分告警推送失败，请检查:")
        print("  1. Webhook URL 是否正确")
        print("  2. 飞书机器人是否启用")
        print("  3. 网络连接是否正常")
    
    return success_count == len(test_alerts)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='测试飞书 Webhook')
    parser.add_argument('--url', '-u', help='自定义 Webhook URL')
    args = parser.parse_args()
    
    if args.url:
        WEBHOOK_URL = args.url
    
    success = test_webhook()
    
    sys.exit(0 if success else 1)
