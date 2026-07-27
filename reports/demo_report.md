# AICHAT-HUB 端到端 Demo 报告 (v1.0.2)

**用户 ID**: demo_student_2026
**开始时间**: 2026-07-21 17:55:07
**总阶段数**: 5
**总 Step 数**: 38
**成功 Step**: 38 (100%)
**失败 Step**: 0

## phase1_career — 职业画像 (大一/大二 探索期): 霍兰德测试 + 行业推荐

**进度**: 8/8 成功

| # | Step | Method | Path | Status | 时长 (ms) |
|---|---|---|---|---|---|
| 1 | 查看虚拟人列表 | GET | `/api/personas` | ✅ 200 | 43.14 |
| 2 | 霍兰德 6 维度说明 | GET | `/api/career/dimensions` | ✅ 200 | 1.17 |
| 3 | 霍兰德 25 codes | GET | `/api/career/codes` | ✅ 200 | 0.01 |
| 4 | 开启霍兰德测试 | POST | `/api/career/start` | ✅ 200 | 2.53 |
| 5 | 答题 sample (Q1) | POST | `/api/career/answer` | ✅ 200 | 0.02 |
| 6 | 生成职业画像 (60 题 demo 跳过) | POST | `/api/career/profile` | ✅ 200 | 0.00 |
| 7 | 行业列表 | GET | `/api/industry/list` | ✅ 200 | 2.22 |
| 8 | 基于霍兰德推荐行业 | POST | `/api/industry/recommend` | ✅ 200 | 0.01 |

## phase2_resume — 简历准备 (大三/研一): 生成 + 改写 + 评分

**进度**: 5/5 成功

| # | Step | Method | Path | Status | 时长 (ms) |
|---|---|---|---|---|---|
| 1 | 简历 personas | GET | `/api/resume/personas` | ✅ 200 | 1.90 |
| 2 | 简历 variants | GET | `/api/resume/variants` | ✅ 200 | 0.01 |
| 3 | 生成简历 | POST | `/api/resume/generate` | ✅ 200 | 0.03 |
| 4 | 改写简历段落 | POST | `/api/resume/rewrite` | ✅ 200 | 0.16 |
| 5 | 简历评分 | POST | `/api/resume/score` | ✅ 200 | 1.31 |

## phase3_interview — 模拟面试 (大四/研二): 多角色 + 多轮

**进度**: 6/6 成功

| # | Step | Method | Path | Status | 时长 (ms) |
|---|---|---|---|---|---|
| 1 | 查看面试官 | GET | `/api/interview/interviewers` | ✅ 200 | 1.68 |
| 2 | 开始面试 (tech_lead) | POST | `/api/interview/start` | ✅ 200 | 0.04 |
| 3 | 回答 Q1 | POST | `/api/interview/answer` | ✅ 200 | 1.58 |
| 4 | 回答 Q2 | POST | `/api/interview/answer` | ✅ 200 | 0.08 |
| 5 | 回答 Q3 | POST | `/api/interview/answer` | ✅ 200 | 0.06 |
| 6 | 结束面试 | POST | `/api/interview/end` | ✅ 200 | 0.09 |

## phase4_alumni — 校友网络 (求职期): 同校 + 同专业 + 内推

**进度**: 7/7 成功

| # | Step | Method | Path | Status | 时长 (ms) |
|---|---|---|---|---|---|
| 1 | 学校列表 | GET | `/api/alumni/schools` | ✅ 200 | 2.11 |
| 2 | 校友列表 | GET | `/api/alumni/list` | ✅ 200 | 0.79 |
| 3 | 校友匹配 (清华 CS) | POST | `/api/alumni/match` | ✅ 200 | 0.20 |
| 4 | 请求内推 | POST | `/api/alumni/refer` | ✅ 200 | 0.05 |
| 5 | 内推状态查询 | POST | `/api/alumni/refer/status` | ✅ 200 | 0.01 |
| 6 | Feed 分类 | GET | `/api/feed/categories` | ✅ 200 | 2.04 |
| 7 | Feed 推荐 | POST | `/api/feed/recommend` | ✅ 200 | 0.66 |

## phase5_papers — 行业洞察 & 论文 (持续学习): FAQ + 论文检索 + 引用 + 对话

**进度**: 12/12 成功

| # | Step | Method | Path | Status | 时长 (ms) |
|---|---|---|---|---|---|
| 1 | 行业详情 (tech) | GET | `/api/industry/profile` | ✅ 200 | 0.02 |
| 2 | 行业 FAQ 提问 | POST | `/api/industry/ask` | ✅ 200 | 1.18 |
| 3 | 论文统计 | GET | `/api/papers/stats` | ✅ 200 | 21.47 |
| 4 | 论文关键词 | GET | `/api/papers/keywords` | ✅ 200 | 0.03 |
| 5 | 论文搜索 (LLM) | POST | `/api/papers/search` | ✅ 200 | 0.15 |
| 6 | 论文引用 (search 首个) | GET | `/api/papers/cite` | ✅ 200 | 0.04 |
| 7 | 开启论文对话 | POST | `/api/paper_chat/start` | ✅ 200 | 1.28 |
| 8 | 论文对话提问 | POST | `/api/paper_chat/ask` | ✅ 200 | 0.54 |
| 9 | 结束论文对话 | POST | `/api/paper_chat/end` | ✅ 200 | 0.02 |
| 10 | 数字人 preset | GET | `/api/human/presets` | ✅ 200 | 1.79 |
| 11 | 数字人 meta | GET | `/api/human/meta` | ✅ 200 | 0.01 |
| 12 | v1.0 release readiness | GET | `/api/release/readiness` | ✅ 200 | 5.24 |

## ✅ 结论

- ✅ 所有 38 个 step 100% 成功
- ✅ 5 阶段用户旅程覆盖全部 25 个模块
- ✅ 沙箱环境(无 LLM key) 友好降级,error 路径不崩