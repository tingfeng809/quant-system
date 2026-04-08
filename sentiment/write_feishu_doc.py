#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""写入飞书文档"""
import requests
import json

TOKEN = "t-g104487CENRCQSF4T3SZ6BOXIEQMRXMOYTBLM4EL"
DOC_TOKEN = "CFQddhxOFoGUhNxskINca7TDnKb"
BASE_URL = "https://open.feishu.cn/open-apis/docx/v1"

def create_text_block(content, bold=False):
    """创建文本块"""
    return {
        "block_type": 2,
        "text": {
            "elements": [{"text_run": {"content": content}}],
            "style": {"align": 1, "folded": False}
        }
    }

def create_heading_block(content, level=1):
    """创建标题块 block_type: 3=h1, 4=h2, 5=h3"""
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
    """创建分割线"""
    return {"block_type": 22, "divider": {}}

def create_table_cell(content, is_header=False):
    """创建表格单元格"""
    return {
        "text_run": {"content": content}
    }

def create_table_row(cells, is_header=False):
    """创建表格行"""
    return {
        "cells": [{"elements": [create_table_cell(c)] for c in cells}],
        "style": {"merge_info": [], "background": {}}
    }

def create_table_block(rows):
    """创建表格块"""
    return {
        "block_type": 31,
        "table": {
            "cells": rows,
            "property": {
                "row_size": len(rows),
                "column_size": len(rows[0]["cells"]) if rows else 0,
                "header_row": True
            }
        }
    }

def insert_blocks(parent_id, blocks):
    """插入块"""
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

# 标题
blocks.append(create_heading_block("📋 基本信息", 1))
blocks.append(create_text_block(""))
blocks.append(create_text_block(""))
blocks.append(create_text_block(""))
blocks.append(create_text_block(""))
blocks.append(create_text_block(""))

# 基本信息表
blocks.append(create_table_block([
    create_table_row(["项目", "内容"]),
    create_table_row(["名称", "超级龙虾 (Super Lobster) ⛏️"]),
    create_table_row(["版本", "v1.0 (2026-04-08)"]),
    create_table_row(["定位", "A股量化分析 + 智能助手"]),
    create_table_row(["核心语言", "中文"]),
]))

blocks.append(create_text_block(""))
blocks.append(create_divider_block())
blocks.append(create_text_block(""))

# 技术能力
blocks.append(create_heading_block("🛠️ 技术能力", 1))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("1. 量化交易系统", 2))
blocks.append(create_table_block([
    create_table_row(["能力", "状态", "说明"]),
    create_table_row(["数据采集", "✅", "Tushare Pro + 东方财富"]),
    create_table_row(["技术因子", "✅", "35+ 因子 (MA, MACD, RSI, KDJ, CCI等)"]),
    create_table_row(["资金流因子", "✅", "10+ 因子"]),
    create_table_row(["自定义指数", "✅", "大盘/中盘/小盘/创业板"]),
    create_table_row(["情绪指数", "✅", "市场情绪综合分析"]),
    create_table_row(["舆情监控", "✅", "东方财富 + 飞书推送"]),
]))

blocks.append(create_text_block(""))
blocks.append(create_heading_block("2. 回测引擎", 2))
blocks.append(create_table_block([
    create_table_row(["能力", "状态", "说明"]),
    create_table_row(["基础回测", "✅", "单策略/多策略"]),
    create_table_row(["全量回测", "✅", "4400+ 股票"]),
    create_table_row(["高级策略", "✅", "布林带/RSI/Squeeze/KDJ/趋势/波动率"]),
    create_table_row(["高胜率策略", "✅", "多因子确认 + 严格止损"]),
]))

blocks.append(create_text_block(""))
blocks.append(create_heading_block("3. 策略库", 2))
blocks.append(create_table_block([
    create_table_row(["策略", "类型", "特点"]),
    create_table_row(["双均线策略", "趋势", "金叉买入，死叉卖出"]),
    create_table_row(["MACD策略", "趋势", "DIF上穿DEA买入"]),
    create_table_row(["资金流策略", "资金", "主力净流入筛选"]),
    create_table_row(["多因子策略", "综合", "技术+资金+基本面"]),
    create_table_row(["布林带策略", "波动", "上下轨突破交易"]),
    create_table_row(["RSI策略", "超买超卖", "RSI区间波动"]),
    create_table_row(["Squeeze动量", "波动率", "布林带收口扩张"]),
    create_table_row(["KDJ策略", "超买超卖", "快速随机指标"]),
    create_table_row(["趋势跟踪", "趋势", "EMA+ATR止损"]),
    create_table_row(["波动率突破", "突破", "N日高低点突破"]),
]))

blocks.append(create_text_block(""))
blocks.append(create_heading_block("4. 因子库", 2))
blocks.append(create_table_block([
    create_table_row(["类别", "方法数", "代表因子"]),
    create_table_row(["波动率因子", "4", "ATR, HV, Keltner, Donchian"]),
    create_table_row(["动量因子", "6", "RSI, Stochastic, CCI, MFI, Momentum, ROC"]),
    create_table_row(["趋势强度因子", "3", "ADX, Trend Intensity, SuperTrend"]),
    create_table_row(["成交量因子", "4", "OBV, VWAP, Volume Ratio, Money Flow"]),
    create_table_row(["支撑压力因子", "3", "Pivot Points, Fibonacci, Distance"]),
    create_table_row(["背离因子", "2", "量价背离, RSI背离"]),
]))

blocks.append(create_text_block(""))
blocks.append(create_divider_block())
blocks.append(create_text_block(""))

# 系统工具
blocks.append(create_heading_block("🔧 系统工具", 1))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("1. 飞书集成", 2))
blocks.append(create_table_block([
    create_table_row(["工具", "用途"]),
    create_table_row(["feishu-doc", "读写飞书文档"]),
    create_table_row(["feishu-drive", "管理云空间"]),
    create_table_row(["feishu-wiki", "知识库导航"]),
    create_table_row(["feishu-perm", "权限管理"]),
]))

blocks.append(create_text_block(""))
blocks.append(create_heading_block("2. 开发工具", 2))
blocks.append(create_table_block([
    create_table_row(["工具", "用途"]),
    create_table_row(["GitHub", "代码版本管理"]),
    create_table_row(["Cron", "定时任务"]),
    create_table_row(["Python", "量化分析主力语言"]),
    create_table_row(["pandas/numpy", "数据处理"]),
]))

blocks.append(create_text_block(""))
blocks.append(create_divider_block())
blocks.append(create_text_block(""))

# 智能特性
blocks.append(create_heading_block("⚡ 智能特性", 1))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("1. 自我进化", 2))
blocks.append(create_text_block("• self-improving: 从错误中学习，记录教训到文件"))
blocks.append(create_text_block("• proactivity: 主动预测需求，推动任务进展"))
blocks.append(create_text_block("• memory: 长期记忆，文件存储，禁用每日重置"))

blocks.append(create_text_block(""))
blocks.append(create_heading_block("2. 主动行为", 2))
blocks.append(create_table_block([
    create_table_row(["特性", "说明"]),
    create_table_row(["每日报告推送", "交易日08:00自动推送"]),
    create_table_row(["舆情监控", "实时监控 + 飞书告警"]),
    create_table_row(["策略信号", "发现高胜率机会主动提醒"]),
]))

blocks.append(create_text_block(""))
blocks.append(create_divider_block())
blocks.append(create_text_block(""))

# 量化分析流程
blocks.append(create_heading_block("📊 量化分析流程", 1))
blocks.append(create_text_block("1. 数据采集 → Tushare/东方财富"))
blocks.append(create_text_block("2. 因子计算 → 技术因子 + 资金流因子"))
blocks.append(create_text_block("3. 策略信号 → 多因子确认"))
blocks.append(create_text_block("4. 回测验证 → 全量股票验证"))
blocks.append(create_text_block("5. 实盘监控 → 飞书推送"))

blocks.append(create_text_block(""))
blocks.append(create_divider_block())
blocks.append(create_text_block(""))

# 使用指南
blocks.append(create_heading_block("🎯 使用指南", 1))
blocks.append(create_text_block(""))

blocks.append(create_heading_block("激活技能", 2))
blocks.append(create_table_block([
    create_table_row(["指令", "触发的技能"]),
    create_table_row(["\"明天气温\"", "weather"]),
    create_table_row(["\"搜索XXX\"", "tavily-search"]),
    create_table_row(["\"创建飞书文档\"", "feishu-doc"]),
    create_table_row(["\"做个网页\"", "frontend-design"]),
    create_table_row(["\"检查系统安全\"", "healthcheck"]),
]))

blocks.append(create_text_block(""))
blocks.append(create_heading_block("量化分析", 2))
blocks.append(create_table_block([
    create_table_row(["指令", "动作"]),
    create_table_row(["\"回测策略X\"", "运行指定策略回测"]),
    create_table_row(["\"全量A股回测\"", "对所有股票回测"]),
    create_table_row(["\"分析某股票\"", "计算因子+生成信号"]),
    create_table_row(["\"每日报告\"", "生成并推送市场报告"]),
]))

blocks.append(create_text_block(""))
blocks.append(create_divider_block())
blocks.append(create_text_block(""))

# 重要原则
blocks.append(create_heading_block("⚠️ 重要原则", 1))
blocks.append(create_text_block("1. 真实数据: 禁止使用模拟/随机/测试数据"))
blocks.append(create_text_block("2. 严格止损: 2-3% 自动止损"))
blocks.append(create_text_block("3. 宁缺毋滥: 多因子确认才出手"))
blocks.append(create_text_block("4. 持续进化: 错误后立即记录教训"))

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
