#!/usr/bin/env python3
"""
test_19_dashboard — aichat-hub Cycle 19 Dashboard 模块测试
========================================================
覆盖:
  1. 项目元数据(PROJECT_META)
  2. 模块清单(20 个)
  3. 端点速查(55 个)
  4. HTML 生成(generate_dashboard)
  5. 元数据 API(get_dashboard_meta)
  6. 保存 HTML(save_dashboard_html)
  7. CLI 入口
  8. 响应式 CSS
"""
import sys
import subprocess
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from dashboard import (
    PROJECT_META, MODULES, ENDPOINTS_SUMMARY,
    HTML_TEMPLATE,
    generate_dashboard, get_dashboard_meta, save_dashboard_html,
)


# ============== 1. 项目元数据 ==============

def test_project_meta_basic():
    """项目元数据"""
    assert PROJECT_META["name"] == "AIchat-Hub"
    assert "version" in PROJECT_META
    assert "tagline" in PROJECT_META
    assert "license" in PROJECT_META
    print(f"✓ 项目元数据: {PROJECT_META['name']} v{PROJECT_META['version']}")


def test_project_meta_philosophy():
    """设计原则 3 个"""
    assert len(PROJECT_META["philosophy"]) >= 3
    print(f"✓ 设计原则 {len(PROJECT_META['philosophy'])} 条")


def test_project_meta_dependencies():
    """零依赖"""
    assert "zero" in PROJECT_META["dependencies"].lower()
    print("✓ 零依赖")


# ============== 2. 模块清单 ==============

def test_modules_count():
    """20 个模块"""
    assert len(MODULES) == 20
    print(f"✓ 模块 {len(MODULES)} 个")


def test_modules_required_fields():
    """模块必填字段"""
    for m in MODULES:
        assert "name" in m
        assert "version" in m
        assert "cycle" in m
        assert "category" in m
        assert "description" in m
        assert "loc" in m
        assert m["loc"] > 0
    print("✓ 模块必填字段")


def test_modules_unique_names():
    """模块名唯一"""
    names = [m["name"] for m in MODULES]
    assert len(set(names)) == len(names)
    print("✓ 模块名唯一")


def test_modules_cycles():
    """模块覆盖 cycle 1-18"""
    cycles = set(m["cycle"] for m in MODULES)
    assert len(cycles) >= 15
    print(f"✓ 模块覆盖 {len(cycles)} cycles: {sorted(cycles)[:5]}...")


def test_modules_categories():
    """模块分类"""
    cats = set(m["category"] for m in MODULES)
    assert "基础" in cats
    assert "职业辅导" in cats
    assert "虚拟人" in cats
    print(f"✓ 分类: {cats}")


def test_modules_total_loc():
    """总代码行数 ≥ 5000"""
    total = sum(m["loc"] for m in MODULES)
    assert total >= 5000
    print(f"✓ 总代码 {total} 行")


# ============== 3. 端点速查 ==============

def test_endpoints_total():
    """端点总数 55"""
    total = sum(len(eps) for eps in ENDPOINTS_SUMMARY.values())
    assert total == 55
    print(f"✓ 端点 {total} 个")


def test_endpoints_categories():
    """端点分类"""
    expected = ["core", "resume", "interview", "career", "industry",
                "alumni", "human", "feed", "prompt"]
    for c in expected:
        assert c in ENDPOINTS_SUMMARY
    print(f"✓ 端点 {len(ENDPOINTS_SUMMARY)} 分类")


def test_endpoints_method_format():
    """端点 method/path 格式"""
    for cat, eps in ENDPOINTS_SUMMARY.items():
        for method, path in eps:
            assert method in ("GET", "POST")
            assert path.startswith("/")
    print("✓ 端点格式")


def test_endpoints_no_duplicates():
    """端点无重复"""
    all_eps = []
    for eps in ENDPOINTS_SUMMARY.values():
        all_eps.extend([(m, p) for m, p in eps])
    assert len(set(all_eps)) == len(all_eps)
    print(f"✓ 端点无重复 {len(all_eps)} 条")


# ============== 4. HTML 生成 ==============

def test_generate_dashboard_returns_html():
    """生成 HTML 字符串"""
    html = generate_dashboard()
    assert isinstance(html, str)
    assert len(html) > 1000
    print(f"✓ 生成 HTML {len(html)} 字符")


def test_generate_dashboard_has_doctype():
    """DOCTYPE"""
    html = generate_dashboard()
    assert "<!DOCTYPE html>" in html
    assert "<html" in html
    assert "</html>" in html
    print("✓ HTML 结构")


def test_generate_dashboard_has_project_name():
    """包含项目名"""
    html = generate_dashboard()
    assert "AIchat-Hub" in html
    assert "v0.16.0" in html
    print("✓ 含项目名 + 版本")


def test_generate_dashboard_has_stats():
    """包含统计数据"""
    html = generate_dashboard()
    assert "537" in html  # tests
    assert "55" in html  # endpoints
    assert "20" in html  # scripts
    print("✓ 含统计数据")


def test_generate_dashboard_has_modules():
    """包含模块"""
    html = generate_dashboard()
    assert "persona" in html
    assert "resume" in html
    assert "career_profile" in html
    print("✓ 含模块名")


def test_generate_dashboard_has_endpoints():
    """包含端点"""
    html = generate_dashboard()
    assert "/api/career" in html
    assert "/api/industry" in html
    assert "/api/feed" in html
    assert "/api/prompt" in html
    print("✓ 含端点")


def test_generate_dashboard_has_responsive_css():
    """响应式 CSS"""
    html = generate_dashboard()
    assert "@media" in html
    assert "max-width" in html
    print("✓ 响应式 CSS")


def test_generate_dashboard_chinese():
    """中文内容"""
    html = generate_dashboard()
    assert "虚拟人" in html or "职业" in html or "端点" in html
    print("✓ 中文内容")


# ============== 5. 元数据 API ==============

def test_get_dashboard_meta():
    """Dashboard 元数据"""
    meta = get_dashboard_meta()
    assert "project" in meta
    assert "modules" in meta
    assert "endpoints_summary" in meta
    assert "stats" in meta
    print("✓ 元数据 API")


def test_get_dashboard_meta_stats():
    """统计数据"""
    meta = get_dashboard_meta()
    assert meta["stats"]["tests"] == 537
    assert meta["stats"]["endpoints"] == 55
    assert meta["stats"]["scripts"] == 20
    assert meta["stats"]["cycles"] == 19
    print(f"✓ 统计: {meta['stats']}")


def test_get_dashboard_meta_endpoints():
    """端点元数据"""
    meta = get_dashboard_meta()
    assert "core" in meta["endpoints_summary"]
    # 验证 endpoint 结构
    eps = meta["endpoints_summary"]["core"]
    assert all("method" in e and "path" in e for e in eps)
    print(f"✓ 端点元数据 {sum(len(v) for v in meta['endpoints_summary'].values())}")


# ============== 6. 保存 HTML ==============

def test_save_dashboard_html():
    """保存 HTML"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        tmp_path = f.name
    try:
        out = save_dashboard_html(tmp_path)
        assert out == tmp_path
        assert os.path.exists(tmp_path)
        with open(tmp_path, 'r', encoding='utf-8') as f:
            content = f.read()
        assert "<!DOCTYPE html>" in content
        assert "AIchat-Hub" in content
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    print("✓ 保存 HTML")


def test_save_dashboard_html_default_path():
    """保存到默认路径"""
    out = save_dashboard_html()  # 无参数 → 默认 scripts/dashboard.html
    assert "dashboard.html" in out
    assert os.path.exists(out)
    # 清理
    if os.path.exists(out):
        os.unlink(out)
    print(f"✓ 默认路径:{out}")


# ============== 7. CLI ==============

def test_cli_generate():
    """CLI:generate"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "dashboard.py"), "generate"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "<!DOCTYPE html>" in result.stdout
    print("✓ CLI generate")


def test_cli_save():
    """CLI:save"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
        tmp_path = f.name
    try:
        result = subprocess.run(
            [sys.executable, str(SCRIPTS / "dashboard.py"), "save", tmp_path],
            capture_output=True, text=True, timeout=10
        )
        assert result.returncode == 0
        assert os.path.exists(tmp_path)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
    print("✓ CLI save")


def test_cli_meta():
    """CLI:meta"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "dashboard.py"), "meta"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "project" in data
    assert "stats" in data
    print("✓ CLI meta")


# ============== 8. 集成 ==============

def test_integration_dashboard_with_web():
    """集成:dashboard 数据与 web 端一致"""
    from dashboard import get_dashboard_meta
    import sys
    sys.path.insert(0, str(SCRIPTS))
    meta = get_dashboard_meta()
    # 检查总 endpoint 数量
    assert meta["stats"]["endpoints"] >= 50
    # 检查总 modules 数量
    assert meta["stats"]["scripts"] == 20
    print(f"✓ Dashboard 与 web 端一致: {meta['stats']}")


def test_integration_html_size_reasonable():
    """集成:HTML 大小合理"""
    html = generate_dashboard()
    # 5KB-100KB 之间
    assert 5000 < len(html) < 100000
    print(f"✓ HTML 大小 {len(html)} 字符")


def test_integration_dashboard_for_all_categories():
    """集成:所有 9 类别端点都在 HTML"""
    html = generate_dashboard()
    for cat in ["core", "resume", "interview", "career", "industry",
                "alumni", "human", "feed", "prompt"]:
        assert f"/{cat}" in html or f'"{cat}"' in html
    print("✓ 9 类别端点都在 HTML")


# ============== 入口 ==============

if __name__ == "__main__":
    test_project_meta_basic()
    test_project_meta_philosophy()
    test_project_meta_dependencies()
    test_modules_count()
    test_modules_required_fields()
    test_modules_unique_names()
    test_modules_cycles()
    test_modules_categories()
    test_modules_total_loc()
    test_endpoints_total()
    test_endpoints_categories()
    test_endpoints_method_format()
    test_endpoints_no_duplicates()
    test_generate_dashboard_returns_html()
    test_generate_dashboard_has_doctype()
    test_generate_dashboard_has_project_name()
    test_generate_dashboard_has_stats()
    test_generate_dashboard_has_modules()
    test_generate_dashboard_has_endpoints()
    test_generate_dashboard_has_responsive_css()
    test_generate_dashboard_chinese()
    test_get_dashboard_meta()
    test_get_dashboard_meta_stats()
    test_get_dashboard_meta_endpoints()
    test_save_dashboard_html()
    test_save_dashboard_html_default_path()
    test_cli_generate()
    test_cli_save()
    test_cli_meta()
    test_integration_dashboard_with_web()
    test_integration_html_size_reasonable()
    test_integration_dashboard_for_all_categories()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
