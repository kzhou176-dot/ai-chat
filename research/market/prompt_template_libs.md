# Prompt 模板库 / LLM 应用框架 横评(2024-2026)

> Cycle 18 调研,支撑 `scripts/prompt_templates.py` 设计
> 用途:为大学生虚拟人功能提供"模块化 prompt 复用"基础

---

## 1. 行业现状

### Prompt 工程问题
- 多数 LLM 应用把 prompt 写在代码里("魔法字符串")
- 改 prompt 要改代码、重新部署
- A/B 测试 prompt 困难
- 跨项目复用难

### 解决方案:Prompt 模板库
- 把 prompt 抽成模板
- 参数化(`{user_name}` / `{target_position}`)
- 分类管理(对话/总结/分类/提取)
- 版本化

---

## 2. 主流方案对比

| 工具 | 模式 | 模板数 | 集成 | 适合 |
|---|---|---|---|---|
| **LangChain PromptTemplate** | 字符串模板 | 无数 | Python 库 | 中大型 LLM 应用 |
| **LlamaIndex Prompts** | Prompt 类 | 数十个 | Python 库 | RAG 应用 |
| **DSPy** | 自动优化 | 动态 | Python 库 | 研究 / 自动调优 |
| **PromptLayer** | SaaS 管理 | 云端 | Web | 团队协作 |
| **OpenAI Cookbook** | 开源示例 | 100+ | GitHub | 学习参考 |
| **Anthropic Prompt Library** | 官方 | 50+ | Web | 通用对话 |
| **自建 JSON/YAML** | 简单 | 自定 | 任何 | 小型项目 |

---

## 3. 现有 aichat-hub Prompt 散落情况

### cycle 1 — Persona
- 3 个内置虚拟人系统 Prompt(在 `persona.py`)
- 性格化回复 Prompt

### cycle 11 — Resume
- 3 个角色系统 Prompt(`mentor` / `hr` / `senior`)
- 弱动词替换模板 / 量化 TODO 模板

### cycle 12 — Interview
- 4 个面试官风格描述(`INTERVIEWER_PROFILES`)
- 32 道题的"关键要点"模板
- 角色化反馈模板

### cycle 13 — Career Profile
- 1 个职业规划师 Prompt
- 25 种 Holland Code 解读模板

### cycle 14 — Industry Insight
- 9 个行业专家系统 Prompt(`INDUSTRY_PROFILES`)
- 182 道 FAQ 题目
- 行业问答 fallback 模板

### cycle 15 — Alumni
- 4 个虚拟学长学姐 Prompt(`SENIOR_PROMPTS`)
- 校友 bio 模板

### cycle 16 — Digital Human
- 8 个虚拟人系统 Prompt(`PRESET_HUMANS`)
- 表情自动检测关键词

### cycle 17 — Feed
- 4 类 Feed(无 prompt,但有个性化推荐公式)

### 散落问题
- Prompt 分散在 8 个文件中
- 改一处要改多文件
- 难以"加载某个角色所有 prompt"使用
- 缺少分类 / 标签 / 关键词检索

---

## 4. AIchat-Hub `scripts/prompt_templates.py` 设计要点

### 4.1 模板库
- 集中存储 30+ Prompt 模板
- 分类:resume / interview / career / industry / alumni / digital_human / feed
- 标签:role / category / scenario

### 4.2 数据模型
- `PromptTemplate`(id / category / role / name / content / variables / tags / version)
- `PromptLibrary`(class 装载所有模板 + CRUD + 检索)

### 4.3 核心 API
- `get_template(id)` — 获取单模板
- `list_templates(category=, role=, tag=)` — 筛选
- `render_template(id, variables)` — 渲染(替换变量)
- `add_template(...)` — 动态添加
- `search_by_keyword(kw)` — 关键词检索

### 4.4 模板分类
- **resume** 4 模板:mentor / hr / senior / 通用改写
- **interview** 5 模板:tech / behavioral / hr / pressure / 反馈生成
- **career** 3 模板:guide / 解读 / 推荐
- **industry** 10 模板:9 行业 + 通用问答
- **alumni** 5 模板:4 学长学姐 + bio
- **digital_human** 9 模板:8 角色 + 表情检测
- **feed** 1 模板:feed 描述生成

### 4.5 变量替换
- 模板支持 `{user_name}` / `{target_position}` 等占位符
- `render_template(id, {"user_name": "小王", ...})` 返回渲染后文本

### 4.6 沙箱安全
- 纯静态模板库
- 变量替换用 `str.format_map` 或简单 replace
- 不依赖 LLM

---

## 5. 数据结构

```python
@dataclass
class PromptTemplate:
    id: str                    # "resume_mentor"
    category: str              # "resume"
    role: str                  # "mentor"
    name: str                  # "简历导师"
    content: str               # "你是一位..."
    variables: List[str]       # ["user_name", "target_position"]
    tags: List[str] = []       # ["中文", "改写", "STAR"]
    version: str = "1.0.0"
    created_at: float = ...
```

---

## 6. 数据来源

- LangChain PromptTemplate 文档
- OpenAI Cookbook GitHub
- Anthropic Prompt Library
- aichat-hub cycle 1-17 已有 Prompt 散落

---

**[CYCLE_18_DONE]** — Cycle 18 调研完成:`scripts/prompt_templates.py` 设计就绪
