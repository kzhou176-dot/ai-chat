#!/usr/bin/env python3
"""
test_23_release — aichat-hub Cycle 23 v1.0 发布工具测试
=====================================================
覆盖:
  1. 数据模型(CheckResult / ReleaseInfo)
  2. 11 项发布就绪检查(README/CHANGELOG/LICENSE/MASTER_PLAN/plan/progress/tests/scripts/research/papers/dashboard)
  3. check_readiness() 总览
  4. 模拟 git tag(create_tag / list_tags / get_latest_tag)
  5. Release Notes 生成
  6. 项目统计
  7. release_history.json 持久化
  8. CLI 入口
  9. 集成
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

from release import (
    ROOT, _RELEASE_HISTORY_PATH,
    CheckResult, ReleaseInfo,
    check_readme, check_changelog, check_license,
    check_master_plan, check_plan, check_progress,
    check_tests, check_scripts, check_research,
    check_papers, check_dashboard,
    run_all_checks, check_readiness,
    create_tag, list_tags, get_latest_tag,
    _load_release_history, _save_release_history,
    generate_release_notes, get_project_stats,
)


# ============== 1. 数据模型 ==============

def test_check_result():
    """CheckResult"""
    c = CheckResult(name="test", passed=True, details="ok", level="info")
    d = c.to_dict()
    assert d["name"] == "test"
    assert d["passed"]
    print("✓ CheckResult")


def test_release_info():
    """ReleaseInfo"""
    r = ReleaseInfo(version="v1.0.0", date="2026-07-21", cycle=23,
                    title="v1.0", description="desc", changes=["c1"])
    d = r.to_dict()
    assert d["version"] == "v1.0.0"
    assert d["cycle"] == 23
    print("✓ ReleaseInfo")


# ============== 2. 11 项检查 ==============

def test_check_readme():
    """README 检查"""
    c = check_readme()
    assert c.name == "README.md"
    # README 应该存在
    assert c.passed, f"README 失败:{c.details}"
    print(f"✓ README:{c.details}")


def test_check_changelog():
    """CHANGELOG 检查"""
    c = check_changelog()
    assert c.passed
    print(f"✓ CHANGELOG:{c.details}")


def test_check_license():
    """LICENSE 检查"""
    c = check_license()
    assert c.passed
    assert "MIT" in c.details
    print(f"✓ LICENSE:{c.details}")


def test_check_master_plan():
    """MASTER_PLAN 检查"""
    c = check_master_plan()
    assert c.passed
    print(f"✓ MASTER_PLAN:{c.details}")


def test_check_plan():
    """plan 检查"""
    c = check_plan()
    assert c.passed
    print(f"✓ plan:{c.details}")


def test_check_progress():
    """progress 检查"""
    c = check_progress()
    assert c.passed
    print(f"✓ progress:{c.details}")


def test_check_tests():
    """tests 检查"""
    c = check_tests()
    assert c.passed
    print(f"✓ tests:{c.details}")


def test_check_scripts():
    """scripts 检查"""
    c = check_scripts()
    assert c.passed
    print(f"✓ scripts:{c.details}")


def test_check_research():
    """research 检查"""
    c = check_research()
    assert c.passed
    print(f"✓ research:{c.details}")


def test_check_papers():
    """papers 检查"""
    c = check_papers()
    assert c.passed
    print(f"✓ papers:{c.details}")


def test_check_dashboard():
    """dashboard 检查"""
    c = check_dashboard()
    # dashboard.html 可能未生成(可选)
    if c.passed:
        print(f"✓ dashboard:{c.details}")
    else:
        print(f"! dashboard:{c.details}(可选,运行 scripts/dashboard.py save 生成)")


# ============== 3. 全部检查 ==============

def test_run_all_checks():
    """全部检查"""
    checks = run_all_checks()
    assert len(checks) == 11
    print(f"✓ 11 项检查")


def test_check_readiness():
    """就绪总览"""
    result = check_readiness()
    assert "total_checks" in result
    assert "passed" in result
    assert "ready" in result
    # 11 项全过(除了可能 dashboard)
    assert result["total_checks"] == 11
    assert result["passed"] >= 10  # 至少 10 项通过(dashboard 可能未生成)
    print(f"✓ 就绪:passed={result['passed']}/{result['total_checks']}, ready={result['ready']}")


def test_readiness_v1_should_be_ready():
    """v1.0 应该就绪"""
    result = check_readiness()
    # failed=0 即就绪
    assert result["failed"] == 0, f"v1.0 应无 error,实际 failed={result['failed']}"
    print(f"✓ v1.0 发布就绪")


# ============== 4. 模拟 git tag ==============

def setup_release_history():
    """清理 release_history.json"""
    if _RELEASE_HISTORY_PATH.exists():
        _RELEASE_HISTORY_PATH.unlink()


def teardown_release_history():
    """清理"""
    if _RELEASE_HISTORY_PATH.exists():
        _RELEASE_HISTORY_PATH.unlink()


def test_create_tag_basic():
    """创建 tag"""
    setup_release_history()
    tag = create_tag("v0.1.0", title="MVP", description="Initial release")
    assert tag["version"] == "v0.1.0"
    assert tag["title"] == "MVP"
    assert "tagged_at" in tag
    assert "checksum" in tag
    teardown_release_history()
    print("✓ 创建 tag")


def test_create_tag_with_changes():
    """创建带 changes 的 tag"""
    setup_release_history()
    tag = create_tag("v1.0.0", title="v1.0", changes=["c1", "c2", "c3"])
    assert len(tag["changes"]) == 3
    teardown_release_history()
    print("✓ 创建带 changes 的 tag")


def test_list_tags():
    """列出 tag"""
    setup_release_history()
    create_tag("v0.1.0")
    create_tag("v0.2.0")
    create_tag("v1.0.0")
    tags = list_tags()
    assert len(tags) == 3
    assert [t["version"] for t in tags] == ["v0.1.0", "v0.2.0", "v1.0.0"]
    teardown_release_history()
    print("✓ 列出 tag")


def test_get_latest_tag():
    """最新 tag"""
    setup_release_history()
    create_tag("v0.1.0")
    create_tag("v0.2.0")
    latest = get_latest_tag()
    assert latest["version"] == "v0.2.0"
    teardown_release_history()
    print("✓ 最新 tag")


def test_tag_persistence():
    """tag 持久化"""
    setup_release_history()
    create_tag("v1.0.0", title="Persistent")
    # 重新加载
    history = _load_release_history()
    assert len(history) == 1
    assert history[0]["title"] == "Persistent"
    teardown_release_history()
    print("✓ tag 持久化")


# ============== 5. Release Notes ==============

def test_generate_release_notes():
    """生成 release notes"""
    notes = generate_release_notes("v1.0.0")
    assert "v1.0.0" in notes
    assert "安装" in notes or "Install" in notes.lower()
    assert "验证" in notes or "verify" in notes.lower()
    print(f"✓ Release notes ({len(notes)} 字符)")


def test_generate_release_notes_with_cycles():
    """从 progress.md 提取 cycles"""
    notes = generate_release_notes("v1.0.0")
    # 应包含至少 1 个 Cycle 标题
    assert "Cycle" in notes
    print("✓ Release notes 含 cycle 列表")


# ============== 6. 项目统计 ==============

def test_get_project_stats():
    """项目统计"""
    stats = get_project_stats()
    assert "modules" in stats
    assert "test_files" in stats
    assert "total_loc" in stats
    assert "research_docs" in stats
    # 至少 20 modules / 20 tests
    assert stats["modules"] >= 20
    assert stats["test_files"] >= 20
    print(f"✓ 项目统计:{stats}")


# ============== 7. CLI ==============

def test_cli_check():
    """CLI:check"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "release.py"), "check"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "README" in result.stdout
    print("✓ CLI check")


def test_cli_readiness():
    """CLI:readiness"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "release.py"), "readiness"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "ready" in data
    print(f"✓ CLI readiness: ready={data['ready']}")


def test_cli_tag():
    """CLI:tag"""
    if _RELEASE_HISTORY_PATH.exists():
        _RELEASE_HISTORY_PATH.unlink()
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "release.py"), "tag", "v1.0.0", "First Release"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "Tagged" in result.stdout
    print("✓ CLI tag")
    if _RELEASE_HISTORY_PATH.exists():
        _RELEASE_HISTORY_PATH.unlink()


def test_cli_tags():
    """CLI:tags"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "release.py"), "tags"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    print("✓ CLI tags")


def test_cli_notes():
    """CLI:notes"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "release.py"), "notes", "v1.0.0"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "v1.0.0" in result.stdout
    print("✓ CLI notes")


def test_cli_stats():
    """CLI:stats"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "release.py"), "stats"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "modules" in data
    print("✓ CLI stats")


# ============== 8. 集成 ==============

def test_integration_full_v1_release():
    """集成:v1.0 完整发布流程"""
    # 1. 检查就绪
    readiness = check_readiness()
    assert readiness["failed"] == 0, f"v1.0 未就绪:failed={readiness['failed']}"
    # 2. 生成 release notes
    notes = generate_release_notes("v1.0.0")
    assert "v1.0.0" in notes
    # 3. 打 tag
    if _RELEASE_HISTORY_PATH.exists():
        _RELEASE_HISTORY_PATH.unlink()
    tag = create_tag("v1.0.0", title="v1.0 Final", description="First stable release",
                     changes=["README", "CHANGELOG", "LICENSE", "691 tests", "69 endpoints"])
    assert tag["version"] == "v1.0.0"
    # 4. 验证 tag
    latest = get_latest_tag()
    assert latest["version"] == "v1.0.0"
    # 5. 统计
    stats = get_project_stats()
    assert stats["modules"] >= 20
    if _RELEASE_HISTORY_PATH.exists():
        _RELEASE_HISTORY_PATH.unlink()
    print(f"✓ 集成 v1.0:就绪={readiness['ready']}, tag={tag['version']}, modules={stats['modules']}")


def test_integration_release_history_file():
    """集成:release_history.json 持久化"""
    if _RELEASE_HISTORY_PATH.exists():
        _RELEASE_HISTORY_PATH.unlink()
    # 1. 第一次 create
    tag1 = create_tag("v0.1.0", title="First")
    # 2. 文件应该存在
    assert _RELEASE_HISTORY_PATH.exists()
    # 3. 第二次 create(追加)
    tag2 = create_tag("v0.2.0", title="Second")
    # 4. 文件有 2 条
    history = _load_release_history()
    assert len(history) == 2
    # 5. 清理
    _RELEASE_HISTORY_PATH.unlink()
    print(f"✓ 持久化:文件 {len(history)} 条 tag")


# ============== 入口 ==============

if __name__ == "__main__":
    test_check_result()
    test_release_info()
    test_check_readme()
    test_check_changelog()
    test_check_license()
    test_check_master_plan()
    test_check_plan()
    test_check_progress()
    test_check_tests()
    test_check_scripts()
    test_check_research()
    test_check_papers()
    test_check_dashboard()
    test_run_all_checks()
    test_check_readiness()
    test_readiness_v1_should_be_ready()
    test_create_tag_basic()
    test_create_tag_with_changes()
    test_list_tags()
    test_get_latest_tag()
    test_tag_persistence()
    test_generate_release_notes()
    test_generate_release_notes_with_cycles()
    test_get_project_stats()
    test_cli_check()
    test_cli_readiness()
    test_cli_tag()
    test_cli_tags()
    test_cli_notes()
    test_cli_stats()
    test_integration_full_v1_release()
    test_integration_release_history_file()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
