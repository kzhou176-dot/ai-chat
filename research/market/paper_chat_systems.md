# 论文对话 / 学术模式 系统横评(2024-2026)

> Cycle 22 调研,支撑 `scripts/paper_chat.py` 设计
> 用途:为 AIchat-Hub v0.6 论文对话 + 学术模式提供设计基础

---

## 1. 现有"论文对话"产品

| 产品 | 模式 | 适合 | 集成 |
|---|---|---|---|
| **ChatPDF** | PDF 上传 → 对话 | 单篇论文问答 | SaaS |
| **Elicit** | 文献综述 + 抽取 | 学术研究 | SaaS |
| **Consensus** | 论文搜索 + 答案 | 找证据 | SaaS |
| **SciSpace** | 多论文 + 引用 | 研究助手 | SaaS |
| **Connected Papers** | 关系图 | 找相关 | SaaS |
| **自建关键词检索** | 简单 | 小项目 | Python |

我们选**自建关键词检索 + 模板回答**:
- 已索引 50+ 论文(cycle 21)
- 沙箱无 LLM 依赖
- 模板化回答,自动加引用

---

## 2. 大学生论文对话需求

### 需求 1:作业 / 报告辅助
- "推荐几篇关于 LLM 的论文"
- "对比 Transformer 和 RNN 的核心创新"
- "什么是 RLHF?有什么经典论文?"

### 需求 2:研究入门
- "我想做 RAG,推荐 3 篇入门论文"
- "多模态方向最近有什么热点?"
- "霍兰德职业测试有什么理论依据?"

### 需求 3:引用规范
- 自动生成 APA / IEEE / BibTeX 引用(已有 cycle 21)
- 回答中嵌入引用链接

---

## 3. AIchat-Hub `scripts/paper_chat.py` 设计要点

### 3.1 论文对话系统
- **多轮对话 session**(类似 cycle 12 interview)
- **检索增强**:
  - 从 50+ 论文(cycle 21)检索相关
  - 关键词匹配 + 摘要相似度
- **回答模板**:
  - 模板 1:列出相关论文(直接列表)
  - 模板 2:对比分析(2-3 篇)
  - 模板 3:核心观点(单篇深入)
  - 模板 4:研究路径(推荐入门 → 进阶)
- **自动引用**:回答末尾自动加 APA 引用

### 3.2 数据模型
- `PaperChatSession`(id/user_id/topic/messages)
- `ChatMessage`(role/user/assistant/content/citations)

### 3.3 核心 API
- `start_chat(user_id, topic)` — 开 session
- `ask(session, question)` — 提问,返回回答 + 引用
- `end_chat(session)` — 结束

### 3.4 沙箱安全
- 检索基于 cycle 21 papers.py(无 LLM)
- 回答用模板(无 LLM)
- 引用自动生成(cycle 21 format_citation)

---

## 4. 回答模板(4 种)

### 模板 1:相关论文列表
> "关于 {topic},推荐以下论文:
> 1. {paper1.title} ({paper1.year}) - {paper1.abstract[:80]}... [1]
> 2. {paper2.title} ({paper2.year}) - {paper2.abstract[:80]}... [2]
> ..."

### 模板 2:对比分析
> "{paper1.title} vs {paper2.title}:
> - 共同点:...
> - 不同点:...
> - 推荐场景:..."

### 模板 3:核心观点
> "{paper.title}({paper.authors[0]} et al., {paper.year})发现:
> {paper.abstract[:200]}... [1]"

### 模板 4:研究路径
> "学习 {topic},建议按以下路径:
> 1. 入门:{paper1.title} - {paper1.abstract[:60]}... [1]
> 2. 进阶:{paper2.title} - {paper2.abstract[:60]}... [2]
> 3. 前沿:{paper3.title} - {paper3.abstract[:60]}... [3]"

---

## 5. 数据结构

```python
@dataclass
class ChatMessage:
    role: str             # "user" / "assistant"
    content: str
    citations: List[str] = field(default_factory=list)  # 引用 arxiv_id 列表
    timestamp: float = field(default_factory=time.time)

@dataclass
class PaperChatSession:
    id: str
    user_id: str
    topic: str = ""
    messages: List[ChatMessage] = field(default_factory=list)
```

---

## 6. 数据来源

- ChatPDF / Elicit / Consensus 官网
- "How to build a RAG chatbot" 技术博客
- 50+ 论文(papers/ 目录)
- cycle 21 论文管理

---

**[CYCLE_22_DONE]** — Cycle 22 调研完成:`scripts/paper_chat.py` 设计就绪
