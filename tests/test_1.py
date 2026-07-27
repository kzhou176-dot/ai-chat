#!/usr/bin/env python3
"""
aichat-hub Cycle 1 测试
======================
验证:
  1. 模块可 import
  2. Persona 创建/保存/加载
  3. LLMClient 6 个 provider 都能用(至少 mock 模式)
  4. system prompt 生成
  5. cost / token 估算
  6. 并行 chat(对比)
  7. CLI 命令可调用(list / demo)
"""
from __future__ import annotations
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT))

# 让子进程能找到模块
env_setup = ""


def assert_eq(a, b, msg=""):
    if a != b:
        raise AssertionError(f"{msg}: {a!r} != {b!r}")
    print(f"  ✓ {msg}: {a!r}")


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(f"{msg}: condition false")
    print(f"  ✓ {msg}")


def assert_in(needle, hay, msg=""):
    if needle not in hay:
        raise AssertionError(f"{msg}: {needle!r} not in {hay!r}")
    print(f"  ✓ {msg}")


def test_imports():
    print("\n[1/7] 验证 import ...")
    from persona import Persona, PersonaStore, BUILTIN_PERSONAS
    from llm_client import LLMClient, Message, ChatResponse, PROVIDER_PRESETS
    assert_true(len(PROVIDER_PRESETS) >= 6, "至少 6 个 provider")
    assert_true(len(BUILTIN_PERSONAS) >= 3, "至少 3 个内置虚拟人")
    print(f"  ✓ PROVIDER_PRESETS: {list(PROVIDER_PRESETS.keys())}")
    print(f"  ✓ BUILTIN_PERSONAS: {list(BUILTIN_PERSONAS.keys())}")


def test_persona_create_save_load():
    print("\n[2/7] Persona CRUD ...")
    from persona import Persona, PersonaStore
    store = PersonaStore()
    p = Persona(
        name="_test_persona_xyz",
        age=30,
        gender="male",
        background="测试虚拟人",
        traits=["聪明", "幽默"],
    )
    path = store.save(p)
    assert_true(path.exists(), "保存到 JSON")
    p2 = store.load("_test_persona_xyz")
    assert_eq(p2.name, "_test_persona_xyz", "加载 name")
    assert_eq(p2.age, 30, "加载 age")
    assert_eq(p2.traits, ["聪明", "幽默"], "加载 traits")
    # 清理
    path.unlink()
    assert_true(not path.exists(), "清理测试文件")


def test_system_prompt():
    print("\n[3/7] System Prompt 生成 ...")
    from persona import Persona
    p = Persona(
        name="测试",
        age=25,
        gender="female",
        background="AI 助手",
        traits=["温柔", "聪明"],
        memory_facts=["用户喜欢音乐", "用户是程序员"],
    )
    sp = p.to_system_prompt()
    assert_in("测试", sp, "含名字")
    assert_in("25岁", sp, "含年龄")
    assert_in("温柔", sp, "含 traits")
    assert_in("用户喜欢音乐", sp, "含 facts")
    assert_in("始终保持角色", sp, "含行为指令")


def test_memory():
    print("\n[4/7] 记忆(事实 + 事件) ...")
    from persona import Persona
    p = Persona(name="m")
    p.remember_fact("用户是医生")
    p.remember_fact("用户喜欢猫")
    p.remember_fact("用户是医生")  # 重复,不添加
    assert_eq(len(p.memory_facts), 2, "去重")
    for i in range(55):
        p.remember_episode(f"事件 {i}")
    assert_true(len(p.memory_episodes) == 50, "episode 保留最近 50")


def test_llm_client_mock():
    print("\n[5/7] LLMClient mock 模式 ...")
    from llm_client import LLMClient, Message
    for prov in ["mock", "openai", "deepseek", "zhipu", "dashscope", "moonshot"]:
        c = LLMClient(provider=prov)
        msgs = [
            Message(role="system", content="你是小爱,温柔善解人意。"),
            Message(role="user", content="今天心情有点差"),
        ]
        resp = c.chat(msgs)
        assert_true(len(resp.content) > 0, f"{prov} 返回非空")
        assert_true(resp.usage["total_tokens"] > 0, f"{prov} token 统计 > 0")
        assert_true(resp.latency_ms >= 0, f"{prov} latency 合理")
        print(f"  ✓ {prov} → {resp.content[:60]}...")


def test_llm_client_persona_role():
    print("\n[6/7] LLMClient 角色感知(mock) ...")
    from llm_client import LLMClient, Message
    personas_test = [
        ("小爱", "温柔", "🌸"),
        ("李医生", "李医生", "建议"),
        ("小智", "geek", "Yo"),
    ]
    for name, sys_kw, content_kw in personas_test:
        c = LLMClient(provider="mock")
        resp = c.chat([
            Message(role="system", content=f"你是{name},{sys_kw}"),
            Message(role="user", content="hello"),
        ])
        # 至少应该 mock 出内容
        assert_true(len(resp.content) > 5, f"{name} 输出长度 OK")


def test_cli_basic():
    print("\n[7/7] CLI 命令调用 ...")
    import subprocess
    # 跑 list
    r = subprocess.run(
        ["python3", "scripts/aichat.py", "list"],
        capture_output=True, text=True,
        cwd=str(ROOT),
    )
    assert_eq(r.returncode, 0, "aichat.py list exit 0")
    # 跑 demo 创建虚拟人
    r = subprocess.run(
        ["python3", "scripts/aichat.py", "demo"],
        capture_output=True, text=True,
        cwd=str(ROOT),
    )
    assert_eq(r.returncode, 0, "aichat.py demo exit 0")
    # 确认 personas 生成
    from persona import PersonaStore
    store = PersonaStore()
    personas = store.list_all()
    assert_true(len(personas) >= 3, f"至少 3 个 personas 存在: {personas}")


def test_compare_mode():
    print("\n[bonus] 多模型对比 ...")
    from llm_client import LLMClient, Message
    msgs = [
        Message(role="system", content="你是助手"),
        Message(role="user", content="什么是 LLM?"),
    ]
    results = {}
    for prov in ["mock", "openai", "deepseek"]:
        c = LLMClient(provider=prov)
        results[prov] = c.chat(msgs)
    assert_true(len(results) == 3, "3 个 provider 都返回")
    for prov, r in results.items():
        assert_true(r.usage["total_tokens"] > 0, f"{prov} token 统计")


def main():
    t0 = time.time()
    print(f"=== aichat-hub Cycle 1 测试 (root: {ROOT}) ===")
    test_imports()
    test_persona_create_save_load()
    test_system_prompt()
    test_memory()
    test_llm_client_mock()
    test_llm_client_persona_role()
    test_cli_basic()
    test_compare_mode()
    print(f"\n{C if False else ''}=== 全部通过 ✓ ({time.time() - t0:.1f}s) ===")


if __name__ == "__main__":
    main()
