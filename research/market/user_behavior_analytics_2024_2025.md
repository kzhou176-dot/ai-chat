# 用户行为分析体系(2024-2025)

> **抓取时间**:2026-07-21
> **来源**:阿里云 / 网易 / CSDN / 腾讯云 / 知乎 / 博客园

## 1. 三大核心模型

### 1.1 漏斗分析(Funnel)
- **定义**:分析用户在多步骤过程中的转化和流失
- **典型 4-7 层级**:引流→激活→留存→转化→复购
- **核心指标**:转化率(本环节/上环节)、流失率(1-转化率)
- **窗口函数**:`window_funnel(window, mode, timestamp, cond1, ..., condN)`
- **电商例子**:访客→浏览→加购→结算→订单→支付
- **SaaS 例子**:广告点击→注册→试用→付费→续费

### 1.2 留存分析(Retention)
- **定义**:初始行为后多少用户会进行后续行为
- **核心指标**:N 日/周/月留存率
- **窗口函数**:`retention(cond1, ..., cond32)`(返回 0/1 数组)
- **Facebook 40-20-10 规则**:次日 40% / 7 日 20% / 30 日 10%
- **Cohort 同期群**:同月份获取用户的后续行为

### 1.3 LTV 预估
- **Gamma-Gamma 模型**:消费金额预测
- **BG/NBD 模型**:购买频率预测
- **应用**:CLV(Customer Lifetime Value)

## 2. AI chat 产品专用指标

### 2.1 核心 KPI
- **北极星指标**:30 日留存率(Day30 Retention)
- **拆解公式**:
  - Day30 = f(首次激活完成度, 功能使用深度, 教育完成度, 推送触达效果)

### 2.2 事件类型(IPA 案例)
| 事件 | 关键属性 | 示例 |
|---|---|---|
| app_launch | channel, os | 小米商店 / Android |
| onboarding_step | step_id, duration | step_3, 15.2s |
| bill_add | bill_type, amount, auto_tag | 餐饮, 28.5 |
| budget_set | category, amount | 餐饮, 1200 |
| invest_view | product_id, risk_level | 0001, R3 |
| push_receive | campaign_id, msg_type | 2025q3_edu |

### 2.3 数据分层
```
ODS(原始)→ DWD(事件明细)→ DWS(用户-日汇总)→ ADS(分析主题宽表)
```

## 3. 分析工具对比

| 工具 | 特点 | 适用 |
|---|---|---|
| **AnalyticDB** | 内置 window_funnel + retention | 大数据场景 |
| **ClickHouse** | 留存分析模型 | 互联网公司 |
| **StarRocks** | 漏斗 + 留存函数(MySQL 兼容) | 实时分析 |
| **易分析** | 用户路径 + 漏斗 + 留存 | 通用 SaaS |
| **retentioneering** | Sankey 行为路径 | Python 研究 |

## 4. 关键洞察(对我们做 analytics.py 的指引)

| 维度 | 主流 | 我们(简化) |
|---|---|---|
| **事件追踪** | 客户端埋点 + 服务端日志 | 从关系/记忆模块汇总 |
| **漏斗** | 4-7 层级 window_funnel | persona 互动链路 |
| **留存** | N 日 + cohort | 活跃天数 + 关系阶段 |
| **LTV** | Gamma-Gamma | cost.py 累计成本 |
| **Cohort** | 按月分组 | 按 persona 分组 |
| **A/B 测试** | 实验平台 | 未来 cycle 集成 |

## 5. 数据来源
- 阿里云"漏斗留存函数"(AnalyticDB)
- 阿里云"漏斗分析与留存分析函数"(PostgreSQL 版)
- 网易"用户行为分析有哪些"
- CSDN"用户行为分析之漏斗模型"
- 腾讯云"AI 个人理财助手用户行为分析"(完整实战)
- 知乎"Retention Analysis 用户留存分析"
- 知乎"用户留存分析之 Cohort 模型"
- CSDN"StarRocks 漏斗留存函数"
- 博客园"vivo 留存分析模型实践"
