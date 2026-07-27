"""
test_10_analytics — 用户行为分析测试
======================================
测试 Analytics:
  - 事件记录(record)
  - 总览(overview)
  - 消息数 / 活跃天数
  - 关系阶段分布
  - 漏斗(funnel)
  - Cohort 留存
  - 用户价值(value_per_user)
  - 综合报告
  - HTTP helper
"""
import sys
import json
import time
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from analytics import (
    Analytics, UserEvent, FunnelStep, CohortMetric,
    analytics_report,
)


TMP_ROOT = ROOT / "data" / "test_analytics_tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


def make_analytics(name: str = "default") -> Analytics:
    return Analytics(root=TMP_ROOT / name)


def test_event_record():
    """基本记录"""
    a = make_analytics("record_test")
    e = a.record("user1", "message", persona="xiaoai", detail={"tokens": 100})
    assert isinstance(e, UserEvent)
    assert e.user_id == "user1"
    assert e.event_type == "message"
    assert e.persona == "xiaoai"
    assert e.detail["tokens"] == 100
    assert len(a.events) == 1
    print("  ✓ event record")


def test_event_record_with_custom_ts():
    """自定义时间戳"""
    a = make_analytics("ts_test")
    custom_ts = time.time() - 86400 * 7  # 7 天前
    a.record("user1", "message", ts=custom_ts)
    assert a.events[0].ts == custom_ts
    print("  ✓ custom timestamp")


def test_overview_empty():
    """空 overview"""
    a = make_analytics("empty_test")
    o = a.overview()
    assert o["total_events"] == 0
    assert o["unique_users"] == 0
    print("  ✓ empty overview")


def test_overview_basic():
    """基本总览"""
    a = make_analytics("overview_test")
    base = time.time() - 86400  # 1 天前
    for i in range(5):
        a.record("user1", "message", ts=base + i * 3600)
    for i in range(3):
        a.record("user2", "message", ts=base + i * 7200)
    a.record("user1", "relationship_change", detail={"stage": "friend"})

    o = a.overview()
    assert o["total_events"] == 9
    assert o["unique_users"] == 2
    assert o["time_range"]["days"] >= 0
    assert o["events_per_user"] == 4.5
    print(f"  ✓ overview: {o['total_events']} events, {o['unique_users']} users")


def test_message_count():
    """消息数统计"""
    a = make_analytics("msg_test")
    for _ in range(5):
        a.record("user1", "message")
    for _ in range(3):
        a.record("user2", "message")
    a.record("user1", "relationship_change")  # 非 message
    cnt = a.message_count()
    assert cnt["user1"] == 5
    assert cnt["user2"] == 3
    # 单用户
    assert a.message_count("user1")["user1"] == 5
    print(f"  ✓ message count: {cnt}")


def test_active_days():
    """活跃天数"""
    a = make_analytics("days_test")
    base = time.time() - 86400 * 5
    # user1: 5 天
    for day in range(5):
        a.record("user1", "message", ts=base + day * 86400)
    # user1: 同一天多次 = 算 1 天
    a.record("user1", "message", ts=base + 0 * 86400 + 3600)
    a.record("user1", "message", ts=base + 0 * 86400 + 7200)
    # user2: 2 天
    a.record("user2", "message", ts=base + 1 * 86400)
    a.record("user2", "message", ts=base + 3 * 86400)
    days = a.active_days()
    assert days["user1"] == 5
    assert days["user2"] == 2
    print(f"  ✓ active days: {days}")


def test_persona_distribution():
    """Persona 分布"""
    a = make_analytics("persona_test")
    a.record("u1", "message", persona="xiaoai")
    a.record("u2", "message", persona="xiaoai")
    a.record("u3", "message", persona="dr_li")
    a.record("u4", "message")  # 无 persona
    d = a.persona_distribution()
    assert d["xiaoai"] == 2
    assert d["dr_li"] == 1
    print(f"  ✓ persona dist: {d}")


def test_relationship_stage_dist():
    """关系阶段分布"""
    a = make_analytics("rel_test")
    a.record("u1", "relationship_change", detail={"stage": "stranger"})
    a.record("u2", "relationship_change", detail={"stage": "stranger"})
    a.record("u3", "relationship_change", detail={"stage": "friend"})
    a.record("u4", "relationship_change", detail={"stage": "intimate"})
    d = a.relationship_stage_dist()
    assert d["stranger"] == 2
    assert d["friend"] == 1
    assert d["intimate"] == 1
    print(f"  ✓ relationship stage dist: {d}")


def test_funnel_basic():
    """基本漏斗"""
    a = make_analytics("funnel_test")
    a.record("u1", "step1")
    a.record("u2", "step1")
    a.record("u3", "step1")
    a.record("u1", "step2")
    a.record("u2", "step2")
    a.record("u1", "step3")
    funnel = a.funnel(["step1", "step2", "step3"])
    assert funnel[0].user_count == 3
    assert funnel[0].conversion_rate == 1.0
    assert funnel[1].user_count == 2
    assert funnel[1].conversion_rate == round(2/3, 4)
    assert funnel[2].user_count == 1
    assert funnel[2].conversion_rate == 0.5
    print(f"  ✓ funnel: {[(s.name, s.user_count, s.conversion_rate) for s in funnel]}")


def test_funnel_empty_step():
    """漏斗某步空"""
    a = make_analytics("funnel_empty_test")
    a.record("u1", "step1")
    a.record("u1", "step3")
    funnel = a.funnel(["step1", "step2", "step3"])
    assert funnel[1].user_count == 0
    assert funnel[1].conversion_rate == 0.0
    assert funnel[2].user_count == 1
    assert funnel[2].conversion_rate == 0.0  # 上一步为 0
    print("  ✓ funnel with empty step")


def test_funnel_single_user():
    """单用户漏斗"""
    a = make_analytics("funnel_single")
    a.record("u1", "step1")
    a.record("u1", "step2")
    funnel = a.funnel(["step1", "step2"], user_id="u1")
    assert funnel[0].user_count == 1
    assert funnel[1].user_count == 1
    assert funnel[1].conversion_rate == 1.0
    print("  ✓ single user funnel")


def test_cohort_retention():
    """Cohort 留存"""
    a = make_analytics("cohort_test")
    base = time.time() - 86400 * 10  # 10 天前
    # user1: 5 个事件,分布在 day 0, 1, 3, 7
    a.record("u1", "message", ts=base + 0)
    a.record("u1", "message", ts=base + 1*86400)
    a.record("u1", "message", ts=base + 3*86400)
    a.record("u1", "message", ts=base + 7*86400)
    a.record("u1", "message", ts=base + 7*86400 + 100)
    # user2: 仅 day 0
    a.record("u2", "message", ts=base + 0)

    cohorts = a.cohort_retention(retention_days=[1, 3, 7])
    # 同一天 cohort(可能 day 0)
    # 至少 1 个 cohort
    assert len(cohorts) >= 1
    print(f"  ✓ cohort retention: {len(cohorts)} cohorts")


def test_value_per_user():
    """用户价值"""
    a = make_analytics("value_test")
    # user1: 5 messages + 2 cost events
    for _ in range(5):
        a.record("u1", "message")
    a.record("u1", "cost", detail={"user_id": "u1", "cost_usd": 0.001})
    a.record("u1", "cost", detail={"user_id": "u1", "cost_usd": 0.002})
    # user2: 3 messages, 1 cost
    for _ in range(3):
        a.record("u2", "message")
    a.record("u2", "cost", detail={"user_id": "u2", "cost_usd": 0.0015})

    v = a.value_per_user()
    assert v["u1"]["messages"] == 5
    assert abs(v["u1"]["cost_usd"] - 0.003) < 1e-6
    assert v["u2"]["messages"] == 3
    print(f"  ✓ value: u1 msgs=5 cost=${v['u1']['cost_usd']:.4f}")


def test_report():
    """综合报告"""
    a = make_analytics("report_test")
    base = time.time() - 86400
    a.record("u1", "message", persona="xiaoai", ts=base)
    a.record("u1", "message", persona="xiaoai", ts=base + 3600)
    a.record("u2", "message", persona="dr_li", ts=base + 7200)
    a.record("u1", "relationship_change", detail={"stage": "friend"})
    a.record("u1", "cost", detail={"cost_usd": 0.001})

    r = a.report()
    assert "overview" in r
    assert "message_count" in r
    assert "active_days" in r
    assert "persona_distribution" in r
    assert "relationship_stage_dist" in r
    assert "value_per_user" in r
    print(f"  ✓ report: {len(r)} sections")


def test_serialization_roundtrip():
    """save/load 数据一致"""
    a1 = make_analytics("ser_test")
    a1.record("u1", "message", persona="xiaoai", detail={"k": "v"})
    a1.save()

    a2 = make_analytics("ser_test")
    assert len(a2.events) == 1
    assert a2.events[0].persona == "xiaoai"
    assert a2.events[0].detail["k"] == "v"
    print("  ✓ save/load roundtrip")


def test_analytics_report_from_dict():
    """从 dict 生成报告"""
    payload = {
        "events": [
            {"user_id": "u1", "event_type": "message", "persona": "xiaoai"},
            {"user_id": "u2", "event_type": "message", "persona": "dr_li"},
        ]
    }
    r = analytics_report(payload)
    assert r["overview"]["total_events"] == 2
    assert r["overview"]["unique_users"] == 2
    print(f"  ✓ analytics_report_from_dict: {r['overview']['total_events']} events")


def test_integration_relationship_events():
    """集成 relationship.py 事件"""
    sys.path.insert(0, str(SCRIPTS))
    from relationship import RelationshipEngine, Stage

    a = make_analytics("rel_integration")
    eng = RelationshipEngine("xiaoai", "demo_user", root=TMP_ROOT / "rel_int")

    # 模拟 10 次互动,触发关系升级
    for i in range(10):
        result = eng.record_interaction(f"msg {i}", "reply", emotion="happy", depth=3)
        # 记录到 analytics
        a.record("demo_user", "message", persona="xiaoai",
                detail={"tokens": 50, "delta": result["delta"]})
        if result["promoted"]:
            a.record("demo_user", "relationship_change",
                    detail={"stage": result["stage"], "level": result["new_level"]})

    o = a.overview()
    assert o["total_events"] >= 10
    rel_dist = a.relationship_stage_dist()
    assert len(rel_dist) >= 1, f"应该有关系升级,得到 {rel_dist}"
    print(f"  ✓ integration: {o['total_events']} events, stages: {list(rel_dist.keys())}")


def test_integration_cost_events():
    """集成 cost.py 事件"""
    sys.path.insert(0, str(SCRIPTS))
    from cost import CostTracker

    a = make_analytics("cost_integration")
    tracker = CostTracker(root=TMP_ROOT / "cost_int")

    for i in range(3):
        e = tracker.record("openai", "gpt-4o-mini", 1000, 500, 800, label="demo_user")
        a.record("demo_user", "cost",
                detail={"cost_usd": e.cost_usd, "user_id": "demo_user"})

    v = a.value_per_user()
    assert v["demo_user"]["cost_usd"] > 0
    print(f"  ✓ cost integration: ${v['demo_user']['cost_usd']:.6f}")


def test_clear():
    """清空"""
    a = make_analytics("clear_test")
    a.record("u1", "message")
    assert len(a.events) == 1
    a.events = []
    assert len(a.events) == 0
    print("  ✓ clear")


def test_max_events():
    """大量事件"""
    a = make_analytics("max_test")
    for i in range(1000):
        a.record(f"u{i % 10}", "message", ts=time.time())
    assert len(a.events) == 1000
    o = a.overview()
    assert o["unique_users"] == 10
    print(f"  ✓ max events: {o['total_events']} events, {o['unique_users']} users")


def cleanup():
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)


if __name__ == "__main__":
    tests = [
        test_event_record,
        test_event_record_with_custom_ts,
        test_overview_empty,
        test_overview_basic,
        test_message_count,
        test_active_days,
        test_persona_distribution,
        test_relationship_stage_dist,
        test_funnel_basic,
        test_funnel_empty_step,
        test_funnel_single_user,
        test_cohort_retention,
        test_value_per_user,
        test_report,
        test_serialization_roundtrip,
        test_analytics_report_from_dict,
        test_integration_relationship_events,
        test_integration_cost_events,
        test_clear,
        test_max_events,
    ]
    print(f"Running {len(tests)} analytics tests...\n")
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
