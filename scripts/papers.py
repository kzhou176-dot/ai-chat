#!/usr/bin/env python3
"""
aichat-Hub Papers (论文管理) 模块
================================
arXiv 论文管理 — 索引 / 检索 / 引用 / 统计。

核心能力:
  1. 论文索引(扫描 papers/ 目录,提取元数据)
  2. 检索(精确 / 模糊 / 作者 / 关键词)
  3. 引用格式(APA / IEEE / BibTeX / 自然语言)
  4. 统计(总数 / 各 keyword / 各年份 / 作者分布)
  5. 论文对话基础(后续 v0.6 接入 LLM)

数据结构:
  - Paper(arxiv_id / title / authors / abstract / year / categories / keyword)

沙箱安全:
  - 纯文件系统操作
  - 无外部 API
  - 无 LLM

Cycle 21 — 论文管理(v0.6 论文对话基础)
"""
from __future__ import annotations
import json
import re
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


# ============== 路径 ==============

ROOT = Path(__file__).parent.parent
PAPERS_DIR = ROOT / "papers"


# ============== 数据模型 ==============

@dataclass
class Paper:
    """论文"""
    arxiv_id: str
    title: str
    authors: List[str] = field(default_factory=list)
    abstract: str = ""
    year: int = 0
    categories: List[str] = field(default_factory=list)
    keyword: str = ""        # 来自哪个 keyword 目录
    pdf_path: str = ""
    parsed_path: str = ""
    url: str = ""

    def __post_init__(self):
        if not self.url and self.arxiv_id:
            self.url = f"https://arxiv.org/abs/{self.arxiv_id}"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============== 论文索引 ==============

def _scan_papers_directory() -> List[Paper]:
    """扫描 papers/ 目录,提取所有论文"""
    papers: List[Paper] = []
    if not PAPERS_DIR.exists():
        return papers
    # 跳过非 keyword 目录
    skip_dirs = {"pdfs", "parsed"}
    for keyword_dir in PAPERS_DIR.iterdir():
        if not keyword_dir.is_dir():
            continue
        if keyword_dir.name in skip_dirs:
            continue
        # 论文 JSON 命名可能是 arxiv_*.json 或 *.json(纯 arxiv_id)
        for json_file in list(keyword_dir.glob("arxiv_*.json")) + list(keyword_dir.glob("*.json")):
            if not json_file.name.startswith("arxiv_") and not _is_arxiv_id_filename(json_file.name):
                continue
            paper = _parse_paper_json(json_file, keyword_dir.name)
            if paper:
                papers.append(paper)
    return papers


def _is_arxiv_id_filename(name: str) -> bool:
    """判断文件名是否是 arxiv ID(如 2607.18081.json)"""
    base = name.replace(".json", "")
    # arxiv ID 格式:YYMM.NNNNN(4 位 . 4-5 位)
    return bool(re.match(r"^\d{4}\.\d{4,5}$", base))


def _parse_paper_json(json_path: Path, keyword: str) -> Optional[Paper]:
    """从 JSON 文件解析论文"""
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        arxiv_id = data.get("arxiv_id") or data.get("id") or json_path.stem.replace("arxiv_", "")
        title = data.get("title", "")
        authors = data.get("authors", [])
        if isinstance(authors, str):
            authors = [a.strip() for a in authors.split(",")]
        abstract = data.get("abstract", "")
        # year 推断
        year = data.get("year", 0)
        if not year and arxiv_id:
            # arxiv ID 格式:YYMM.NNNNN(YY = 2 位年份)
            try:
                yy = int(arxiv_id[:2])
                year = 2000 + yy if yy < 80 else 1900 + yy
            except (ValueError, IndexError):
                year = 0
        categories = data.get("categories", [])
        return Paper(
            arxiv_id=arxiv_id,
            title=title,
            authors=authors,
            abstract=abstract,
            year=year,
            categories=categories,
            keyword=keyword,
        )
    except (json.JSONDecodeError, OSError) as e:
        return None


# ============== 论文索引(去重) ==============

_paper_index_cache: Optional[List[Paper]] = None


def _get_paper_index() -> List[Paper]:
    """获取论文索引(缓存)"""
    global _paper_index_cache
    if _paper_index_cache is None:
        _paper_index_cache = _scan_papers_directory()
    return _paper_index_cache


def reset_paper_index():
    """重置索引缓存(测试用)"""
    global _paper_index_cache
    _paper_index_cache = None


# ============== 检索 ==============

def get_paper(arxiv_id: str) -> Optional[Dict[str, Any]]:
    """按 arxiv_id 精确查找"""
    for p in _get_paper_index():
        if p.arxiv_id == arxiv_id:
            return p.to_dict()
    return None


def search_by_title(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """按标题模糊搜索"""
    kw = keyword.lower()
    results = []
    for p in _get_paper_index():
        if kw in p.title.lower():
            results.append(p.to_dict())
        if len(results) >= limit:
            break
    return results


def search_by_author(author: str, limit: int = 10) -> List[Dict[str, Any]]:
    """按作者搜索"""
    au = author.lower()
    results = []
    for p in _get_paper_index():
        if any(au in a.lower() for a in p.authors):
            results.append(p.to_dict())
        if len(results) >= limit:
            break
    return results


def list_by_keyword(keyword: str) -> List[Dict[str, Any]]:
    """按 keyword 列出"""
    return [p.to_dict() for p in _get_paper_index() if p.keyword == keyword]


def list_by_year(year: int) -> List[Dict[str, Any]]:
    """按年份列出"""
    return [p.to_dict() for p in _get_paper_index() if p.year == year]


def search_by_abstract(keyword: str, limit: int = 10) -> List[Dict[str, Any]]:
    """按摘要搜索"""
    kw = keyword.lower()
    results = []
    for p in _get_paper_index():
        if kw in p.abstract.lower():
            results.append(p.to_dict())
        if len(results) >= limit:
            break
    return results


# ============== 引用格式 ==============

def format_apa(paper: Dict[str, Any]) -> str:
    """APA 格式"""
    authors = paper.get("authors", [])
    if not authors:
        authors_str = "Unknown"
    else:
        # APA:Author, A. A.
        apa_authors = []
        for a in authors[:5]:  # APA 最多列 5 作者
            parts = a.split()
            if len(parts) > 1:
                last = parts[-1]
                initials = ". ".join(p[0] for p in parts[:-1]) + "."
                apa_authors.append(f"{last}, {initials}")
            else:
                apa_authors.append(a)
        if len(authors) > 5:
            authors_str = ", ".join(apa_authors) + ", et al."
        else:
            authors_str = ", ".join(apa_authors)
    year = paper.get("year", "n.d.")
    title = paper.get("title", "Untitled")
    arxiv_id = paper.get("arxiv_id", "")
    return f"{authors_str} ({year}). {title}. arXiv:{arxiv_id}."


def format_ieee(paper: Dict[str, Any]) -> str:
    """IEEE 格式"""
    authors = paper.get("authors", [])
    if not authors:
        authors_str = "Unknown"
    else:
        # IEEE:A. B. Author
        ieee_authors = []
        for a in authors[:3]:  # IEEE 最多 3 个
            parts = a.split()
            if len(parts) > 1:
                initials = ". ".join(p[0] for p in parts[:-1]) + "."
                last = parts[-1]
                ieee_authors.append(f"{initials} {last}")
            else:
                ieee_authors.append(a)
        if len(authors) > 3:
            authors_str = ", ".join(ieee_authors) + " et al."
        else:
            authors_str = ", ".join(ieee_authors)
    year = paper.get("year", "n.d.")
    title = paper.get("title", "Untitled")
    arxiv_id = paper.get("arxiv_id", "")
    return f'{authors_str}, "{title}," arXiv:{arxiv_id}, {year}.'


def format_bibtex(paper: Dict[str, Any]) -> str:
    """BibTeX 格式"""
    arxiv_id = paper.get("arxiv_id", "unknown").replace(".", "")
    authors = paper.get("authors", [])
    year = paper.get("year", "")
    title = paper.get("title", "Untitled")
    # 简化 author 列表
    if not authors:
        author_str = "Unknown"
    else:
        author_str = " and ".join(authors)
    return (
        f"@article{{{arxiv_id},\n"
        f"  title     = {{{title}}},\n"
        f"  author    = {{{author_str}}},\n"
        f"  year      = {{{year}}},\n"
        f"  journal   = {{arXiv preprint arXiv:{paper.get('arxiv_id', '')}}},\n"
        f"  url       = {{{paper.get('url', '')}}}\n"
        f"}}"
    )


def format_natural(paper: Dict[str, Any]) -> str:
    """自然语言引用"""
    authors = paper.get("authors", [])
    year = paper.get("year", "")
    title = paper.get("title", "Untitled")
    arxiv_id = paper.get("arxiv_id", "")
    if not authors:
        author_str = "未知作者"
    elif len(authors) == 1:
        author_str = authors[0]
    elif len(authors) == 2:
        author_str = f"{authors[0]} 和 {authors[1]}"
    else:
        author_str = f"{authors[0]} 等"
    return f"{author_str}({year})发表《{title}》(arXiv:{arxiv_id})"


def format_citation(paper: Dict[str, Any], style: str = "apa") -> str:
    """格式引用(支持 4 种风格)"""
    style = style.lower()
    if style == "apa":
        return format_apa(paper)
    elif style == "ieee":
        return format_ieee(paper)
    elif style == "bibtex":
        return format_bibtex(paper)
    elif style in ("natural", "nl"):
        return format_natural(paper)
    else:
        return format_apa(paper)


# ============== 统计 ==============

def get_statistics() -> Dict[str, Any]:
    """统计"""
    papers = _get_paper_index()
    # keyword 分布
    keywords = Counter(p.keyword for p in papers)
    # 年份分布
    years = Counter(p.year for p in papers if p.year > 0)
    # 作者(前 20)
    authors = Counter()
    for p in papers:
        for a in p.authors:
            authors[a] += 1
    return {
        "total_papers": len(papers),
        "by_keyword": dict(keywords.most_common()),
        "by_year": dict(sorted(years.items())),
        "top_authors": dict(authors.most_common(20)),
        "total_unique_authors": len(authors),
    }


def list_keywords() -> List[str]:
    """列出所有 keyword"""
    keywords = sorted(set(p.keyword for p in _get_paper_index() if p.keyword))
    return keywords


# ============== 核心 API ==============

def total_papers() -> int:
    return len(_get_paper_index())


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 papers.py {list|get|search|stats|keywords|cite}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "list":
        n = total_papers()
        print(f"Total: {n} papers")
        for p in _get_paper_index()[:5]:
            print(f"  [{p.keyword}] {p.arxiv_id} - {p.title[:50]}")
    elif cmd == "get":
        if len(sys.argv) < 3:
            print("Usage: ... get <arxiv_id>", file=sys.stderr)
            sys.exit(1)
        paper = get_paper(sys.argv[2])
        print(json.dumps(paper, ensure_ascii=False, indent=2) if paper else "Not found")
    elif cmd == "search":
        kw = sys.argv[2] if len(sys.argv) > 2 else ""
        if not kw:
            print("Usage: ... search <keyword>", file=sys.stderr)
            sys.exit(1)
        results = search_by_title(kw, limit=10)
        print(f"Search '{kw}': {len(results)} results")
        for p in results:
            print(f"  [{p['keyword']}] {p['arxiv_id']} - {p['title'][:60]}")
    elif cmd == "stats":
        stats = get_statistics()
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    elif cmd == "keywords":
        for kw in list_keywords():
            count = sum(1 for p in _get_paper_index() if p.keyword == kw)
            print(f"  {kw}: {count}")
    elif cmd == "cite":
        if len(sys.argv) < 4:
            print("Usage: ... cite <arxiv_id> <style>", file=sys.stderr)
            sys.exit(1)
        paper = get_paper(sys.argv[2])
        if not paper:
            print("Not found")
            sys.exit(1)
        print(format_citation(paper, sys.argv[3]))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
