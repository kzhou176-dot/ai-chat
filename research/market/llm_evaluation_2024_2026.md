# LLM 评测体系全景(2024-2026)

> **抓取时间**:2026-07-21
> **来源**:CSDN / 博客园 / 知乎 / 腾讯云 / 搜狐

## 1. 主流 Benchmark 横向对比

| 评测 | 类型 | 评分方式 | 现状(2026) |
|---|---|---|---|
| **MMLU** | 综合知识(57 学科) | 多选准确率 | 已饱和(86-90%) |
| **MMLU-Pro** | 综合知识升级 | 多选+推理 | 70-85%,仍有效 |
| **GPQA Diamond** | 博士级科学推理 | 多选 | 推理模型分水岭 |
| **HellaSwag** | 常识推理 | 完形填空 | 已饱和 |
| **HumanEval** | Python 函数 | pass@k | 已饱和(90%+) |
| **GSM8K** | 小学数学 | 准确率 | 已饱和(97%+) |
| **MATH-500** | 竞赛数学 | 准确率 | 85-95% |
| **AIME 2025** | 数学邀请赛 | 准确率 | 80%+,区分度降 |
| **FrontierMath** | 前沿数学 | 准确率 | GPT-5.5 约 25%,仍是难关 |
| **ARC-AGI-2** | 抽象推理 | 模式归纳 | 30-50%,最强刷分抗性 |
| **HLE** | Humanity's Last Exam | 综合 | 2025 新终极测试 |

## 2. 实战派评测(Code/Agent)

| 评测 | 测试内容 | 当前 TOP | 局限 |
|---|---|---|---|
| **SWE-bench Verified** | 修 GitHub Issue | ~60%(GPT-5.5) | 题目较旧,易污染 |
| **SWE-bench Pro** | 更复杂企业代码 | 58.4%(GLM-5.1) | 闭源模型主导 |
| **LiveCodeBench** | 持续更新编程竞赛 | 抗污染 | 持续更新 |
| **Terminal-Bench 2.0** | Agent 任务 | 78.4%(Forge + Gemini 3.1) | 89 个任务,Docker |
| **GAIA** | 通用 AI 助理 | Claude Mythos 52.3% | 真实任务 |

## 3. 对话/生成评测

| 评测 | 特点 | 代表 |
|---|---|---|
| **MT-Bench** | 多轮对话 + GPT-4 评分 | MoA 9.25 / GPT-4o 9.19 |
| **AlpacaEval** | 胜率对比 vs GPT-3.5 | MoA 65.1% / GPT-4o 57.5% |
| **AlpacaEval 2.0** | LC Win Rate(长度控制) | 防冗长偏差 |
| **Chatbot Arena** | 人类盲评 ELO | LMSYS,最贴近用户 |
| **AlignBench** | 中文对齐 | 8 类 683 样本 |
| **FLASK** | 细粒度 | 正确性/事实性/洞察力/完整性 |

## 4. 长上下文评测

| 评测 | 方法 | 当前 |
|---|---|---|
| **NIAH** | 长文中插针 | 入门级 |
| **RULER** | 多合成任务 | 比 NIAH 严格 |
| **BABILong** | 长文档推理 | 真实场景 |
| **LongBench v2** | 综合 | 中等 |

## 5. 中文评测

- **C-Eval**:52 学科 14000+ 题
- **CMMLU**:中文 MMLU 对等
- **SuperCLUE**:中文通用
- **CIF-Bench**:中文指令遵循
- **C-SimpleQA**:中文事实

## 6. 2026 关键洞察

| 现象 | 数据 | 应对 |
|---|---|---|
| **基准饱和** | HumanEval/MMLU/GSM8K 都饱和 | 转向 HLE/FrontierMath/ARC-AGI-2 |
| **数据污染** | 伯克利 10 行 Python 拿 SWE-bench 满分 | LiveBench(每月新题) |
| **寿命缩短** | HumanEval 2 年 / SWE-bench 18 个月 | 自建私有评测 |
| **LLM-as-Judge** | GPT-4 评分 0.94 皮尔逊 | 偏差:位置/长度/自我强化 |
| **Agent 评测** | 7 个任务(代码/数学/博弈等) | Terminal-Bench + SWE-bench Pro |

## 7. 对我们做 5 维评分的指引

| 我们的维度 | 主流对应 | 简化实现 |
|---|---|---|
| 长度 | BLEU/ROUGE | char_count 区间评分 |
| 格式 | 规则 | markdown/code/list 检测 |
| 相关性 | RAGAS Answer Relevancy | 关键词覆盖度 |
| 多样性 | Distinct-N | unique n-gram 比例 |
| 响应时间 | Latency(秒) | 直接测 latency_ms |

## 8. 关键数据来源
- CSDN"LLM 学习记录 DAY14"评测范式总览
- CSDN"AI 大模型评测体系 2026 年 5 月演进"基准竞赛
- CSDN"系统学 AI 05 LLM 模型评测体系"
- CSDN"MoA vs GPT-4 Omni 双榜冠军"
- CSDN"AlignBench 中文对齐"
- 博客园"Starling-7B RLAIF"
