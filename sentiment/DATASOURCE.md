# 舆情系统数据源配置说明

**⛏️ 淘金者舆情监控系统 - 数据源集成指南**

---

## 📊 当前数据源状态

### ✅ 已激活数据源

| 数据源 | 类型 | 状态 | 说明 |
|--------|------|------|------|
| **Tushare 新闻 API** | API | ✅ 已激活 | 新浪财经新闻，实时更新 |

**配置位置**: `crawler/news_collector.py`

```python
# 主数据源
pro.news(src='sina', start_date=..., end_date=...)
```

---

### ⚠️ 待激活数据源

#### 1. 财联社 RSS

**RSS 地址**:
- 电报：https://www.cls.cn/rss/teletext.php
- A 股：https://www.cls.cn/rss/stock.php
- 要闻：https://www.cls.cn/rss/news.php

**状态**: ⚠️ 有反爬机制 (HTTP 418)

**解决方案**:
1. 使用代理 IP
2. 添加 Cookies
3. 降低采集频率
4. 使用官方 API (需申请)

**配置文件**: `config/rss_feeds.yaml`
**采集器**: `crawler/rss_collector.py`

---

#### 2. 其他财经 RSS

| 媒体 | RSS 地址 | 状态 |
|------|---------|------|
| 东方财富 | https://rss.eastmoney.com/news_cj.xml | 📝 待测试 |
| 新浪财经 | https://finance.sina.com.cn/rss/finance.xml | 📝 待测试 |
| 证券时报 | https://www.stcn.com/rss/news.xml | 📝 待测试 |

---

### 📋 规划中数据源

#### 官方渠道 (权重 1.0)
- 巨潮资讯 - 官方公告
- 上交所 - 监管信息
- 深交所 - 监管信息

#### 权威媒体 (权重 0.8)
- 证券时报
- 上海证券报
- 中国证券报
- 财新网

#### 社交平台 (权重 0.3)
- 雪球
- 淘股吧
- 微博财经

---

## 🔧 激活财联社 RSS 步骤

### 方案 1: 使用代理 (推荐)

```python
# 在 rss_collector.py 中添加代理
proxies = {
    'http': 'http://proxy-ip:port',
    'https': 'http://proxy-ip:port',
}

feed = feedparser.parse(feed_url, request_headers=self.headers, proxies=proxies)
```

### 方案 2: 添加 Cookies

```python
# 从浏览器复制 Cookies
self.headers['Cookie'] = 'sessionid=xxx; other_cookie=yyy'
```

### 方案 3: 降低频率

```yaml
# config/rss_feeds.yaml
cls_rss:
  telegraph:
    check_interval: 300  # 改为 5 分钟
```

### 方案 4: 官方 API

联系财联社获取官方 API 权限：
- 官网：https://www.cls.cn
- API 文档：需申请

---

## 📈 数据源优先级

### P0 - 必须接入
1. ✅ Tushare 新闻 API (已激活)
2. ⚠️ 财联社电报 (有反爬)

### P1 - 重要数据源
3. 📝 巨潮资讯 (官方公告)
4. 📝 交易所 RSS

### P2 - 补充数据源
5. 📝 东方财富
6. 📝 新浪财经
7. 📝 证券时报

### P3 - 可选数据源
8. 📝 雪球
9. 📝 淘股吧
10. 📝 微博

---

## 🧪 测试方法

### 测试 RSS 采集
```bash
cd /home/li/.openclaw/workspace/quant/sentiment
python3 crawler/rss_collector.py
```

### 测试 Tushare 新闻
```bash
python3 crawler/news_collector.py
```

### 测试完整流程
```bash
python3 main.py monitor --test
```

---

## 📊 数据源对比

| 数据源 | 速度 | 准确性 | 覆盖率 | 稳定性 | 权重 |
|--------|------|--------|--------|--------|------|
| Tushare API | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 0.6 |
| 财联社电报 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | 0.9 |
| 巨潮资讯 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 1.0 |
| 东方财富 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 0.6 |

---

## ⚠️ 注意事项

### 合规性
- ✅ 仅采集公开信息
- ✅ 遵守 robots.txt
- ✅ 控制采集频率
- ❌ 不爬付费内容
- ❌ 不商用未经授权数据

### 反爬应对
- 使用真实 User-Agent
- 控制请求频率
- 使用代理 IP
- 添加随机延迟

### 数据质量
- 多源交叉验证
- 去重过滤
- 来源权重评分
- 时间有效性检查

---

*最后更新：2026-04-06*
