# Changelog

> 记录 aichat-hub 的所有变更
> 格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)

## [v1.0.0] - 2026-07-21 - 第一个稳定发布 🎉

### Added
- `LICENSE` MIT 协议 + 中文/英文附加说明
- `scripts/release.py` v1.0 发布工具(11 项就绪检查 / 模拟 git tag / release notes / 项目统计)
- 5 个新 web endpoint:`/api/release/*`(readiness / stats / tags / notes / tag)
- **web.py 版本号 0.20.0 → 1.0.0**(v1.0 发布标记)

### 最终统计
- 24 cycles / 24 scripts / 23 test files
- **723 tests / 100% pass**
- 74 web endpoints
- 11689 行代码
- 50 篇论文 / 27 篇市场调研
- 32 prompt 模板 / 8 预设角色

## [v1.0.1] - 2026-07-21 - 性能基准收尾 🔬

### Added
- `scripts/benchmark.py` (17.7KB) — 端点性能基准工具
  - `run_endpoint(method, path, payload)` 单次请求计时
  - `run_endpoint_n(method, path, payload, n)` 多次统计 p50/p95/p99/min/max/mean
  - `benchmark_all(endpoints, n, skip_paths)` 批量跑 74 端点
  - `get_all_endpoints()` 反射 web.ROUTES
  - `generate_report(results)` markdown 报告(Top 10/分类汇总/全量)
  - `save_results / save_report` JSON + Markdown 持久化
  - `sample_memory` macOS/Linux 跨平台内存采样
  - CLI:`run / one / list / report / summary`
- arxiv `mock_interview` 关键词 5 篇(累计 50 → 55)
- `research/market/perf_benchmarking.md` 性能测试市场调研

### Performance
- **74 端点 n=20 全跑通,0 错误 100% 成功**
- 全局平均 p95: **0.23ms**
- 最快端点:0.00ms (典型 enum 列表)
- 最慢端点:4.33ms (paper list 全文搜索)

### Tests
- `tests/test_24_benchmark.py` (12.8KB) — **32/32 通过**
- 累计:**755 tests / 100% pass**

### Fixed
- macOS ru_maxrss 单位错误(原阈值过大,改 1M 触发)
- 移动端 PWA + i18n(2 语言)

---

## [v0.20.0] - 2026-07-21 - cycle 22 论文对话

### Added
- `scripts/paper_chat.py` - 论文对话系统
- 多轮对话 session + 4 回答模板(列表/对比/核心观点/研究路径)
- 检索增强(基于 cycle 21 的 50+ 论文)
- 意图识别(对比/核心/路径/默认)
- 自动引用(arxiv_id)
- 3 个新 web endpoint(`/api/paper_chat/*`)
- `tests/test_22_paper_chat.py` - 36 个测试

### Changed
- web.py 版本号 0.19.0 → 0.20.0

## [v0.19.0] - 2026-07-21 - cycle 21 论文管理

### Added
- `scripts/papers.py` - arXiv 论文管理(索引 / 检索 / 4 引用格式 / 统计)
- 50 篇论文(2023-2026)/ 12 keyword / 303 作者
- 4 引用格式:APA / IEEE / BibTeX / 自然语言
- 6 个新 web endpoint(`/api/papers/*`)
- `tests/test_21_papers.py` - 41 个测试

### Changed
- web.py 版本号 0.18.0 → 0.19.0

## [v0.18.0] - 2026-07-21 - cycle 20 移动端 PWA + i18n

### Added
- `scripts/mobile.py` - 移动端 PWA + i18n(2 语言)
- PWA Manifest / Mobile CSS(响应式 / 触摸 / iOS 安全区域 / 暗色)
- 25 翻译键(zh-CN + en-US)
- 分页辅助 + UA 检测
- 4 个新 web endpoint(`/api/mobile/*`)
- `tests/test_20_mobile.py` - 45 个测试

### Changed
- web.py 版本号 0.17.0 → 0.18.0

## [v0.17.0] - 2026-07-21 - cycle 19 README/CHANGELOG/Dashboard

### Added
- `README.md` 完整项目说明
- `CHANGELOG.md` 完整变更日志
- `scripts/dashboard.py` 静态 HTML Dashboard(20 模块 / 55 端点)
- 2 个新 web endpoint(`/api/dashboard/*`)
- `tests/test_19_dashboard.py` - 32 个测试

### Changed
- web.py 版本号 0.16.0 → 0.17.0

## [v0.16.0] - 2026-07-21 - cycle 18 Prompt 模板库

### Added
- `scripts/prompt_templates.py` - Prompt 模板库(8 类别 32 模板)
- 32 个模板覆盖 cycle 1-17 全部角色 Prompt
- 变量替换 + 搜索评分 + 增删
- 6 个新 web endpoint(`/api/prompt/*`)
- `tests/test_18_prompt_templates.py` - 46 个测试

### Changed
- web.py 版本号 0.15.0 → 0.16.0

## [v0.15.0] - 2026-07-21 - cycle 17 Feed

### Added
- `scripts/feed.py` - Feed 时间线(4 类 + 30 内容 + 个性化推荐)
- 4 类 Feed / 30 静态内容 / 互动(点赞/评论/分享)
- 5 因子个性化推荐
- 7 个新 web endpoint(`/api/feed/*`)
- `tests/test_17_feed.py` - 47 个测试

### Changed
- web.py 版本号 0.14.0 → 0.15.0

## [v0.14.0] - 2026-07-21 - cycle 16 数字虚拟人

### Added
- `scripts/digital_human.py` - 数字虚拟人抽象层
- 6 表情/6 动作/5 状态/4 风格 + 8 预设角色
- 表情自动检测(关键词匹配)
- 6 个新 web endpoint(`/api/human/*`)
- `tests/test_16_digital_human.py` - 48 个测试

### Changed
- web.py 版本号 0.13.0 → 0.14.0

## [v0.13.0] - 2026-07-21 - cycle 15 校友 + 内推

### Added
- `scripts/alumni.py` - 校友匹配(4 维) + 内推(7 状态)
- 30 校友(13 学校 / 7 行业)
- 30+ 学校邮箱域名
- 4 虚拟学长学姐角色
- 5 个新 web endpoint(`/api/alumni/*`)
- `tests/test_15_alumni.py` - 52 个测试

### Changed
- web.py 版本号 0.12.0 → 0.13.0

## [v0.12.0] - 2026-07-21 - cycle 14 行业洞察

### Added
- `scripts/industry_insight.py` - 9 行业专家对话(182 FAQ)
- Holland Code → 行业推荐
- 行业问答(2-gram 中文分词)
- 6 个新 web endpoint(`/api/industry/*`)
- `tests/test_14_industry.py` - 42 个测试

### Changed
- web.py 版本号 0.11.0 → 0.12.0

## [v0.11.0] - 2026-07-21 - cycle 13 霍兰德

### Added
- `scripts/career_profile.py` - 霍兰德 RIASEC 测试(60 题 + 25 code)
- 10 岗位 RIASEC 期望词典
- 5 个新 web endpoint(`/api/career/*`)
- `tests/test_13_career_profile.py` - 42 个测试

### Changed
- web.py 版本号 0.10.0 → 0.11.0

## [v0.10.0] - 2026-07-21 - cycle 12 模拟面试

### Added
- `scripts/interview.py` - 模拟面试官(4 角色 + 5 维)
- 32 道题库
- 4 个新 web endpoint(`/api/interview/*`)
- `tests/test_12_interview.py` - 41 个测试

### Changed
- web.py 版本号 0.9.0 → 0.10.0

## [v0.9.0] - 2026-07-21 - cycle 11 简历

### Added
- `scripts/resume.py` - 简历生成/改写/评分(3 角色 + 5 维)
- 3 简历变体(技术/产品/运营)
- 10 岗位关键词词典
- 5 个新 web endpoint(`/api/resume/*`)
- `tests/test_11_resume.py` - 33 个测试

### Changed
- web.py 版本号 0.8.0 → 0.9.0

## [v0.8.0] - 2026-07-21 - cycle 10 analytics

### Added
- `scripts/analytics.py` - 用户行为分析(漏斗/留存/Cohort)
- 2 个新 web endpoint(`/api/cost` / `/api/analytics`)
- `tests/test_10_analytics.py` - 20 个测试

### Changed
- web.py 版本号 0.7.0 → 0.8.0

## [v0.7.0] - 2026-07-21 - cycle 9 cost

### Added
- `scripts/cost.py` - 成本追踪(7 provider)
- 1 个新 web endpoint(`/api/cost`)
- `tests/test_9_cost.py` - 23 个测试

### Changed
- web.py 版本号 0.6.0 → 0.7.0

## [v0.6.0] - 2026-07-21 - cycle 8 scoring

### Added
- `scripts/scoring.py` - 5 维自动评分
- 1 个新 web endpoint(`/api/score`)
- `tests/test_8_scoring.py` - 27 个测试

### Changed
- web.py 版本号 0.5.0 → 0.6.0

## [v0.5.0] - 2026-07-21 - cycle 7 web

### Added
- `scripts/web.py` - 零依赖 HTTP 后端(8 endpoint)
- `tests/test_7_web.py` - 21 个测试

## [v0.4.0] - 2026-07-21 - cycle 6 avatar

### Added
- `scripts/avatar_video.py` - 嘴型同步抽象(4 provider)
- `tests/test_6_avatar_video.py` - 21 个测试

## [v0.3.0] - 2026-07-21 - cycle 5 tts

### Added
- `scripts/tts.py` - TTS 抽象层(3 provider)
- `tests/test_5_tts.py` - 20 个测试

## [v0.2.1] - 2026-07-21 - cycle 4 scene

### Added
- `scripts/scene.py` - 场景系统(7 类型)
- `tests/test_4_scene.py` - 17 个测试

## [v0.2.0] - 2026-07-21 - cycle 3 relationship

### Added
- `scripts/relationship.py` - 关系阶段(4 阶段)
- `tests/test_3_relationship.py` - 17 个测试

## [v0.1.2] - 2026-07-21 - cycle 2 memory

### Added
- `scripts/memory.py` - 长期记忆(episodic + semantic + RAG)
- `tests/test_2_memory.py` - 13 个测试

## [v0.1.1] - 2026-07-21 - cycle 1 基础

### Added
- `scripts/persona.py` - 虚拟人系统(3 预设)
- `scripts/llm_client.py` - 6 provider 统一客户端
- `scripts/aichat.py` - CLI 入口
- `tests/test_1.py` - 7 个测试

## [v0.1.0] - 2026-07-21 - cycle 0 项目初始化

### Added
- 项目初始化
- `MASTER_PLAN.md` 总方案
- `plan.md` 循环追踪
- `progress.md` 详细日志
- 目录结构(research / papers / scripts / tests / data)

---

## 累计统计(cycle 0-23)

| 指标 | 数量 |
|---|---|
| Cycles | 24 |
| Scripts | 24 |
| Tests | **723 (100% pass)** |
| Web Endpoints | 74 |
| 代码行数 | 11689 |
| 市场调研 | 27 |
| arxiv 论文 | 50 |
| Prompt 模板 | 32 |
| 预设角色 | 8 |
| LLM Providers | 6 |

## 路线图进度

- ✅ v0.1 MVP(cycle 1-5)
- ✅ v0.2(cycle 6-10)
- ✅ v0.3 职业辅导(cycle 11-15)
- ✅ v0.4 数字虚拟人 + Feed + Prompt(cycle 16-18)
- ✅ v0.4.1 README/CHANGELOG/Dashboard(cycle 19)
- ✅ v0.4.2 移动端 PWA(cycle 20)
- ✅ v0.6 论文管理 + 对话(cycle 21-22)
- ✅ **v1.0 发布(cycle 23)** 🎉

## [Unreleased] - v0.4.1 移动端 + Dashboard

### Added
- `scripts/dashboard.py` 静态 HTML dashboard(项目统计 + 模块卡片 + API 列表 + 端点速查)
- `README.md` 完整项目说明
- `CHANGELOG.md` 本文件
- mobile-responsive 优化(响应式 CSS)

## [v0.16.0] - 2026-07-21 - cycle 18

### Added
- `scripts/prompt_templates.py` - Prompt 模板库(8 类别 32 模板)
- 32 个模板覆盖 cycle 1-17 全部角色 Prompt(resume 3 / interview 5 / career 3 / industry 10 / alumni 4 / digital_human 4 / feed 1 / general 2)
- 变量替换 `{var}` 模板引擎
- 关键词搜索评分(name +3 / content +2 / tag +1 / category/role +2)
- web 端 6 个新 endpoint(`/api/prompt/*`)
- `tests/test_18_prompt_templates.py` - 46 个测试

### Changed
- web.py 版本号 0.15.0 → 0.16.0

## [v0.15.0] - 2026-07-21 - cycle 17

### Added
- `scripts/feed.py` - Feed 时间线引擎(4 类 Feed + 30+ 静态内容)
- 4 类 Feed:校友动态 / 行业洞察 / 求职技巧 / 校招资讯
- 个性化推荐(5 因子评分:Holland / 学校 / 行业 / 热度 / 时间)
- 点赞 / 评论 / 分享 互动
- web 端 7 个新 endpoint(`/api/feed/*`)
- `tests/test_17_feed.py` - 47 个测试

### Changed
- web.py 版本号 0.14.0 → 0.15.0

## [v0.14.0] - 2026-07-21 - cycle 16

### Added
- `scripts/digital_human.py` - 数字虚拟人抽象层
- 6 表情 / 6 动作 / 5 状态 / 4 风格
- 8 预设角色(跨 5 模块)
- 表情自动检测(关键词匹配)
- 渲染元数据(沙箱友好)
- web 端 6 个新 endpoint(`/api/human/*`)
- `tests/test_16_digital_human.py` - 48 个测试

### Changed
- web.py 版本号 0.13.0 → 0.14.0

## [v0.13.0] - 2026-07-21 - cycle 15

### Added
- `scripts/alumni.py` - 校友匹配 + 内推
- 4 维匹配(同校 0.4 / 同院同专业 0.3 / 同行业 0.2 / 同城 0.1)
- 30 静态校友(13 学校,7 行业)
- 30+ 985/211 学校邮箱域名(身份验证)
- 内推状态机(7 状态)
- 4 虚拟学长学姐角色(👨‍💻 工程师 / 👩‍💼 PM / 💼 金融 / 🎨 设计)
- web 端 5 个新 endpoint(`/api/alumni/*`)
- `tests/test_15_alumni.py` - 52 个测试

### Changed
- web.py 版本号 0.12.0 → 0.13.0

## [v0.12.0] - 2026-07-21 - cycle 14

### Added
- `scripts/industry_insight.py` - 9 行业专家对话
- 9 行业:algorithm / product / operation / design / data / finance / consulting / fmcg / realestate
- 182 道 FAQ(每行业 20-22 题)
- Holland Code → 行业推荐
- 行业问答(规则 + 2-gram 中文分词)
- web 端 6 个新 endpoint(`/api/industry/*`)
- `tests/test_14_industry.py` - 42 个测试

### Changed
- web.py 版本号 0.11.0 → 0.12.0

## [v0.11.0] - 2026-07-21 - cycle 13

### Added
- `scripts/career_profile.py` - 霍兰德 RIASEC 6 维测试
- 60 题完整题库 + 30 题简版
- 25 种 Holland Code 解读
- 10 岗位 RIASEC 期望词典
- web 端 5 个新 endpoint(`/api/career/*`)
- `tests/test_13_career_profile.py` - 42 个测试

### Changed
- web.py 版本号 0.10.0 → 0.11.0

## [v0.10.0] - 2026-07-21 - cycle 12

### Added
- `scripts/interview.py` - 模拟面试官(4 角色)
- 4 面试官:tech / behavioral / hr / pressure
- 32 道题库
- 5 维评分:logic / expression / depth / adaptability / fit
- 角色化反馈
- 多轮对话 + 复盘
- web 端 4 个新 endpoint(`/api/interview/*`)
- `tests/test_12_interview.py` - 41 个测试

### Changed
- web.py 版本号 0.9.0 → 0.10.0

## [v0.9.0] - 2026-07-21 - cycle 11

### Added
- `scripts/resume.py` - 简历生成/改写/评分
- 3 角色:mentor / hr / senior
- 3 简历变体:technical / product / operation
- 5 维评分:completeness / quantification / star_compliance / relevance / format
- 弱动词词典 + 量化 TODO 标记
- 10 岗位关键词词典
- web 端 5 个新 endpoint(`/api/resume/*`)
- `tests/test_11_resume.py` - 33 个测试

### Changed
- web.py 版本号 0.8.0 → 0.9.0

## [v0.8.0] - 2026-07-21 - cycle 10

### Added
- `scripts/analytics.py` - 用户行为分析
- 6 大功能:漏斗 / 留存 / Cohort / 价值 / Persona 分布
- web 端 2 个新 endpoint(`/api/cost` / `/api/analytics`)
- `tests/test_10_analytics.py` - 20 个测试

### Changed
- web.py 版本号 0.7.0 → 0.8.0

## [v0.7.0] - 2026-07-21 - cycle 9

### Added
- `scripts/cost.py` - 成本追踪(7 provider 累计 + 分类)
- web 端 1 个新 endpoint(`/api/cost`)
- `tests/test_9_cost.py` - 23 个测试

### Changed
- web.py 版本号 0.6.0 → 0.7.0

## [v0.6.0] - 2026-07-21 - cycle 8

### Added
- `scripts/scoring.py` - 5 维自动评分(长度/格式/相关性/多样性/响应时间)
- web 端 1 个新 endpoint(`/api/score`)
- `tests/test_8_scoring.py` - 27 个测试

### Changed
- web.py 版本号 0.5.0 → 0.6.0

## [v0.5.0] - 2026-07-21 - cycle 7

### Added
- `scripts/web.py` - 零依赖 HTTP 后端(http.server + JSON)
- 8 个 endpoint(基础 CRUD)
- `tests/test_7_web.py` - 21 个测试

## [v0.4.0] - 2026-07-21 - cycle 6

### Added
- `scripts/avatar_video.py` - 嘴型同步抽象(4 provider)
- Wav2Lip / SadTalker / MuseTalk / Mock
- `tests/test_6_avatar_video.py` - 21 个测试

## [v0.3.0] - 2026-07-21 - cycle 5

### Added
- `scripts/tts.py` - TTS 抽象层(3 provider)
- ChatTTS / Edge TTS / ElevenLabs
- `tests/test_5_tts.py` - 20 个测试

## [v0.2.1] - 2026-07-21 - cycle 4

### Added
- `scripts/scene.py` - 场景系统(7 类型)
- 议程 + 好感度事件
- `tests/test_4_scene.py` - 17 个测试

## [v0.2.0] - 2026-07-21 - cycle 3

### Added
- `scripts/relationship.py` - 关系阶段(陌生人→熟人→朋友→亲密)
- `tests/test_3_relationship.py` - 17 个测试

## [v0.1.2] - 2026-07-21 - cycle 2

### Added
- `scripts/memory.py` - 长期记忆(episodic + semantic + RAG)
- `tests/test_2_memory.py` - 13 个测试

## [v0.1.1] - 2026-07-21 - cycle 1

### Added
- `scripts/persona.py` - 虚拟人系统(3 预设)
- `scripts/llm_client.py` - 6 provider 统一客户端
- `scripts/aichat.py` - CLI 入口
- `tests/test_1.py` - 7 个测试

## [v0.1.0] - 2026-07-21 - cycle 0

### Added
- 项目初始化
- `MASTER_PLAN.md` 总方案
- `plan.md` 循环追踪
- `progress.md` 详细日志
- 目录结构(research / papers / scripts / tests / data)

---

## 累计统计(cycle 0-18)

| 指标 | 数量 |
|---|---|
| Cycles | 19 |
| Scripts | 20 |
| Tests | **537 (100% pass)** |
| Web Endpoints | 55 |
| LLM Providers | 6 |
| 角色预设 | 8 |
| 行业专家 | 9 |
| 校友 | 30 |
| Feed | 30+ |
| Prompt 模板 | 32 |
| 市场调研 | 17 篇 |
| arxiv 论文 | 50+ |

## 路线图进度

- ✅ v0.1 MVP(cycle 1-5):文本虚拟人
- ✅ v0.2(cycle 6-10):形象 + 分析
- ✅ v0.3 职业辅导(cycle 11-15):**5/5 完成**
- ✅ v0.4 数字虚拟人 + Feed(cycle 16-18):**3/3 完成**
- ✅ v0.4.1 移动端 + Dashboard(cycle 19-20)
- ✅ v0.6 论文管理 + 对话(cycle 21-22)
- ✅ v1.0 发布(cycle 23)
- ✅ v1.0.1 性能基准(cycle 24)
- ✅ v1.0.2 端到端 demo(cycle 25) — 收官
- 🎉 **[DONE]** 累计 25+ cycles,停止 cron 推进

## [v1.0.2] - 2026-07-21 - 端到端 Demo 收官 🚀

### Added
- `scripts/e2e_demo.py` (20KB) — 5 阶段端到端 demo runner
  - `DemoRunner` 类 — 完整用户旅程
  - `run_phase1_career / run_phase2_resume / run_phase3_interview / run_phase4_alumni / run_phase5_papers`
  - `run_all()` 一键跑全部 5 阶段 38 step
  - `_call / _extract_field / _extract_alumni_id / _extract_arxiv_id` — 沙箱直调 helper
  - `generate_report()` markdown 报告
  - CLI:`all / phase / report`
- arxiv `rag_recruitment` 关键词 5 篇(累计 55 → 60)
- `research/market/e2e_testing.md` 端到端测试市场调研

### Demo 结果
- **5 阶段 38 step 端到端 100% 通过**
- 覆盖:职业画像 → 简历 → 面试 → 校友 → 论文
- 产出:`data/demo_log.json` + `reports/demo_report.md` (3.3KB)

### Tests
- `tests/test_25_e2e.py` (13KB) — **32/32 通过**
- 累计:**787 tests / 100% pass**

### Fixed
- career/answer API payload 格式(`qid+answer` 单题,不是 `answers` 列表)
- resume profile 字段结构(`profile` 包裹 + `period` + `internships/projects` 列表)
- papers API 字段名(`results` 不是 `papers`,query 用 `id` 不是 `arxiv_id`)

## 🎉 收官统计

| 指标 | 数量 |
|---|---|
| **Cycles** | 26 |
| **Scripts** | 26 |
| **Tests** | 787 (100% pass) |
| **Web Endpoints** | 74 |
| **代码行数** | ~13K |
| **市场调研** | 29 |
| **arxiv 论文** | 60 |
| **Prompt 模板** | 32 |
| **角色** | 8 + 4 + 9 + 4 |
| **LLM Providers** | 6 |
| **语言** | 2 (zh-CN + en-US) |
| **Demo Step** | 38 (100%) |
| **性能基线** | p95 mean 0.23ms |

**停止信号**:`[DONE]` 标记写入 plan.md,后续 cron 任务不再推进。
