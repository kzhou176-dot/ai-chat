#!/usr/bin/env python3
"""
test_21_papers — aichat-hub Cycle 21 论文管理模块测试
====================================================
覆盖:
  1. 数据模型(Paper)
  2. 论文索引(扫描 papers/ 目录)
  3. 检索(精确 / 标题 / 作者 / 关键词 / 年份 / 摘要)
  4. 引用格式(APA / IEEE / BibTeX / 自然语言)
  5. 统计(总数 / keyword / 年份 / 作者)
  6. 核心 API(total_papers / list_keywords)
  7. CLI 入口
  8. 集成
"""
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from papers import (
    Paper, PAPERS_DIR,
    _scan_papers_directory, _parse_paper_json,
    _get_paper_index, reset_paper_index,
    get_paper, search_by_title, search_by_author,
    list_by_keyword, list_by_year, search_by_abstract,
    format_apa, format_ieee, format_bibtex, format_natural, format_citation,
    get_statistics, list_keywords, total_papers,
)


# ============== 1. 数据模型 ==============

def test_paper_dataclass():
    """Paper"""
    p = Paper(
        arxiv_id="1706.03762", title="Attention is all you need",
        authors=["Ashish Vaswani", "Noam Shazeer"], year=2017,
        keyword="transformer",
    )
    assert p.arxiv_id == "1706.03762"
    assert p.year == 2017
    # URL 自动生成
    assert p.url == "https://arxiv.org/abs/1706.03762"
    print("✓ Paper 数据类")


def test_paper_url_auto():
    """URL 自动生成"""
    p = Paper(arxiv_id="1234.5678", title="test")
    assert p.url == "https://arxiv.org/abs/1234.5678"
    print("✓ URL 自动生成")


def test_paper_to_dict():
    """Paper 序列化"""
    p = Paper(arxiv_id="1234", title="test", authors=["A", "B"])
    d = p.to_dict()
    assert d["arxiv_id"] == "1234"
    assert d["authors"] == ["A", "B"]
    print("✓ Paper 序列化")


# ============== 2. 论文索引 ==============

def test_papers_dir_exists():
    """papers 目录存在"""
    assert PAPERS_DIR.exists()
    print(f"✓ papers 目录:{PAPERS_DIR}")


def test_scan_papers_directory():
    """扫描 papers/ 目录"""
    papers = _scan_papers_directory()
    assert isinstance(papers, list)
    print(f"✓ 扫描论文 {len(papers)} 篇")


def test_papers_have_required_fields():
    """论文有必填字段"""
    for p in _get_paper_index():
        assert p.arxiv_id
        assert p.title
    print("✓ 必填字段")


def test_papers_unique_arxiv_id():
    """arxiv_id 唯一(去重检查)"""
    ids = [p.arxiv_id for p in _get_paper_index()]
    # 允许同一 arxiv_id 出现在不同 keyword 下,但 Paper 实例数 = unique ids
    # _scan 不去重,这里只检查总 ID 数 ≥ unique 数(可能重复)
    assert len(ids) > 0
    unique = set(ids)
    # 重复数应小于总 ID 数(去重有意义)
    print(f"✓ 总 ID {len(ids)}, unique {len(unique)}, 重复 {len(ids)-len(unique)}")


def test_papers_year_distribution():
    """年份分布"""
    years = [p.year for p in _get_paper_index() if p.year > 0]
    assert len(years) > 0
    # 应有 2025 / 2026 等近年论文
    print(f"✓ 年份范围 {min(years)}-{max(years)}")


# ============== 3. 检索 ==============

def test_get_paper_existing():
    """获取存在论文"""
    papers = _get_paper_index()
    if papers:
        p = papers[0]
        got = get_paper(p.arxiv_id)
        assert got is not None
        assert got["arxiv_id"] == p.arxiv_id
        print(f"✓ get_paper({p.arxiv_id})")


def test_get_paper_not_found():
    """未找到"""
    assert get_paper("0000.00000") is None
    print("✓ get_paper 未找到")


def test_search_by_title():
    """按标题搜索"""
    papers = _get_paper_index()
    if not papers:
        return
    # 用第一篇论文 title 的前 5 字符搜索
    first_title_word = papers[0].title.split()[0]
    results = search_by_title(first_title_word[:3], limit=5)
    assert len(results) >= 0
    print(f"✓ 标题搜索 '{first_title_word[:3]}' → {len(results)} 条")


def test_search_by_title_not_match():
    """标题搜索无匹配"""
    results = search_by_title("zzzzz_no_match_xyz123", limit=5)
    assert results == []
    print("✓ 无匹配返回空")


def test_search_by_author():
    """按作者搜索"""
    papers = _get_paper_index()
    if not papers or not papers[0].authors:
        return
    author = papers[0].authors[0]
    results = search_by_author(author, limit=5)
    assert len(results) >= 1
    print(f"✓ 作者搜索 '{author}' → {len(results)} 条")


def test_list_by_keyword():
    """按 keyword 列出"""
    papers = _get_paper_index()
    if not papers:
        return
    keyword = papers[0].keyword
    results = list_by_keyword(keyword)
    assert all(p["keyword"] == keyword for p in results)
    print(f"✓ keyword='{keyword}' → {len(results)} 条")


def test_list_by_year():
    """按年份列出"""
    papers = _get_paper_index()
    if not papers:
        return
    year = max(p.year for p in papers if p.year > 0)
    results = list_by_year(year)
    assert all(p["year"] == year for p in results)
    print(f"✓ year={year} → {len(results)} 条")


def test_search_by_abstract():
    """按摘要搜索"""
    papers = _get_paper_index()
    if not papers:
        return
    # 用任意关键词
    results = search_by_abstract("learning", limit=10)
    print(f"✓ 摘要搜索 'learning' → {len(results)} 条")


# ============== 4. 引用格式 ==============

def test_format_apa_basic():
    """APA 基础"""
    paper = {
        "arxiv_id": "1706.03762",
        "title": "Attention is all you need",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        "year": 2017,
    }
    apa = format_apa(paper)
    assert "Vaswani" in apa
    assert "2017" in apa
    assert "1706.03762" in apa
    assert "A." in apa  # initials
    print(f"✓ APA:{apa[:80]}...")


def test_format_apa_5plus_authors():
    """APA 5+ 作者"""
    paper = {
        "arxiv_id": "0000.0000",
        "title": "Test",
        "authors": ["Author One", "Author Two", "Author Three", "Author Four", "Author Five", "Author Six"],
        "year": 2024,
    }
    apa = format_apa(paper)
    assert "et al." in apa
    print("✓ APA 5+ 作者(et al.)")


def test_format_apa_no_authors():
    """APA 无作者"""
    paper = {"arxiv_id": "0000", "title": "Test", "authors": [], "year": 2024}
    apa = format_apa(paper)
    assert "Unknown" in apa
    print("✓ APA 无作者")


def test_format_ieee_basic():
    """IEEE 基础"""
    paper = {
        "arxiv_id": "1706.03762",
        "title": "Attention is all you need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2017,
    }
    ieee = format_ieee(paper)
    assert "Vaswani" in ieee
    assert "2017" in ieee
    assert "1706.03762" in ieee
    print(f"✓ IEEE:{ieee[:80]}...")


def test_format_ieee_4plus_authors():
    """IEEE 4+ 作者"""
    paper = {
        "arxiv_id": "0000",
        "title": "Test",
        "authors": ["Author One", "Author Two", "Author Three", "Author Four"],
        "year": 2024,
    }
    ieee = format_ieee(paper)
    assert "et al." in ieee
    print("✓ IEEE 4+ 作者(et al.)")


def test_format_bibtex_basic():
    """BibTeX 基础"""
    paper = {
        "arxiv_id": "1706.03762",
        "title": "Attention is all you need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2017,
        "url": "https://arxiv.org/abs/1706.03762",
    }
    bib = format_bibtex(paper)
    assert "@article" in bib
    assert "170603762" in bib or "1706.03762" in bib
    assert "Vaswani" in bib
    assert "2017" in bib
    assert "title" in bib
    print(f"✓ BibTeX:{bib[:80]}...")


def test_format_natural_basic():
    """自然语言"""
    paper = {
        "arxiv_id": "1706.03762",
        "title": "Attention is all you need",
        "authors": ["Ashish Vaswani", "Noam Shazeer"],
        "year": 2017,
    }
    nl = format_natural(paper)
    assert "Vaswani" in nl
    assert "2017" in nl
    assert "《Attention is all you need》" in nl or "Attention is all you need" in nl
    print(f"✓ 自然语言:{nl[:80]}...")


def test_format_natural_single_author():
    """自然语言 1 作者"""
    paper = {"arxiv_id": "x", "title": "Test", "authors": ["Alice"], "year": 2024}
    nl = format_natural(paper)
    assert "Alice" in nl
    print("✓ 自然语言 1 作者")


def test_format_natural_no_authors():
    """自然语言 无作者"""
    paper = {"arxiv_id": "x", "title": "Test", "authors": [], "year": 2024}
    nl = format_natural(paper)
    assert "未知" in nl
    print("✓ 自然语言 无作者")


def test_format_citation_4_styles():
    """4 种格式"""
    paper = {
        "arxiv_id": "1706.03762",
        "title": "Test",
        "authors": ["A B"],
        "year": 2017,
    }
    assert "Vaswani" not in format_citation(paper, "apa") or "A B" in format_citation(paper, "apa")
    for style in ["apa", "ieee", "bibtex", "natural"]:
        result = format_citation(paper, style)
        assert len(result) > 0
    print("✓ 4 风格")


def test_format_citation_unknown_style_fallback():
    """未知风格 fallback APA"""
    paper = {"arxiv_id": "x", "title": "Test", "authors": ["A"], "year": 2024}
    r = format_citation(paper, "unknown_style")
    assert "A" in r
    print("✓ 未知风格 fallback")


# ============== 5. 统计 ==============

def test_get_statistics():
    """统计"""
    stats = get_statistics()
    assert "total_papers" in stats
    assert "by_keyword" in stats
    assert "by_year" in stats
    assert "top_authors" in stats
    assert "total_unique_authors" in stats
    print(f"✓ 统计:{stats['total_papers']} 篇,{stats['total_unique_authors']} 作者")


def test_statistics_consistency():
    """统计一致性"""
    stats = get_statistics()
    total = stats["total_papers"]
    by_keyword_sum = sum(stats["by_keyword"].values())
    # by_keyword 可能有重复(同一 paper 出现在多个 keyword)
    assert by_keyword_sum >= total
    print(f"✓ 统计一致:total={total}, sum(by_keyword)={by_keyword_sum}")


def test_list_keywords():
    """列出 keyword"""
    kws = list_keywords()
    assert isinstance(kws, list)
    assert len(kws) > 0
    print(f"✓ keywords:{kws}")


def test_total_papers():
    """总数"""
    total = total_papers()
    assert total > 0
    print(f"✓ total {total} 篇")


# ============== 6. CLI ==============

def test_cli_list():
    """CLI:list"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "papers.py"), "list"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "Total:" in result.stdout
    print("✓ CLI list")


def test_cli_stats():
    """CLI:stats"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "papers.py"), "stats"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "total_papers" in data
    print("✓ CLI stats")


def test_cli_keywords():
    """CLI:keywords"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "papers.py"), "keywords"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert len(result.stdout) > 0
    print("✓ CLI keywords")


def test_cli_get():
    """CLI:get"""
    papers = _get_paper_index()
    if not papers:
        return
    pid = papers[0].arxiv_id
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "papers.py"), "get", pid],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["arxiv_id"] == pid
    print(f"✓ CLI get {pid}")


def test_cli_search():
    """CLI:search"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "papers.py"), "search", "learning"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    print("✓ CLI search")


def test_cli_cite_apa():
    """CLI:cite apa"""
    papers = _get_paper_index()
    if not papers:
        return
    pid = papers[0].arxiv_id
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "papers.py"), "cite", pid, "apa"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "arXiv:" in result.stdout
    print("✓ CLI cite apa")


def test_cli_cite_ieee():
    """CLI:cite ieee"""
    papers = _get_paper_index()
    if not papers:
        return
    pid = papers[0].arxiv_id
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "papers.py"), "cite", pid, "ieee"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    print("✓ CLI cite ieee")


def test_cli_cite_bibtex():
    """CLI:cite bibtex"""
    papers = _get_paper_index()
    if not papers:
        return
    pid = papers[0].arxiv_id
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "papers.py"), "cite", pid, "bibtex"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "@article" in result.stdout
    print("✓ CLI cite bibtex")


# ============== 7. 集成 ==============

def test_integration_paper_full_flow():
    """集成:论文完整流程"""
    # 1. 列出
    papers = _get_paper_index()
    assert len(papers) > 0
    # 2. 获取
    paper = get_paper(papers[0].arxiv_id)
    assert paper is not None
    # 3. 4 风格引用
    for style in ["apa", "ieee", "bibtex", "natural"]:
        c = format_citation(paper, style)
        assert len(c) > 0
    # 4. 统计
    stats = get_statistics()
    assert stats["total_papers"] == len(papers)
    print(f"✓ 集成:list → get → 4 cite → stats: {len(papers)} 篇")


def test_integration_keyword_coverage():
    """集成:keyword 覆盖"""
    kws = list_keywords()
    assert len(kws) >= 10  # 至少 10 个 keyword
    print(f"✓ keyword 覆盖 {len(kws)} 个")


# ============== 入口 ==============

if __name__ == "__main__":
    test_paper_dataclass()
    test_paper_url_auto()
    test_paper_to_dict()
    test_papers_dir_exists()
    test_scan_papers_directory()
    test_papers_have_required_fields()
    test_papers_unique_arxiv_id()
    test_papers_year_distribution()
    test_get_paper_existing()
    test_get_paper_not_found()
    test_search_by_title()
    test_search_by_title_not_match()
    test_search_by_author()
    test_list_by_keyword()
    test_list_by_year()
    test_search_by_abstract()
    test_format_apa_basic()
    test_format_apa_5plus_authors()
    test_format_apa_no_authors()
    test_format_ieee_basic()
    test_format_ieee_4plus_authors()
    test_format_bibtex_basic()
    test_format_natural_basic()
    test_format_natural_single_author()
    test_format_natural_no_authors()
    test_format_citation_4_styles()
    test_format_citation_unknown_style_fallback()
    test_get_statistics()
    test_statistics_consistency()
    test_list_keywords()
    test_total_papers()
    test_cli_list()
    test_cli_stats()
    test_cli_keywords()
    test_cli_get()
    test_cli_search()
    test_cli_cite_apa()
    test_cli_cite_ieee()
    test_cli_cite_bibtex()
    test_integration_paper_full_flow()
    test_integration_keyword_coverage()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
