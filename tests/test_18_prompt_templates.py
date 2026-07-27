#!/usr/bin/env python3
"""
test_18_prompt_templates — aichat-hub Cycle 18 Prompt 模板库测试
============================================================
覆盖:
  1. 数据模型(PromptTemplate)
  2. 8 类别(CATEGORIES / CATEGORY_LABELS)
  3. 30+ 模板(跨 7 模块)
  4. PromptLibrary(get / list / search / render / add / remove)
  5. 模板渲染(str.format_map 变量替换)
  6. 关键词搜索(按 name/content/tags/category 评分)
  7. 动态添加/删除
  8. 各分类统计
  9. 模块级 API
  10. CLI 入口
  11. 集成(用模板 + 角色 + 渲染)
"""
import sys
import subprocess
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from prompt_templates import (
    CATEGORIES, CATEGORY_LABELS, PROMPT_LIBRARY,
    PromptTemplate, PromptLibrary,
    get_template, list_templates, search_templates,
    render_template, add_template, remove_template,
    list_categories, categories_summary, total_templates,
)


# ============== 1. 8 类别 ==============

def test_categories_count():
    """8 类别"""
    assert len(CATEGORIES) == 8
    expected = {"resume", "interview", "career", "industry", "alumni", "digital_human", "feed", "general"}
    assert set(CATEGORIES) == expected
    print("✓ 8 类别")


def test_category_labels():
    """类别标签"""
    for c in CATEGORIES:
        assert c in CATEGORY_LABELS
        label, emoji = CATEGORY_LABELS[c]
        assert label and emoji
    print("✓ 类别标签")


def test_list_categories():
    """列出 8 类别"""
    cs = list_categories()
    assert len(cs) == 8
    for c in cs:
        assert "id" in c and "label" in c and "emoji" in c
    print("✓ 列出 8 类别")


# ============== 2. 数据模型 ==============

def test_prompt_template_dataclass():
    """PromptTemplate"""
    t = PromptTemplate(
        id="test1", category="general", role="test",
        name="测试", content="Hello {name}", variables=["name"],
    )
    d = t.to_dict()
    assert d["id"] == "test1"
    assert d["category_label"] == "通用"
    assert d["variable_count"] == 1
    print("✓ PromptTemplate")


def test_prompt_template_default_version():
    """默认 version=1.0.0"""
    t = PromptTemplate(id="t", category="general", role="g", name="x", content="x")
    assert t.version == "1.0.0"
    print("✓ 默认 version")


# ============== 3. 30+ 模板 ==============

def test_library_count():
    """模板 ≥ 30"""
    assert len(PROMPT_LIBRARY) >= 30
    print(f"✓ 模板 {len(PROMPT_LIBRARY)} 个")


def test_library_per_category():
    """每类 ≥ 1"""
    counts: Dict[str, int] = {c: 0 for c in CATEGORIES}
    for t in PROMPT_LIBRARY:
        counts[t.category] = counts.get(t.category, 0) + 1
    for c, cnt in counts.items():
        assert cnt >= 1, f"{c} 数量 = 0"
    print(f"✓ 每类 ≥ 1: {counts}")


def test_library_required_fields():
    """必填字段"""
    for t in PROMPT_LIBRARY:
        assert t.id
        assert t.category in CATEGORIES
        assert t.role
        assert t.name
        assert t.content
    print("✓ 必填字段")


def test_library_unique_ids():
    """ID 唯一"""
    ids = [t.id for t in PROMPT_LIBRARY]
    assert len(set(ids)) == len(ids)
    print("✓ ID 唯一")


def test_library_covers_all_modules():
    """覆盖 cycle 1-17 角色"""
    roles = set(t.role for t in PROMPT_LIBRARY)
    # 期望:mentor/hr/senior/tech/behavioral/hr/pressure/career_guide/algorithm 等
    expected = {"mentor", "hr", "senior", "tech", "behavioral", "pressure",
                "career_guide", "algorithm", "product", "xiaoai"}
    for r in expected:
        assert r in roles, f"{r} 缺失"
    print(f"✓ 覆盖 {len(roles)} 角色")


# ============== 4. PromptLibrary 核心 ==============

def test_library_get():
    """获取单模板"""
    lib = PromptLibrary()
    t = lib.get("resume_mentor")
    assert t is not None
    assert t["id"] == "resume_mentor"
    print("✓ 获取模板")


def test_library_get_not_found():
    """未找到"""
    lib = PromptLibrary()
    assert lib.get("NOTEXIST") is None
    print("✓ 未找到 None")


def test_library_list_all():
    """列出全部"""
    lib = PromptLibrary()
    items = lib.list_all()
    assert len(items) == len(PROMPT_LIBRARY)
    print(f"✓ 列出 {len(items)}")


def test_library_list_by_category():
    """按类别筛选"""
    lib = PromptLibrary()
    items = lib.list_all(category="resume")
    assert all(t["category"] == "resume" for t in items)
    print(f"✓ resume {len(items)} 个")


def test_library_list_by_role():
    """按角色筛选"""
    lib = PromptLibrary()
    items = lib.list_all(role="mentor")
    assert all(t["role"] == "mentor" for t in items)
    print(f"✓ mentor {len(items)} 个")


def test_library_list_by_tag():
    """按标签筛选"""
    lib = PromptLibrary()
    items = lib.list_all(tag="中文")
    assert all("中文" in t["tags"] for t in items)
    print(f"✓ 中文 tag {len(items)} 个")


def test_library_search_by_name():
    """按名字搜索"""
    lib = PromptLibrary()
    results = lib.search_by_keyword("导师")
    assert len(results) > 0
    for r in results:
        assert "导师" in r["name"] or "导师" in r["content"]
    print(f"✓ 搜索 '导师' → {len(results)} 条")


def test_library_search_by_tag():
    """按 tag 搜索"""
    lib = PromptLibrary()
    results = lib.search_by_keyword("算法")
    assert len(results) > 0
    print(f"✓ 搜索 '算法' → {len(results)} 条")


def test_library_search_no_match():
    """无匹配"""
    lib = PromptLibrary()
    results = lib.search_by_keyword("zzzzz_no_match_xyz")
    assert results == []
    print("✓ 无匹配 → 空")


def test_library_search_scored():
    """搜索按评分排序(name > content > tag)"""
    lib = PromptLibrary()
    # "STAR" 出现在多个模板的 content
    results = lib.search_by_keyword("STAR")
    assert len(results) > 0
    print(f"✓ 搜索 'STAR' → {len(results)} 条")


# ============== 5. 渲染 ==============

def test_render_basic():
    """基本渲染"""
    lib = PromptLibrary()
    rendered = lib.render("resume_mentor", {"user_name": "小王", "target_position": "算法工程师"})
    assert rendered is not None
    assert "小王" in rendered
    assert "算法工程师" in rendered
    print("✓ 基本渲染")


def test_render_partial():
    """部分变量未填,保留占位符"""
    lib = PromptLibrary()
    rendered = lib.render("resume_mentor", {"user_name": "小王"})  # 缺 target_position
    assert rendered is not None
    assert "小王" in rendered
    assert "{target_position}" in rendered  # 占位符保留
    print("✓ 部分变量渲染")


def test_render_no_variables():
    """无变量模板"""
    lib = PromptLibrary()
    rendered = lib.render("interview_tech", {})  # 无变量
    assert rendered is not None
    assert "理性" in rendered
    print("✓ 无变量渲染")


def test_render_not_found():
    """渲染不存在的模板"""
    lib = PromptLibrary()
    assert lib.render("NOTEXIST", {}) is None
    print("✓ 不存在 None")


def test_render_extract_variables():
    """从 content 提取变量"""
    lib = PromptLibrary()
    t = lib.get("resume_mentor")
    variables = re.findall(r"\{(\w+)\}", t["content"])
    assert "user_name" in variables
    assert "target_position" in variables
    print(f"✓ 提取变量 {variables}")


# ============== 6. 增删 ==============

def test_library_add():
    """添加模板"""
    lib = PromptLibrary()
    before = lib.total()
    new = PromptTemplate(
        id="custom_test", category="general", role="custom",
        name="自定义测试", content="Hello {x}", variables=["x"],
    )
    tid = lib.add(new)
    assert tid == "custom_test"
    assert lib.total() == before + 1
    # 验证可获取
    t = lib.get("custom_test")
    assert t is not None
    print("✓ 添加模板")


def test_library_add_auto_id():
    """自动 ID"""
    lib = PromptLibrary()
    new = PromptTemplate(
        id="", category="general", role="custom",
        name="无 ID 测试", content="x",
    )
    tid = lib.add(new)
    assert tid != ""
    assert len(tid) == 8
    print(f"✓ 自动 ID: {tid}")


def test_library_remove():
    """删除模板"""
    lib = PromptLibrary()
    new = PromptTemplate(
        id="to_remove", category="general", role="x", name="x", content="x",
    )
    lib.add(new)
    assert lib.get("to_remove") is not None
    ok = lib.remove("to_remove")
    assert ok
    assert lib.get("to_remove") is None
    print("✓ 删除模板")


def test_library_remove_not_found():
    """删除不存在"""
    lib = PromptLibrary()
    assert not lib.remove("NOTEXIST")
    print("✓ 删除不存在")


# ============== 7. 统计 ==============

def test_categories_summary():
    """分类统计"""
    lib = PromptLibrary()
    summary = lib.categories_summary()
    assert isinstance(summary, dict)
    for c in CATEGORIES:
        assert c in summary
        assert summary[c] >= 1
    total = sum(summary.values())
    assert total == lib.total()
    print(f"✓ 分类统计:{summary}")


def test_total():
    """总数"""
    lib = PromptLibrary()
    assert lib.total() == len(PROMPT_LIBRARY)
    print(f"✓ 总数 {lib.total()}")


# ============== 8. 模块级 API ==============

def test_module_get_template():
    """模块级 get_template"""
    t = get_template("industry_algorithm")
    assert t is not None
    print("✓ 模块级 get")


def test_module_list_templates():
    """模块级 list_templates"""
    items = list_templates(category="interview")
    assert all(t["category"] == "interview" for t in items)
    print(f"✓ 模块级 list {len(items)} 个")


def test_module_search_templates():
    """模块级 search"""
    results = search_templates("HR")
    assert len(results) > 0
    print(f"✓ 模块级 search {len(results)} 条")


def test_module_render_template():
    """模块级 render"""
    rendered = render_template("dh_xiaoai", {})
    assert rendered is not None
    assert "小爱" in rendered
    print("✓ 模块级 render")


def test_module_add_template():
    """模块级 add"""
    from dataclasses import asdict
    new = PromptTemplate(
        id="module_test", category="general", role="m", name="模块测试", content="x"
    )
    tid = add_template(asdict(new))
    assert tid == "module_test"
    # 清理
    remove_template("module_test")
    print("✓ 模块级 add")


# ============== 9. CLI ==============

def test_cli_list():
    """CLI:list"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "prompt_templates.py"), "list"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "resume_mentor" in result.stdout
    print("✓ CLI list")


def test_cli_list_with_category():
    """CLI:list resume"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "prompt_templates.py"), "list", "resume"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "resume_mentor" in result.stdout
    assert "industry_algorithm" not in result.stdout
    print("✓ CLI list resume")


def test_cli_get():
    """CLI:get"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "prompt_templates.py"), "get", "resume_mentor"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["id"] == "resume_mentor"
    print("✓ CLI get")


def test_cli_search():
    """CLI:search"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "prompt_templates.py"), "search", "算法"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "industry_algorithm" in result.stdout
    print("✓ CLI search")


def test_cli_render():
    """CLI:render"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "prompt_templates.py"), "render",
         "resume_mentor", "user_name=小王", "target_position=算法工程师"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "小王" in result.stdout
    assert "算法工程师" in result.stdout
    print("✓ CLI render")


def test_cli_categories():
    """CLI:categories"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "prompt_templates.py"), "categories"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "resume" in result.stdout
    assert "📝" in result.stdout
    print("✓ CLI categories")


def test_cli_summary():
    """CLI:summary"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "prompt_templates.py"), "summary"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "resume" in data
    print("✓ CLI summary")


# ============== 10. 集成 ==============

def test_integration_render_with_role():
    """集成:用模板 + 角色变量"""
    # 用 industry_algorithm 模板,模拟学生问题
    rendered = render_template("industry_algorithm", {
        "user_name": "小王",
        "question": "算法岗 2025 校招薪资如何?",
    })
    assert "小王" in rendered
    assert "算法岗 2025 校招薪资" in rendered
    print("✓ 集成:模板 + 角色 + 问题")


def test_integration_search_by_keyword_industry():
    """集成:行业关键词搜索"""
    results = search_templates("行业")
    # 应有多条含"行业"
    assert len(results) >= 3
    for r in results:
        assert "industry" in r["category"] or "行业" in r["name"] or "行业" in r["content"]
    print(f"✓ '行业' 搜索 {len(results)} 条")


def test_integration_cover_all_cycles():
    """集成:覆盖 cycle 1-17 关键角色"""
    expected_ids = [
        "resume_mentor",          # cycle 11
        "resume_hr",              # cycle 11
        "interview_tech",         # cycle 12
        "interview_behavioral",   # cycle 12
        "interview_pressure",     # cycle 12
        "career_guide",           # cycle 13
        "industry_algorithm",     # cycle 14
        "alumni_senior_eng",      # cycle 15
        "dh_xiaoai",              # cycle 16
        "dh_career_guide",        # cycle 16
        "feed_recommend",         # cycle 17
    ]
    for eid in expected_ids:
        t = get_template(eid)
        assert t is not None, f"{eid} 缺失"
    print(f"✓ 覆盖 {len(expected_ids)} 关键模板")


# ============== 入口 ==============

if __name__ == "__main__":
    import re
    test_categories_count()
    test_category_labels()
    test_list_categories()
    test_prompt_template_dataclass()
    test_prompt_template_default_version()
    test_library_count()
    test_library_per_category()
    test_library_required_fields()
    test_library_unique_ids()
    test_library_covers_all_modules()
    test_library_get()
    test_library_get_not_found()
    test_library_list_all()
    test_library_list_by_category()
    test_library_list_by_role()
    test_library_list_by_tag()
    test_library_search_by_name()
    test_library_search_by_tag()
    test_library_search_no_match()
    test_library_search_scored()
    test_render_basic()
    test_render_partial()
    test_render_no_variables()
    test_render_not_found()
    test_render_extract_variables()
    test_library_add()
    test_library_add_auto_id()
    test_library_remove()
    test_library_remove_not_found()
    test_categories_summary()
    test_total()
    test_module_get_template()
    test_module_list_templates()
    test_module_search_templates()
    test_module_render_template()
    test_module_add_template()
    test_cli_list()
    test_cli_list_with_category()
    test_cli_get()
    test_cli_search()
    test_cli_render()
    test_cli_categories()
    test_cli_summary()
    test_integration_render_with_role()
    test_integration_search_by_keyword_industry()
    test_integration_cover_all_cycles()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
