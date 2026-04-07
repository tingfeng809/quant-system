# -*- coding: utf-8 -*-
"""
飞书告警机器人
⛏️ 淘金者版 - 3 分钟黄金窗口推送
"""

import requests
import json
from datetime import datetime
from typing import Dict, List


class FeishuAlertBot:
    """
    飞书告警机器人
    
    功能:
    - 预警推送
    - 交互式卡片
    - 告警历史
    """
    
    def __init__(self, webhook_url: str = None):
        """
        初始化
        
        Args:
            webhook_url: 飞书 Webhook URL
        """
        self.webhook_url = webhook_url
        self.alert_history = []
    
    def send_alert(self, alert: Dict) -> bool:
        """
        发送告警
        
        Args:
            alert: 告警信息 {
                'level': '🔴 红色',
                'stock': '贵州茅台',
                'code': '600519.SH',
                'title': '大股东减持 1%',
                'source': '巨潮资讯',
                'score': -0.75,
                'content': '...',
                'timestamp': '2026-04-06 20:15:00'
            }
        
        Returns:
            bool: 是否成功
        """
        if not self.webhook_url:
            print(f"告警 (未配置 Webhook): {alert['title']}")
            return False
        
        # 构建交互式卡片
        card = self._build_card(alert)
        
        payload = {
            "msg_type": "interactive",
            "card": card
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('StatusCode') == 0 or result.get('code') == 0:
                    print(f"✅ 告警推送成功：{alert['title']}")
                    self.alert_history.append({
                        **alert,
                        'sent_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'status': 'success'
                    })
                    return True
            
            print(f"❌ 告警推送失败：{response.text}")
            return False
        
        except Exception as e:
            print(f"告警推送异常：{e}")
            return False
    
    def _build_card(self, alert: Dict) -> Dict:
        """
        构建交互式卡片
        
        Args:
            alert: 告警信息
        
        Returns:
            Dict: 卡片配置
        """
        # 根据级别设置颜色
        level_colors = {
            '🔴 红色': 'red',
            '🟠 橙色': 'orange',
            '🟡 黄色': 'yellow',
            '🔵 蓝色': 'blue',
            '⚪ 关注': 'gray'
        }
        
        level_tag = alert.get('level', '⚪ 关注')
        color = level_colors.get(level_tag, 'gray')
        
        # 情感分数显示
        score = alert.get('score', 0)
        if score > 0:
            score_display = f"+{score:.2f} 📈"
        elif score < 0:
            score_display = f"{score:.2f} 📉"
        else:
            score_display = f"{score:.2f} ➖"
        
        card = {
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "template": color,
                "title": {
                    "tag": "plain_text",
                    "content": f"{level_tag} 舆情预警 - {alert.get('stock', '未知股票')}"
                }
            },
            "elements": [
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**{alert.get('title', '无标题')}**\n\n"
                    }
                },
                {
                    "tag": "div",
                    "fields": [
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**股票代码:**\n{alert.get('code', 'N/A')}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**情感分数:**\n{score_display}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**信息来源:**\n{alert.get('source', '未知')}"
                            }
                        },
                        {
                            "is_short": True,
                            "text": {
                                "tag": "lark_md",
                                "content": f"**发布时间:**\n{alert.get('timestamp', '未知')}"
                            }
                        }
                    ]
                },
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": f"**内容摘要:**\n{alert.get('content', '无')[:200]}..."
                    }
                },
                {
                    "tag": "action",
                    "actions": [
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "📊 查看详情"
                            },
                            "url": f"http://quote.eastmoney.com/{alert.get('code', '').replace('.','')}.html",
                            "type": "default"
                        },
                        {
                            "tag": "button",
                            "text": {
                                "tag": "plain_text",
                                "content": "🔍 历史舆情"
                            },
                            "type": "default"
                        }
                    ]
                }
            ]
        }
        
        return card
    
    def send_batch_alerts(self, alerts: List[Dict]) -> Dict:
        """
        批量发送告警
        
        Args:
            alerts: 告警列表
        
        Returns:
            Dict: 发送结果统计
        """
        result = {
            'total': len(alerts),
            'success': 0,
            'failed': 0
        }
        
        for alert in alerts:
            if self.send_alert(alert):
                result['success'] += 1
            else:
                result['failed'] += 1
        
        return result
    
    def get_alert_history(self, limit: int = 10) -> List[Dict]:
        """
        获取告警历史
        
        Args:
            limit: 数量限制
        
        Returns:
            List[Dict]: 告警历史
        """
        return self.alert_history[-limit:]


# ==================== 测试 ====================
def test_feishu_bot():
    """测试飞书机器人"""
    print("=" * 70)
    print("飞书告警机器人测试")
    print("=" * 70)
    
    # 示例告警
    test_alerts = [
        {
            'level': '🔴 红色',
            'stock': '贵州茅台',
            'code': '600519.SH',
            'title': '大股东减持 1%',
            'source': '巨潮资讯',
            'score': -0.75,
            'content': '公司控股股东通过集中竞价交易方式减持公司股份 XXX 万股，占总股本的 1%。',
            'timestamp': '2026-04-06 20:15:00'
        },
        {
            'level': '🟠 橙色',
            'stock': '宁德时代',
            'code': '300750.SZ',
            'title': '中标 50 亿订单',
            'source': '财联社',
            'score': 0.82,
            'content': '公司中标某大型电池采购项目，金额约 50 亿元，预计对未来业绩产生积极影响。',
            'timestamp': '2026-04-06 20:12:00'
        },
    ]
    
    bot = FeishuAlertBot()  # 不配置 webhook，仅测试
    
    print("\n测试告警推送:")
    for alert in test_alerts:
        print(f"\n告警：{alert['title']}")
        print(f"  级别：{alert['level']}")
        print(f"  股票：{alert['stock']} ({alert['code']})")
        print(f"  分数：{alert['score']:.2f}")
        bot.send_alert(alert)
    
    print(f"\n告警历史：{len(bot.alert_history)} 条")
    
    print("\n✅ 测试完成！")


if __name__ == '__main__':
    test_feishu_bot()
