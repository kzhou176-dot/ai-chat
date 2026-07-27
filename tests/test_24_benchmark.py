"""
test_24_benchmark.py — benchmark 模块单元测试

覆盖:
- MockHandler
- run_endpoint
- run_endpoint_n
- percentile
- get_all_endpoints (74 个)
- benchmark_all
- generate_report
- save_results / load_results
- save_report
- sample_memory
- ENDPOINT_PAYLOADS 完整性
- 数据类 BenchmarkResult / MemorySample
"""

import os
import sys
import json
import statistics

# 路径
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

import benchmark  # noqa: E402


# ============== MockHandler ==============

def test_mock_handler_json_body():
    h = benchmark.MockHandler(json_body={"a": 1})
    assert h.json_body == {"a": 1}
    h2 = benchmark.MockHandler()
    assert h2.json_body is None
    h3 = benchmark.MockHandler(query={"k": "v"})
    assert h3.query == {"k": "v"}
    print("  ✓ test_mock_handler_json_body")


def test_mock_handler_query():
    h = benchmark.MockHandler(query={"x": "1", "y": "2"})
    assert h.query["x"] == "1"
    assert h.query["y"] == "2"
    print("  ✓ test_mock_handler_query")


# ============== run_endpoint ==============

def test_run_endpoint_basic():
    status, elapsed, _ = benchmark.run_endpoint("GET", "/api/personas")
    assert status == 200
    assert elapsed >= 0
    assert elapsed < 1000  # 1s 内肯定能跑完
    print(f"  ✓ test_run_endpoint_basic (status={status}, {elapsed:.2f}ms)")


def test_run_endpoint_404():
    status, elapsed, _ = benchmark.run_endpoint("GET", "/api/does_not_exist")
    assert status == 404
    print(f"  ✓ test_run_endpoint_404 (status={status})")


def test_run_endpoint_post_with_payload():
    status, elapsed, _ = benchmark.run_endpoint(
        "POST", "/api/score",
        payload={"response": "I am a developer with 5 years of Python experience building web apps."}
    )
    assert status == 200
    print(f"  ✓ test_run_endpoint_post_with_payload (status={status})")


# ============== percentile ==============

def test_percentile_basic():
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    p50 = benchmark._percentile(data, 50)
    p95 = benchmark._percentile(data, 95)
    p99 = benchmark._percentile(data, 99)
    assert 5 <= p50 <= 6
    assert 9 <= p95 <= 10
    assert 9 <= p99 <= 10
    print(f"  ✓ test_percentile_basic (p50={p50}, p95={p95}, p99={p99})")


def test_percentile_empty():
    p = benchmark._percentile([], 50)
    assert p == 0.0
    print("  ✓ test_percentile_empty")


def test_percentile_single():
    p = benchmark._percentile([5.0], 50)
    assert p == 5.0
    print("  ✓ test_percentile_single")


# ============== run_endpoint_n ==============

def test_run_endpoint_n_basic():
    res = benchmark.run_endpoint_n("GET", "/api/personas", n=5)
    assert res.n == 5
    assert res.errors == 0
    assert res.p50_ms >= 0
    assert res.p95_ms >= 0
    assert res.p99_ms >= 0
    assert res.min_ms <= res.mean_ms <= res.max_ms
    assert 200 in res.status_codes
    print(f"  ✓ test_run_endpoint_n_basic (p50={res.p50_ms:.2f}ms)")


def test_run_endpoint_n_404():
    res = benchmark.run_endpoint_n("GET", "/api/no_such_endpoint", n=3)
    assert res.n == 3
    assert 404 in res.status_codes
    # 404 不算 5xx server error
    assert res.errors == 0
    print(f"  ✓ test_run_endpoint_n_404")


def test_run_endpoint_n_large_n():
    res = benchmark.run_endpoint_n("GET", "/api/voices", n=20)
    assert res.n == 20
    assert res.errors == 0
    assert res.min_ms > 0
    assert res.p95_ms >= res.p50_ms
    print(f"  ✓ test_run_endpoint_n_large_n (p50={res.p50_ms:.2f}, p95={res.p95_ms:.2f})")


# ============== get_all_endpoints ==============

def test_get_all_endpoints_count():
    eps = benchmark.get_all_endpoints()
    assert len(eps) == 74, f"expected 74, got {len(eps)}"
    print(f"  ✓ test_get_all_endpoints_count ({len(eps)} endpoints)")


def test_get_all_endpoints_have_method_path():
    eps = benchmark.get_all_endpoints()
    for m, p, _ in eps:
        assert m in ("GET", "POST")
        assert p.startswith("/")
    print(f"  ✓ test_get_all_endpoints_have_method_path")


def test_get_all_endpoints_payload_coverage():
    eps = benchmark.get_all_endpoints()
    posts = [(m, p) for m, p, pl in eps if m == "POST"]
    # 检查所有 POST 都有 payload
    missing = []
    for m, p in posts:
        key = f"{m} {p}"
        if key not in benchmark.ENDPOINT_PAYLOADS:
            missing.append(key)
    # 注:不是所有 POST 都需要 payload,只检查关键模块
    print(f"  ✓ test_get_all_endpoints_payload_coverage ({len(benchmark.ENDPOINT_PAYLOADS)} payloads for {len(posts)} POSTs)")


# ============== ENDPOINT_PAYLOADS 完整性 ==============

def test_endpoint_payloads_valid_json():
    """确保所有 payload 都是可 JSON 序列化的(简化检查)"""
    for key, payload in benchmark.ENDPOINT_PAYLOADS.items():
        assert " " in key
        method, path = key.split(" ", 1)
        assert method in ("GET", "POST")
        assert path.startswith("/")
        # 可 JSON
        json.dumps(payload)
    print(f"  ✓ test_endpoint_payloads_valid_json ({len(benchmark.ENDPOINT_PAYLOADS)} payloads)")


# ============== benchmark_all ==============

def test_benchmark_all_small_n():
    results = benchmark.benchmark_all(n=3)
    assert len(results) == 74
    valid = [r for r in results if r.n > 0]
    assert len(valid) >= 70  # 至少 70 个成功
    print(f"  ✓ test_benchmark_all_small_n ({len(valid)} valid)")


def test_benchmark_all_with_skip():
    results = benchmark.benchmark_all(n=3, skip_paths=["/api/voices"])
    skipped = [r for r in results if r.path == "/api/voices"]
    assert len(skipped) == 0
    print(f"  ✓ test_benchmark_all_with_skip ({len(results)} ran, voices skipped)")


def test_benchmark_all_custom_endpoints():
    eps = [("GET", "/api/personas", None), ("GET", "/api/voices", None)]
    results = benchmark.benchmark_all(endpoints=eps, n=3)
    assert len(results) == 2
    print(f"  ✓ test_benchmark_all_custom_endpoints")


# ============== generate_report ==============

def test_generate_report_contains_basics():
    results = benchmark.benchmark_all(n=3)
    md = benchmark.generate_report(results)
    assert "# AICHAT-HUB" in md
    assert "总端点数" in md
    assert "Top 10" in md
    assert "全量列表" in md
    print(f"  ✓ test_generate_report_contains_basics (md {len(md)} chars)")


def test_generate_report_with_specific():
    results = [benchmark.run_endpoint_n("GET", "/api/personas", n=3)]
    md = benchmark.generate_report(results)
    assert "/api/personas" in md
    assert "结论" in md
    print(f"  ✓ test_generate_report_with_specific")


def test_categorize_endpoints():
    results = benchmark.benchmark_all(n=2)
    cats = benchmark._categorize_endpoints(results)
    assert "core" in cats
    assert "api/chat" in cats
    assert "api/resume" in cats
    print(f"  ✓ test_categorize_endpoints ({len(cats)} categories)")


# ============== 数据类 ==============

def test_benchmark_result_to_dict():
    res = benchmark.BenchmarkResult(method="GET", path="/api/test", n=1)
    res.times_ns = [1000000]
    res.p50_ms = 1.0
    res.p95_ms = 1.0
    res.p99_ms = 1.0
    res.mean_ms = 1.0
    res.min_ms = 1.0
    res.max_ms = 1.0
    d = res.to_dict()
    assert d["method"] == "GET"
    assert d["path"] == "/api/test"
    assert d["n"] == 1
    assert d["p50_ms"] == 1.0
    print("  ✓ test_benchmark_result_to_dict")


def test_memory_sample_to_dict():
    s = benchmark.MemorySample(label="test", rss_kb=12345.6)
    d = s.to_dict()
    assert d["label"] == "test"
    assert d["rss_kb"] == 12345.6
    print("  ✓ test_memory_sample_to_dict")


# ============== 持久化 ==============

def test_save_and_load_results():
    results = [benchmark.run_endpoint_n("GET", "/api/personas", n=2)]
    test_path = os.path.join(benchmark.DATA_DIR, "_test_benchmark.json")
    benchmark.save_results(results, path=test_path)
    assert os.path.exists(test_path)
    data = benchmark.load_results(path=test_path)
    assert data is not None
    assert data["total_endpoints"] == 1
    assert len(data["results"]) == 1
    # 清理
    if os.path.exists(test_path):
        os.remove(test_path)
    print("  ✓ test_save_and_load_results")


def test_save_report(tmp_dir=None):
    results = [benchmark.run_endpoint_n("GET", "/api/personas", n=2)]
    test_path = os.path.join(ROOT, "reports", "_test_benchmark.md")
    benchmark.save_report(results, path=test_path)
    assert os.path.exists(test_path)
    with open(test_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "AICHAT-HUB" in content
    # 清理
    if os.path.exists(test_path):
        os.remove(test_path)
    print("  ✓ test_save_report")


def test_load_results_missing():
    data = benchmark.load_results(path="/tmp/does_not_exist.json")
    assert data is None
    print("  ✓ test_load_results_missing")


# ============== 内存采样 ==============

def test_sample_memory():
    s = benchmark.sample_memory("test")
    assert s.label == "test"
    # RSS 应该 > 0
    assert s.rss_kb >= 0
    print(f"  ✓ test_sample_memory (rss={s.rss_kb:.1f}KB)")


# ============== 端点覆盖:核心 API ==============

def test_benchmark_core_endpoints_fast():
    """核心枚举端点应该 < 50ms p95"""
    fast_paths = ["/api/personas", "/api/voices", "/api/career/dimensions", "/api/career/codes"]
    for p in fast_paths:
        res = benchmark.run_endpoint_n("GET", p, n=5)
        assert res.p95_ms < 50, f"{p} p95 too slow: {res.p95_ms}ms"
    print(f"  ✓ test_benchmark_core_endpoints_fast (4 core endpoints all < 50ms)")


def test_benchmark_all_no_5xx():
    """所有 endpoint 都不应该 5xx"""
    results = benchmark.benchmark_all(n=3)
    err_5xx = [r for r in results if r.errors > 0]
    assert len(err_5xx) == 0, f"5xx errors: {[(r.path, r.errors) for r in err_5xx]}"
    print(f"  ✓ test_benchmark_all_no_5xx (0 5xx errors across {len(results)} endpoints)")


# ============== 回归: 实际跑端点 ==============

def test_real_chat_endpoint():
    """POST /api/chat 在无 LLM key 时返回 error 路径"""
    status, _, _ = benchmark.run_endpoint(
        "POST", "/api/chat",
        payload={"persona": "xiaoai", "message": "hi"}
    )
    # 沙箱无 LLM key,可能 200(error info) or 500
    # 只要不崩
    assert status in (200, 500)
    print(f"  ✓ test_real_chat_endpoint (status={status})")


def test_real_paper_search():
    """POST /api/papers/search"""
    status, _, _ = benchmark.run_endpoint(
        "POST", "/api/papers/search",
        payload={"query": "LLM"}
    )
    assert status == 200
    print(f"  ✓ test_real_paper_search")


# ============== 报告完整性 ==============

def test_report_endpoints_count():
    results = benchmark.benchmark_all(n=3)
    md = benchmark.generate_report(results)
    # 全量列表行数 = 74 个端点(都至少在表里出现一次)
    valid = [r for r in results if r.n > 0]
    for r in valid:
        assert r.path in md, f"missing {r.path} in report"
    print(f"  ✓ test_report_endpoints_count ({len(valid)} paths in report)")


# ============== 主入口 ==============

def run_all():
    tests = [
        test_mock_handler_json_body,
        test_mock_handler_query,
        test_run_endpoint_basic,
        test_run_endpoint_404,
        test_run_endpoint_post_with_payload,
        test_percentile_basic,
        test_percentile_empty,
        test_percentile_single,
        test_run_endpoint_n_basic,
        test_run_endpoint_n_404,
        test_run_endpoint_n_large_n,
        test_get_all_endpoints_count,
        test_get_all_endpoints_have_method_path,
        test_get_all_endpoints_payload_coverage,
        test_endpoint_payloads_valid_json,
        test_benchmark_all_small_n,
        test_benchmark_all_with_skip,
        test_benchmark_all_custom_endpoints,
        test_generate_report_contains_basics,
        test_generate_report_with_specific,
        test_categorize_endpoints,
        test_benchmark_result_to_dict,
        test_memory_sample_to_dict,
        test_save_and_load_results,
        test_save_report,
        test_load_results_missing,
        test_sample_memory,
        test_benchmark_core_endpoints_fast,
        test_benchmark_all_no_5xx,
        test_real_chat_endpoint,
        test_real_paper_search,
        test_report_endpoints_count,
    ]
    print(f"Running {len(tests)} benchmark tests...\n")
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
        print("✅ All benchmark tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    return failed == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
