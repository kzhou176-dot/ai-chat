# E2E 端到端测试 & Demo Runner 调研 (2026-07-21)

## 调研背景
v1.0.1 收尾,25 cycle 即将收官。需要一个 **E2E demo runner** 串起 25 个模块,
证明从 "新生入学" 到 "拿到 offer" 的完整用户旅程在沙箱中可演示。

## 行业现状 (2026)

### 主流 E2E 测试范式
| 工具 | 形态 | 适用 |
|---|---|---|
| **Postman / Insomnia** | GUI/API 客户端 | 手动 / 协作 |
| **Playwright / Cypress** | 浏览器自动化 | Web SPA |
| **httpx / requests + pytest** | Python 脚本 | API E2E |
| **Locust / k6** | 负载 + 流程 | 性能 + 流程 |
| **Allure Report** | 报告生成 | 多框架聚合 |
| **自定义 smoke test** | 启动后跑核心 flow | 沙箱友好 |

**结论**:沙箱 + stdlib 场景, **自写 smoke runner** 是最简方案。

### aichat-hub 用户旅程 (5 阶段)

```
1️⃣ 入学探索 (大一/大二)
   → GET /api/personas 选虚拟人
   → POST /api/career/start 霍兰德测试
   → POST /api/career/answer × 60 题
   → POST /api/career/profile 画像
   → GET /api/industry/recommend 行业推荐

2️⃣ 简历准备 (大三/研一)
   → POST /api/resume/generate 生成
   → POST /api/resume/rewrite 改写
   → POST /api/resume/score 评分

3️⃣ 模拟面试 (大四/研二)
   → GET /api/interview/interviewers 选角色
   → POST /api/interview/start 开场
   → POST /api/interview/answer × 5-10 轮
   → POST /api/interview/end 总结

4️⃣ 校友/内推 (求职期)
   → GET /api/alumni/schools 看校友库
   → POST /api/alumni/match 4 维匹配
   → POST /api/alumni/refer 内推
   → GET /api/feed/list 看 feed

5️⃣ 行业洞察 & 论文
   → GET /api/industry/list 看行业
   → POST /api/industry/ask FAQ
   → POST /api/papers/search 论文
   → GET /api/papers/cite 引用
   → POST /api/paper_chat/start 论文对话
```

## v1.0.2 e2e_demo.py 设计

### 核心 API
- `DemoRunner` 类 — 5 阶段旅程
- `run_phase1_career(user_id)` 职业画像
- `run_phase2_resume()` 简历
- `run_phase3_interview()` 面试
- `run_phase4_alumni()` 校友
- `run_phase5_papers()` 论文
- `run_all(user_id)` 跑全部
- `generate_report()` 输出 markdown
- `PhaseResult` 数据类

### 沙箱友好原则
- 不依赖 LLM (用 mock error 路径)
- 不依赖网络 (用本地 web.ROUTES)
- 不依赖时序 (mock 全部可重复)
- 每个 phase 独立 try/except,失败不中断

### Demo 输出
- `data/demo_log.json` — 每步详细日志
- `reports/demo_report.md` — 人类可读报告

## 产出
- `research/market/e2e_testing.md` (本文件)
- `scripts/e2e_demo.py` (~13KB)
- `tests/test_25_e2e.py` (~8KB)
- `data/demo_log.json`
- `reports/demo_report.md`
- 5 篇 RAG × recruitment arxiv 论文(累计 55 → 60)
