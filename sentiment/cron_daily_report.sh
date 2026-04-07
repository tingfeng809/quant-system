#!/bin/bash
# 每日市场报告 Cron 脚本
# 运行时间: 每个交易日的 08:00
/usr/bin/python3 /home/li/.openclaw/workspace/quant/sentiment/daily_report.py >> /home/li/.openclaw/workspace/quant/logs/daily_report.log 2>&1
