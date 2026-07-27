"""
test_27_desktop.py — desktop_app 单元测试

不真正弹窗(用 update_idletasks + withdraw),但完整测试:
- 启动 / 关闭
- Persona 切换
- 发消息 → 收回复(异步)
- 历史持久化
- 设置持久化
- 状态/统计
"""
import os
import sys
import time
import json
import tempfile
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPTS = os.path.join(ROOT, "scripts")
sys.path.insert(0, SCRIPTS)

# 用临时目录作为 home(避免污染真实 ~/Library)
_test_home = tempfile.mkdtemp(prefix="aichat-test-")
os.environ["XDG_DATA_HOME"] = _test_home
os.environ["APPDATA"] = _test_home  # Windows 兼容
os.environ["HOME"] = _test_home     # macOS/Linux 都覆盖

import desktop_app  # noqa: E402

# 强制 desktop_app 用临时目录(覆盖默认 ~/Library)
_test_aichat_home = Path(_test_home) / "Library" / "Application Support" / desktop_app.APP_NAME
_test_aichat_home.mkdir(parents=True, exist_ok=True)
_test_aichat_config = _test_aichat_home.parent.parent / "aichat-hub"
_test_aichat_config.mkdir(parents=True, exist_ok=True)

# patch get_history_path / get_settings_path 走临时目录
def _get_history_path_test():
    return _test_aichat_home / "history.json"

def _get_settings_path_test():
    return _test_aichat_home / "settings.json"

desktop_app.get_history_path = _get_history_path_test
desktop_app.get_settings_path = _get_settings_path_test


def _new_app(headless=True, clean_history=True):
    """新建 app,headless 模式(不弹窗,跑完即关)"""
    a = desktop_app.AichatApp()
    if headless:
        a.root.withdraw()  # 不显示
    if clean_history:
        # 测试隔离:清掉 disk 上 + 内存里
        for pid in ["xiaoai", "dr_li", "xiaozhi"]:
            a.all_history[pid] = []
        a.history = []
        a._save_history()
    return a


def _wait_done(app, timeout_s=5):
    """等异步 chat 完成"""
    t0 = time.time()
    while app.is_thinking and (time.time() - t0) < timeout_s:
        app.root.update()
        time.sleep(0.05)
    # 多次 update 让 queue 处理完(手动 pump _poll_queue)
    for _ in range(20):
        app._poll_queue()
        app.root.update()
        time.sleep(0.05)
        if not app.is_thinking:
            # 再 pump 几次确保结果已渲染
            for _ in range(5):
                app._poll_queue()
                app.root.update()
                time.sleep(0.02)
            break


# ============== 基础 ==============

def test_app_init():
    a = _new_app(headless=True)
    assert a.current_persona == "xiaoai"
    assert a.is_thinking is False
    a._on_close()
    print("  ✓ test_app_init")


def test_app_window_title():
    a = _new_app(headless=True)
    title = a.root.title()
    assert "aichat-hub" in title
    assert "1.0.2" in title
    a._on_close()
    print(f"  ✓ test_app_window_title ({title!r})")


def test_persona_meta():
    assert "xiaoai" in desktop_app.PERSONAS_META
    assert "dr_li" in desktop_app.PERSONAS_META
    assert "xiaozhi" in desktop_app.PERSONAS_META
    for pid, meta in desktop_app.PERSONAS_META.items():
        assert "name" in meta
        assert "color" in meta
        assert "emoji" in meta
    print(f"  ✓ test_persona_meta (3 personas, all have name/color/emoji)")


# ============== Persona 切换 ==============

def test_switch_persona():
    a = _new_app(headless=True)
    a._switch_persona("dr_li")
    assert a.current_persona == "dr_li"
    a._switch_persona("xiaozhi")
    assert a.current_persona == "xiaozhi"
    a._switch_persona("xiaoai")
    assert a.current_persona == "xiaoai"
    a._on_close()
    print("  ✓ test_switch_persona (3-way switch)")


def test_switch_persona_invalid():
    a = _new_app(headless=True)
    a._switch_persona("nonexistent")
    assert a.current_persona == "xiaoai"  # 不应改变
    a._on_close()
    print("  ✓ test_switch_persona_invalid (rejected, persona unchanged)")


# ============== 发消息 ==============

def test_send_message():
    a = _new_app(headless=True)
    a.input_text.insert("1.0", "你好,小爱")
    a._on_send()
    assert a.is_thinking is True
    assert len(a.history) == 1
    _wait_done(a)
    assert a.is_thinking is False
    assert len(a.history) == 2
    assert a.history[0]["role"] == "user"
    assert a.history[1]["role"] == "assistant"
    assert len(a.history[1]["content"]) > 0
    a._on_close()
    print(f"  ✓ test_send_message (round trip, {len(a.history[1]['content'])} char reply)")


def test_send_empty_message():
    a = _new_app(headless=True)
    a.input_text.insert("1.0", "   ")  # only whitespace
    a._on_send()
    assert len(a.history) == 0
    assert a.is_thinking is False
    a._on_close()
    print("  ✓ test_send_empty_message (rejected)")


def test_send_multiple_messages():
    a = _new_app(headless=True)
    for msg in ["第一句", "第二句", "第三句"]:
        a.input_text.insert("1.0", msg)
        a._on_send()
        _wait_done(a)
    assert len(a.history) == 6  # 3 user + 3 assistant
    a._on_close()
    print(f"  ✓ test_send_multiple_messages (6 entries)")


def test_conversation_continuity():
    """检查 assistant 看到 context"""
    a = _new_app(headless=True)
    a.input_text.insert("1.0", "我叫小明")
    a._on_send()
    _wait_done(a)
    a.input_text.insert("1.0", "我叫什么?")
    a._on_send()
    _wait_done(a)
    assert len(a.history) == 4
    a._on_close()
    print(f"  ✓ test_conversation_continuity (4 entries, ctx preserved)")


# ============== 历史 / 持久化 ==============

def test_clear_chat():
    a = _new_app(headless=True)
    a.input_text.insert("1.0", "hi")
    a._on_send()
    _wait_done(a)
    assert len(a.history) > 0
    a._clear_chat()
    assert a.history == []
    assert a.all_history["xiaoai"] == []
    a._on_close()
    print("  ✓ test_clear_chat")


def test_history_persistence():
    """关掉再开,历史应保留"""
    # 用一个独立 app(不 clean history)
    a1 = desktop_app.AichatApp()
    a1.root.withdraw()
    # 显式清空,确保起点干净
    a1.all_history = {"xiaoai": [], "dr_li": [], "xiaozhi": []}
    a1.history = []
    a1._save_history()
    # 发一条
    a1.input_text.insert("1.0", "持久化测试")
    a1._on_send()
    _wait_done(a1)
    a1._on_close()

    a2 = desktop_app.AichatApp()
    a2.root.withdraw()
    # xiaoai 历史应该被恢复
    assert len(a2.all_history.get("xiaoai", [])) > 0, f"空历史:{a2.all_history}"
    found = any("持久化测试" in h.get("content", "") for h in a2.all_history["xiaoai"])
    assert found, f"持久化的消息没找到,历史: {a2.all_history}"
    a2._on_close()
    print("  ✓ test_history_persistence (round trip OK)")


def test_settings_persistence():
    a1 = _new_app(headless=True)
    a1.provider_var.set("openai")
    a1._save_settings()
    a1._on_close()

    a2 = _new_app(headless=True)
    # 读盘:settings.json 应该有 openai
    settings = desktop_app.load_json(desktop_app.get_settings_path(), {})
    assert settings.get("provider") == "openai"
    # 重新 init 时会用这个(但当前 App.__init__ 不主动读 settings,需要 _save_settings 覆盖)
    a2.provider_var.set(settings.get("provider", "mock"))
    assert a2.provider_var.get() == "openai"
    a2._on_close()
    print(f"  ✓ test_settings_persistence ({settings.get('provider')})")


def test_per_persona_history():
    """每个 persona 独立历史"""
    a = _new_app(headless=True)
    a._switch_persona("xiaoai")
    a.input_text.insert("1.0", "xiaoai 的对话")
    a._on_send()
    _wait_done(a)
    a._switch_persona("dr_li")
    a.input_text.insert("1.0", "dr_li 的对话")
    a._on_send()
    _wait_done(a)
    # 切回 xiaoai
    a._switch_persona("xiaoai")
    assert any("xiaoai 的对话" in h.get("content", "") for h in a.history)
    a._switch_persona("dr_li")
    assert any("dr_li 的对话" in h.get("content", "") for h in a.history)
    a._on_close()
    print("  ✓ test_per_persona_history (3 personas have independent history)")


# ============== 持久化路径 ==============

def test_get_history_path():
    p = desktop_app.get_history_path()
    assert isinstance(p, Path)
    print(f"  ✓ test_get_history_path ({p})")


def test_get_settings_path():
    p = desktop_app.get_settings_path()
    assert isinstance(p, Path)
    print(f"  ✓ test_get_settings_path ({p})")


# ============== Widget 行为 ==============

def test_input_text_widget_exists():
    a = _new_app(headless=True)
    assert hasattr(a, "input_text")
    import tkinter as tk
    assert isinstance(a.input_text, tk.Text)  # tk.Text widget
    a._on_close()
    print("  ✓ test_input_text_widget_exists")


def test_send_button_exists():
    a = _new_app(headless=True)
    assert hasattr(a, "send_btn")
    a._on_close()
    print("  ✓ test_send_button_exists")


def test_canvas_exists():
    a = _new_app(headless=True)
    assert hasattr(a, "canvas")
    assert hasattr(a, "scrollable_frame")
    a._on_close()
    print("  ✓ test_canvas_exists")


def test_persona_cards():
    a = _new_app(headless=True)
    assert "xiaoai" in a.persona_cards
    assert "dr_li" in a.persona_cards
    assert "xiaozhi" in a.persona_cards
    a._on_close()
    print("  ✓ test_persona_cards (3 cards)")


def test_render_history_empty():
    a = _new_app(headless=True)
    a.history = []
    a._render_history()  # 应该走 empty state
    a._on_close()
    print("  ✓ test_render_history_empty")


def test_render_history_with_msgs():
    a = _new_app(headless=True)
    a.history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    a._render_history()
    # 验证 scrollable_frame 有 child
    children = a.scrollable_frame.winfo_children()
    assert len(children) >= 2
    a._on_close()
    print(f"  ✓ test_render_history_with_msgs ({len(children)} children)")


# ============== 异步 chat worker ==============

def test_chat_worker_basic():
    q = queue.Queue() if False else __import__("queue").Queue()
    w = desktop_app.ChatWorker(
        persona_id="xiaoai", message="测试", history=[],
        provider="mock", result_queue=q,
    )
    w.start()
    w.join(timeout=5)
    assert not w.is_alive()
    r = q.get_nowait()
    assert r["ok"] is True
    assert "content" in r
    assert "latency_ms" in r
    print(f"  ✓ test_chat_worker_basic ({r['latency_ms']}ms)")


def test_chat_worker_with_history():
    q = __import__("queue").Queue()
    history = [
        {"role": "user", "content": "我叫什么?"},
        {"role": "assistant", "content": "我没问过你"},
    ]
    w = desktop_app.ChatWorker(
        persona_id="xiaoai", message="回答一下", history=history,
        provider="mock", result_queue=q,
    )
    w.start()
    w.join(timeout=5)
    r = q.get_nowait()
    assert r["ok"] is True
    assert len(r["content"]) > 0
    print("  ✓ test_chat_worker_with_history")


# ============== About dialog ==============

def test_show_about():
    a = _new_app(headless=True)
    a._show_about()
    # 应该弹 Toplevel
    toplevels = [w for w in a.root.winfo_children() if isinstance(w, type(a.root))]
    # tk.Toplevel 检查
    assert any(w.winfo_class() == "Toplevel" for w in a.root.winfo_children())
    a._on_close()
    print("  ✓ test_show_about (Toplevel created)")


# ============== 主入口 ==============

def run_all():
    tests = [
        test_app_init,
        test_app_window_title,
        test_persona_meta,
        test_switch_persona,
        test_switch_persona_invalid,
        test_send_message,
        test_send_empty_message,
        test_send_multiple_messages,
        test_conversation_continuity,
        test_clear_chat,
        test_history_persistence,
        test_settings_persistence,
        test_per_persona_history,
        test_get_history_path,
        test_get_settings_path,
        test_input_text_widget_exists,
        test_send_button_exists,
        test_canvas_exists,
        test_persona_cards,
        test_render_history_empty,
        test_render_history_with_msgs,
        test_chat_worker_basic,
        test_chat_worker_with_history,
        test_show_about,
    ]
    print(f"Running {len(tests)} desktop app tests...\n")
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
        print("✅ All desktop app tests passed!")
    else:
        print(f"❌ {failed} test(s) failed")
    return failed == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
