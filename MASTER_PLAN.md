# AIchat-Hub 总方案

> **活文档 — 任何 agent cold-start 必读**
> 本文件是**唯一权威**:调研方向、开发方案、三阶段协议、循环记录、cron 行为都在这里。
> 配套文件:`plan.md`(循环 markers)、`progress.md`(详细日志)、`research/`(调研产物)、`scripts/`(代码)、`tests/`(测试)。

---

## 0. 元信息

- **项目名**:AIchat-Hub(中国大学生职业社交 + 数字虚拟人框架)
- **创建日期**:2026-07-21
- **主题**:**中国大陆内领英的替代版本** — 以**大学生群体**为客户,以**数字虚拟人**为产品形态,提供"职业身份 + 校友网络 + 行业洞察 + AI 求职辅导"四件套
- **目标用户**:中国大陆本科/研究生(大一-大四 + 研一-研三 + 应届毕业生)
- **产品形态**:Web + 移动端 + 数字虚拟人(2D Live + TTS),本地优先 / 沙箱安全
- **循环协议**:15 分钟 1 个 cycle,严格 3 阶段(调研→实践→测试),由 cron 持续触发
- **停止信号**:用户在 plan.md 写 `[DONE]` / `[PAUSE]` / `[ASK_USER]` 时,agent 收手
- **主题演化**(三次调整):
  - cycle 0:多模型聚合客户端
  - cycle 1:对齐为"虚拟人 AI chat"(通用)
  - **cycle 10.5(本次)**:重定位为"**中国大学生职业领英替代 + 数字虚拟人界面**",原因 = 领英 2023-08-09 退出中国大陆、国产招聘工具无社交属性、大学生求职 P0 场景(简历/模拟面试/校友/行业洞察)无人覆盖

---

## 1. 主题 & 差异化定位

### 1.1 主题范围(Cycle 10.5 重定位)

**AIchat-Hub = 中国大学生职业社交平台 + 数字虚拟人界面**

= **LinkedIn 已退(2023-08-09)+ 国产招聘工具无社交属性 + 数字虚拟人作为人机交互形态**

具体覆盖:
- **职业社交层**:校友网络 / 同校同专业垂直 / 内推 / 行业动态
- **求职辅导层**:简历生成 / 模拟面试 / 职业画像 / 行业洞察
- **数字虚拟人层**:模拟面试官 / 学长学姐 / 行业专家 / HR 顾问 / 职业规划师

### 1.2 竞品全谱(分 3 层)

**L1 — 招聘工具(我们的"补位"竞品)**:
- BOSS直聘、智联招聘、前程无忧 51job、应届生求职网、国家大学生就业服务平台(24365)、拉勾、猎聘、脉脉
- **共性短板**:无校友关系网络、无 AI 辅导、行业洞察弱

**L2 — 通用职业内容(我们的"间接"竞品)**:
- 小红书(求职经验)、知乎(行业问答)、即刻(互联网从业者社区)、公众号
- **共性短板**:信息碎片、社交弱、无 AI 辅导

**L3 — AI 职业辅导(我们的"正面"竞品)**:
- 简历智能工具:超级简历、Canva 简历、WonderCV
- 模拟面试:InterviewBit AI、Final Round AI(海外)
- 职业规划:Boss 直聘的 AI 助手
- **共性短板**:都只解决单点问题,无"社交 + 辅导 + 虚拟人"整合

**L0 — 已退场竞品**:
- **LinkedIn 领英中国** — 2021-10 关闭 InCareer,2023-08-09 关闭"领英职场",**留下的市场空缺 = 我们的核心机会**

### 1.3 差异化定位

**我们做**:**中国大学生自己的职业领英替代版,以数字虚拟人为产品形态**

核心价值(4 维):
1. **职业身份** — 学校 + 专业 + 届 + 行业 四元身份,基于邮箱 + 学号轻量认证
2. **校友网络** — 同校 / 同院 / 同专业 / 同行业 4 维垂直社交,虚拟学长学姐(经授权)数字分身
3. **AI 求职辅导** — 简历生成 / 改写 / 评分 / 模拟面试(多角色)/ 职业画像 / 行业洞察
4. **开源 + 本地优先** — 数据本地化,沙箱安全,6 LLM 可插拔,无 VPN 需求,合规

目标用户(分层):
| 学段 | 核心需求 | 适合的虚拟人 |
|---|---|---|
| 大一-大二(探索期) | 专业认知 / 兴趣探索 | 职业规划师 / 行业概览助手 / 同专业学长学姐 |
| 大三-大四(求职期) | 校招 / 简历 / 面试 / offer 选择 | 模拟面试官 / 简历 AI / HR 顾问 / 校友内推 |
| 研一-研三(冲刺期) | 实习 / 垂直行业 / 读研 vs 工作 | 行业专家(算法/产品/运营)/ 资深 HR |

### 1.4 不做什么(主动收缩)
- ❌ 不做 3D 高保真数字人(头部厂商重资本,卷不过)
- ❌ 不做真人即时通讯工具(微信 / 脉脉已经做)
- ❌ 不做 BOSS直聘的"求职者直聊 HR"模式(同质化)
- ❌ 不做海外市场(LinkedIn 还在,不冲突)
- ❌ 不做 NSFW(政策风险)
- ❌ 不做硬件外设
- ✅ 专注 **2D 数字虚拟人 + 强 LLM + 强记忆 + 校友社交 + AI 求职辅导**

---

## 2. 调研清单(每个词至少 30 篇 arxiv)

### 2.1 市场产品(覆盖维度,Cycle 10.5 修正)

| 类别 | 关键词 | 目标数量 | 当前 |
|---|---|---|---|
| **招聘工具(主竞品)** | BOSS直聘, 智联, 前程无忧, 应届生求职网, 24365 平台 | 5+ 详细 | 0/5 |
| **LinkedIn 退出分析** | 领英职场 2023-08-09 停服、Microsoft 调整、中国本地化挑战 | 1 详细 | 1/1 ✅ |
| **大学生需求画像** | 简历 / 模拟面试 / 职业画像 / 校友 / 行业洞察 | 1 综合 | 1/1 ✅ |
| **国产职业内容平台** | 小红书求职、知乎行业、即刻、脉脉 | 4+ | 0/4 |
| **AI 求职工具** | 超级简历、InterviewBit AI、WonderCV | 3+ | 0/3 |
| 角色扮演型虚拟人 | Character.AI, Replika, Janitor AI, Crushon.AI, Talkie | 5+ 详细 | 2/5 |
| 国产数字人厂商 | 百度曦灵, 商汤如影, 阿里数字人, 字节豆包, 讯飞, 小冰, 聆心 Emohaa | 7+ 详细 | 1/7 |
| 数字人/IP | HeyGen, Synthesia, D-ID, Soul Machines, MiniMax | 5+ | 0/5 |
| 通用 chat LLM | ChatGPT, Claude, Gemini, 文心, 通义, Kimi, DeepSeek, 智谱, 豆包, 混元, 讯飞, 百川 | 12 核心 | 0/12 |
| 评测体系 | LMSYS, AlpacaEval, MT-Bench, WildBench, LiveBench, OpenCompass | 6+ | 0/6 |

### 2.2 arxiv 关键词(每词 ≥ 30 篇,持续累加;**Cycle 10.5 新增职业/求职方向**)

**虚拟人专属**:
1. `digital human` ✅ 6 篇
2. `virtual human`
3. `avatar` — 2D / 3D 形象
4. `speech synthesis` — TTS
5. `lip sync` — 嘴型同步
6. `talking head` — 说话头像
7. `facial animation` — 表情动画
8. `text to video` — 数字人视频生成
9. `character ai`
10. `companion ai`

**核心 LLM**:
11. `large language model` ✅ 8 篇
12. `instruction tuning` ✅ 5 篇
13. `RLHF` — 人类反馈强化学习
14. `prompt engineering` — 提示工程
15. `chain of thought` — 思维链
16. `RAG` — 检索增强生成
17. `agent` — LLM 智能体
18. `multimodal` — 多模态
19. `long context` — 长上下文
20. `long term memory` — 长期记忆

**国产模型**:
21. `DeepSeek`
22. `Qwen` — 通义千问
23. `GLM` — 智谱
24. `Moonshot Kimi`

**评测/对齐**:
25. `LLM evaluation` — 评测
26. `alignment` — 对齐
27. `hallucination` — 幻觉
28. `safety` — 安全

**架构/训练**:
29. `Mixture of Experts` — MoE
30. `quantization` — 量化
31. `transformer` — 基础架构
32. `pre-training` — 预训练

**🆕 职业/求职方向(Cycle 10.5 新增)**:
33. `resume parsing` — 简历解析
34. `job recommendation` — 职位推荐
35. `career counseling` — 职业咨询 / 辅导
36. `Holland career interest` — 霍兰德职业兴趣测试
37. `mock interview` — 模拟面试(LLM-based)
38. `STAR method` — STAR 法则(NLP 视角)
39. `person job fit` — 人岗匹配
40. `mentor matching` — 校友/导师匹配
41. `job interview analysis` — 面试分析
42. `talent assessment` — 人才评估

**目标**:每词 ≥ 30 篇,持续到毕业。当前进度:2/42 词已有论文。

---

## 3. 开发方案(产品路线图)

> **Cycle 10.5 重定位**:路线图对齐到"中国大学生职业领英替代 + 数字虚拟人"。

### 3.1 v0.1 MVP(cycle 1-5):文本虚拟人基础 ✅ 已完成
- ✅ `scripts/aichat.py` — CLI 入口(对话 REPL)
- ✅ `scripts/llm_client.py` — 6 provider 统一客户端(mock 模式)
- ✅ `scripts/persona.py` — 虚拟人定义(性格/记忆/系统提示)
- ✅ `scripts/memory.py` — 长期记忆(episodic + semantic, RAG 检索)
- ✅ `scripts/tts.py` — 接入 TTS(ChatTTS / Edge TTS / ElevenLabs)

### 3.2 v0.2(cycle 6-10):形象虚拟人 + 分析层 ✅ 已完成
- ✅ `scripts/avatar_video.py` — 2D Live 形象驱动(SadTalker / Live2D / EMO)
- ✅ `scripts/scoring.py` — 5 维自动评分
- ✅ `scripts/cost.py` — 成本追踪
- ✅ `scripts/analytics.py` — 漏斗/留存/Cohort
- ✅ `scripts/web.py` — 零依赖 HTTP 后端(11 endpoints)

### 3.3 v0.3(cycle 11-15):**职业辅导核心模块** ⬅️ **新方向重点**
- ⬜ `scripts/resume.py` — 简历生成 / 改写 / 评分(STAR 法则 + 量化)
- ⬜ `scripts/interview.py` — 模拟面试官(技术 / 行为 / HR / 压力面)
- ⬜ `scripts/career_profile.py` — 霍兰德职业兴趣测试 + 6 维画像
- ⬜ `scripts/industry_insight.py` — 行业专家对话(算法/产品/运营/设计/金融)
- ⬜ `scripts/alumni.py` — 校友匹配(同校 / 同院 / 同专业 / 同行业)

### 3.4 v0.4(cycle 16-20):数字虚拟人 + 校友社交
- `scripts/digital_human.py` — 2D Live 虚拟人(学长学姐 / 行业专家 / HR)
- 嘴型同步、表情动作
- 校友关系图谱 + 内推助手

### 3.5 v0.5(cycle 21-25):Web + 移动端
- Web 前端(原生 HTML + JS,虚拟人形象 + 对话气泡 + TTS 播放)
- 校友 feed + 行业洞察流
- persona JSON 分享(可导出)

### 3.6 v0.6(cycle 26-30):论文对话 + 学术模式
- arxiv 论文对话模式(用户上传 PDF,虚拟人基于论文回答)
- 引用追溯
- prompt 模板库(简历 / 面试 / 职业规划 / 行业分析)

### 3.7 v1.0(cycle 31+):发布
- benchmark 报告(简历评分 / 模拟面试 / 职业画像)
- README + 文档 + Demo 视频
- v1.0 release tag
- 开源发布 + 投论文(NeurIPS / EMNLP / CHI)

---

## 4. 三阶段协议(每轮 15 min)

### 阶段 1:调研(约 5-6 min)
- **arXiv**:从 §2.2 选 1-2 个关键词下载(`<keyword>` 累加未达 30 篇的优先)
- 存 `papers/<keyword>/arxiv_<id>.json` + `<id>.pdf` + `<id>.txt`
- **市场产品**:补充 1-2 个新数据点到 `research/market/<category>.md`
- **用户评价**:摘录 1-2 条到 `research/user_feedback/<product>.md`

### 阶段 2:实践(约 5-6 min)
- 根据当前 cycle 目标,实现 1 个模块/切片
- 代码写进 `scripts/` 或新文件
- 必须可读、可 import、无语法错
- 单脚本自测 OK

### 阶段 3:测试(约 3-4 min)
- 下载/生成小数据集
- 写 `tests/test_<N>.py`,跑测试
- 验证:HTTP 200 / 语法正确 / 输出符合预期
- 失败要修,直到通过

### 重要纪律
- 3 阶段都动,**不跳过**
- 每轮写明 loop 计数到 `progress.md` 和 `plan.md` 的 `[CYCLE_N_DONE]`
- 任一阶段完全无产出,本轮记为 `WEAK`,自我分析

---

## 5. 循环记录表

| Cycle | 日期 | 调研 | 实践 | 测试 | 状态 |
|---|---|---|---|---|---|
| 0 | 2026-07-21 | 主题+方案 | MASTER_PLAN | 框架 | DONE |
| 1 | 2026-07-21 | 3 市场调研(Character.AI/Replika/国产)+ arxiv 19篇(LLM 8+InsTune 5+数字人 6) | aichat.py + llm_client.py + persona.py | test_1.py 7/7 + bonus ✓ | DONE |
| 2 | 2026-07-21 | 7平台横评+星野分析+arxiv 15篇(3关键词:vh/avatar/th) | memory.py 长期记忆(episodic+semantic+RAG) | test_2_memory.py 13/13 ✓ | DONE |
| 3 | 2026-07-21 | CrushOn.AI深度+arxiv 1篇(CoT 限流) | relationship.py 4阶段(陌生人→亲密) | test_3_relationship.py 17/17 ✓ | DONE |
| 4 | 2026-07-21 | 国内AI生态(智谱/Glow/X Eva)+arxiv 3篇(hallucination) | scene.py 7场景类型+议程+好感事件 | test_4_scene.py 17/17 ✓ | DONE |
| 5 | 2026-07-21 | HeyGen ARR 3500万 + 12款产品对比(arxiv 0篇限流) | tts.py 抽象层(3 provider) | test_5_tts.py 20/20 ✓ | DONE |
| 6 | 2026-07-21 | 7个开源项目对比(Wav2Lip/SadTalker/MuseTalk等)+arxiv 3篇(transformer) | avatar_video.py 嘴型同步抽象(4 provider) | test_6_avatar_video.py 21/21 ✓ | DONE |
| 7 | 2026-07-21 | NextChat 81.2K+LobeChat+8个客户端+arxiv 3篇(pre_training) | web.py 零依赖HTTP后端(8 endpoints) | test_7_web.py 21/21 ✓ | DONE |
| 8 | 2026-07-21 | 5大评测体系(MMLU/MT-Bench/AlpacaEval/LiveBench)+arxiv 3篇(llm_evaluation) | scoring.py 5维自动评分(零LLM依赖) | test_8_scoring.py 27/27 ✓ | DONE |
| 9 | 2026-07-21 | AlignBench 683样本+FLASK+BERTScore+arxiv 3篇(reasoning) | cost.py 成本追踪(7 provider) | test_9_cost.py 23/23 ✓ | DONE |
| 10 | 2026-07-21 | 漏斗/留存/Cohort 体系(arxiv 0篇限流) | analytics.py 6 大分析功能 | test_10_analytics.py 20/20 ✓ | DONE |
| 11 | (cron 推进) | | | | |
| ... | | | | | |

完成标准:**[CYCLE_N_DONE] × 25+** 或 **v1.0 发布**。

---

## 6. 关键纪律(从 CoPiano v3.0 学到的)

1. **每个 cycle 预算 12 min 工作 + 3 min logging**
2. **不要用 `write` 改大文件** — 用 `edit` 追加
3. **每 cycle 1 个聚焦特性**,不堆叠
4. **测试 100% 通过** 是硬约束
5. **不要在 1 cycle 内做多件事** — 失去焦点
6. **bug 修复时间 ≤ 3 个/cycle**,否则要 pause
7. **5-7 cycle 后达 80% 完成度**,10 cycle 后应进入 polish/docs/release
8. **看 plan.md 的 `[CYCLE_N_DONE]` 决定下一步**,不要 micromanage

---

## 7. 跨项目参考

- CoPiano v3.0 经验:`/Users/yuefeng/.mavis/agents/mavis/memory/MEMORY.md` 多个 entry
- v6-loop 协议:`/Users/yuefeng/.mavis/agents/mavis/workspace/v6-loop/`
- arxiv 工具:复用 `v6-loop/scripts/` 里的 downloader
- 论文格式:arxiv JSON metadata + PDF + plain text 三件套

---

**最后更新**:2026-07-21(cycle 10.5 完成,主题重定位为"中国大学生职业领英替代 + 数字虚拟人")
**下次必读**:`plan.md` 找最后一个 `[CYCLE_N_DONE]`,决定 cycle N+1 目标
