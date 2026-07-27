# ArXiv 论文管理工具横评(2024-2026)

> Cycle 21 调研,支撑 `scripts/papers.py` 设计
> 用途:为 v0.6 论文对话 + 学术模式提供论文管理基础

---

## 1. 论文管理痛点

### 痛点 1:文件散落
- 50+ 论文 PDF/JSON 散落在 papers/ 多个子目录
- 找不到某篇论文 / 不知道在哪个 keyword 下
- 重复下载(没去重)

### 痛点 2:引用格式混乱
- 论文用于不同场景:APA / IEEE / BibTeX / 自然语言
- 不同格式需要不同模板,人工转换繁琐
- 容易出错(作者顺序 / 年份 / 期刊)

### 痛点 3:摘要/全文检索
- 50+ 论文需要快速找相关主题
- 文件名/标题检索不够,需要看摘要/全文
- 关键词/主题分类很重要

### 痛点 4:对比/汇总
- 同一关键词下多篇论文,需要看哪篇最新/最相关
- 实验结果对比、相关工作梳理
- 自动化工具可减少重复劳动

---

## 2. 主流方案对比

| 工具 | 模式 | 适合 | 集成 |
|---|---|---|---|
| **Zotero** | 桌面应用 | 学术研究 | 桌面 |
| **Mendeley** | 云端 | 学术研究 | Web |
| **arXiv API** | 数据源 | 原始数据 | 任意 |
| **Connected Papers** | 关系图 | 找相关工作 | Web |
| **Semantic Scholar** | 学术搜索 | 找论文 | Web API |
| **自建 JSON/SQLite** | 简单 | 小型项目 | Python |

我们选**自建 JSON + 摘要/标题关键词**:
- 项目已 50+ 论文 JSON 散落
- 沙箱无外部 API
- Python 标准库足够

---

## 3. AIchat-Hub `scripts/papers.py` 设计要点

### 3.1 论文清单
- 扫描 `papers/` 目录,索引所有 JSON 文件
- 提取:arxiv_id / title / authors / abstract / year / categories / keyword
- 去重(同一 arxiv_id 可能在多个 keyword 下)

### 3.2 检索
- 按 arxiv_id 精确查找
- 按 title 模糊匹配
- 按 author 匹配
- 按 category / keyword 分类
- 按 abstract 关键词搜索

### 3.3 引用格式
- **APA**:"Author, A. (Year). Title. arXiv:xxx."
- **IEEE**:"A. Author, 'Title,' arXiv:xxx, Year."
- **BibTeX**:@article{...}
- **自然语言**:"作者(年份)发现..."

### 3.4 统计
- 总论文数 / 各 keyword 数 / 各年份数
- 关键词云(高频词)
- 作者分布

### 3.5 沙箱安全
- 纯文件系统操作
- 无外部 API
- 无 LLM

---

## 4. 数据结构

```python
@dataclass
class Paper:
    arxiv_id: str       # "2607.18081"
    title: str
    authors: List[str]
    abstract: str
    year: int
    categories: List[str]
    keyword: str
    pdf_path: str = ""  # papers/pdfs/<id>.pdf
    parsed_path: str = ""  # papers/parsed/<id>.txt
    url: str = f"https://arxiv.org/abs/{arxiv_id}"
```

---

## 5. 引用格式示例

### APA
> Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł., & Polosukhin, I. (2017). Attention is all you need. arXiv:1706.03762.

### IEEE
> A. Vaswani et al., "Attention is all you need," arXiv:1706.03762, 2017.

### BibTeX
```bibtex
@article{vaswani2017attention,
  title={Attention is all you need},
  author={Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and ...},
  year={2017},
  journal={arXiv preprint arXiv:1706.03762}
}
```

---

## 6. 数据来源

- arXiv API 文档
- 现有 `papers/` 目录(50+ 论文)
- BibTeX 格式规范
- APA / IEEE 引用规范

---

**[CYCLE_21_DONE]** — Cycle 21 调研完成:`scripts/papers.py` 设计就绪
