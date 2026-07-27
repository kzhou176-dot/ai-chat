"""
test_2_memory — 长期记忆模块测试
================================
测试 MemoryStore 的:
  - 写入(fact/episode)
  - 检索(关键词匹配 + 时间衰减)
  - 去重(重复 fact 不重复加)
  - 序列化/反序列化
  - 与 Persona 集成(生成 system prompt 上下文)
"""
import sys
import json
import time
import tempfile
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from memory import (
    MemoryStore, Episode, Fact, RecallResult, tokenize
)


# 每个 test 用独立 tmp 目录
TMP_ROOT = ROOT / "data" / "test_memory_tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


def make_store(name: str = "test_persona") -> MemoryStore:
    """创建一个使用 tmp 目录的 store"""
    return MemoryStore(persona_name=name, root=TMP_ROOT)


def test_tokenize_chinese():
    """中文 2-gram 分词"""
    toks = tokenize("我喜欢喝咖啡")
    # 期望:我喜 喜欢 欢喝 喝咖 咖啡
    assert "喜欢" in toks
    assert "咖啡" in toks
    # 停用词不在内
    assert "我的" not in toks and "的" not in toks
    print(f"  ✓ tokenize zh: {toks}")


def test_tokenize_english():
    """英文分词"""
    toks = tokenize("I love drinking coffee in the morning")
    assert "love" in toks
    assert "drinking" in toks
    assert "coffee" in toks
    # 停用词不在内
    assert "the" not in toks
    print(f"  ✓ tokenize en: {toks}")


def test_add_fact_dedup():
    """重复 fact 不重复加,confidence 取最高"""
    s = make_store("dedup_test")
    s.add_fact("用户叫小李", confidence=0.8)
    s.add_fact("用户叫小李", confidence=0.95)
    s.add_fact("用户叫小李", confidence=0.7)
    assert len(s.facts) == 1, f"expected 1 fact, got {len(s.facts)}"
    assert s.facts[0].confidence == 0.95, "confidence should be max"
    print("  ✓ fact dedup + max confidence")


def test_add_episode_importance_clamp():
    """importance 必须在 1-10"""
    s = make_store("imp_test")
    e1 = s.add_episode("test 1", importance=15)  # 上限
    e2 = s.add_episode("test 2", importance=0)   # 下限
    assert e1.importance == 10
    assert e2.importance == 1
    print("  ✓ importance clamp 1-10")


def test_recall_keyword_match():
    """关键词能匹配到对应 fact/episode"""
    s = make_store("recall_test")
    s.add_fact("用户喜欢喝美式咖啡", confidence=0.9, tags=["饮食", "偏好"])
    s.add_fact("用户是程序员", confidence=0.8, tags=["职业"])
    s.add_episode("用户说周末想去爬山", importance=5, tags=["周末", "运动"])

    r = s.recall("咖啡")
    assert len(r.facts) > 0
    fact_texts = [f.text for f, _ in r.facts]
    assert any("咖啡" in t for t in fact_texts)
    print(f"  ✓ recall('咖啡') → {len(r.facts)} facts, top: {r.facts[0][0].text[:30]}")


def test_recall_no_match_returns_empty():
    """无匹配时返回空(不抛)"""
    s = make_store("nomatch_test")
    s.add_fact("用户喜欢猫", confidence=0.9)
    r = s.recall("量子计算")
    assert isinstance(r, RecallResult)
    assert len(r.facts) == 0
    assert len(r.episodes) == 0
    print("  ✓ recall no-match returns empty")


def test_recall_time_decay():
    """时间衰减:15 天前的比 1 天前的分数低"""
    s = make_store("decay_test")
    now = time.time()
    # 1 天前
    s.add_episode("用户喜欢打篮球", importance=5, tags=["运动"])
    s.episodes[-1].ts = now - 86400
    # 15 天前
    s.add_episode("用户喜欢打篮球", importance=5, tags=["运动"])
    s.episodes[-1].ts = now - 15 * 86400

    r = s.recall("篮球", now=now)
    assert len(r.episodes) == 2, f"expected 2, got {len(r.episodes)}"
    # 1 天前应排第一
    assert r.episodes[0][0].ts > r.episodes[1][0].ts
    assert r.episodes[0][1] > r.episodes[1][1]
    print(f"  ✓ time decay: fresh={r.episodes[0][1]:.3f} > old={r.episodes[1][1]:.3f}")


def test_serialization_roundtrip():
    """save → load 数据一致"""
    s1 = make_store("ser_test")
    s1.add_fact("用户养了一只猫", confidence=0.9)
    s1.add_episode("用户说猫叫小白", importance=6, emotion="happy")
    s1.save()

    s2 = make_store("ser_test")
    assert len(s2.facts) == 1
    assert len(s2.episodes) == 1
    assert s2.facts[0].text == "用户养了一只猫"
    assert s2.episodes[0].summary == "用户说猫叫小白"
    print("  ✓ save/load roundtrip")


def test_to_context_format():
    """RecallResult.to_context() 输出可读格式"""
    s = make_store("ctx_test")
    s.add_fact("用户是设计师", confidence=0.9)
    s.add_episode("用户分享了设计灵感", importance=6)
    r = s.recall("设计")
    ctx = r.to_context()
    assert "你记住的关于用户的事实" in ctx or "事实" in ctx
    assert "用户是设计师" in ctx
    print(f"  ✓ to_context() formatted ({len(ctx)} chars)")


def test_stats():
    """stats 输出完整统计"""
    s = make_store("stats_test")
    s.add_fact("a", 0.5)
    s.add_fact("b", 0.7)
    s.add_episode("e1", importance=5)
    st = s.stats()
    assert st["facts"] == 2
    assert st["episodes"] == 1
    assert 0 < st["avg_importance"] <= 10
    print(f"  ✓ stats: {st}")


def test_integration_with_persona():
    """memory 可以为 Persona 提供 system_prompt 上下文"""
    sys.path.insert(0, str(SCRIPTS))
    from persona import Persona, PersonaStore, BUILTIN_PERSONAS

    # 准备小爱 + memory
    pstore = PersonaStore(root=TMP_ROOT / "personas")
    pconf = dict(BUILTIN_PERSONAS["xiaoai"])  # copy
    pconf.pop("name", None)  # 避免与 create_default(name=...) 冲突
    p = pstore.create_default("xiaoai", **pconf)
    m = MemoryStore("xiaoai", root=TMP_ROOT / "mem")
    m.add_fact("用户说今天心情不好", confidence=0.9, tags=["情绪"])
    m.add_episode("用户说工作压力大", importance=7, emotion="sad")
    m.save()

    # recall 并注入 system prompt
    r = m.recall("心情")
    ctx = r.to_context()

    # 原始 system prompt
    base_prompt = p.to_system_prompt()
    # 组合
    full_prompt = base_prompt + "\n\n" + ctx

    assert "心情" in full_prompt
    assert "小爱" in full_prompt
    print(f"  ✓ integration: prompt len {len(full_prompt)} chars")


def test_empty_query():
    """空 query 不抛"""
    s = make_store("empty_test")
    s.add_fact("a")
    r = s.recall("")
    assert isinstance(r, RecallResult)
    print("  ✓ empty query handled")


def test_episode_pruning():
    """超过 200 个 episode 时按重要度剪枝"""
    s = make_store("prune_test")
    # 加 250 个,重要度随机
    import random
    random.seed(42)
    for i in range(250):
        s.add_episode(f"event {i}", importance=random.randint(1, 10))
    assert len(s.episodes) <= 200, f"expected <=200, got {len(s.episodes)}"
    # 留下的应该都是重要度较高的
    avg = sum(e.importance for e in s.episodes) / len(s.episodes)
    assert avg >= 5, f"avg importance should be >= 5, got {avg:.1f}"
    print(f"  ✓ pruning: {len(s.episodes)} kept, avg imp={avg:.1f}")


def cleanup():
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)


if __name__ == "__main__":
    tests = [
        test_tokenize_chinese,
        test_tokenize_english,
        test_add_fact_dedup,
        test_add_episode_importance_clamp,
        test_recall_keyword_match,
        test_recall_no_match_returns_empty,
        test_recall_time_decay,
        test_serialization_roundtrip,
        test_to_context_format,
        test_stats,
        test_integration_with_persona,
        test_empty_query,
        test_episode_pruning,
    ]
    print(f"Running {len(tests)} memory tests...\n")
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
