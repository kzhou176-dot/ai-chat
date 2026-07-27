"""
test_3_relationship — 关系阶段模块测试
=====================================
测试 RelationshipEngine 的:
  - 阶段映射(level 0-30 → 4 阶段)
  - 互动打分(正向/负向)
  - 阶段晋升触发
  - 称呼/语气变化
  - 持久化
  - 边界条件
"""
import sys
import json
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from relationship import (
    RelationshipEngine, Relationship, Stage, STAGE_META, Interaction
)


TMP_ROOT = ROOT / "data" / "test_rel_tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


def make_engine(persona: str = "test_p", user: str = "test_u") -> RelationshipEngine:
    return RelationshipEngine(persona, user, root=TMP_ROOT)


def test_stage_mapping():
    """level → 阶段映射"""
    assert Stage.from_int(0) == Stage.STRANGER
    assert Stage.from_int(4) == Stage.STRANGER
    assert Stage.from_int(5) == Stage.ACQUAINTANCE
    assert Stage.from_int(14) == Stage.ACQUAINTANCE
    assert Stage.from_int(15) == Stage.FRIEND
    assert Stage.from_int(24) == Stage.FRIEND
    assert Stage.from_int(25) == Stage.INTIMATE
    assert Stage.from_int(30) == Stage.INTIMATE
    print("  ✓ level → stage mapping (4 stages)")


def test_stage_meta_completeness():
    """4 阶段都有完整元数据"""
    for stage in Stage:
        m = STAGE_META[stage]
        assert "label_zh" in m
        assert "address" in m
        assert "tone" in m
        assert "memory_threshold" in m
        assert "unlocked" in m
        assert "color" in m
        assert "level_range" in m
    print("  ✓ all 4 stages have full meta")


def test_initial_state():
    """新建关系是陌生人"""
    e = make_engine("init_test", "u1")
    assert e.rel.level == 0
    assert e.rel.stage == Stage.STRANGER
    assert e.rel.total_messages == 0
    assert e.rel.meta["address"] == "您"
    print("  ✓ initial state is STRANGER")


def test_positive_interaction_increases_level():
    """积极互动 +level"""
    e = make_engine("pos_test", "u1")
    result = e.record_interaction("hi", "hi", emotion="happy", depth=2)
    assert result["delta"] > 0
    assert e.rel.level > 0
    print(f"  ✓ positive: +{result['delta']} → level {e.rel.level}")


def test_negative_interaction_decreases_level():
    """负向互动 -level"""
    e = make_engine("neg_test", "u1")
    e.rel.level = 10  # 给个初始值,避免边界
    result = e.record_interaction("滚", "?", emotion="angry", depth=1)
    assert result["delta"] < 0
    print(f"  ✓ negative: {result['delta']} → level {e.rel.level}")


def test_level_clamp_0_30():
    """level 0-30 clamp"""
    e = make_engine("clamp_test", "u1")
    # 负数不能低于 0
    e.rel.level = 0
    e.record_interaction("滚", "?", emotion="angry", depth=1)
    assert e.rel.level >= 0, f"level went negative: {e.rel.level}"
    # 高于 30 不能超
    e.rel.level = 30
    e.record_interaction("love you", "❤️", emotion="loving", depth=5)
    assert e.rel.level <= 30, f"level over 30: {e.rel.level}"
    print(f"  ✓ level clamp 0-30 (now: {e.rel.level})")


def test_stage_promotion():
    """深度互动触发阶段晋升"""
    e = make_engine("promo_test", "u1")
    assert e.rel.stage == Stage.STRANGER

    # 6 次友好对话 → 应进入 ACQUAINTANCE (level ~6)
    # 每次 depth=2 emotion=happy: 0.1 + 0.3 + 0.2 = 0.6
    # 6 次 = 3.6 不到 5?再 4 次 = 6.0
    for i in range(10):
        e.record_interaction(f"hi {i}", "hi", emotion="happy", depth=2)
    assert e.rel.stage == Stage.ACQUAINTANCE, f"expected ACQUAINTANCE, got {e.rel.stage} (level={e.rel.level})"

    # 再来 20 次 → FRIEND
    # 每次 0.6,20 次 = 12,加上已有 6 = 18 ≥ 15
    for i in range(20):
        e.record_interaction(f"miss u {i}", "me too", emotion="happy", depth=2)
    assert e.rel.stage == Stage.FRIEND, f"expected FRIEND, got {e.rel.stage} (level={e.rel.level})"

    # 再来 30 次深度 → INTIMATE
    # depth=5 emotion=loving: 0.1 + 1.2 + 0.5 = 1.8
    # 30 次 = 54,加 18 = 72 → cap 30
    for i in range(30):
        e.record_interaction(f"future {i}", "yes", emotion="loving", depth=5)
    assert e.rel.stage == Stage.INTIMATE, f"expected INTIMATE, got {e.rel.stage} (level={e.rel.level})"
    print(f"  ✓ stage promotion: stranger → acquaintance → friend → intimate")


def test_promotion_returns_promoted_flag():
    """record_interaction 返回 promoted 标志"""
    e = make_engine("flag_test", "u1")
    # 第 1 次肯定不晋升
    r = e.record_interaction("hi", "hi", emotion="happy", depth=1)
    # 累计到 5 应该晋升
    promoted_count = 0
    for i in range(50):
        r = e.record_interaction(f"msg {i}", f"reply {i}", emotion="happy", depth=2)
        if r["promoted"]:
            promoted_count += 1
    # 至少晋升 1 次(陌生人→熟人→朋友→亲密)
    assert promoted_count >= 1
    print(f"  ✓ promoted flag triggered {promoted_count} times in 50 interactions")


def test_to_system_prompt():
    """system_prompt 包含关系信息"""
    e = make_engine("ctx_test", "u1")
    e.rel.level = 18  # FRIEND
    e.set_nickname("小宝")
    e.add_special_moment("一起看了樱花")
    prompt = e.to_system_prompt()
    assert "朋友" in prompt
    assert "你" in prompt  # 朋友用"你"不是"您"
    assert "小宝" in prompt
    assert "樱花" in prompt
    assert "18/30" in prompt
    print(f"  ✓ system_prompt formatted (len={len(prompt)})")


def test_address_changes_by_stage():
    """不同阶段称呼不同"""
    e = make_engine("addr_test", "u1")
    e.rel.level = 2  # STRANGER
    assert e.rel.meta["address"] == "您"
    e.rel.level = 20  # FRIEND
    assert e.rel.meta["address"] == "你"
    e.rel.level = 28  # INTIMATE
    assert "亲爱的" in e.rel.meta["address"] or "宝贝" in e.rel.meta["address"]
    print("  ✓ address changes by stage: 您 → 你 → 亲爱的")


def test_memory_threshold_by_stage():
    """亲密阶段记忆阈值降低(能 recall 更多)"""
    e = make_engine("mem_test", "u1")
    e.rel.level = 2
    stranger_th = e.rel.meta["memory_threshold"]
    e.rel.level = 28
    intimate_th = e.rel.meta["memory_threshold"]
    assert intimate_th < stranger_th, \
        f"intimate threshold should be lower than stranger ({intimate_th} vs {stranger_th})"
    print(f"  ✓ memory threshold: stranger={stranger_th} > intimate={intimate_th}")


def test_serialization_roundtrip():
    """save → load 数据一致"""
    e1 = make_engine("ser_test", "u1")
    e1.record_interaction("hi", "hello", emotion="happy", depth=2)
    e1.record_interaction("miss u", "me too", emotion="loving", depth=4)
    e1.set_nickname("宝贝")
    e1.save()

    e2 = make_engine("ser_test", "u1")
    assert e2.rel.total_messages == 2
    assert e2.rel.nickname_given == "宝贝"
    assert e2.rel.positive_emotions == 2
    print(f"  ✓ save/load: level={e2.rel.level}, stage={e2.rel.stage.value}")


def test_special_moments_dedupe():
    """special_moments 去重 + 限制 10 个"""
    e = make_engine("dup_test", "u1")
    e.add_special_moment("一起看了樱花")
    e.add_special_moment("一起看了樱花")  # 重复
    assert len(e.rel.special_moments) == 1
    for i in range(15):
        e.add_special_moment(f"moment {i}")
    assert len(e.rel.special_moments) <= 10
    print(f"  ✓ special_moments dedup + cap 10")


def test_stats():
    """stats 输出完整"""
    e = make_engine("stats_test", "u1")
    e.rel.level = 16
    e.record_interaction("a", "b", emotion="loving", depth=5)
    e.record_interaction("c", "d", emotion="happy", depth=3)
    s = e.stats()
    # level 在 2 次互动后应该 >= 16 (因为 +0.1 + 1.2 + 0.5 = 1.8 / 次)
    assert s["level"] >= 16
    assert s["stage"] in ("friend", "intimate")  # 16 起步,可能到 20
    assert s["total_messages"] == 2
    assert s["deep_conversations"] == 2  # depth >= 3
    assert s["positive_emotions"] == 2
    print(f"  ✓ stats: level={s['level']}, stage={s['stage']}")


def test_empty_interaction():
    """空消息也接受(不抛)"""
    e = make_engine("empty_test", "u1")
    r = e.record_interaction("", "", emotion="neutral", depth=1)
    assert "delta" in r
    print("  ✓ empty interaction handled")


def test_progress_pct():
    """阶段内进度 0-100"""
    e = make_engine("prog_test", "u1")
    e.rel.level = 5  # ACQUAINTANCE 起点
    assert e.rel.progress_pct == 0.0
    e.rel.level = 10  # 中点
    assert 40 < e.rel.progress_pct < 60
    e.rel.level = 14  # 接近末点(15 已是 FRIEND 起点)
    assert e.rel.progress_pct >= 90.0
    print(f"  ✓ progress_pct at 10/15 = {e.rel.progress_pct:.0f}%")


def test_integration_with_persona():
    """relationship 可以与 Persona 联动"""
    sys.path.insert(0, str(SCRIPTS))
    from persona import PersonaStore, BUILTIN_PERSONAS

    pstore = PersonaStore(root=TMP_ROOT / "personas")
    pconf = dict(BUILTIN_PERSONAS["xiaoai"])
    pconf.pop("name", None)
    p = pstore.create_default("xiaoai", **pconf)

    eng = RelationshipEngine("xiaoai", "demo_user", root=TMP_ROOT / "rel")
    for i in range(20):
        eng.record_interaction(f"love u {i}", "❤️", emotion="loving", depth=4)
    eng.set_nickname("宝")

    base_prompt = p.to_system_prompt()
    rel_prompt = eng.to_system_prompt()
    combined = base_prompt + "\n\n" + rel_prompt

    assert "小爱" in combined
    assert "关系" in combined or "亲密" in combined or "熟人" in combined or "朋友" in combined
    assert "宝" in combined
    print(f"  ✓ integration: combined prompt {len(combined)} chars")


def cleanup():
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)


if __name__ == "__main__":
    tests = [
        test_stage_mapping,
        test_stage_meta_completeness,
        test_initial_state,
        test_positive_interaction_increases_level,
        test_negative_interaction_decreases_level,
        test_level_clamp_0_30,
        test_stage_promotion,
        test_promotion_returns_promoted_flag,
        test_to_system_prompt,
        test_address_changes_by_stage,
        test_memory_threshold_by_stage,
        test_serialization_roundtrip,
        test_special_moments_dedupe,
        test_stats,
        test_empty_interaction,
        test_progress_pct,
        test_integration_with_persona,
    ]
    print(f"Running {len(tests)} relationship tests...\n")
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
