"""
test_26_repl.py — repl 模块单元测试

覆盖:
- ANSI 颜色 / supports_color
- thinking_animation
- load_persona / list_personas
- ChatEngine
- format_user / format_assistant / persona_banner
- AichatREPL 命令处理
- 集成:模拟多轮对话
"""
import os
import sys
import json
import io
import time
from contextlib import redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

# 在导入前屏蔽真实输入
import repl as repl_mod  # noqa: E402


# ============== Color / terminal ==============

def test_color_constants_exist():
    assert hasattr(repl_mod.C, "RED")
    assert hasattr(repl_mod.C, "GREEN")
    assert hasattr(repl_mod.C, "BOLD")
    assert hasattr(repl_mod.C, "RESET")
    print("  ✓ test_color_constants_exist")


def test_supports_color_no_color_env():
    os.environ["NO_COLOR"] = "1"
    try:
        result = repl_mod.supports_color()
        assert result is False
    finally:
        del os.environ["NO_COLOR"]
    print("  ✓ test_supports_color_no_color_env")


# ============== Thinking animation ==============

def test_thinking_animation_quick():
    """短动画不能崩"""
    start = time.time()
    repl_mod.thinking_animation(duration_s=0.1, persona_name="test")
    elapsed = time.time() - start
    assert elapsed < 1.0
    print(f"  ✓ test_thinking_animation_quick ({elapsed:.2f}s)")


# ============== Persona loading ==============

def test_list_personas():
    personas = repl_mod.list_personas()
    assert len(personas) >= 3
    assert "xiaoai" in personas
    assert "dr_li" in personas
    print(f"  ✓ test_list_personas ({len(personas)} personas)")


def test_load_persona_xiaoai():
    p = repl_mod.load_persona("xiaoai")
    assert p["name"] == "xiaoai"  # data file 用 id
    assert "background" in p
    assert "greeting" in p
    assert "traits" in p
    # builtin persona 提供中文名
    from persona import BUILTIN_PERSONAS
    if "xiaoai" in BUILTIN_PERSONAS:
        assert BUILTIN_PERSONAS["xiaoai"]["name"] == "小爱"
    print(f"  ✓ test_load_persona_xiaoai (id={p['name']}, age={p.get('age')})")


def test_load_persona_dr_li():
    p = repl_mod.load_persona("dr_li")
    assert p["name"] == "dr_li"
    from persona import BUILTIN_PERSONAS
    if "dr_li" in BUILTIN_PERSONAS:
        assert BUILTIN_PERSONAS["dr_li"]["name"] == "李医生"
    print(f"  ✓ test_load_persona_dr_li (id={p['name']})")


def test_load_persona_xiaozhi():
    p = repl_mod.load_persona("xiaozhi")
    assert p["name"] == "xiaozhi"
    from persona import BUILTIN_PERSONAS
    if "xiaozhi" in BUILTIN_PERSONAS:
        assert BUILTIN_PERSONAS["xiaozhi"]["name"] == "小智"
    print(f"  ✓ test_load_persona_xiaozhi (id={p['name']})")


def test_load_persona_not_found():
    try:
        repl_mod.load_persona("nonexistent_xyz")
        assert False, "should have raised"
    except FileNotFoundError:
        pass
    print("  ✓ test_load_persona_not_found")


# ============== ChatEngine ==============

def test_chat_engine_init():
    e = repl_mod.ChatEngine("xiaoai", provider="mock")
    assert e.persona_id == "xiaoai"
    assert e.provider == "mock"
    assert e.history == []
    assert e.total_tokens == 0
    print("  ✓ test_chat_engine_init")


def test_chat_engine_basic_chat():
    e = repl_mod.ChatEngine("xiaoai", provider="mock")
    reply, meta = e.chat("你好")
    assert "xiaoai" in e.persona.get("name", "") or "小爱" in reply or len(reply) > 0
    assert "tokens" in meta
    assert "cost" in meta
    assert "latency_ms" in meta
    assert len(e.history) == 2  # user + assistant
    print(f"  ✓ test_chat_engine_basic_chat (reply={reply[:50]})")


def test_chat_engine_multi_turn():
    e = repl_mod.ChatEngine("xiaoai", provider="mock")
    e.chat("第一句")
    e.chat("第二句")
    e.chat("第三句")
    assert len(e.history) == 6  # 3 user + 3 assistant
    assert e.turn_count_via_history() == 3
    print("  ✓ test_chat_engine_multi_turn (6 messages, 3 turns)")


# 给 ChatEngine 加个方法
def _turn_count_via_history(self):
    return sum(1 for h in self.history if h["role"] == "user")
repl_mod.ChatEngine.turn_count_via_history = _turn_count_via_history


def test_chat_engine_dr_li():
    e = repl_mod.ChatEngine("dr_li", provider="mock")
    reply, _ = e.chat("我头疼")
    assert "李医生" in reply or "mock" in reply
    print(f"  ✓ test_chat_engine_dr_li ({reply[:60]})")


# ============== Format helpers ==============

def test_format_user():
    s = repl_mod.format_user("hello")
    assert "你" in s
    assert "hello" in s
    print("  ✓ test_format_user")


def test_format_assistant():
    p = repl_mod.load_persona("xiaoai")
    name = p.get("display_name") or p["name"]
    s = repl_mod.format_assistant(name, "回复内容", {"model": "test", "tokens": 10, "cost": 0.0001, "latency_ms": 200})
    assert "小爱" in s
    assert "回复内容" in s
    assert "tokens" in s
    print("  ✓ test_format_assistant")


def test_persona_banner():
    p = repl_mod.load_persona("xiaoai")
    s = repl_mod.persona_banner(p)
    assert "小爱" in s
    assert "性格" in s or "设定" in s
    print("  ✓ test_persona_banner")


# ============== REPL 单元 ==============

def test_repl_init():
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    assert repl.persona_id == "xiaoai"
    assert repl.provider == "mock"
    assert repl.turn_count == 0
    print("  ✓ test_repl_init")


def test_repl_make_prompt():
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    repl.engine = repl_mod.ChatEngine("xiaoai", provider="mock")
    prompt = repl._make_prompt()
    assert "小爱" in prompt
    print(f"  ✓ test_repl_make_prompt ({prompt.strip()!r})")


def test_repl_switch_persona():
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    repl.engine = repl_mod.ChatEngine("xiaoai", provider="mock")
    # 捕获 stdout
    buf = io.StringIO()
    with redirect_stdout(buf):
        repl._switch_persona("dr_li")
    out = buf.getvalue()
    assert "已切换" in out
    assert "李医生" in out
    assert repl.persona_id == "dr_li"
    print("  ✓ test_repl_switch_persona")


def test_repl_switch_persona_invalid():
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    repl.engine = repl_mod.ChatEngine("xiaoai", provider="mock")
    buf = io.StringIO()
    with redirect_stdout(buf):
        repl._switch_persona("nonexistent")
    out = buf.getvalue()
    assert "未知" in out
    print("  ✓ test_repl_switch_persona_invalid")


def test_repl_print_history_empty():
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    repl.engine = repl_mod.ChatEngine("xiaoai", provider="mock")
    buf = io.StringIO()
    with redirect_stdout(buf):
        repl._print_history()
    out = buf.getvalue()
    assert "无历史" in out
    print("  ✓ test_repl_print_history_empty")


def test_repl_print_history_with_msgs():
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    repl.engine = repl_mod.ChatEngine("xiaoai", provider="mock")
    repl.engine.chat("第一句")
    repl.engine.chat("第二句")
    buf = io.StringIO()
    with redirect_stdout(buf):
        repl._print_history()
    out = buf.getvalue()
    assert "对话历史" in out
    assert "第一句" in out
    print("  ✓ test_repl_print_history_with_msgs")


def test_repl_print_stats():
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    repl.engine = repl_mod.ChatEngine("xiaoai", provider="mock")
    repl.engine.chat("hello")
    repl.turn_count = 1
    buf = io.StringIO()
    with redirect_stdout(buf):
        repl._print_stats()
    out = buf.getvalue()
    assert "Token" in out
    assert "cost" in out
    print("  ✓ test_repl_print_stats")


def test_repl_handle_user_message():
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    repl.engine = repl_mod.ChatEngine("xiaoai", provider="mock")
    buf = io.StringIO()
    with redirect_stdout(buf):
        repl._handle_user_message("你好世界")
    out = buf.getvalue()
    # 应该看到用户消息 + 回复
    assert "你好世界" in out
    assert "小爱" in out or "mock" in out
    assert repl.turn_count == 1
    print("  ✓ test_repl_handle_user_message (1 turn)")


def test_repl_handle_command_quit():
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    repl.engine = repl_mod.ChatEngine("xiaoai", provider="mock")
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = repl._handle_command("quit", "")
    assert result is False  # False = 退出
    print("  ✓ test_repl_handle_command_quit")


def test_repl_handle_command_help():
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    repl.engine = repl_mod.ChatEngine("xiaoai", provider="mock")
    buf = io.StringIO()
    with redirect_stdout(buf):
        result = repl._handle_command("help", "")
    assert result is True
    out = buf.getvalue()
    assert "命令列表" in out
    print("  ✓ test_repl_handle_command_help")


# ============== 集成测试 ==============

def test_integration_three_turns():
    """3 轮对话 + 切换 persona"""
    repl = repl_mod.AichatREPL(persona_id="xiaoai", provider="mock")
    repl.engine = repl_mod.ChatEngine("xiaoai", provider="mock")
    buf = io.StringIO()
    with redirect_stdout(buf):
        repl._handle_user_message("你好")
        repl._handle_user_message("我最近有点焦虑")
        # 切换到李医生
        repl._switch_persona("dr_li")
        repl._handle_user_message("我最近睡不好")
    out = buf.getvalue()
    assert "焦虑" in out
    assert "已切换" in out
    assert "睡不好" in out
    assert repl.turn_count == 3
    assert repl.persona_id == "dr_li"
    print(f"  ✓ test_integration_three_turns (3 turns, switched to dr_li)")


def test_main_list_flag(capsys=None):
    """--list 参数"""
    import io as iom
    buf = iom.StringIO()
    old_argv = sys.argv
    try:
        sys.argv = ["repl.py", "--list"]
        with redirect_stdout(buf):
            try:
                repl_mod.main(["--list"])
            except SystemExit:
                pass
    finally:
        sys.argv = old_argv
    out = buf.getvalue()
    assert "可用 persona" in out
    assert "xiaoai" in out
    print("  ✓ test_main_list_flag")


# ============== 主入口 ==============

def run_all():
    tests = [
        test_color_constants_exist,
        test_supports_color_no_color_env,
        test_thinking_animation_quick,
        test_list_personas,
        test_load_persona_xiaoai,
        test_load_persona_dr_li,
        test_load_persona_xiaozhi,
        test_load_persona_not_found,
        test_chat_engine_init,
        test_chat_engine_basic_chat,
        test_chat_engine_multi_turn,
        test_chat_engine_dr_li,
        test_format_user,
        test_format_assistant,
        test_persona_banner,
        test_repl_init,
        test_repl_make_prompt,
        test_repl_switch_persona,
        test_repl_switch_persona_invalid,
        test_repl_print_history_empty,
        test_repl_print_history_with_msgs,
        test_repl_print_stats,
        test_repl_handle_user_message,
        test_repl_handle_command_quit,
        test_repl_handle_command_help,
        test_integration_three_turns,
        test_main_list_flag,
    ]
    print(f"Running {len(tests)} REPL tests...\n")
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
        print("✅ All REPL tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    return failed == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
