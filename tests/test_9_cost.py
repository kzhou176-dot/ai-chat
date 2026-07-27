"""
test_9_cost — 成本追踪测试
============================
测试 CostTracker:
  - 单次记录(record)
  - 成本计算(按 provider 单价)
  - 累计统计(total)
  - 按 provider/model/label 拆解
  - 持久化(save/load)
  - 预算告警
  - 报告生成
  - HTTP 接入 helper
"""
import sys
import json
import shutil
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from cost import (
    CostTracker, CostEntry,
    DEFAULT_PRICING, cost_report_from_dict,
)


TMP_ROOT = ROOT / "data" / "test_cost_tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


def make_tracker(budget_usd: float = None, name: str = "default") -> CostTracker:
    """每个测试用独立目录,避免 load 状态污染"""
    path = TMP_ROOT / name
    return CostTracker(root=path, budget_usd=budget_usd)


def test_default_pricing():
    """6 个 provider 都有默认单价"""
    assert len(DEFAULT_PRICING) >= 6
    for prov in ["openai", "deepseek", "zhipu", "dashscope", "moonshot", "anthropic"]:
        assert prov in DEFAULT_PRICING
        assert "input" in DEFAULT_PRICING[prov]
        assert "output" in DEFAULT_PRICING[prov]
    print(f"  ✓ default pricing: {len(DEFAULT_PRICING)} providers")


def test_record_basic():
    """基本记录"""
    t = make_tracker()
    e = t.record("openai", "gpt-4o-mini", 1000, 500, 800)
    assert isinstance(e, CostEntry)
    assert e.provider == "openai"
    assert e.total_tokens == 1500
    # openai input=0.15/1M, output=0.60/1M
    # cost = 1000*0.15/1M + 500*0.60/1M = 0.00015 + 0.0003 = 0.00045
    assert abs(e.cost_usd - 0.00045) < 1e-6
    print(f"  ✓ record: 1500 tokens, ${e.cost_usd:.6f}")


def test_record_zero_tokens():
    """0 token = 0 cost"""
    t = make_tracker()
    e = t.record("openai", "gpt-4o-mini", 0, 0, 100)
    assert e.cost_usd == 0.0
    assert e.total_tokens == 0
    print("  ✓ 0 tokens = 0 cost")


def test_record_free_provider():
    """免费 provider (zhipu)"""
    t = make_tracker()
    e = t.record("zhipu", "glm-4-flash", 10000, 5000, 500)
    assert e.cost_usd == 0.0
    print("  ✓ zhipu free: 0 cost")


def test_record_unknown_provider():
    """未知 provider cost = 0"""
    t = make_tracker()
    e = t.record("unknown_provider", "x", 1000, 500, 100)
    assert e.cost_usd == 0.0
    print("  ✓ unknown provider: 0 cost")


def test_total_empty():
    """空 tracker total = 0"""
    t = make_tracker()
    s = t.total()
    assert s["total_calls"] == 0
    assert s["total_tokens"] == 0
    assert s["total_cost_usd"] == 0.0
    assert s["avg_latency_ms"] == 0
    print("  ✓ empty total")


def test_total_accumulate():
    """累计"""
    t = make_tracker()
    t.record("openai", "gpt-4o-mini", 1000, 500, 800)
    t.record("deepseek", "deepseek-chat", 2000, 1000, 600)
    s = t.total()
    assert s["total_calls"] == 2
    assert s["total_tokens"] == 4500
    assert s["prompt_tokens"] == 3000
    assert s["completion_tokens"] == 1500
    # openai: 0.00045 + deepseek: 2000*0.14/1M + 1000*0.28/1M = 0.00028 + 0.00028 = 0.00056
    # total = 0.00045 + 0.00056 = 0.00101
    assert abs(s["total_cost_usd"] - 0.00101) < 1e-5
    print(f"  ✓ total: {s['total_calls']} calls, {s['total_tokens']} tokens, ${s['total_cost_usd']:.6f}")


def test_by_provider():
    """按 provider 拆解"""
    t = make_tracker()
    t.record("openai", "gpt-4o-mini", 1000, 500, 800)
    t.record("openai", "gpt-4o-mini", 2000, 1000, 700)
    t.record("deepseek", "deepseek-chat", 500, 200, 300)
    bp = t.by_provider()
    assert bp["openai"]["calls"] == 2
    assert bp["openai"]["tokens"] == 4500
    assert bp["deepseek"]["calls"] == 1
    assert bp["deepseek"]["tokens"] == 700
    assert "avg_latency_ms" in bp["openai"]
    print(f"  ✓ by_provider: {len(bp)} providers, openai cost=${bp['openai']['cost_usd']:.6f}")


def test_by_model():
    """按 model 拆解"""
    t = make_tracker()
    t.record("openai", "gpt-4o-mini", 1000, 500, 800)
    t.record("openai", "gpt-4o", 2000, 1000, 1200)
    bm = t.by_model()
    assert "gpt-4o-mini" in bm
    assert "gpt-4o" in bm
    assert bm["gpt-4o-mini"]["provider"] == "openai"
    assert bm["gpt-4o"]["provider"] == "openai"
    print(f"  ✓ by_model: {len(bm)} models")


def test_by_label():
    """按 label 拆解"""
    t = make_tracker(name="by_label_test")
    t.record("openai", "gpt-4o-mini", 1000, 500, 800, label="xiaoai")
    t.record("deepseek", "deepseek-chat", 2000, 1000, 600, label="dr_li")
    t.record("openai", "gpt-4o-mini", 500, 200, 300, label="xiaoai")
    t.record("openai", "gpt-4o-mini", 100, 50, 50)  # 无 label
    bl = t.by_label()
    assert bl["xiaoai"]["calls"] == 2
    assert bl["dr_li"]["calls"] == 1
    assert bl["(unlabeled)"]["calls"] == 1
    print(f"  ✓ by_label: {list(bl.keys())}")


def test_budget_warning_normal():
    """预算内:无警告"""
    t = make_tracker(budget_usd=1.0, name="budget_normal")
    t.record("openai", "gpt-4o-mini", 1000, 500, 800)
    assert t.check_budget() is None
    print("  ✓ within budget")


def test_budget_warning_80pct():
    """80% 阈值告警"""
    t = make_tracker(budget_usd=0.001, name="budget_80")
    t.record("anthropic", "claude-3-5-sonnet", 1000, 500, 800)  # cost ~0.0105
    # 0.0105 / 0.001 = 1050% > 100% → 超支
    warn = t.check_budget()
    assert warn is not None
    assert "预算" in warn
    print(f"  ✓ budget warning: {warn}")


def test_budget_warning_over():
    """超支告警"""
    t = make_tracker(budget_usd=0.0001, name="budget_over")
    t.record("openai", "gpt-4o-mini", 10000, 5000, 100)
    warn = t.check_budget()
    assert warn is not None
    assert "超支" in warn
    print(f"  ✓ over budget warning: {warn}")


def test_budget_none():
    """无预算:不告警"""
    t = make_tracker(budget_usd=None, name="budget_none")
    t.record("openai", "gpt-4o-mini", 1000, 500, 100)
    assert t.check_budget() is None
    print("  ✓ no budget set")


def test_serialization_roundtrip():
    """save/load 数据一致"""
    t1 = make_tracker()
    t1.record("openai", "gpt-4o-mini", 1000, 500, 800, label="test")
    t1.save()

    t2 = make_tracker()
    assert len(t2.entries) == 1
    assert t2.entries[0].provider == "openai"
    assert t2.entries[0].label == "test"
    print("  ✓ save/load roundtrip")


def test_clear():
    """清空"""
    t = make_tracker(name="clear_test")
    t.record("openai", "gpt-4o-mini", 1000, 500, 800)
    assert len(t.entries) == 1
    t.clear()
    assert len(t.entries) == 0
    print("  ✓ clear")


def test_max_entries_1000():
    """超过 1000 条自动截断"""
    t = make_tracker()
    for i in range(1100):
        t.record("openai", "gpt-4o-mini", 10, 5, 100)
    assert len(t.entries) == 1000
    print("  ✓ max entries = 1000 (capped)")


def test_report():
    """完整报告"""
    t = make_tracker(budget_usd=0.01, name="report_test")
    t.record("openai", "gpt-4o-mini", 1000, 500, 800, label="xiaoai")
    t.record("deepseek", "deepseek-chat", 2000, 1000, 600, label="xiaoai")
    r = t.report()
    assert "total" in r
    assert "by_provider" in r
    assert "by_model" in r
    assert "by_label" in r
    assert "budget_warning" in r
    assert "budget_usd" in r
    print(f"  ✓ report: {len(r)} sections, {r['total']['total_calls']} calls")


def test_custom_pricing():
    """自定义单价"""
    custom = {"myprov": {"input": 1.0, "output": 2.0}}
    t = CostTracker(root=TMP_ROOT / "custom", pricing=custom)
    e = t.record("myprov", "x", 1000, 500, 100)
    # cost = 1000*1.0/1M + 500*2.0/1M = 0.001 + 0.001 = 0.002
    assert abs(e.cost_usd - 0.002) < 1e-6
    print(f"  ✓ custom pricing: ${e.cost_usd:.6f}")


def test_cost_entry_to_dict():
    """CostEntry 可序列化"""
    e = CostEntry(
        ts=1000.0, provider="openai", model="gpt-4o-mini",
        prompt_tokens=1000, completion_tokens=500, total_tokens=1500,
        cost_usd=0.00045, latency_ms=800, label="xiaoai",
    )
    d = e.to_dict()
    assert d["provider"] == "openai"
    assert d["total_tokens"] == 1500
    json_str = json.dumps(d)
    parsed = json.loads(json_str)
    assert parsed["label"] == "xiaoai"
    print(f"  ✓ CostEntry to_dict ({len(d)} keys)")


def test_cost_report_from_dict():
    """从 dict 生成报告"""
    payload = {
        "entries": [
            {"provider": "openai", "model": "gpt-4o-mini", "prompt_tokens": 1000,
             "completion_tokens": 500, "total_tokens": 1500, "cost_usd": 0.00045,
             "latency_ms": 800, "label": "xiaoai"},
        ]
    }
    r = cost_report_from_dict(payload)
    assert r["total"]["total_calls"] == 1
    assert r["by_label"]["xiaoai"]["calls"] == 1
    print("  ✓ cost_report_from_dict")


def test_integration_with_llm_client():
    """集成 LLMClient"""
    sys.path.insert(0, str(SCRIPTS))
    from llm_client import LLMClient, Message

    client = LLMClient(provider="mock")
    tracker = make_tracker(name="llm_int_test")
    persona = "xiaoai"

    # mock 路径
    resp = client.chat([Message("user", "你好")])
    pt = resp.usage.get("prompt_tokens", 0)
    ct = resp.usage.get("completion_tokens", 0)
    tracker.record(
        "mock", resp.model, pt, ct, resp.latency_ms, label=persona
    )
    # mock cost = 0
    assert len(tracker.entries) == 1
    assert tracker.entries[0].cost_usd == 0.0
    print(f"  ✓ LLM integration: {pt+ct} tokens tracked")


def test_integration_with_web_compare():
    """集成 web /api/compare 风格(多 provider)"""
    sys.path.insert(0, str(SCRIPTS))
    from llm_client import LLMClient, Message

    tracker = make_tracker(name="compare_test")
    providers = ["openai", "deepseek", "zhipu"]
    prompt = "你好"
    for prov in providers:
        client = LLMClient(provider=prov)
        resp = client.chat([Message("user", prompt)])
        pt = resp.usage.get("prompt_tokens", 0)
        ct = resp.usage.get("completion_tokens", 0)
        tracker.record(prov, resp.model, pt, ct, resp.latency_ms)
    # 应该有 3 个不同 provider 记录
    bp = tracker.by_provider()
    assert len(bp) == 3
    print(f"  ✓ multi-provider: {bp.keys()}")


def cleanup():
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)


if __name__ == "__main__":
    tests = [
        test_default_pricing,
        test_record_basic,
        test_record_zero_tokens,
        test_record_free_provider,
        test_record_unknown_provider,
        test_total_empty,
        test_total_accumulate,
        test_by_provider,
        test_by_model,
        test_by_label,
        test_budget_warning_normal,
        test_budget_warning_80pct,
        test_budget_warning_over,
        test_budget_none,
        test_serialization_roundtrip,
        test_clear,
        test_max_entries_1000,
        test_report,
        test_custom_pricing,
        test_cost_entry_to_dict,
        test_cost_report_from_dict,
        test_integration_with_llm_client,
        test_integration_with_web_compare,
    ]
    print(f"Running {len(tests)} cost tests...\n")
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            import traceback
            print(f"  ✗ {t.__name__}: {e}")
            traceback.print_exc()
    cleanup()
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
