#!/usr/bin/env python3
"""
test_16_digital_human — aichat-hub Cycle 16 数字虚拟人模块测试
=========================================================
覆盖:
  1. 枚举(EXPRESSIONS / ACTIONS / STATES / STYLES)
  2. 数据模型(Appearance / ReactionLog / DigitalHuman)
  3. 预设角色(8 个)
  4. create_digital_human(从预设 / 自定义)
  5. 状态切换 + 表情触发 + 动作
  6. 表情自动检测(detect_expression_from_text)
  7. 内存 session 存储
  8. 渲染元数据(沙箱友好)
  9. CLI 入口
  10. 集成(与现有模块联动)
"""
import sys
import subprocess
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from digital_human import (
    EXPRESSIONS, EXPRESSION_LABELS,
    ACTIONS, ACTION_LABELS,
    STATES, STATE_LABELS,
    STYLES, STYLE_LABELS,
    PRESET_HUMANS, EXPRESSION_TRIGGERS,
    Appearance, ReactionLog, DigitalHuman,
    list_presets, get_preset,
    create_digital_human,
    save_human, get_human, list_humans,
    render_metadata,
    detect_expression_from_text,
    _HUMAN_SESSIONS,
)


# ============== 1. 枚举 ==============

def test_expressions_count():
    """6 基础表情"""
    assert len(EXPRESSIONS) == 6
    expected = {"happy", "sad", "angry", "surprised", "fearful", "neutral"}
    assert set(EXPRESSIONS) == expected
    print("✓ 6 基础表情")


def test_expression_labels():
    """表情标签"""
    for e in EXPRESSIONS:
        assert e in EXPRESSION_LABELS
        label, emoji = EXPRESSION_LABELS[e]
        assert label
        assert emoji
    print("✓ 表情标签")


def test_actions_count():
    """6 基础动作"""
    assert len(ACTIONS) == 6
    expected = {"wave", "nod", "shake_head", "bow", "point", "clap"}
    assert set(ACTIONS) == expected
    print("✓ 6 基础动作")


def test_action_labels():
    """动作标签"""
    for a in ACTIONS:
        assert a in ACTION_LABELS
        assert ACTION_LABELS[a]
    print("✓ 动作标签")


def test_states_count():
    """5 状态"""
    assert len(STATES) == 5
    expected = {"idle", "listening", "thinking", "speaking", "reacting"}
    assert set(STATES) == expected
    print("✓ 5 状态")


def test_state_labels():
    """状态标签"""
    for s in STATES:
        assert s in STATE_LABELS
    print("✓ 状态标签")


def test_styles():
    """4 风格"""
    assert len(STYLES) == 4
    for s in STYLES:
        assert s in STYLE_LABELS
    print(f"✓ {len(STYLES)} 风格")


# ============== 2. 数据模型 ==============

def test_appearance_dataclass():
    """Appearance 数据类"""
    a = Appearance(style="anime", hair_style="长发", hair_color="棕色",
                   clothing="连衣裙", color_scheme="粉色系", body_type="纤细")
    assert a.style == "anime"
    d = a.to_dict()
    assert d["style"] == "anime"
    print("✓ Appearance")


def test_appearance_auto_description():
    """外观自动描述"""
    a = Appearance(style="anime", hair_style="长发", hair_color="棕色",
                   clothing="连衣裙", color_scheme="粉色系", body_type="纤细",
                   age_appearance=20)
    desc = a.auto_description("小爱")
    assert "小爱" in desc
    assert "长发" in desc
    assert "棕色" in desc
    assert "连衣裙" in desc
    print(f"✓ 自动描述:{desc}")


def test_reaction_log():
    """ReactionLog"""
    log = ReactionLog(timestamp=time.time(), trigger="用户说谢谢", expression="happy", action="wave", note="友好")
    d = log.to_dict()
    assert d["trigger"] == "用户说谢谢"
    print("✓ ReactionLog")


def test_digital_human_creation():
    """DigitalHuman 创建"""
    h = DigitalHuman(id="DH001", name="测试", role_type="persona", role_id="custom")
    assert h.id == "DH001"
    assert h.current_state == "idle"
    assert h.current_expression == "neutral"
    print("✓ DigitalHuman 基础创建")


def test_digital_human_to_dict():
    """DigitalHuman 序列化"""
    h = DigitalHuman(id="DH001", name="测试", role_type="persona", role_id="x")
    d = h.to_dict()
    assert d["id"] == "DH001"
    assert d["current_state_label"] == "待机"
    assert d["current_expression_label"] == "中性"
    assert d["reaction_count"] == 0
    print("✓ DigitalHuman 序列化")


# ============== 3. 预设角色 ==============

def test_preset_count():
    """预设 ≥ 8 个"""
    assert len(PRESET_HUMANS) >= 8
    print(f"✓ 预设 {len(PRESET_HUMANS)} 个")


def test_preset_structure():
    """预设结构"""
    for pid, p in PRESET_HUMANS.items():
        assert "name" in p
        assert "role_type" in p
        assert "role_id" in p
        assert "gender" in p
        assert "age" in p
        assert "appearance" in p
        assert isinstance(p["appearance"], Appearance)
        assert "personality" in p
        assert "knowledge_base" in p
        assert "system_prompt" in p
    print("✓ 预设结构完整")


def test_list_presets():
    """列出预设"""
    ps = list_presets()
    assert len(ps) == len(PRESET_HUMANS)
    for p in ps:
        assert "id" in p
        assert "name" in p
    print(f"✓ 列出 {len(ps)} 预设")


def test_get_preset():
    """获取预设"""
    p = get_preset("xiaoai")
    assert p is not None
    assert p["name"] == "小爱"
    assert get_preset("nonexistent") is None
    print("✓ 获取预设")


def test_preset_cover_all_modules():
    """预设覆盖所有 cycle 模块"""
    role_types = set(p["role_type"] for p in PRESET_HUMANS.values())
    # 应有 persona + interviewer + career_guide + industry_expert + senior
    assert "persona" in role_types
    assert "interviewer" in role_types
    assert "career_guide" in role_types
    assert "industry_expert" in role_types
    assert "senior" in role_types
    print(f"✓ 预设覆盖 5 模块:{role_types}")


# ============== 4. create_digital_human ==============

def test_create_from_preset():
    """从预设创建"""
    h = create_digital_human(preset_id="xiaoai")
    assert h.name == "小爱"
    assert h.role_type == "persona"
    assert h.role_id == "xiaoai"
    assert h.appearance.style == "anime"
    assert "温柔" in h.personality
    print(f"✓ 从 xiaoai 预设创建: {h.name}")


def test_create_custom():
    """完全自定义"""
    h = create_digital_human(
        name="我的虚拟人", role_type="custom", role_id="my_001",
        custom_personality=["活泼", "幽默"],
    )
    assert h.name == "我的虚拟人"
    assert h.role_type == "custom"
    assert "活泼" in h.personality
    print("✓ 自定义创建")


def test_create_with_custom_appearance():
    """自定义外观"""
    app = Appearance(style="realistic", hair_style="长发", hair_color="金色",
                     clothing="西装", color_scheme="黑色", body_type="高挑")
    h = create_digital_human(name="MyHuman", custom_appearance=app)
    assert h.appearance.style == "realistic"
    assert h.appearance.hair_color == "金色"
    print("✓ 自定义外观")


def test_create_unknown_preset_custom():
    """未知预设 → 完全自定义"""
    h = create_digital_human(preset_id="nonexistent", name="Fallback")
    assert h.name == "Fallback"
    print("✓ 未知预设 fallback")


# ============== 5. 状态 + 表情 + 动作 ==============

def test_set_state():
    """设置状态"""
    h = DigitalHuman(id="X", name="X", role_type="p", role_id="r")
    h.set_state("listening")
    assert h.current_state == "listening"
    h.set_state("thinking")
    assert h.current_state == "thinking"
    print("✓ 设置状态")


def test_set_invalid_state_raises():
    """无效状态抛错"""
    h = DigitalHuman(id="X", name="X", role_type="p", role_id="r")
    try:
        h.set_state("invalid_state")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 无效状态抛错")


def test_react_basic():
    """触发反应"""
    h = DigitalHuman(id="X", name="X", role_type="p", role_id="r")
    log = h.react("用户答对", expression="happy", action="clap", note="鼓励")
    assert log.expression == "happy"
    assert log.action == "clap"
    assert h.current_expression == "happy"
    assert h.current_action == "clap"
    assert h.current_state == "reacting"
    assert len(h.reaction_history) == 1
    print(f"✓ 触发反应: {log.trigger} → happy + clap")


def test_react_invalid_expression_raises():
    """无效表情抛错"""
    h = DigitalHuman(id="X", name="X", role_type="p", role_id="r")
    try:
        h.react("trigger", expression="invalid_expr")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 无效表情抛错")


def test_react_invalid_action_raises():
    """无效动作抛错"""
    h = DigitalHuman(id="X", name="X", role_type="p", role_id="r")
    try:
        h.react("trigger", action="invalid_action")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 无效动作抛错")


def test_react_no_action():
    """无动作反应"""
    h = DigitalHuman(id="X", name="X", role_type="p", role_id="r")
    log = h.react("trigger", expression="neutral")
    assert log.action == ""
    print("✓ 无动作反应")


def test_react_history():
    """反应历史"""
    h = DigitalHuman(id="X", name="X", role_type="p", role_id="r")
    for i in range(5):
        h.react(f"trigger_{i}", expression="happy")
    assert len(h.reaction_history) == 5
    d = h.to_dict()
    assert d["reaction_count"] == 5
    print("✓ 反应历史")


# ============== 6. 表情自动检测 ==============

def test_detect_happy():
    """检测 happy"""
    assert detect_expression_from_text("太棒了!") == "happy"
    assert detect_expression_from_text("我通过了") == "happy"
    assert detect_expression_from_text("拿到 offer 了,赞!") == "happy"
    print("✓ 检测 happy")


def test_detect_sad():
    """检测 sad"""
    assert detect_expression_from_text("挂了") == "sad"
    assert detect_expression_from_text("没通过,很遗憾") == "sad"
    print("✓ 检测 sad")


def test_detect_surprised():
    """检测 surprised"""
    assert detect_expression_from_text("哇,真的吗?") == "surprised"
    assert detect_expression_from_text("天哪!") == "surprised"
    print("✓ 检测 surprised")


def test_detect_fearful():
    """检测 fearful"""
    assert detect_expression_from_text("好紧张,担心挂了") == "fearful"
    assert detect_expression_from_text("很焦虑") == "fearful"
    print("✓ 检测 fearful")


def test_detect_neutral_default():
    """无触发词 → neutral"""
    assert detect_expression_from_text("我今天去图书馆") == "neutral"
    assert detect_expression_from_text("hello world") == "neutral"
    assert detect_expression_from_text("") == "neutral"
    print("✓ 无触发 → neutral")


def test_detect_multiple_expressions():
    """多个表情词 → 取最高分"""
    text = "我成功了!太棒了!通过!"  # 多 happy 词
    assert detect_expression_from_text(text) == "happy"
    print("✓ 多表情取最高分")


# ============== 7. 内存存储 ==============

def test_save_and_get_human():
    """保存和获取"""
    # 清理之前的 session
    _HUMAN_SESSIONS.clear()
    h = create_digital_human(preset_id="xiaoai")
    hid = save_human(h)
    assert hid == h.id
    got = get_human(hid)
    assert got is not None
    assert got.name == "小爱"
    print(f"✓ 保存和获取: {hid}")


def test_get_nonexistent():
    """获取不存在的"""
    _HUMAN_SESSIONS.clear()
    h = get_human("NOTEXIST")
    assert h is None
    print("✓ 不存在返回 None")


def test_list_humans():
    """列出所有虚拟人"""
    _HUMAN_SESSIONS.clear()
    save_human(create_digital_human(preset_id="xiaoai"))
    save_human(create_digital_human(preset_id="dr_li"))
    save_human(create_digital_human(preset_id="xiaozhi"))
    ls = list_humans()
    assert len(ls) == 3
    print(f"✓ 列出 {len(ls)} 虚拟人")


# ============== 8. 渲染元数据 ==============

def test_render_metadata():
    """渲染元数据"""
    h = create_digital_human(preset_id="xiaoai")
    h.set_state("speaking")
    h.react("回答用户", expression="happy", action="nod")
    meta = render_metadata(h)
    assert meta["human_id"] == h.id
    assert meta["style"] == "anime"
    # react() 会把 state 设为 "reacting"
    assert meta["current_state"] == "reacting"
    assert meta["current_expression"] == "happy"
    assert meta["renderer"] == "mock"
    assert "appearance_description" in meta
    print("✓ 渲染元数据")


def test_render_metadata_sandbox_safe():
    """渲染元数据沙箱安全"""
    h = create_digital_human(preset_id="xiaoai")
    meta = render_metadata(h)
    assert "沙箱" in meta["note"] or "metadata" in meta["render_status"]
    # 不应有实际图像数据
    assert "image_data" not in meta
    assert "video_data" not in meta
    print("✓ 沙箱安全")


# ============== 9. CLI ==============

def test_cli_presets():
    """CLI:presets"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "digital_human.py"), "presets"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "xiaoai" in result.stdout
    assert "dr_li" in result.stdout
    print("✓ CLI presets")


def test_cli_expressions():
    """CLI:expressions"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "digital_human.py"), "expressions"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "happy" in result.stdout
    assert "😊" in result.stdout
    print("✓ CLI expressions")


def test_cli_actions():
    """CLI:actions"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "digital_human.py"), "actions"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "wave" in result.stdout
    assert "点头" in result.stdout
    print("✓ CLI actions")


def test_cli_states():
    """CLI:states"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "digital_human.py"), "states"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "idle" in result.stdout
    assert "待机" in result.stdout
    print("✓ CLI states")


def test_cli_create():
    """CLI:create"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "digital_human.py"), "create", "xiaoai"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["name"] == "小爱"
    print("✓ CLI create")


# ============== 10. 集成 ==============

def test_integration_xiaoai_full_flow():
    """集成:小爱完整对话流程"""
    _HUMAN_SESSIONS.clear()
    h = create_digital_human(preset_id="xiaoai")
    save_human(h)
    # 1. 用户说话 → listening
    h.set_state("listening")
    # 2. AI 生成 → thinking
    h.set_state("thinking")
    # 3. AI 输出 → speaking
    h.set_state("speaking")
    h.react("回答用户提问", expression="happy", action="nod", note="友好回应")
    # 4. 渲染元数据
    meta = render_metadata(h)
    assert meta["current_state"] == "reacting"
    assert meta["current_expression"] == "happy"
    print(f"✓ 集成:listen → think → speak → react: {h.name}")


def test_integration_interview_pressure():
    """集成:压力面状态切换"""
    h = create_digital_human(preset_id="interview_tech")
    h.set_state("speaking")
    # 压力面 → 严肃
    h.react("用户答错了", expression="angry", action="shake_head", note="质疑")
    h.set_state("reacting")
    assert h.current_expression == "angry"
    print("✓ 压力面状态切换")


def test_integration_career_guide_happy():
    """集成:职业规划师鼓励用户"""
    h = create_digital_human(preset_id="career_guide")
    text = "我通过了霍兰德测试,代码是 IAS!"
    expr = detect_expression_from_text(text)
    h.react(text, expression=expr, action="clap", note="鼓励")
    assert h.current_expression == "happy"  # "通过" 触发 happy
    print(f"✓ 职业规划师自动检测: {text} → {expr}")


def test_integration_expression_auto_chain():
    """集成:多轮对话自动检测表情"""
    h = create_digital_human(preset_id="xiaozhi")
    messages = [
        "你好",                     # neutral
        "我通过了!",                # happy
        "挂了,没进面试",            # sad
        "天哪,真的吗?",            # surprised
        "好紧张,担心",              # fearful
    ]
    expected = ["neutral", "happy", "sad", "surprised", "fearful"]
    for msg, exp in zip(messages, expected):
        e = detect_expression_from_text(msg)
        h.react(msg, expression=e)
        assert h.current_expression == exp, f"{msg} 期望 {exp} 实际 {e}"
    assert len(h.reaction_history) == 5
    print(f"✓ 多轮表情自动检测 {len(messages)} 轮")


# ============== 入口 ==============

if __name__ == "__main__":
    import time  # for ReactionLog timestamp
    test_expressions_count()
    test_expression_labels()
    test_actions_count()
    test_action_labels()
    test_states_count()
    test_state_labels()
    test_styles()
    test_appearance_dataclass()
    test_appearance_auto_description()
    test_reaction_log()
    test_digital_human_creation()
    test_digital_human_to_dict()
    test_preset_count()
    test_preset_structure()
    test_list_presets()
    test_get_preset()
    test_preset_cover_all_modules()
    test_create_from_preset()
    test_create_custom()
    test_create_with_custom_appearance()
    test_create_unknown_preset_custom()
    test_set_state()
    test_set_invalid_state_raises()
    test_react_basic()
    test_react_invalid_expression_raises()
    test_react_invalid_action_raises()
    test_react_no_action()
    test_react_history()
    test_detect_happy()
    test_detect_sad()
    test_detect_surprised()
    test_detect_fearful()
    test_detect_neutral_default()
    test_detect_multiple_expressions()
    test_save_and_get_human()
    test_get_nonexistent()
    test_list_humans()
    test_render_metadata()
    test_render_metadata_sandbox_safe()
    test_cli_presets()
    test_cli_expressions()
    test_cli_actions()
    test_cli_states()
    test_cli_create()
    test_integration_xiaoai_full_flow()
    test_integration_interview_pressure()
    test_integration_career_guide_happy()
    test_integration_expression_auto_chain()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
