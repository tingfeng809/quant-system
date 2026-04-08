#!/bin/bash
# 检查后台回测进程，完成后发飞书通知（仅通知一次）
# 用法: ./backtest_monitor.sh <日志文件> <策略名> <锁文件>

LOG_FILE="$1"
STRATEGY_NAME="$2"
LOCK_FILE="$3"
WEBHOOK_URL="https://open.feishu.cn/open-apis/bot/v2/hook/aa04be2c-9535-40a6-b1c0-cdeab1cd73a7"

# 检查锁文件（防止重复发送）
if [ -f "$LOCK_FILE" ]; then
    echo "$(date '+%Y-%m-%d %H:%M'): 已发送过通知，跳过"
    exit 0
fi

# 检查是否有python回测进程在运行
PY_COUNT=$(ps aux | grep "python3.*backtest" | grep -v grep | wc -l)
if [ "$PY_COUNT" -gt 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M'): 有$PY_COUNT个回测进程仍在运行..."
    exit 0
fi

echo "$(date '+%Y-%m-%d %H:%M'): 没有回测进程在运行!"

# 检查日志文件是否存在且有内容
if [ -f "$LOG_FILE" ] && [ -s "$LOG_FILE" ]; then
    # 提取关键指标
    TOTAL=$(grep "总测试:" "$LOG_FILE" | head -1 | awk '{print $3}')
    POSITIVE=$(grep "正收益:" "$LOG_FILE" | head -1 | awk '{print $3}')
    WIN_RATE=$(grep "正收益:" "$LOG_FILE" | head -1 | awk '{print $5}' | tr -d '()%')
    AVG_RETURN=$(grep "平均收益率:" "$LOG_FILE" | head -1 | awk '{print $3}')
    DURATION=$(grep "耗时:" "$LOG_FILE" | head -1 | awk '{print $4}')
    
    # 构建消息 (使用\n换行)
    MESSAGE="✅ ${STRATEGY_NAME}回测完成!\n📊 总测试: ${TOTAL}只\n🏆 正收益: ${POSITIVE}只 (${WIN_RATE}%)\n📈 平均收益: ${AVG_RETURN}\n⏱️ 耗时: ${DURATION}分钟"
    
    # 发送到飞书
    curl -s -X POST "$WEBHOOK_URL" \
        -H "Content-Type: application/json" \
        -d "{\"msg_type\":\"text\",\"content\":{\"text\":\"$MESSAGE\"}}" 2>/dev/null
    
    # 创建锁文件
    touch "$LOCK_FILE"
    
    echo "飞书通知已发送"
else
    echo "日志文件不存在或为空: $LOG_FILE"
fi

exit 0
