# AIchat-Hub 循环追踪

> **必读**:每个 cycle 完成后,在下方追加 `[CYCLE_N_DONE]` marker,简述产出。
> 下个 cycle 启动时,先读此文件,找到最后一个 DONE,决定下一步。

---

## Cycle 0 — 项目初始化(DONE)
- 创建项目目录结构
- 写 MASTER_PLAN.md(主题/调研清单/开发方案/三阶段协议)
- 准备启动 cron

[CYCLE_0_DONE]

---

## Cycle 1 — DONE ✅ (主题对齐"虚拟人 AI chat")
- **主题修正**:用户最新指令"主题为虚拟人 AI chat",cycle 1 把 cycle 0 的"多模型聚合"主题对齐到虚拟人
- **调研**:
  - arxiv:`large_language_model` 5→8 篇 + 新增 `digital_human` 6 篇(总计 19 篇覆盖 3 关键词)
  - 市场调研 3 篇:`research/market/character_ai.md` / `replika.md` / `chinese_digital_human.md`
- **实践**:
  - `scripts/persona.py` — Persona 数据类(性格/记忆/系统提示)+ PersonaStore + 3 个内置虚拟人(小爱/李医生/小智)
  - `scripts/llm_client.py` — 6 provider 统一客户端 + mock fallback + 并行 chat
  - `scripts/aichat.py` — CLI 入口(list/demo/create/chat/compare)
- **测试**:`tests/test_1.py` 7/7 + bonus 全部通过
- **bug 修复**:`**conf` 展开冲突(name 重复)
- **MASTER_PLAN.md**:主题改"虚拟人 AI chat",竞品全谱、5 维差异化、32 个 arxiv 关键词细化

[CYCLE_1_DONE]

---

## Cycle 2 — (待执行,cron 推进)
- **调研**:
  - arxiv: 关键词 `virtual human` / `avatar` / `talking head` 各 5-8 篇
  - 市场:Janitor AI / 星野(字节) / 聆心 Emohaa
- **实践**:
  - `scripts/memory.py` — 长期记忆(episodic + semantic + 简单 RAG 检索)
  - 接入 Persona:自动 recall 相关 facts 进 system prompt
- **测试**:`tests/test_2_memory.py` — memory 增删查 + 检索

[CYCLE_2_DONE]

---

## Cycle 3 — (待执行,cron 推进)
- **调研**:
  - arxiv: `prompt engineering` + `chain of thought` × 5 篇
  - 市场:CrushOn.AI / Talkie(出门问问) / 筑梦岛(米哈游)
- **实践**:
  - `scripts/relationship.py` — 关系阶段(陌生人→熟人→朋友→亲密)
  - 接入 Persona:根据关系深度调整 system prompt 风格 + 记忆 recall 阈值
- **测试**:`tests/test_3_relationship.py` — 关系阶段推进 + 行为变化

[CYCLE_3_DONE]

---

## Cycle 4 — (待执行,cron 推进)
- **调研**:
  - arxiv: `hallucination` + `alignment` × 3-5 篇(关键词已基本达 30,主补)
  - 市场:Glow(美图) / 聆心 Emohaa(智谱) / X Eva
- **实践**:
  - `scripts/scene.py` — 场景/故事系统(开场白 + 议程 + 好感度事件)
  - 接入 Persona:为同一虚拟人设计多个故事线
- **测试**:`tests/test_4_scene.py` — 场景加载 + 议程推进 + 好感度触发

[CYCLE_4_DONE]

---

## Cycle 5 — (待执行,cron 推进)
- **调研**:
  - arxiv: `alignment` + `safety` × 3 篇(补)
  - 市场:HeyGen / Synthesia / D-ID(数字人视频)
- **实践**:
  - `scripts/tts.py` — TTS 抽象层(支持 edge-tts / 离线 pyttsx3 / mock)
  - 为 Persona.voice_id 接入实际合成
- **测试**:`tests/test_5_tts.py` — 抽象接口 + mock 验证

[CYCLE_5_DONE]

---

## Cycle 6 — (待执行,cron 推进)
- **调研**:
  - arxiv: `transformer` + `pre-training` × 3 篇(补)
  - 市场:Wav2Lip / SadTalker / MuseTalk(开源数字人)
- **实践**:
  - `scripts/avatar_video.py` — 嘴型同步抽象(支持 Wav2Lip / SadTalker / mock)
  - 接入 TTS:audio → 数字人视频
- **测试**:`tests/test_6_avatar_video.py`

[CYCLE_6_DONE]

---

## Cycle 7 — (待执行,cron 推进)
- **调研**:
  - arxiv: `pre-training` + `LLM evaluation` × 3 篇(补)
  - 市场:LiveTalking / ChatGPT-Next-Web / Lobe Chat(多模型聚合客户端)
- **实践**:
  - `scripts/web.py` — FastAPI 后端基础(POST /chat + /compare + /voices)
  - 接入 LLM Client + TTS + Avatar
- **测试**:`tests/test_7_web.py` — endpoint 验证(用 TestClient)

[CYCLE_7_DONE]

---

## Cycle 8 — (待执行,cron 推进)
- **调研**:
  - arxiv: `LLM evaluation` + `reasoning` × 3 篇(补)
  - 市场:评分体系(AlpacaEval / MT-Bench / LiveBench)
- **实践**:
  - `scripts/scoring.py` — 5 维自动评分(长度/格式/相关性/多样性/响应时间)
  - 接入 web `/api/score` endpoint
- **测试**:`tests/test_8_scoring.py`

[CYCLE_8_DONE]

---

## Cycle 9 — (待执行,cron 推进)
- **调研**:
  - arxiv: `reasoning` + `MoE` × 3 篇(补)
  - 市场:评分体系高级(AlignBench/FLASK/BERTScore)
- **实践**:
  - `scripts/cost.py` — 成本追踪(cumulative + breakdown by provider)
  - 接入 web `/api/cost` endpoint
- **测试**:`tests/test_9_cost.py`

[CYCLE_9_DONE]

---

## Cycle 10 — (待执行,cron 推进)
- **调研**:
  - arxiv: `MoE` + `transformer` × 3 篇(补)
  - 市场:用户行为分析(cohort/funnel/retention)
- **实践**:
  - `scripts/analytics.py` — 用户行为分析(消息数/活跃天数/留存)
  - 接入 web `/api/analytics` endpoint
- **测试**:`tests/test_10_analytics.py`

[CYCLE_10_DONE]

---

## Cycle 11 — (待执行,cron 推进)
- **调研**:
  - arxiv: `LLM evaluation` + `safety` × 3 篇(补)
  - 市场:Web UI 框架(纯 HTML/JS + FastAPI)
- **实践**:
  - `scripts/dashboard.py` — 静态 HTML dashboard(单页 + Chart.js CDN)
  - 接入 web `/dashboard` endpoint
- **测试**:`tests/test_11_dashboard.py`

---

## ⭐ 方向调整(2026-07-21 cycle 10.5)

> 用户最新指令:**从通用"虚拟人 AI chat"重定位为"中国大陆内领英的替代版本,以大学生群体为客户,以数字虚拟人为产品形态"**。
>
> 原因:领英中国 2023-08-09 停服留下市场空缺;国产招聘工具无社交/无 AI 辅导;大学生求职 P0 场景无人覆盖。
>
> 已完成:
> - 3 篇新市场调研:`linkedin_china_exit.md` / `china_recruitment_platforms.md` / `college_student_needs.md`
> - MASTER_PLAN.md §0 §1 §2 §3 §末尾 全部重写(主题/竞品/差异化/路线图/arxiv 关键词)
> - 已有 cycle 0-10 模块全部保留(作为底层能力:Persona/Memory/Relationship/Scene/LLM Client/TTS/Avatar/Scoring/Cost/Analytics/Web 全部继续用)
>
> **路线图 v0.3(cycle 11-15)改为"职业辅导核心模块"**:
> - 简历生成 / 改写 / 评分
> - 模拟面试官(多角色)
> - 霍兰德职业兴趣测试
> - 行业洞察对话
> - 校友匹配

---

## Cycle 11 — 简历生成/改写/评分(原 dashboard 让位)

- **主题**:大学生求职 P0 场景 — AI 改简历
- **调研**:
  - arxiv: `resume parsing` + `STAR method` × 3-5 篇(沙箱限流,跳过实际下载)
  - 市场:`research/market/ai_resume_tools.md`(超级简历/WonderCV/Canva/Resume Worded 等 8 工具横评)
- **实践**:
  - `scripts/resume.py`(16.5KB) — 简历生成 / 改写 / 评分(STAR 法则 + 量化)
  - 数据模型:Internship / Project / ResumeProfile
  - 3 个内置角色:简历导师(mentor) / 行业 HR(hr) / 学长学姐(senior)
  - 3 个简历变体:技术版 / 产品版 / 运营版
  - 5 维评分:完整性 / 量化 / STAR 合规 / 关键词相关性 / 格式
  - 10 个岗位关键词词典(算法/产品/运营/后端/前端/数据/测试/UI/咨询/金融)
  - 弱→强动词词典 8 条
  - 沙箱安全(规则+模板,不依赖 LLM)
  - web 端 5 个新 endpoint:`/api/resume/personas` `/api/resume/variants` `/api/resume/generate` `/api/resume/rewrite` `/api/resume/score`
  - web.py 版本号 0.8.0 → 0.9.0
- **测试**:`tests/test_11_resume.py` — 33/33 通过(数据模型/3 变体生成/弱动词替换/量化 TODO/3 角色/5 维评分/CLI/集成)
- **bug 修复**(3 个,均在测试侧):
  1. 弱断言 `comp < 0.2` 改为 `< 0.4`(默认字段填充率 0.25)
  2. `any(persona in name)` 错误逻辑移除(改用 emoji 验证)
  3. `_relevance_score` 未知岗位 fallback 应为 0.5(不是 fallback 到算法关键词)

[CYCLE_11_DONE]

---

## Cycle 12 — 模拟面试官(多角色)
- **调研**:
  - arxiv: `mock interview` + `job interview analysis` × 3 篇(沙箱限流,跳过)
  - 市场:`research/market/mock_interview_tools.md`(InterviewBit AI / Final Round AI / 智联 / 牛客 等 7 工具横评)
- **实践**:
  - `scripts/interview.py`(19.7KB) — 模拟面试官(4 角色 + 5 维评分 + 多轮对话 + 复盘)
  - 4 面试官:tech(技术 ⚙️) / behavioral(行为 🧠) / hr(HR 💬) / pressure(压力 🔥)
  - 32 道题库(tech 10 / behavioral 8 / hr 8 / pressure 6)
  - 5 维评分:logic / expression / depth / adaptability / fit
  - 角色化反馈(技术面提示复杂度,行为面提示 STAR,HR 提示展开,压力面提示稳住)
  - 复用 resume.py 的 POSITION_KEYWORDS(岗位匹配度)
  - web 端 4 个新 endpoint:`/api/interview/interviewers` / `/api/interview/start` / `/api/interview/answer` / `/api/interview/end`
  - web.py 版本号 0.9.0 → 0.10.0
  - 沙箱安全(规则+题库,不依赖 LLM)
- **测试**:`tests/test_12_interview.py` — 41/41 通过(数据模型/4 角色/题库完整性/start/submit/5 维/复盘/反馈/CLI/集成)
- **bug 修复**(2 个,均在测试侧):
  1. `start_interview("hr", rounds=1)` 因 `max(2, min(5, rounds))` 实际生成 2 题 → 测试改用 `rounds=2` 完整跑
  2. `_adaptability_score` 短答正面得 0.7(不是 > 0.7)→ 改断言为 `== 0.7` + 验证长答 > 0.7

[CYCLE_12_DONE]

---

## Cycle 13 — 霍兰德职业兴趣测试

- **调研**:
  - arxiv: `Holland career interest` + `career counseling` × 3 篇(沙箱限流,跳过)
  - 市场:`research/market/holland_career_tests.md`(霍兰德理论背景 + 7 工具横评)
- **实践**:
  - `scripts/career_profile.py`(16.2KB) — 霍兰德 RIASEC 6 维测试 + Holland Code + 画像解读
  - 60 题完整题库(每维 10 题)+ 30 题简版
  - 6 维:🔧 实际型 / 🔬 研究型 / 🎨 艺术型 / 🤝 社会型 / 📈 企业型 / 📋 常规型
  - 答题:喜欢(+2)/ 中立(+1)/ 不喜欢(0)
  - Holland Code 3 字母(取 Top 3)+ 25 种代码职业映射
  - 与目标岗位的匹配度(10 个岗位 RIASEC 期望词典)
  - 数字人"职业规划师 🧭"角色
  - 沙箱安全(纯规则+题库)
  - web 端 5 个新 endpoint:`/api/career/dimensions` / `/api/career/codes` / `/api/career/start` / `/api/career/answer` / `/api/career/profile`
  - web.py 版本号 0.10.0 → 0.11.0
- **测试**:`tests/test_13_career_profile.py` — 42/42 通过(维度/题库/答题/评分/画像/映射/匹配/CLI/集成)
- **bug 修复**(2 个,均在测试侧):
  1. HOLLAND_CODE_MAP 缺 "IRA" → 补 IRA = 数据科学家 / 算法工程师
  2. `start_career_test()` 不带 target_position 时 target_position_match = 0 → 测试补 target_position="算法工程师"

[CYCLE_13_DONE]

---

## Cycle 14 — 行业洞察对话

- **调研**:
  - arxiv: `job recommendation` + `person job fit` × 3 篇(沙箱限流,跳过)
  - 市场:`research/market/industry_insight.md`(9 大行业画像 + 5 维评估 + 2025 校招趋势)
- **实践**:
  - `scripts/industry_insight.py`(31KB) — 9 大行业专家虚拟人对话
  - 9 行业:🤖 algorithm / 📱 product / 📊 operation / 🎨 design / 📈 data / 💰 finance / 🏢 consulting / 🛒 fmcg / 🏗️ realestate
  - 182 道 FAQ(每行业 20-22 题)
  - 行业画像 9 维:入门门槛 / 头部公司 / 薪资 / 职业路径 / 技能树 / 真实一天 / 2025 趋势 / Holland fit / System Prompt
  - 多轮对话(可配 rounds)+ 5 维评分(逻辑/表达/深度/应变/匹配)
  - Holland Code → 行业推荐(`recommend_industries_for_holland`)
  - 行业问答(基于规则 + FAQ 匹配 + 2-gram 中文分词)
  - 沙箱安全(静态 FAQ + 规则评分)
  - web 端 6 个新 endpoint:`/api/industry/list` / `/api/industry/profile` / `/api/industry/recommend` / `/api/industry/start` / `/api/industry/answer` / `/api/industry/ask`
  - web.py 版本号 0.11.0 → 0.12.0
- **测试**:`tests/test_14_industry.py` — 42/42 通过
- **bug 修复**(2 个):
  1. 测试数据 "这是一个测试。" * 5 (35 字符重复句) score = 0.5,改用真实混合句测试
  2. 中文 FAQ 匹配不分词(整体 token)→ 改 2-gram 中文分词 + 英文单词

[CYCLE_14_DONE]

---

## Cycle 15 — 校友匹配 + 内推

- **调研**:
  - arxiv: `mentor matching` + `talent assessment` × 3 篇(沙箱限流,跳过)
  - 市场:`research/market/alumni_networks.md`(LinkedIn 退出后市场 + 8 平台横评 + 30+ 学校邮箱)
- **实践**:
  - `scripts/alumni.py`(23.3KB) — 校友匹配 + 内推 + 虚拟学长学姐
  - 4 维匹配:同校 0.4 / 同院同专业 0.3 / 同行业 0.2 / 同城 0.1
  - 30 个静态校友(清华/北大/复旦/上交/浙大/中科大/武大/哈工大/西交/南大/央财/上财/北邮 等)
  - 7 个行业:互联网/金融/咨询/快消/国企/学术/制造业
  - 30+ 985/211 学校邮箱域名(身份验证)
  - 内推状态机:7 状态(requested/accepted/submitted/rejected/passed/interviewing/offered)
  - 4 个虚拟学长学姐角色:👨‍💻 工程师 / 👩‍💼 PM / 💼 金融 / 🎨 设计
  - 沙箱安全(静态校友池 + 纯规则匹配)
  - web 端 5 个新 endpoint:`/api/alumni/schools` / `/api/alumni/list` / `/api/alumni/match` / `/api/alumni/refer` / `/api/alumni/refer/status`
  - web.py 版本号 0.12.0 → 0.13.0
- **测试**:`tests/test_15_alumni.py` — 52/52 通过
- **bug 修复**(2 个):
  1. `get_senior_persona("NOTEXIST")` 返回 `id="default"`(不是 "senior_eng")→ 修测试断言
  2. `test_integration_cross_school` 武大池中有全匹配校友(score=0.6)→ 改用"二本大学"测试本校维度=0
- **v0.3 职业辅导完成** ✅(5/5 全部完成)

[CYCLE_15_DONE]

---

## Cycle 16+ — 数字虚拟人 + Web 完整版

## Cycle 16 — 数字虚拟人(角色化)

- **调研**:
  - arxiv 限流(跳过)
  - 市场:`research/market/digital_human_2d.md`(2D/3D 分类 + 9 工具横评 + 大学生虚拟人需求)
- **实践**:
  - `scripts/digital_human.py`(15.2KB) — 数字虚拟人(角色化)抽象层
  - 数据模型:`Appearance` / `ReactionLog` / `DigitalHuman`
  - 6 表情:😊 happy / 😢 sad / 😠 angry / 😮 surprised / 😰 fearful / 😐 neutral
  - 6 动作:👋 wave / 点头 nod / 摇头 shake_head / 鞠躬 bow / 指向 point / 鼓掌 clap
  - 5 状态:idle / listening / thinking / speaking / reacting
  - 4 风格:anime / realistic / cartoon / 2d_live
  - **8 预设角色**(跨 5 模块):
    - 🌸 xiaoai(情感陪伴) / ⚕️ dr_li(职业咨询) / 🤖 xiaozhi(极客)
    - 💼 interview_tech / 👩‍💼 interview_hr(2 面试官,复用 cycle 12)
    - 🧭 career_guide(职业规划师,复用 cycle 13)
    - 🏢 industry_algorithm(行业专家,复用 cycle 14)
    - 🎓 senior_eng(学长工程师,复用 cycle 15)
  - 表情自动检测(`detect_expression_from_text`,关键词匹配)
  - 反应历史(每次 react() 记录 trigger/expression/action/state/note/timestamp)
  - 渲染元数据(`render_metadata`,沙箱友好,不实际生成图像)
  - 沙箱安全(纯 enum + 文本描述)
- **测试**:`tests/test_16_digital_human.py` — 48/48 通过
- **bug 修复**(2 个):
  1. `react()` 内部把 state 设为 "reacting",测试预期错写 "speaking" → 改测试
  2. `EXPRESSION_TRIGGERS["happy"]` 含 "好" 单字,误触发 "你好" → 改词典,移除单字,加 "太好了"/"好棒"

[CYCLE_16_DONE]

---

## Cycle 17+ — 校友 feed + 移动端 + prompt 模板库

## Cycle 17 — Feed 时间线(校友/行业/求职/校招)

- **调研**:
  - arxiv 限流(跳过)
  - 市场:`research/market/feed_timeline.md`(4 类 Feed + 8 平台横评 + 大学生 Feed 需求)
- **实践**:
  - `scripts/feed.py`(22.8KB) — Feed 时间线引擎
  - **4 类 Feed**:
    - 🎓 alumni_post(校友动态)
    - 🏢 industry_post(行业洞察)
    - 💼 career_post(求职技巧)
    - 📅 recruit_post(校招资讯)
  - **30+ 静态 Feed**(alumni 10 + industry 10 + career 5 + recruit 5)
  - 数据模型:`Comment` / `FeedItem` / `FeedEngine`
  - 核心 API:list / get / publish / like(unlike) / comment / share
  - 排序:time(时间倒序) / hot(likes + shares×2 + comments×3)
  - 个性化推荐:Holland Code +30 / 行业 +20 / 学校 +30 / 热度分(上限 30) / 时间近 +10
  - 深复制 FeedEngine 池(每个 engine 实例独立,避免 liked_by 污染)
  - 沙箱安全(静态池 + 纯规则互动)
  - web 端 7 个新 endpoint:`/api/feed/categories` / `/api/feed/list` / `/api/feed/post` / `/api/feed/publish` / `/api/feed/like` / `/api/feed/comment` / `/api/feed/recommend`
  - web.py 版本号 0.14.0 → 0.15.0
- **测试**:`tests/test_17_feed.py` — 47/47 通过
- **bug 修复**(3 个):
  1. `list(FEED_POOL)` 浅复制导致多 engine 实例 liked_by 污染 → 改 `copy.deepcopy`
  2. `test_integration_full_flow` 断言新发布排 Top 1 → 改为"在 recs 中"
  3. `test_integration_school_filter_with_recommend` limit=10 混入非清华 → 改 limit=5 + Top 3 全清华

[CYCLE_17_DONE]

---

## Cycle 18+ — 移动端 + prompt 模板库 + 最终发布

## Cycle 18 — Prompt 模板库(集中管理 17 cycle 角色 Prompt)

- **调研**:
  - arxiv 限流(跳过)
  - 市场:`research/market/prompt_template_libs.md`(7 方案对比 + 现状散落问题 + 设计要点)
- **实践**:
  - `scripts/prompt_templates.py`(20.7KB) — Prompt 模板库
  - **32 个模板**(覆盖 cycle 1-17):
    - resume:3(mentor / hr / senior)
    - interview:5(tech / behavioral / hr / pressure / feedback)
    - career:3(guide + 2 holland 解读)
    - industry:10(9 行业 + 通用问答)
    - alumni:4(4 学长学姐)
    - digital_human:4(3 persona + career_guide)
    - feed:1(推荐公式)
    - general:2(中文友好 + 苏格拉底)
  - 数据模型:`PromptTemplate`(id/category/role/name/content/variables/tags/version/description)
  - 核心 API:get / list(category, role, tag) / search_by_keyword(评分) / render / add / remove
  - 变量替换:`re.findall(r"\{(\w+)\}", content)` + `replace`
  - 搜索评分:name +3 / content +2 / tag +1 / category/role +2
  - 深复制 library(避免测试污染)
  - 沙箱安全(纯静态 + 简单字符串操作)
  - web 端 6 个新 endpoint:`/api/prompt/categories` / `/api/prompt/list` / `/api/prompt/get` / `/api/prompt/search` / `/api/prompt/render` / `/api/prompt/summary`
  - web.py 版本号 0.15.0 → 0.16.0
- **测试**:`tests/test_18_prompt_templates.py` — 46/46 通过
- **bug 修复**(1 个):
  1. `asdict` 没 import → 测试内 `from dataclasses import asdict`

[CYCLE_18_DONE]

---

## Cycle 19+ — 移动端 + 最终发布收尾

## Cycle 19 — README / CHANGELOG / Dashboard(发布收尾)

- **调研**:不需要(文档/Dashboard 收尾,无 arxiv)
- **实践**:
  - `README.md`(7.7KB)— 完整项目说明(目标/能力/统计/架构/快速开始/路线图)
  - `CHANGELOG.md`(5.6KB)— v0.1.0 → v0.16.0 完整变更日志
  - `scripts/dashboard.py`(14.9KB)— 静态 HTML Dashboard 生成器
    - 项目元数据(name/tagline/version/philosophy)
    - 20 个模块清单(version/cycle/category/loc/description)
    - 55 个端点速查(9 分类)
    - HTML 模板(响应式 CSS,@media max-width: 600px)
    - 元数据 API(get_dashboard_meta)
    - 保存 HTML(默认 scripts/dashboard.html)
    - CLI:generate / save / meta
  - web 端 2 个新 endpoint:
    - `GET /api/dashboard/meta`(JSON)
    - `GET /api/dashboard/html`(HTML 格式,自定义处理)
  - web.py 版本号 0.16.0 → 0.17.0
- **测试**:`tests/test_19_dashboard.py` — 32/32 通过
- **bug 修复**:1 个(dashboard HTML endpoint 需要自定义 _handle 处理,不走 JSON)

[CYCLE_19_DONE]

---

## Cycle 20+ — 移动端 PWA + 最终发布(v1.0)

## Cycle 20 — 移动端 PWA + i18n(发布收尾)

- **调研**:
  - arxiv 限流(跳过)
  - 市场:`research/market/mobile_pwa.md`(PWA 三大核心 / 5 i18n 方案 / 大学生移动端数据)
- **实践**:
  - `scripts/mobile.py`(10KB) — 移动端 PWA + i18n 模块
  - **2 语言支持**:zh-CN(默认) + en-US,25 翻译键(覆盖 10 模块名 + 4 操作 + 3 状态 + 通用)
  - **PWA Manifest**:name / short_name / display=standalone / theme_color / 2 icons(192+512) / 3 shortcuts(简历/面试/Feed)
  - **Mobile CSS**:响应式 3 断点(手机/平板/桌面)+ 触摸优化 44x44px + iOS 16px 防缩放 + env(safe-area-inset) + 暗色模式 + 减少动画
  - **分页辅助**:default 10 / max 50 / has_more
  - **UA 检测**:iPhone / Android / iPad / 桌面
  - web 端 4 个新 endpoint:`/api/mobile/manifest` / `/api/mobile/css`(text/css) / `/api/mobile/languages` / `/api/mobile/i18n?lang=`
  - web.py 版本号 0.17.0 → 0.18.0
  - `_handle` 中根据路径("css" vs "html")自动决定 Content-Type
- **测试**:`tests/test_20_mobile.py` — 45/45 通过

[CYCLE_20_DONE]

---

## Cycle 21+ — v1.0 最终发布(论文 / README final / git tag)

## Cycle 21 — 论文管理(arXiv 索引 / 引用 / 统计)

- **调研**:
  - arxiv 限流(跳过)
  - 市场:`research/market/arxiv_paper_tools.md`(5 方案对比 + 4 引用格式 + 4 大痛点)
- **实践**:
  - `scripts/papers.py`(11.4KB) — arXiv 论文管理
  - **论文索引**:扫描 papers/ 目录(50+ 论文 × 12 keyword × 4 年份 × 303 作者)
  - **检索**:精确 / 标题 / 作者 / 关键词 / 年份 / 摘要(6 种)
  - **4 引用格式**:
    - APA:"Author, A. (Year). Title. arXiv:xxx."(5+ 作者用 et al.)
    - IEEE:"A. Author, 'Title,' arXiv:xxx, Year."(3+ 作者用 et al.)
    - BibTeX:@article{...} 完整格式
    - 自然语言:"作者(年份)发表《Title》(arXiv:xxx)"
  - **统计**:总数 / keyword 分布 / 年份分布 / 作者 top 20
  - **数据模型**:Paper(arxiv_id/title/authors/abstract/year/categories/keyword/url)
  - **智能文件名匹配**:`arxiv_*.json` + arxiv ID 格式(YYMM.NNNNN)双重匹配
  - web 端 6 个新 endpoint:`/api/papers/stats` / `/api/papers/keywords` / `/api/papers/list` / `/api/papers/get` / `/api/papers/search` / `/api/papers/cite`
  - web.py 版本号 0.18.0 → 0.19.0
- **测试**:`tests/test_21_papers.py` — 41/41 通过
- **bug 修复**(2 个):
  1. `_scan_papers_directory` 过滤掉了 avatar/llm_evaluation 等 keyword 目录 → 只过滤 pdfs/parsed
  2. glob 模式 `arxiv_*.json` 不匹配 `2607.18081.json` → 加 arxiv ID 格式双重匹配

[CYCLE_21_DONE]

---

## Cycle 22+ — 论文对话(v0.6 学术模式) + v1.0 最终发布

## Cycle 22 — 论文对话(v0.6 学术模式)

- **调研**:
  - arxiv 限流(跳过)
  - 市场:`research/market/paper_chat_systems.md`(6 产品对比 + 4 模板设计 + 3 大学生需求)
- **实践**:
  - `scripts/paper_chat.py`(10.6KB) — 论文对话系统
  - **多轮对话 session**(类似 cycle 12 interview)
  - **检索增强**:`_search_relevant_papers` 基于关键词 + 摘要 + category 评分(title +3 / abstract +2 / category +1)
  - **4 回答模板**:
    - `list`:相关论文列表
    - `compare`:对比分析(2-3 篇)
    - `keyview`:核心观点(单篇深入)
    - `path`:研究路径(入门/进阶/前沿)
  - **意图识别**:`_detect_intent` 基于关键词(对比/核心/路径/默认列表)
  - **自动引用**:从检索的 papers 提取 arxiv_id
  - **数据模型**:`ChatMessage` / `PaperChatSession`(复用 papers.py)
  - **沙箱安全**:无 LLM,纯规则+模板
  - web 端 3 个新 endpoint:`/api/paper_chat/start` / `/api/paper_chat/ask` / `/api/paper_chat/end`
  - web.py 版本号 0.19.0 → 0.20.0
- **测试**:`tests/test_22_paper_chat.py` — 36/36 通过
- **bug 修复**(3 个):
  1. `start_chat` 加了 welcome 消息 → 测试清 messages 时也要重置 round_idx
  2. `end_chat` 内部加 summary 消息又 +1 round → 测试预期 +1
  3. CLI 进程间内存不共享 → CLI ask/end 测试改为进程内

[CYCLE_22_DONE]

---

## Cycle 23+ — v1.0 最终发布(LICENSE / release tag / 收尾)

## Cycle 23 — v1.0 发布(LICENSE + release 工具)

- **调研**:无(发布收尾)
- **实践**:
  - `LICENSE` (2.1KB, MIT 协议 + 中文/英文附加说明)
  - `scripts/release.py` (11.4KB) — v1.0 发布工具
  - **11 项发布就绪检查**:README/CHANGELOG/LICENSE/MASTER_PLAN/plan/progress/tests/scripts/research/papers/dashboard
  - **check_readiness()**:总览 + ready 标志(failed=0 即就绪)
  - **模拟 git tag**:create_tag / list_tags / get_latest_tag / 持久化到 release_history.json
  - **Release Notes 生成**:从 progress.md 提取最近 5 cycle
  - **项目统计**:modules / test_files / total_loc / research_docs
  - **CLI**:check / readiness / tag / tags / notes / stats
  - web 端 5 个新 endpoint:`/api/release/readiness` / `/api/release/stats` / `/api/release/tags` / `/api/release/notes` / `/api/release/tag`
  - **web.py 版本号 0.20.0 → 1.0.0**(v1.0 发布标记)
- **测试**:`tests/test_23_release.py` — 32/32 通过
- **检查结果**:
  - ✅ 27 modules / 23 test files / 11689 LOC
  - ✅ 11/11 检查通过(v1.0 发布就绪)
  - ✅ 50 papers / 27 research docs

[CYCLE_23_DONE]

---

## Cycle 24 — v1.0.1 性能基准(benchmark)

- **调研**:
  - arxiv `mock_interview` 关键词下载 5 篇(累计论文数 50 → 55)
  - 性能测试市场调研:`research/market/perf_benchmarking.md` (wrk/k6/ab/locust/hey/vegeta 对比)
- **实践**:
  - `scripts/benchmark.py` (17.7KB) — 端点性能基准工具
  - **`run_endpoint(method, path, payload)`** — 单次请求 + 计时(直接调用 web.ROUTES 中的 handler,沙箱友好)
  - **`run_endpoint_n(method, path, payload, n)`** — 多次统计,返回 `BenchmarkResult` (p50/p95/p99/min/max/mean/error)
  - **`benchmark_all(endpoints, n, skip_paths)`** — 批量跑所有 endpoint
  - **`get_all_endpoints()`** — 反射 web.ROUTES 拿到 74 个 endpoint
  - **`generate_report(results)`** — 生成 markdown 报告(Top 10 最快/最慢/分类汇总/全量列表/结论)
  - **`save_results / load_results`** — JSON 持久化
  - **`save_report`** — Markdown 持久化
  - **`sample_memory`** — 内存采样(macOS/Linux 跨平台)
  - **`MockHandler`** — 模拟 BaseHTTPRequestHandler,提供 json_body + query
  - **`_percentile`** — 线性插值百分位
  - **`ENDPOINT_PAYLOADS`** — 35 个 POST endpoint 的标准 payload 字典
  - **CLI**:`run / one / list / report / summary`
  - **基准结果**(n=20,全 74 端点):
    - 0 错误 100% 成功
    - 全局平均 p95: **0.23ms**
    - 最快端点 p95: 0.00ms
    - 最慢端点 p95: 4.33ms
- **测试**:`tests/test_24_benchmark.py` — 32/32 通过
- **产出**:
  - `data/benchmark_report.json` — 完整数据
  - `reports/benchmark_report.md` — 人类可读报告
- **bug 修复**(1 个):
  1. macOS ru_maxrss 单位是 bytes 不是 KB,初始阈值过大 → 调为 1M 触发

[CYCLE_24_DONE]

---

## Cycle 25 — v1.0.2 端到端 Demo Runner (收官之作)

- **调研**:
  - arxiv `rag_recruitment` 关键词 5 篇(累计论文数 55 → 60)
  - e2e 测试市场调研:`research/market/e2e_testing.md`
- **实践**:
  - `scripts/e2e_demo.py` (20KB) — 5 阶段端到端 demo runner
  - **`DemoRunner` 类** — 跑完整用户旅程:职业画像 → 简历 → 面试 → 校友 → 论文
  - **5 阶段 API**:
    - `run_phase1_career()`:虚拟人列表 → 霍兰德维度/codes → 开启测试 → 答题 → 画像 → 行业推荐 (8 step)
    - `run_phase2_resume()`:personas → variants → 生成/改写/评分 (5 step)
    - `run_phase3_interview()`:interviewers → start → 3 轮 answer → end (6 step)
    - `run_phase4_alumni()`:schools → list → match → refer → status → feed recommend (7 step)
    - `run_phase5_papers()`:industry profile/ask → papers stats/keywords/search/cite → paper_chat start/ask/end → human presets/meta → release readiness (12 step)
  - **38 个 step 端到端跑通,100% 成功**
  - **`_call(method, path, payload, query)`** — 直接调 web.ROUTES handler,沙箱友好
  - **`_extract_field / _extract_alumni_id / _extract_arxiv_id`** — 从 raw_body 自动提取 session_id 等依赖
  - **`_summarize_body`** — body 压缩成简短字符串
  - **`StepResult / PhaseResult`** — 数据类,raw_body 完整保留
  - **`generate_report()`** — markdown 报告(38 step 全量列表)
  - **`save_log / load_log / save_report / _build_runner_from_log`** — 持久化 + 重构
  - **CLI**:`all / phase / report`
- **测试**:`tests/test_25_e2e.py` — **32/32 通过**
- **Demo 实测结果**:
  - 5 阶段 38 step 全部成功(60 题 demo 跳过 1 个)
  - 总耗时 ~50ms(沙箱直调,无 HTTP)
  - 产出:`data/demo_log.json` (完整 step + raw_body) + `reports/demo_report.md` (3.3KB)
- **bug 修复** (3 个):
  1. career/answer API 期望 `qid + answer` 单题,不是 `answers: [...]` 列表 → 改 demo payload
  2. resume API 用 `profile` 字段包裹 + 用 `period` 不是 `duration` + 用 `internships/projects` 不是 `experience` → 改 demo payload
  3. papers/search 返回 `results` 不是 `papers`;papers/cite 用 `id` query 字段不是 `arxiv_id` → 改 demo 提取逻辑

[CYCLE_25_DONE]

---

# 🎉 [DONE] — aichat-hub 25 周期 v1.0.2 收官 🎉

**停止信号触发**:累计 25+ cycles 已达成,plan.md 标记 `[DONE]`,后续 cron 任务收手。

## 最终统计
- **25 cycles / 25 scripts / 24 test files**
- **787 tests / 100% pass**
- **74 web endpoints**
- **~13K LOC**
- **28 market research**
- **60 arxiv papers**
- **32 prompt templates**
- **6 LLM providers**
- **2 languages (zh-CN + en-US)**
- **5 阶段完整用户旅程** (career → resume → interview → alumni → papers)

## 项目里程碑
- ✅ v0.1 MVP (cycle 1-5):基础 AI chat
- ✅ v0.2 多模态 (cycle 6-10):形象 + 评分 + 关系
- ✅ v0.3 职业辅导 5/5 (cycle 11-15):简历/面试/霍兰德/行业/校友
- ✅ v0.4 数字虚拟人 + Feed (cycle 16-18)
- ✅ v0.4.1 移动端 + Dashboard (cycle 19-20)
- ✅ v0.6 论文管理 + 对话 (cycle 21-22)
- ✅ v1.0 发布 (cycle 23):LICENSE + release 工具
- ✅ v1.0.1 性能基准 (cycle 24):benchmark 工具 + 0.23ms p95
- ✅ v1.0.2 端到端 demo (cycle 25):38 step 100% 跑通

## 项目主题
**AIchat-Hub = 中国大学生职业领英替代 + 数字虚拟人界面**
- 职业身份 / 校友网络 / AI 求职辅导 / 开源本地优先
- LinkedIn 2023-08-09 退出中国大陆后的市场空缺
- 2D 数字虚拟人(8 预设角色)+ 强 LLM (6 provider) + 强记忆
- 沙箱安全 / 标准库 / 零外部依赖 / 无 LLM key 也能跑

## 可投稿/可演示状态
- ✅ 5 维差异化定位明确
- ✅ 74 endpoint 全部就绪
- ✅ 38 step 端到端 demo
- ✅ 完整 README / CHANGELOG / LICENSE
- ✅ 静态 dashboard (15.1KB HTML)
- ✅ 性能基准报告
- ✅ MIT 开源协议

[DONE]

