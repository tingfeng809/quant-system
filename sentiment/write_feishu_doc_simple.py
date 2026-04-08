#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""写入飞书文档 - 简化版"""
import requests
import json

TOKEN = "t-g104487CENRCQSF4T3SZ6BOXIEQMRXMOYTBLM4EL"
DOC_TOKEN = "CFQddhxOFoGUhNxskINca7TDnKb"
BASE_URL = "https://open.feishu.cn/open-apis/docx/v1"

def create_text_block(content):
    return {
        "block_type": 2,
        "text": {
            "elements": [{"text_run": {"content": content}}],
            "style": {"align": 1, "folded": False}
        }
    }

def create_heading_block(content, level=1):
    bt = {1: 3, 2: 4, 3: 5}.get(level, 3)
    key = f"heading{level}"
    return {
        "block_type": bt,
        key: {
            "elements": [{"text_run": {"content": content}}],
            "style": {"align": 1, "folded": False}
        }
    }

def create_divider_block():
    return {"block_type": 22, "divider": {}}

def insert_blocks(parent_id, blocks):
    url = f"{BASE_URL}/documents/{DOC_TOKEN}/blocks/{parent_id}/children"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    data = {"children": blocks}
    resp = requests.post(url, headers=headers, json=data)
    return resp.json()

# 构建文档内容
blocks = []

# 基本信息
blocks.append(create_heading_block("📋 基本信息", 1))
blocks.append(create_text_block(""))
blocks.append(create_text_block("名称: 超级龙虾 (Super Lobster) ⛏️"))
blocks.append(create_text_block("版本: v1.0 (2026-04-08)"))
blocks.append(create_text_block("定位: A股量化分析 + 智能助手"))
blocks.append(create_text_block("核心语言: 中文"))
blocks.append(create_text_block(""))
blocks.append(create_divider_block())

# 技术能力
blocks.append(create_heading_block("🛠️ 技术能力", 1))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("1. 量化交易系统", 2))
blocks.append(create_text_block("✅ 数据采集: Tushare Pro + 东方财富"))
blocks.append(create_text_block("✅ 技术因子: 35+ 因子 (MA, MACD, RSI, KDJ, CCI等)"))
blocks.append(create_text_block("✅ 资金流因子: 10+ 因子"))
blocks.append(create_text_block("✅ 自定义指数: 大盘/中盘/小盘/创业板"))
blocks.append(create_text_block("✅ 情绪指数: 市场情绪综合分析"))
blocks.append(create_text_block("✅ 舆情监控: 东方财富 + 飞书推送"))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("2. 回测引擎", 2))
blocks.append(create_text_block("✅ 基础回测: 单策略/多策略"))
blocks.append(create_text_block("✅ 全量回测: 4400+ 股票"))
blocks.append(create_text_block("✅ 高级策略: 布林带/RSI/Squeeze/KDJ/趋势/波动率"))
blocks.append(create_text_block("✅ 高胜率策略: 多因子确认 + 严格止损"))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("3. 策略库", 2))
blocks.append(create_text_block("• 双均线策略: 金叉买入，死叉卖出"))
blocks.append(create_text_block("• MACD策略: DIF上穿DEA买入"))
blocks.append(create_text_block("• 资金流策略: 主力净流入筛选"))
blocks.append(create_text_block("• 多因子策略: 技术+资金+基本面"))
blocks.append(create_text_block("• 布林带策略: 上下轨突破交易"))
blocks.append(create_text_block("• RSI策略: RSI区间波动"))
blocks.append(create_text_block("• Squeeze动量: 布林带收口扩张"))
blocks.append(create_text_block("• KDJ策略: 快速随机指标"))
blocks.append(create_text_block("• 趋势跟踪: EMA+ATR止损"))
blocks.append(create_text_block("• 波动率突破: N日高低点突破"))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("4. 因子库", 2))
blocks.append(create_text_block("• 波动率因子 (4): ATR, HV, Keltner, Donchian"))
blocks.append(create_text_block("• 动量因子 (6): RSI, Stochastic, CCI, MFI, Momentum, ROC"))
blocks.append(create_text_block("• 趋势强度因子 (3): ADX, Trend Intensity, SuperTrend"))
blocks.append(create_text_block("• 成交量因子 (4): OBV, VWAP, Volume Ratio, Money Flow"))
blocks.append(create_text_block("• 支撑压力因子 (3): Pivot Points, Fibonacci, Distance"))
blocks.append(create_text_block("• 背离因子 (2): 量价背离, RSI背离"))
blocks.append(create_text_block(""))
blocks.append(create_divider_block())

# 系统工具
blocks.append(create_heading_block("🔧 系统工具", 1))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("1. 飞书集成", 2))
blocks.append(create_text_block("• feishu-doc: 读写飞书文档"))
blocks.append(create_text_block("• feishu-drive: 管理云空间"))
blocks.append(create_text_block("• feishu-wiki: 知识库导航"))
blocks.append(create_text_block("• feishu-perm: 权限管理"))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("2. 开发工具", 2))
blocks.append(create_text_block("• GitHub: 代码版本管理"))
blocks.append(create_text_block("• Cron: 定时任务"))
blocks.append(create_text_block("• Python: 量化分析主力语言"))
blocks.append(create_text_block("• pandas/numpy: 数据处理"))
blocks.append(create_text_block(""))
blocks.append(create_divider_block())

# 智能特性
blocks.append(create_heading_block("⚡ 智能特性", 1))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("1. 自我进化", 2))
blocks.append(create_text_block("• self-improving: 从错误中学习，记录教训到文件"))
blocks.append(create_text_block("• proactivity: 主动预测需求，推动任务进展"))
blocks.append(create_text_block("• memory: 长期记忆，文件存储，禁用每日重置"))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("2. 主动行为", 2))
blocks.append(create_text_block("• 每日报告推送: 交易日08:00自动推送"))
blocks.append(create_text_block("• 舆情监控: 实时监控 + 飞书告警"))
blocks.append(create_text_block("• 策略信号: 发现高胜率机会主动提醒"))
blocks.append(create_text_block(""))
blocks.append(create_divider_block())

# 量化分析流程
blocks.append(create_heading_block("📊 量化分析流程", 1))
blocks.append(create_text_block("1. 数据采集 → Tushare/东方财富"))
blocks.append(create_text_block("2. 因子计算 → 技术因子 + 资金流因子"))
blocks.append(create_text_block("3. 策略信号 → 多因子确认"))
blocks.append(create_text_block("4. 回测验证 → 全量股票验证"))
blocks.append(create_text_block("5. 实盘监控 → 飞书推送"))
blocks.append(create_text_block(""))
blocks.append(create_divider_block())

# 使用指南
blocks.append(create_heading_block("🎯 使用指南", 1))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("激活技能", 2))
blocks.append(create_text_block("• \"明天气温\" → weather"))
blocks.append(create_text_block("• \"搜索XXX\" → tavily-search"))
blocks.append(create_text_block("• \"创建飞书文档\" → feishu-doc"))
blocks.append(create_text_block("• \"做个网页\" → frontend-design"))
blocks.append(create_text_block("• \"检查系统安全\" → healthcheck"))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("量化分析", 2))
blocks.append(create_text_block("• \"回测策略X\" → 运行指定策略回测"))
blocks.append(create_text_block("• \"全量A股回测\" → 对所有股票回测"))
blocks.append(create_text_block("• \"分析某股票\" → 计算因子+生成信号"))
blocks.append(create_text_block("• \"每日报告\" → 生成并推送市场报告"))
blocks.append(create_text_block(""))
blocks.append(create_divider_block())

# 重要原则
blocks.append(create_heading_block("⚠️ 重要原则", 1))
blocks.append(create_text_block("1. 真实数据: 禁止使用模拟/随机/测试数据"))
blocks.append(create_text_block("2. 严格止损: 2-3% 自动止损"))
blocks.append(create_text_block("3. 宁缺毋滥: 多因子确认才出手"))
blocks.append(create_text_block("4. 持续进化: 错误后立即记录教训"))
blocks.append(create_text_block(""))
blocks.append(create_divider_block())
blocks.append(create_text_block(""))
blocks.append(create_text_block("---"))
blocks.append(create_text_block("最后更新: 2026-04-08 by 超级龙虾"))

# 批量插入 (每次最多50个)
BATCH_SIZE = 50
print(f"准备插入 {len(blocks)} 个块...")

for i in range(0, len(blocks), BATCH_SIZE):
    batch = blocks[i:i+BATCH_SIZE]
    print(f"插入第 {i//BATCH_SIZE + 1} 批: {len(batch)} 个块")
    result = insert_blocks(DOC_TOKEN, batch)
    if result.get('code') != 0:
        print(f"错误: {json.dumps(result, ensure_ascii=False)}")
    else:
        print(f"成功插入 {len(batch)} 个块")

print("完成!")
