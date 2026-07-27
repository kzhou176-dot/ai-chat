#!/usr/bin/env python3
"""
aichat-Hub Release (v1.0 发布工具) 模块
======================================
v1.0 发布就绪检查 + release notes 生成 + 模拟 git tag。

核心能力:
  1. 发布就绪检查(README / CHANGELOG / LICENSE / tests / modules)
  2. 生成 release notes(从 progress.md)
  3. 模拟 git tag(写入 release_history.json)
  4. 验证项目元数据
  5. CLI 集成

Cycle 23 — v1.0 最终发布
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

ROOT = Path("/Users/yuefeng/.mavis/agents/mavis/workspace/aichat-hub")


# ============== 数据模型 ==============

@dataclass
class CheckResult:
    """检查结果"""
    name: str
    passed: bool
    details: str = ""
    level: str = "info"  # info / warn / error

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ReleaseInfo:
    """Release 信息"""
    version: str
    date: str
    cycle: int
    title: str
    description: str
    changes: List[str] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============== 发布就绪检查 ==============

def check_readme() -> CheckResult:
    """检查 README.md"""
    path = ROOT / "README.md"
    if not path.exists():
        return CheckResult("README.md", False, "文件不存在", "error")
    content = path.read_text(encoding="utf-8")
    if len(content) < 1000:
        return CheckResult("README.md", False, f"内容过短:{len(content)} 字符", "warn")
    return CheckResult("README.md", True, f"{len(content)} 字符", "info")


def check_changelog() -> CheckResult:
    """检查 CHANGELOG.md"""
    path = ROOT / "CHANGELOG.md"
    if not path.exists():
        return CheckResult("CHANGELOG.md", False, "文件不存在", "error")
    content = path.read_text(encoding="utf-8")
    return CheckResult("CHANGELOG.md", True, f"{len(content)} 字符", "info")


def check_license() -> CheckResult:
    """检查 LICENSE"""
    path = ROOT / "LICENSE"
    if not path.exists():
        return CheckResult("LICENSE", False, "文件不存在", "error")
    content = path.read_text(encoding="utf-8")
    if "MIT" not in content and "Apache" not in content and "GPL" not in content:
        return CheckResult("LICENSE", False, "不是标准协议", "warn")
    return CheckResult("LICENSE", True, f"{len(content)} 字符,MIT", "info")


def check_master_plan() -> CheckResult:
    """检查 MASTER_PLAN.md"""
    path = ROOT / "MASTER_PLAN.md"
    if not path.exists():
        return CheckResult("MASTER_PLAN.md", False, "文件不存在", "error")
    return CheckResult("MASTER_PLAN.md", True, f"{len(path.read_text(encoding='utf-8'))} 字符", "info")


def check_plan() -> CheckResult:
    """检查 plan.md"""
    path = ROOT / "plan.md"
    if not path.exists():
        return CheckResult("plan.md", False, "文件不存在", "error")
    content = path.read_text(encoding="utf-8")
    cycle_count = content.count("[CYCLE_")
    return CheckResult("plan.md", True, f"{cycle_count} cycles 已完成", "info")


def check_progress() -> CheckResult:
    """检查 progress.md"""
    path = ROOT / "progress.md"
    if not path.exists():
        return CheckResult("progress.md", False, "文件不存在", "error")
    content = path.read_text(encoding="utf-8")
    return CheckResult("progress.md", True, f"{len(content)} 字符", "info")


def check_tests() -> CheckResult:
    """检查测试套件"""
    tests_dir = ROOT / "tests"
    if not tests_dir.exists():
        return CheckResult("tests/", False, "目录不存在", "error")
    test_files = list(tests_dir.glob("test_*.py"))
    if len(test_files) < 10:
        return CheckResult("tests/", False, f"只有 {len(test_files)} 个测试文件", "warn")
    return CheckResult("tests/", True, f"{len(test_files)} 个测试文件", "info")


def check_scripts() -> CheckResult:
    """检查 scripts/ 模块"""
    scripts_dir = ROOT / "scripts"
    if not scripts_dir.exists():
        return CheckResult("scripts/", False, "目录不存在", "error")
    modules = [f for f in scripts_dir.glob("*.py") if f.name != "__init__.py"]
    if len(modules) < 10:
        return CheckResult("scripts/", False, f"只有 {len(modules)} 个模块", "warn")
    return CheckResult("scripts/", True, f"{len(modules)} 个模块", "info")


def check_research() -> CheckResult:
    """检查 research/ 调研"""
    research = ROOT / "research" / "market"
    if not research.exists():
        return CheckResult("research/market/", False, "目录不存在", "warn")
    docs = list(research.glob("*.md"))
    if len(docs) < 5:
        return CheckResult("research/market/", False, f"只有 {len(docs)} 篇调研", "warn")
    return CheckResult("research/market/", True, f"{len(docs)} 篇调研", "info")


def check_papers() -> CheckResult:
    """检查 papers/"""
    papers = ROOT / "papers"
    if not papers.exists():
        return CheckResult("papers/", False, "目录不存在", "warn")
    # 统计 json 文件
    json_files = list(papers.glob("*/arxiv_*.json")) + list(papers.glob("*/*.json"))
    json_files = [j for j in json_files if "pdfs" not in str(j) and "parsed" not in str(j)]
    if len(json_files) < 10:
        return CheckResult("papers/", False, f"只有 {len(json_files)} 篇论文", "warn")
    return CheckResult("papers/", True, f"{len(json_files)} 篇论文", "info")


def check_dashboard() -> CheckResult:
    """检查 dashboard.html"""
    path = ROOT / "scripts" / "dashboard.html"
    if not path.exists():
        return CheckResult("dashboard.html", False, "未生成(运行 scripts/dashboard.py save)", "warn")
    return CheckResult("dashboard.html", True, f"{len(path.read_text(encoding='utf-8'))} 字符", "info")


def run_all_checks() -> List[CheckResult]:
    """运行所有检查"""
    return [
        check_readme(),
        check_changelog(),
        check_license(),
        check_master_plan(),
        check_plan(),
        check_progress(),
        check_tests(),
        check_scripts(),
        check_research(),
        check_papers(),
        check_dashboard(),
    ]


def check_readiness() -> Dict[str, Any]:
    """发布就绪总览"""
    checks = run_all_checks()
    passed = sum(1 for c in checks if c.passed)
    failed = sum(1 for c in checks if not c.passed and c.level == "error")
    warned = sum(1 for c in checks if not c.passed and c.level == "warn")
    return {
        "total_checks": len(checks),
        "passed": passed,
        "failed": failed,
        "warned": warned,
        "ready": failed == 0,  # 无 error 即就绪
        "checks": [c.to_dict() for c in checks],
    }


# ============== 模拟 git tag ==============

_RELEASE_HISTORY_PATH = ROOT / "release_history.json"


def _load_release_history() -> List[Dict[str, Any]]:
    """加载发布历史"""
    if not _RELEASE_HISTORY_PATH.exists():
        return []
    try:
        with open(_RELEASE_HISTORY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_release_history(history: List[Dict[str, Any]]):
    """保存发布历史"""
    with open(_RELEASE_HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)


def create_tag(
    version: str,
    title: str = "",
    description: str = "",
    changes: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """模拟 git tag(创建版本发布)"""
    history = _load_release_history()
    tag = {
        "version": version,
        "title": title,
        "description": description,
        "changes": changes or [],
        "tagged_at": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime()),
        "tagger": "aichat-hub-release-tool",
        "checksum": f"sha256-{int(time.time())}",
    }
    history.append(tag)
    _save_release_history(history)
    return tag


def list_tags() -> List[Dict[str, Any]]:
    """列出所有 tag"""
    return _load_release_history()


def get_latest_tag() -> Optional[Dict[str, Any]]:
    """获取最新 tag"""
    history = _load_release_history()
    return history[-1] if history else None


# ============== Release Notes 生成 ==============

def generate_release_notes(version: str) -> str:
    """生成 release notes(从 progress.md 提取)"""
    progress_path = ROOT / "progress.md"
    if not progress_path.exists():
        return f"# {version}\n\n暂无变更日志"
    content = progress_path.read_text(encoding="utf-8")
    # 提取最近的 CYCLE_N_DONE 段
    cycle_dones = re.findall(
        r"## (Cycle \d+[^+]*)[\s\S]+?\[CYCLE_\d+_DONE\]",
        content,
    )
    # 简化:取最近 5 个 cycle 标题
    recent = re.findall(r"## (Cycle \d+[^—\n]*) — [^\n]+", content)
    recent = recent[-5:] if recent else []
    parts = [f"# Release Notes — {version}", ""]
    parts.append(f"发布日期:{time.strftime('%Y-%m-%d')}")
    parts.append("")
    parts.append("## 本次发布包含")
    if recent:
        for cycle in recent:
            parts.append(f"- {cycle.strip()}")
    else:
        parts.append("- 见 CHANGELOG.md")
    parts.append("")
    parts.append("## 安装")
    parts.append("```bash")
    parts.append("# 纯标准库,无需 pip install")
    parts.append("git clone <repo>")
    parts.append("cd aichat-hub")
    parts.append("cd scripts && python3 web.py")
    parts.append("```")
    parts.append("")
    parts.append("## 验证")
    parts.append("```bash")
    parts.append("cd tests && for f in test_*.py; do python3 \"$f\"; done")
    parts.append("```")
    return "\n".join(parts)


# ============== 项目统计 ==============

def get_project_stats() -> Dict[str, Any]:
    """项目统计"""
    tests_dir = ROOT / "tests"
    scripts_dir = ROOT / "scripts"
    # 数测试文件 + 数 module
    test_files = list(tests_dir.glob("test_*.py"))
    modules = [f for f in scripts_dir.glob("*.py") if f.name != "__init__.py"]
    # 总行数
    total_loc = 0
    for f in modules:
        try:
            total_loc += sum(1 for _ in f.open(encoding="utf-8"))
        except OSError:
            pass
    return {
        "modules": len(modules),
        "test_files": len(test_files),
        "total_loc": total_loc,
        "research_docs": len(list((ROOT / "research" / "market").glob("*.md"))) if (ROOT / "research" / "market").exists() else 0,
    }


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 release.py {check|readiness|tag|notes|tags|stats}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "check":
        for c in run_all_checks():
            mark = "✓" if c.passed else "✗" if c.level == "error" else "!"
            print(f"  {mark} {c.name}: {c.details}")
    elif cmd == "readiness":
        result = check_readiness()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif cmd == "tag":
        if len(sys.argv) < 3:
            print("Usage: ... tag <version> [title]", file=sys.stderr)
            sys.exit(1)
        version = sys.argv[2]
        title = sys.argv[3] if len(sys.argv) > 3 else ""
        tag = create_tag(version, title=title)
        print(f"Tagged: {tag['version']} - {tag['title']}")
    elif cmd == "notes":
        version = sys.argv[2] if len(sys.argv) > 2 else "v1.0.0"
        print(generate_release_notes(version))
    elif cmd == "tags":
        for t in list_tags():
            print(f"  {t['version']} ({t['tagged_at']}) - {t.get('title', '')}")
    elif cmd == "stats":
        print(json.dumps(get_project_stats(), ensure_ascii=False, indent=2))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
