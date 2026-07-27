"""
test_25_e2e.py — e2e_demo 模块单元测试

覆盖:
- MockHandler
- _call (web.ROUTES 调用)
- StepResult / PhaseResult 数据类
- DemoRunner 5 阶段
- _summarize_body / _extract_field / _extract_alumni_id / _extract_arxiv_id
- save_log / save_report / load_log
- _build_runner_from_log
"""

import os
import sys
import json
import time

# 路径
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

import e2e_demo  # noqa: E402


# ============== MockHandler ==============

def test_mock_handler_json_body():
    h = e2e_demo.MockHandler(json_body={"a": 1})
    assert h.json_body == {"a": 1}
    h2 = e2e_demo.MockHandler()
    assert h2.json_body is None
    h3 = e2e_demo.MockHandler(query={"k": "v"})
    assert h3.query == {"k": "v"}
    print("  ✓ test_mock_handler_json_body")


# ============== _call ==============

def test_call_existing_route():
    result = e2e_demo._call("GET", "/api/personas")
    assert result["status"] == 200
    assert result["ok"] is True
    assert "body" in result
    print(f"  ✓ test_call_existing_route (status={result['status']})")


def test_call_404():
    result = e2e_demo._call("GET", "/api/no_such")
    assert result["status"] == 404
    assert result["ok"] is False
    print(f"  ✓ test_call_404")


def test_call_with_payload():
    result = e2e_demo._call("POST", "/api/career/start", payload={"user_id": "test"})
    assert result["status"] == 200
    body = result["body"]
    assert "session_id" in body
    print(f"  ✓ test_call_with_payload (session_id={body.get('session_id')[:8]})")


# ============== StepResult / PhaseResult ==============

def test_step_result_to_dict():
    s = e2e_demo.StepResult(
        phase="test", name="step1", method="GET", path="/x",
        status=200, ok=True, duration_ms=1.0, body_summary="ok"
    )
    d = s.to_dict()
    assert d["phase"] == "test"
    assert d["ok"] is True
    print("  ✓ test_step_result_to_dict")


def test_phase_result_add():
    p = e2e_demo.PhaseResult(name="test", description="desc")
    s1 = e2e_demo.StepResult(phase="test", name="s1", method="GET", path="/x", status=200, ok=True)
    s2 = e2e_demo.StepResult(phase="test", name="s2", method="GET", path="/x", status=500, ok=False)
    p.add(s1)
    p.add(s2)
    assert len(p.steps) == 2
    assert p.success is False  # 500 让 success = False
    print("  ✓ test_phase_result_add")


def test_phase_result_add_404_still_success():
    """404 客户端错误不算 server 错误,phase 仍 success"""
    p = e2e_demo.PhaseResult(name="test", description="desc")
    s = e2e_demo.StepResult(phase="test", name="s", method="GET", path="/x", status=404, ok=False)
    p.add(s)
    assert p.success is True
    print("  ✓ test_phase_result_add_404_still_success")


# ============== DemoRunner ==============

def test_runner_init():
    r = e2e_demo.DemoRunner(user_id="u1")
    assert r.user_id == "u1"
    assert r.phases == []
    assert r._interview_session_id is None
    assert r._career_session_id is None
    print("  ✓ test_runner_init")


def test_runner_phase1_career():
    r = e2e_demo.DemoRunner(user_id="u1")
    phase = r.run_phase1_career()
    assert phase.name == "phase1_career"
    assert len(phase.steps) >= 5
    print(f"  ✓ test_runner_phase1_career ({len(phase.steps)} steps)")


def test_runner_phase2_resume():
    r = e2e_demo.DemoRunner(user_id="u1")
    phase = r.run_phase2_resume()
    assert phase.name == "phase2_resume"
    assert len(phase.steps) == 5
    print(f"  ✓ test_runner_phase2_resume ({len(phase.steps)} steps)")


def test_runner_phase3_interview():
    r = e2e_demo.DemoRunner(user_id="u1")
    phase = r.run_phase3_interview()
    assert phase.name == "phase3_interview"
    assert len(phase.steps) == 6
    print(f"  ✓ test_runner_phase3_interview ({len(phase.steps)} steps)")


def test_runner_phase4_alumni():
    r = e2e_demo.DemoRunner(user_id="u1")
    phase = r.run_phase4_alumni()
    assert phase.name == "phase4_alumni"
    assert len(phase.steps) >= 5
    print(f"  ✓ test_runner_phase4_alumni ({len(phase.steps)} steps)")


def test_runner_phase5_papers():
    r = e2e_demo.DemoRunner(user_id="u1")
    phase = r.run_phase5_papers()
    assert phase.name == "phase5_papers"
    assert len(phase.steps) >= 8
    print(f"  ✓ test_runner_phase5_papers ({len(phase.steps)} steps)")


def test_runner_all_phases():
    r = e2e_demo.DemoRunner(user_id="u1")
    phases = r.run_all()
    assert len(phases) == 5
    total = sum(len(p.steps) for p in phases)
    assert total >= 30
    print(f"  ✓ test_runner_all_phases ({len(phases)} phases, {total} steps total)")


# ============== _summarize_body ==============

def test_summarize_body_error():
    s = e2e_demo._summarize_body({"error": "test error"})
    assert "error" in s
    print("  ✓ test_summarize_body_error")


def test_summarize_body_session():
    s = e2e_demo._summarize_body({"session_id": "abc123"})
    assert "abc123" in s
    print("  ✓ test_summarize_body_session")


def test_summarize_body_collections():
    s1 = e2e_demo._summarize_body({"personas": [1, 2, 3]})
    assert "3" in s1
    s2 = e2e_demo._summarize_body({"papers": [1, 2, 3, 4]})
    assert "4" in s2
    s3 = e2e_demo._summarize_body({"matches": [1]})
    assert "1" in s3
    print("  ✓ test_summarize_body_collections")


def test_summarize_body_other():
    s = e2e_demo._summarize_body({"unknown_key": 1})
    assert "unknown_key" in s or "keys" in s
    print(f"  ✓ test_summarize_body_other ({s[:50]})")


# ============== _extract_field ==============

def test_extract_field_ok():
    step = e2e_demo.StepResult(phase="t", name="n", method="GET", path="/x", status=200, ok=True,
                                raw_body={"session_id": "abc"})
    val = e2e_demo._extract_field(step, "session_id")
    assert val == "abc"
    print("  ✓ test_extract_field_ok")


def test_extract_field_not_ok():
    step = e2e_demo.StepResult(phase="t", name="n", method="GET", path="/x", status=500, ok=False)
    val = e2e_demo._extract_field(step, "session_id")
    assert val is None
    print("  ✓ test_extract_field_not_ok")


def test_extract_field_missing_key():
    step = e2e_demo.StepResult(phase="t", name="n", method="GET", path="/x", status=200, ok=True,
                                raw_body={"other": 1})
    val = e2e_demo._extract_field(step, "session_id")
    assert val is None
    print("  ✓ test_extract_field_missing_key")


# ============== _extract_alumni_id ==============

def test_extract_alumni_id():
    step = e2e_demo.StepResult(phase="t", name="n", method="POST", path="/x", status=200, ok=True,
                                raw_body={"matches": [{"alumni": {"id": "TH001"}, "score": 0.9}]})
    aid = e2e_demo._extract_alumni_id(step)
    assert aid == "TH001"
    print("  ✓ test_extract_alumni_id")


def test_extract_alumni_id_no_match():
    step = e2e_demo.StepResult(phase="t", name="n", method="POST", path="/x", status=200, ok=True,
                                raw_body={"matches": []})
    aid = e2e_demo._extract_alumni_id(step)
    assert aid is None
    print("  ✓ test_extract_alumni_id_no_match")


# ============== _extract_arxiv_id ==============

def test_extract_arxiv_id_results():
    step = e2e_demo.StepResult(phase="t", name="n", method="POST", path="/x", status=200, ok=True,
                                raw_body={"results": [{"arxiv_id": "1706.03762"}]})
    aid = e2e_demo._extract_arxiv_id(step)
    assert aid == "1706.03762"
    print("  ✓ test_extract_arxiv_id_results")


def test_extract_arxiv_id_papers():
    step = e2e_demo.StepResult(phase="t", name="n", method="POST", path="/x", status=200, ok=True,
                                raw_body={"papers": [{"id": "P1"}]})
    aid = e2e_demo._extract_arxiv_id(step)
    assert aid == "P1"
    print("  ✓ test_extract_arxiv_id_papers")


def test_extract_arxiv_id_no_results():
    step = e2e_demo.StepResult(phase="t", name="n", method="POST", path="/x", status=200, ok=True,
                                raw_body={"results": []})
    aid = e2e_demo._extract_arxiv_id(step)
    assert aid is None
    print("  ✓ test_extract_arxiv_id_no_results")


# ============== 持久化 ==============

def test_save_and_load_log():
    r = e2e_demo.DemoRunner(user_id="test_save")
    r.run_phase1_career()
    test_path = os.path.join(e2e_demo.DATA_DIR, "_test_e2e_log.json")
    e2e_demo.save_log(r, path=test_path)
    assert os.path.exists(test_path)
    log = e2e_demo.load_log(path=test_path)
    assert log is not None
    assert log["user_id"] == "test_save"
    assert len(log["phases"]) == 1
    # 清理
    if os.path.exists(test_path):
        os.remove(test_path)
    print("  ✓ test_save_and_load_log")


def test_save_report():
    r = e2e_demo.DemoRunner(user_id="test_report")
    r.run_phase1_career()
    test_path = os.path.join(ROOT, "reports", "_test_e2e_report.md")
    e2e_demo.save_report(r, path=test_path)
    assert os.path.exists(test_path)
    with open(test_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "AICHAT-HUB" in content
    assert "phase1_career" in content
    # 清理
    if os.path.exists(test_path):
        os.remove(test_path)
    print("  ✓ test_save_report")


def test_build_runner_from_log():
    r = e2e_demo.DemoRunner(user_id="u1")
    r.run_phase1_career()
    log = {
        "user_id": r.user_id,
        "started_at": r.started_at,
        "phases": [p.to_dict() for p in r.phases],
    }
    r2 = e2e_demo._build_runner_from_log(log)
    assert r2.user_id == r.user_id
    assert len(r2.phases) == len(r.phases)
    print("  ✓ test_build_runner_from_log")


# ============== generate_report ==============

def test_generate_report_basic():
    r = e2e_demo.DemoRunner(user_id="u1")
    r.run_all()
    md = r.generate_report()
    assert "AICHAT-HUB" in md
    assert "总 Step 数" in md
    assert "phase1_career" in md
    assert "phase5_papers" in md
    assert "结论" in md
    print(f"  ✓ test_generate_report_basic ({len(md)} chars)")


# ============== 集成:跑一次完整 demo ==============

def test_full_demo_run():
    """集成测试:5 阶段全部跑通"""
    r = e2e_demo.DemoRunner(user_id="integration_test")
    phases = r.run_all()
    total = sum(len(p.steps) for p in phases)
    ok = sum(1 for p in phases for s in p.steps if s.ok)
    # 不强制 100%(60 题 demo 跳过是特例),但大部分通过
    assert ok >= total - 2, f"too many failures: {ok}/{total}"
    print(f"  ✓ test_full_demo_run ({ok}/{total} steps successful)")


def test_demo_log_contains_raw_body():
    """StepResult 持久化后保留 raw_body"""
    r = e2e_demo.DemoRunner(user_id="test")
    r.run_phase3_interview()
    test_path = os.path.join(e2e_demo.DATA_DIR, "_test_e2e_raw.json")
    e2e_demo.save_log(r, path=test_path)
    with open(test_path, "r", encoding="utf-8") as f:
        log = json.load(f)
    # 检查 raw_body 存在
    steps_with_body = [s for p in log["phases"] for s in p["steps"] if s.get("raw_body")]
    assert len(steps_with_body) > 0
    # 清理
    if os.path.exists(test_path):
        os.remove(test_path)
    print(f"  ✓ test_demo_log_contains_raw_body ({len(steps_with_body)} steps with raw_body)")


# ============== 主入口 ==============

def run_all():
    tests = [
        test_mock_handler_json_body,
        test_call_existing_route,
        test_call_404,
        test_call_with_payload,
        test_step_result_to_dict,
        test_phase_result_add,
        test_phase_result_add_404_still_success,
        test_runner_init,
        test_runner_phase1_career,
        test_runner_phase2_resume,
        test_runner_phase3_interview,
        test_runner_phase4_alumni,
        test_runner_phase5_papers,
        test_runner_all_phases,
        test_summarize_body_error,
        test_summarize_body_session,
        test_summarize_body_collections,
        test_summarize_body_other,
        test_extract_field_ok,
        test_extract_field_not_ok,
        test_extract_field_missing_key,
        test_extract_alumni_id,
        test_extract_alumni_id_no_match,
        test_extract_arxiv_id_results,
        test_extract_arxiv_id_papers,
        test_extract_arxiv_id_no_results,
        test_save_and_load_log,
        test_save_report,
        test_build_runner_from_log,
        test_generate_report_basic,
        test_full_demo_run,
        test_demo_log_contains_raw_body,
    ]
    print(f"Running {len(tests)} e2e tests...\n")
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{'='*60}")
    print(f"Passed: {passed}/{len(tests)}")
    if failed == 0:
        print("✅ All e2e tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    return failed == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
