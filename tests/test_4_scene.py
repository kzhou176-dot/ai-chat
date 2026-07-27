"""
test_4_scene — 场景/故事系统测试
================================
测试 Scene / SceneStore / 议程触发 / 好感度事件:
  - Scene 数据结构完整性
  - 7 种场景类型
  - 议程触发(关键词匹配)
  - 好感度事件触发
  - 序列化/反序列化
  - 开场白 + to_system_prompt
  - Persona 集成
"""
import sys
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from scene import (
    Scene, SceneStore, SceneType, AgendaItem, AffectionEvent,
    BUILTIN_SCENES, seed_builtin_scenes
)


TMP_ROOT = ROOT / "data" / "test_scene_tmp"
TMP_ROOT.mkdir(parents=True, exist_ok=True)


def make_store() -> SceneStore:
    return SceneStore(root=TMP_ROOT)


def test_scene_type_enum():
    """7 种场景类型"""
    types = list(SceneType)
    assert len(types) == 7
    assert SceneType.DAILY in types
    assert SceneType.ROMANCE in types
    assert SceneType.ADVENTURE in types
    assert SceneType.FANTASY in types
    assert SceneType.SCIFI in types
    assert SceneType.HISTORICAL in types
    assert SceneType.MYSTERY in types
    print(f"  ✓ 7 scene types: {[t.value for t in types]}")


def test_agenda_item_creation():
    """AgendaItem 字段"""
    a = AgendaItem(topic="test", description="desc", trigger_keywords=["a", "b"])
    assert a.topic == "test"
    assert a.completed is False
    assert a.triggered_at is None
    print("  ✓ AgendaItem init")


def test_affection_event_creation():
    """AffectionEvent 字段"""
    e = AffectionEvent(
        name="test_event", condition="some_cond",
        affection_delta=3, script="剧情",
    )
    assert e.name == "test_event"
    assert e.affection_delta == 3
    assert e.triggered is False
    print("  ✓ AffectionEvent init")


def test_scene_to_system_prompt():
    """Scene.to_system_prompt 输出完整"""
    scene = Scene(
        id="test1",
        title="测试场景",
        scene_type=SceneType.DAILY,
        persona_name="小爱",
        description="描述",
        setting="氛围",
        opening_line="开场白",
        agenda=[AgendaItem(topic="a", description="a_desc", trigger_keywords=["x"])],
        affection_events=[
            AffectionEvent(name="e1", condition="c1", affection_delta=2, script="s1")
        ],
        tags=["tag1"],
    )
    prompt = scene.to_system_prompt()
    assert "测试场景" in prompt
    assert "daily" in prompt
    assert "tag1" in prompt
    assert "开场白" in prompt
    assert "a_desc" in prompt
    assert "e1" in prompt
    print(f"  ✓ to_system_prompt formatted ({len(prompt)} chars)")


def test_agenda_trigger_by_keyword():
    """议程关键词触发"""
    store = make_store()
    seed_builtin_scenes(store)
    # xiaoai_coffee 有 agenda: 分享近况(关键词 最近/今天/工作/学习)
    triggered = store.check_agenda("xiaoai_coffee", "最近工作好累")
    assert len(triggered) >= 1
    assert any("近况" in t.topic for t in triggered)
    print(f"  ✓ agenda trigger: 触发 {len(triggered)} 项 ({[t.topic for t in triggered]})")


def test_agenda_no_repeat_trigger():
    """同一议程不重复触发"""
    store = make_store()
    seed_builtin_scenes(store)
    t1 = store.check_agenda("xiaoai_coffee", "最近工作好累")
    t2 = store.check_agenda("xiaoai_coffee", "今天学习了 Python")
    # 第二次同议程不应再触发(已 completed)
    recent_topic = t1[0].topic if t1 else None
    if recent_topic:
        assert not any(t.topic == recent_topic for t in t2), \
            f"{recent_topic} triggered twice"
    print("  ✓ agenda no repeat trigger")


def test_agenda_no_keyword_no_trigger():
    """无关键词不触发"""
    store = make_store()
    seed_builtin_scenes(store)
    triggered = store.check_agenda("xiaoai_coffee", "你叫什么名字?")
    # 这句话不含任何议程关键词
    assert len(triggered) == 0
    print("  ✓ no keyword → no trigger")


def test_affection_event_trigger():
    """好感度事件触发"""
    store = make_store()
    seed_builtin_scenes(store)
    ev = store.check_affection_event("xiaoai_coffee", "first_nickname")
    assert ev is not None
    assert ev.name == "第一次叫出昵称"
    assert ev.affection_delta == 2
    assert ev.triggered is True
    print(f"  ✓ affection event: {ev.name} (+{ev.affection_delta})")


def test_affection_event_not_repeat():
    """事件不重复触发"""
    store = make_store()
    seed_builtin_scenes(store)
    e1 = store.check_affection_event("xiaoai_coffee", "first_nickname")
    e2 = store.check_affection_event("xiaoai_coffee", "first_nickname")
    assert e1 is not None
    assert e2 is None, "should not re-trigger"
    print("  ✓ affection event no repeat")


def test_unknown_scene_returns_empty():
    """未知 scene_id 不抛"""
    store = make_store()
    t = store.check_agenda("nonexistent", "hi")
    assert t == []
    e = store.check_affection_event("nonexistent", "any")
    assert e is None
    print("  ✓ unknown scene handled")


def test_serialization_roundtrip():
    """save → load 数据一致"""
    store1 = make_store()
    seed_builtin_scenes(store1)
    store1.save()

    store2 = make_store()
    assert len(store2.scenes) == len(BUILTIN_SCENES)
    s1 = store1.get("xiaoai_coffee")
    s2 = store2.get("xiaoai_coffee")
    assert s1.title == s2.title
    assert len(s1.agenda) == len(s2.agenda)
    assert len(s1.affection_events) == len(s2.affection_events)
    print(f"  ✓ save/load: {len(store2.scenes)} scenes")


def test_list_by_persona():
    """按虚拟人筛选场景"""
    store = make_store()
    seed_builtin_scenes(store)
    xiaoai_scenes = store.list_by_persona("小爱")
    assert len(xiaoai_scenes) >= 1
    assert all(s.persona_name == "小爱" for s in xiaoai_scenes)
    print(f"  ✓ list_by_persona('小爱'): {len(xiaoai_scenes)} 个")


def test_get_opening_line():
    """获取开场白"""
    store = make_store()
    seed_builtin_scenes(store)
    line = store.get_opening_line("xiaoai_coffee")
    assert line and "拿铁" in line
    print(f"  ✓ opening line: {line[:30]}...")


def test_builtin_scenes_complete():
    """3 个内置场景都有完整字段"""
    assert len(BUILTIN_SCENES) >= 3
    for sid, conf in BUILTIN_SCENES.items():
        for field in ("title", "scene_type", "persona_name", "description",
                      "setting", "opening_line"):
            assert field in conf, f"{sid} 缺 {field}"
    print(f"  ✓ {len(BUILTIN_SCENES)} builtin scenes complete")


def test_seed_idempotent():
    """seed 多次不重复"""
    store = make_store()
    seed_builtin_scenes(store)
    n1 = len(store.scenes)
    seed_builtin_scenes(store)
    n2 = len(store.scenes)
    assert n1 == n2, f"seed duplicated: {n1} → {n2}"
    print(f"  ✓ seed idempotent: {n1} scenes")


def test_integration_with_persona():
    """Scene + Persona 组合注入 system prompt"""
    sys.path.insert(0, str(SCRIPTS))
    from persona import PersonaStore, BUILTIN_PERSONAS

    pstore = PersonaStore(root=TMP_ROOT / "personas")
    pconf = dict(BUILTIN_PERSONAS["xiaoai"])
    pconf.pop("name", None)
    p = pstore.create_default("xiaoai", **pconf)

    sstore = SceneStore(root=TMP_ROOT / "scenes")
    seed_builtin_scenes(sstore)
    scene = sstore.get("xiaoai_coffee")

    combined = p.to_system_prompt() + "\n\n" + scene.to_system_prompt()
    assert "小爱" in combined
    assert "午后咖啡馆" in combined
    assert "拿铁" in combined
    print(f"  ✓ integration: combined prompt {len(combined)} chars")


def test_affection_event_progress():
    """场景进度(完成项 / 总项)"""
    store = make_store()
    seed_builtin_scenes(store)
    scene = store.get("xiaoai_coffee")
    total_agenda = len(scene.agenda)
    completed = 0
    for _ in range(5):
        triggered = store.check_agenda("xiaoai_coffee", "最近工作好累")
        if not triggered:
            break
        completed += 1
    assert completed <= total_agenda
    print(f"  ✓ agenda progress: {completed}/{total_agenda}")


def cleanup():
    if TMP_ROOT.exists():
        shutil.rmtree(TMP_ROOT)


if __name__ == "__main__":
    tests = [
        test_scene_type_enum,
        test_agenda_item_creation,
        test_affection_event_creation,
        test_scene_to_system_prompt,
        test_agenda_trigger_by_keyword,
        test_agenda_no_repeat_trigger,
        test_agenda_no_keyword_no_trigger,
        test_affection_event_trigger,
        test_affection_event_not_repeat,
        test_unknown_scene_returns_empty,
        test_serialization_roundtrip,
        test_list_by_persona,
        test_get_opening_line,
        test_builtin_scenes_complete,
        test_seed_idempotent,
        test_integration_with_persona,
        test_affection_event_progress,
    ]
    print(f"Running {len(tests)} scene tests...\n")
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
