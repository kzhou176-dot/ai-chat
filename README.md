# AIchat-Hub

> **中国大学生职业社交平台 + 数字虚拟人框架**
> *以大学生群体为客户,以数字虚拟人为产品形态,LinkedIn 中国大陆的替代版本*

[![Tests](https://img.shields.io/badge/tests-537%20passed-brightgreen)]()
[![Python](https://img.shields.io/badge/python-3.8%2B-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Sandbox](https://img.shields.io/badge/sandbox-friendly-blue)]()

## 🎯 项目定位

**AIchat-Hub** = **中国大学生职业社交平台 + 数字虚拟人框架**

- **目标用户**:中国大陆本科/研究生(大一-大四 + 研一-研三 + 应届毕业生)
- **产品形态**:数字虚拟人(2D Live + TTS) + Web + 移动端
- **市场机会**:领英(LinkedIn)中国 2023-08-09 停服留下市场空缺 + 国产招聘工具无社交属性
- **差异化**:**校友关系 + 职业内容 + AI 求职辅导** 三件套,数字虚拟人作为产品形态

## ✨ 核心能力

### 🏠 基础能力(cycle 1-10)
- **多 LLM 客户端**:6+ 国产 + 海外 OpenAI 兼容 provider(OpenAI/DeepSeek/智谱/通义/Kimi/Anthropic)
- **虚拟人系统**:性格/记忆/系统 Prompt + 3 个内置虚拟人(小爱/李医生/小智)
- **长期记忆**:episodic + semantic + RAG 检索
- **关系阶段**:陌生人 → 熟人 → 朋友 → 亲密(4 阶段)
- **场景系统**:7 种场景类型 + 议程 + 好感度事件
- **TTS 抽象**:3 provider(ChatTTS / Edge TTS / ElevenLabs)
- **2D Live 虚拟形象**:4 provider(Wav2Lip / SadTalker / MuseTalk / Mock)
- **5 维自动评分**:长度/格式/相关性/多样性/响应时间
- **成本追踪**:7 provider 累计 + 分类
- **用户分析**:漏斗/留存/Cohort

### 🎓 职业辅导(v0.3 cycle 11-15,5/5 完成)
- **📝 简历生成/改写/评分**:3 角色虚拟人(导师/HR/学长)+ 5 维评分(完整性/量化/STAR/关键词/格式)
- **💼 模拟面试官**:4 角色(技术/行为/HR/压力)+ 32 道题 + 5 维评分 + 复盘
- **🧭 霍兰德职业兴趣测试**:RIASEC 6 维 + 60 题 + 25 种 Holland Code 解读 + 岗位匹配
- **🏢 行业洞察对话**:9 大行业专家(算法/产品/运营/设计/数据/金融/咨询/快消/地产)+ 182 FAQ
- **🎓 校友匹配 + 内推**:30 校友 + 4 维匹配(校 0.4/院 0.3/业 0.2/城 0.1) + 7 状态内推状态机

### 🤖 数字虚拟人 + Feed(v0.4 cycle 16-18,3/3 进行中)
- **🎭 数字虚拟人**:6 表情/6 动作/5 状态/4 风格 + 8 预设角色(跨 5 模块) + 自动检测表情
- **📰 Feed 时间线**:4 类 Feed(校友/行业/求职/校招)+ 30+ 静态内容 + 个性化推荐(5 因子)
- **🧩 Prompt 模板库**:8 类别 32 模板(覆盖 cycle 1-17)+ 变量替换 + 搜索评分

## 📊 累计统计

| 指标 | 数量 |
|---|---|
| **Cycles 完成** | 19 / 25+ |
| **Scripts 模块** | 20 |
| **Test 文件** | 19 |
| **Tests 通过** | **537 (100%)** |
| **Web Endpoints** | **55** |
| **LLM Providers** | 6 |
| **虚拟人角色** | 8 预设 + 3 基础 |
| **行业专家** | 9 |
| **校友档案** | 30 |
| **Feed 静态** | 30+ |
| **Prompt 模板** | 32 |
| **市场调研文档** | 17 |

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Web 客户端(零依赖)                         │
│         HTML/JS/CSS(原生,无构建,无打包,移动端响应式)         │
└─────────────────────────────────────────────────────────────┘
                              ↕ HTTP
┌─────────────────────────────────────────────────────────────┐
│                  Web 后端 (scripts/web.py)                   │
│         55 个 REST endpoint + JSON 请求/响应                  │
│         http.server(标准库) + 内存 session 存储               │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                  职业辅导模块 (v0.3 5/5)                      │
│  resume → interview → career_profile → industry → alumni     │
│  (改简历)  (模拟面试)  (霍兰德测试)   (行业专家)  (校友内推)  │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                  数字虚拟人 + Feed (v0.4 3/3)                 │
│         digital_human + feed + prompt_templates               │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                  基础能力层 (cycle 1-10)                      │
│  persona + memory + relationship + scene + llm_client        │
│  + tts + avatar_video + scoring + cost + analytics           │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速开始

### 安装(零依赖)

```bash
# 纯标准库,Python 3.8+
git clone <repo>
cd aichat-hub
# 不需要 pip install
```

### 运行 Web 后端

```bash
cd scripts
python3 web.py
# 服务运行在 http://127.0.0.1:8765
```

### 调用 API

```bash
# 获取根信息
curl http://127.0.0.1:8765/

# 列虚拟人
curl http://127.0.0.1:8765/api/personas

# 改简历
curl -X POST http://127.0.0.1:8765/api/resume/rewrite \
  -H "Content-Type: application/json" \
  -d '{"profile": {...}, "persona": "mentor"}'

# 模拟面试
curl -X POST http://127.0.0.1:8765/api/interview/start \
  -H "Content-Type: application/json" \
  -d '{"interviewer": "tech", "rounds": 3}'

# 霍兰德测试
curl -X POST http://127.0.0.1:8765/api/career/start \
  -H "Content-Type: application/json" \
  -d '{"target_position": "算法工程师"}'

# 行业洞察
curl -X POST http://127.0.0.1:8765/api/industry/ask \
  -H "Content-Type: application/json" \
  -d '{"industry": "algorithm", "question": "真实一天是什么?"}'

# 校友匹配
curl -X POST http://127.0.0.1:8765/api/alumni/match \
  -H "Content-Type: application/json" \
  -d '{"school": "清华大学", "target_industry": "互联网"}'

# Feed 推荐
curl -X POST http://127.0.0.1:8765/api/feed/recommend \
  -H "Content-Type: application/json" \
  -d '{"holland_code": "IAS", "user_school": "清华大学"}'

# 数字虚拟人
curl http://127.0.0.1:8765/api/human/presets
curl -X POST http://127.0.0.1:8765/api/human/create \
  -H "Content-Type: application/json" \
  -d '{"preset_id": "xiaoai"}'

# Prompt 模板
curl http://127.0.0.1:8765/api/prompt/list?category=resume
curl -X POST http://127.0.0.1:8765/api/prompt/render \
  -H "Content-Type: application/json" \
  -d '{"template_id": "resume_mentor", "variables": {"user_name": "小王", "target_position": "算法工程师"}}'
```

### 运行测试

```bash
cd tests
for f in test_*.py; do python3 "$f"; done
# 所有测试 100% 通过
```

## 🛠️ 技术栈

- **后端**:Python 3.8+(标准库 only)— http.server / urllib / json
- **LLM**:6 provider OpenAI 兼容(零客户端包)
- **存储**:内存 + JSON 文件(沙箱友好)
- **前端**:原生 HTML + JS(无构建/无框架,直接打开 HTML 即可)
- **测试**:unittest 风格,每个 test 独立命名空间

## 🎯 三大设计原则

### 1. 沙箱安全
- **零外部依赖**:不 pip install 任何包
- **纯标准库**:Python 标准库足够
- **Mock 优先**:所有 provider(LLM/TTS/Avatar)都有 mock fallback
- **静态池**:校友/行业/Feed 都是静态数据,无需数据库
- **规则化**:评分/匹配/推荐都用规则,不依赖 LLM

### 2. 零 LLM 依赖
- 所有对话/评分/匹配/推荐都可以**纯规则**完成
- LLM 是可选加成,有 key 时接通,无 key 时 mock
- 测试只验 mock 路径,沙箱环境永远能跑

### 3. 模块化复用
- 19 个独立模块,每个 200-700 行
- 跨模块复用(Persona → Industry → Interview → Career → Alumni → Digital Human)
- 统一数据模型 + 角色 + Prompt
- 8 类别 32 模板集中管理

## 📁 目录结构

```
aichat-hub/
├── README.md                # 本文件
├── CHANGELOG.md             # 变更日志
├── LICENSE                  # MIT 协议
├── MASTER_PLAN.md           # 总方案(主题/调研/开发/协议)
├── plan.md                  # 循环 markers
├── progress.md              # 详细历史
├── research/                # 调研
│   ├── market/              # 17 篇市场调研
│   ├── user_feedback/       # 用户评价
│   └── arxiv/               # arxiv 论文
├── papers/                  # 50+ arxiv 论文
├── scripts/                 # 20 个核心模块
│   ├── aichat.py
│   ├── llm_client.py
│   ├── persona.py
│   ├── memory.py
│   ├── relationship.py
│   ├── scene.py
│   ├── tts.py
│   ├── avatar_video.py
│   ├── web.py
│   ├── scoring.py
│   ├── cost.py
│   ├── analytics.py
│   ├── resume.py
│   ├── interview.py
│   ├── career_profile.py
│   ├── industry_insight.py
│   ├── alumni.py
│   ├── digital_human.py
│   ├── feed.py
│   ├── prompt_templates.py
│   └── dashboard.py
└── tests/                   # 19 个测试文件,537 tests
    ├── test_1.py ~ test_19.py
```

## 🗺️ 路线图

- ✅ **v0.1 MVP**(cycle 1-5):文本虚拟人
- ✅ **v0.2**(cycle 6-10):形象虚拟人 + 分析层
- ✅ **v0.3 职业辅导**(cycle 11-15):5/5 完成
  - ✅ C11 简历 / C12 面试 / C13 霍兰德 / C14 行业 / C15 校友
- ✅ **v0.4 数字虚拟人 + Feed**(cycle 16-18):3/3 完成
  - ✅ C16 数字虚拟人 / C17 Feed / C18 Prompt 模板
- 🔜 **v0.4.1 移动端 / Dashboard**(cycle 19+):发布收尾
- 🔜 **v0.5**(cycle 21-25):校友 feed 流 + 移动端适配
- 🔜 **v0.6**(cycle 26-30):论文对话 + 学术模式
- 🔜 **v1.0**(cycle 31+):发布 + 投论文(NeurIPS / EMNLP / CHI)

## 📝 License

MIT License

## 👥 贡献

本项目通过 15 分钟 1 个 cycle 的 cron 自动推进,3 阶段协议(调研 → 实践 → 测试)。
详见 `MASTER_PLAN.md` 和 `progress.md`。

---

**最后更新**:2026-07-21(cycle 18 完成,537 tests pass,55 endpoints,32 prompt 模板)
