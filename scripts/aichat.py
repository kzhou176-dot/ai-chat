#!/usr/bin/env python3
"""
aichat-hub CLI 入口
===================
和虚拟人聊天的命令行界面。

用法:
  python3 aichat.py list                                # 列出所有虚拟人
  python3 aichat.py chat <persona>                       # 进入单虚拟人聊天
  python3 aichat.py chat <persona> --provider openai     # 指定 LLM provider
  python3 aichat.py compare <persona> "问题"              # 多模型对比
  python3 aichat.py demo                                 # 内置 demo(无需 key)
  python3 aichat.py create <name> --bg "..."             # 创建虚拟人

Cycle 1 目标: 最简可用的 CLI,支持 mock 模式(无 key 也能跑)
"""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

from persona import Persona, PersonaStore, BUILTIN_PERSONAS
from llm_client import LLMClient, Message, PROVIDER_PRESETS


# ANSI 颜色
class C:
    H = "\033[95m"  # 标题
    B = "\033[94m"  # 蓝
    G = "\033[92m"  # 绿
    Y = "\033[93m"  # 黄
    R = "\033[91m"  # 红
    E = "\033[0m"   # 结束
    BOLD = "\033[1m"


def banner():
    print(f"""{C.H}{C.BOLD}
   ___  ____ ___   _   _       _      _    ___  _  _
  / _ \\/ ___|_ _| | | | | ___ | |__  | |_ / _ \\| \\| |
 | | | \\___ \\| |  | |_| |/ _ \\| '_ \\ | __| | | | .` |
 | |_| |___) | |  |  _  | (_) | | | || |_| |_| | |\\  |
  \\___/|____/___| |_| |_|\\___/|_| |_| \\__|\\___/|_| \\_|

{C.E}{C.G}  虚拟人 AI 对话聚合客户端  v0.1 (cycle 1){C.E}
""")


def cmd_list(args):
    """列出所有虚拟人"""
    store = PersonaStore()
    personas = store.list_all()
    if not personas:
        print("还没有虚拟人,运行: python3 aichat.py demo  生成示例")
        return
    print(f"{C.BOLD}虚拟人列表 ({len(personas)} 个){C.E}\n")
    for name in personas:
        p = store.load(name)
        print(f"  {C.G}●{C.E} {C.BOLD}{p.name}{C.E} "
              f"({p.gender}, {p.age}岁, {p.avatar_style})")
        print(f"    背景: {p.background[:60]}...")
        if p.traits:
            print(f"    性格: {', '.join(p.traits)}")
        print()


def cmd_demo(args):
    """生成内置 demo 虚拟人"""
    store = PersonaStore()
    created = []
    for name, conf in BUILTIN_PERSONAS.items():
        path = store.root / f"{name}.json"
        if path.exists():
            print(f"  {C.Y}○{C.E} 跳过(已存在): {name}")
            continue
        # 避免 name 参数重复(位置 + **conf 里的 name)
        conf_safe = {k: v for k, v in conf.items() if k != "name"}
        p = store.create_default(name, **conf_safe)
        created.append(p.name)
        print(f"  {C.G}●{C.E} 创建: {p.name}")
    print(f"\n{C.BOLD}共 {len(created)} 个新虚拟人{C.E}")
    if created:
        print(f"\n试试: python3 aichat.py chat {created[0]}")


def cmd_create(args):
    """创建自定义虚拟人"""
    store = PersonaStore()
    p = store.create_default(
        args.name,
        background=args.bg or "你是一个 AI 虚拟人,愿意和用户聊天。",
        age=args.age or 25,
        gender=args.gender or "neutral",
        traits=args.traits.split(",") if args.traits else ["友好"],
    )
    print(f"{C.G}✓{C.E} 创建虚拟人: {p.name} → {store.root / (p.name + '.json')}")


def cmd_chat(args):
    """单虚拟人聊天 REPL"""
    store = PersonaStore()
    p = store.load(args.persona)
    if not p:
        print(f"{C.R}✗{C.E} 虚拟人 {args.persona} 不存在,先运行: aichat.py demo")
        return

    client = LLMClient(provider=args.provider)
    print(banner())
    print(f"{C.BOLD}与 {p.name} 聊天{C.E} "
          f"(provider: {args.provider}, model: {client.model})")
    print(f"{C.Y}输入 'quit' 退出, 'fact:xxx' 教虚拟人记住事实, "
          f"'reset' 清空对话{C.E}\n")
    print(f"{C.G}{p.name}{C.E}: {p.greeting.format(name=p.name)}\n")

    history: List[Message] = [
        Message(role="system", content=p.to_system_prompt()),
        Message(role="assistant", content=p.greeting.format(name=p.name)),
    ]
    total_cost = 0.0
    total_tokens = 0
    while True:
        try:
            user_input = input(f"{C.B}你{C.E}> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见~")
            break
        if not user_input:
            continue
        if user_input.lower() in ("quit", "exit", "q"):
            print(f"\n{C.Y}本次对话: {total_tokens} tokens, ${total_cost:.6f}{C.E}")
            break
        if user_input.lower() == "reset":
            history = [history[0]]
            print(f"{C.Y}已重置对话(保留 persona){C.E}")
            continue
        if user_input.startswith("fact:"):
            fact = user_input[5:].strip()
            p.remember_fact(fact)
            store.save(p)
            print(f"{C.Y}({p.name} 记住了: {fact}){C.E}")
            continue

        history.append(Message(role="user", content=user_input))
        resp = client.chat(history)
        history.append(Message(role="assistant", content=resp.content))
        total_cost += resp.cost_usd
        total_tokens += resp.usage["total_tokens"]

        # 截断 history,避免超长
        if len(history) > 22:
            history = [history[0]] + history[-20:]

        print(f"\n{C.G}{p.name}{C.E}: {resp.content}")
        print(f"  {C.Y}({resp.usage['total_tokens']} tokens, "
              f"${resp.cost_usd:.6f}, {resp.latency_ms}ms){C.E}\n")

        # 长期记忆(每 5 轮自动总结)
        if len(history) % 10 == 0 and len(history) > 2:
            p.remember_episode(
                f"对话进展 {len(history)//2} 轮, "
                f"用户最近说: {user_input[:50]}"
            )
            store.save(p)


def cmd_compare(args):
    """多模型对比(同一 prompt)"""
    persona_name = args.persona
    question = args.question
    store = PersonaStore()
    p = store.load(persona_name)
    if not p:
        print(f"{C.R}✗{C.E} 虚拟人 {persona_name} 不存在")
        return
    providers = (args.providers or "mock,openai,deepseek,zhipu,dashscope").split(",")
    print(banner())
    print(f"{C.BOLD}多模型对比{C.E} (虚拟人: {p.name})")
    print(f"问题: {question}\n")

    messages = [
        Message(role="system", content=p.to_system_prompt()),
        Message(role="user", content=question),
    ]
    results = {}
    for prov in providers:
        c = LLMClient(provider=prov)
        resp = c.chat(messages)
        results[prov] = resp
        print(f"{C.BOLD}━━━ {prov} ({c.model}) ━━━{C.E}")
        print(f"{resp.content}\n")
        print(f"  {C.Y}{resp.usage['total_tokens']} tokens, "
              f"${resp.cost_usd:.6f}, {resp.latency_ms}ms{C.E}\n")

    # 评分(MVP:长度 + 响应时间)
    print(f"{C.BOLD}━━━ 评分(简版) ━━━{C.E}")
    print(f"{'Provider':<12} {'Tokens':>8} {'Cost':>10} {'Latency':>10}")
    for prov, r in results.items():
        print(f"{prov:<12} {r.usage['total_tokens']:>8} "
              f"${r.cost_usd:>9.6f} {r.latency_ms:>9}ms")


def main():
    banner()
    ap = argparse.ArgumentParser(
        description="aichat-hub 虚拟人 AI chat CLI"
    )
    sub = ap.add_subparsers(dest="cmd")

    sub.add_parser("list", help="列出所有虚拟人")
    sub.add_parser("demo", help="生成内置示例虚拟人")

    c = sub.add_parser("create", help="创建自定义虚拟人")
    c.add_argument("name")
    c.add_argument("--bg", help="背景设定")
    c.add_argument("--age", type=int)
    c.add_argument("--gender")
    c.add_argument("--traits", help="逗号分隔")

    ch = sub.add_parser("chat", help="和虚拟人聊天")
    ch.add_argument("persona")
    ch.add_argument("--provider", default="mock",
                    choices=list(PROVIDER_PRESETS.keys()))

    cp = sub.add_parser("compare", help="多模型对比")
    cp.add_argument("persona")
    cp.add_argument("question")
    cp.add_argument("--providers",
                    default="mock,openai,deepseek,zhipu,dashscope")

    args = ap.parse_args()
    if args.cmd == "list":
        cmd_list(args)
    elif args.cmd == "demo":
        cmd_demo(args)
    elif args.cmd == "create":
        cmd_create(args)
    elif args.cmd == "chat":
        cmd_chat(args)
    elif args.cmd == "compare":
        cmd_compare(args)
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
