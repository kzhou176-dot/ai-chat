"""
repl.py — aichat-hub 交互式 REPL(命令行对话)

用法:
  python3 scripts/repl.py                  # 用默认 persona (xiaoai)
  python3 scripts/repl.py dr_li            # 指定 persona 启动
  python3 scripts/repl.py --provider openai  # 指定 LLM provider
  python3 scripts/repl.py --list            # 列出所有 persona

命令(在 REPL 内):
  /help           显示帮助
  /persona        切换 persona
  /switch NAME    切到 NAME (xiaoai/dr_li/xiaozhi)
  /clear          清屏
  /history        显示对话历史
  /cost           显示本次会话 cost / token
  /provider NAME  切 LLM provider
  /quit 或 /exit  退出

特点:
  - 真实交互:输入 → 思考动画 → 回复
  - Persona-aware mock(无 LLM key 也能用)
  - 多轮上下文
  - 命令补全
  - 彩色输出(终端)
"""
from __future__ import annotations

import json
import os
import sys
import time
import cmd
import shlex
from typing import Any, Dict, List, Optional, Tuple

# 路径
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


# ============== ANSI 颜色 ==============

class C:
    """终端颜色"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"


def supports_color() -> bool:
    """是否支持颜色"""
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    return True


if not supports_color():
    # 简化:全部置空
    for k in dir(C):
        if k.isupper() and not k.startswith("_"):
            setattr(C, k, "")


# ============== 思考动画 ==============

def thinking_animation(duration_s: float = 0.5, persona_name: str = "AI") -> None:
    """简单的打字动画"""
    frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    end = time.time() + duration_s
    i = 0
    while time.time() < end:
        sys.stdout.write(f"\r  {C.DIM}{C.CYAN}{frames[i % len(frames)]} {persona_name} 正在思考...{C.RESET}")
        sys.stdout.flush()
        time.sleep(0.08)
        i += 1
    sys.stdout.write("\r" + " " * 60 + "\r")
    sys.stdout.flush()


# ============== Persona 加载 ==============

def load_persona(persona_id: str) -> Dict[str, Any]:
    """从 data/personas/ 加载 persona,如果存在 builtin 中文名则补全"""
    path = os.path.join(ROOT, "data", "personas", f"{persona_id}.json")
    if not os.path.exists(path):
        raise FileNotFoundError(f"persona not found: {persona_id}")
    with open(path, "r", encoding="utf-8") as f:
        p = json.load(f)
    # 尝试补全中文名(从 builtin 加载)
    try:
        from persona import BUILTIN_PERSONAS
        if persona_id in BUILTIN_PERSONAS and not p.get("display_name"):
            p["display_name"] = BUILTIN_PERSONAS[persona_id]["name"]
    except ImportError:
        pass
    return p


def list_personas() -> List[str]:
    """列出所有可用 persona"""
    d = os.path.join(ROOT, "data", "personas")
    return sorted([f.replace(".json", "") for f in os.listdir(d) if f.endswith(".json")])


# ============== LLM 调用 ==============

class ChatEngine:
    """简单的 chat 引擎,封装 llm_client"""

    def __init__(self, persona_id: str, provider: str = "mock"):
        self.persona_id = persona_id
        self.provider = provider
        self.persona = load_persona(persona_id)
        self.history: List[Dict[str, str]] = []
        self.total_tokens = 0
        self.total_cost = 0.0
        self.total_latency = 0
        self._init_llm()

    def _init_llm(self) -> None:
        try:
            from llm_client import LLMClient, Message
            # 用 persona 名字做 system prompt
            self._client = LLMClient(provider=self.provider)
            self._Message = Message
        except ImportError as e:
            raise RuntimeError(f"无法导入 llm_client: {e}")

    def _build_messages(self) -> List[Any]:
        msgs = []
        # system = persona background
        bg = self.persona.get("background", "")
        if bg:
            msgs.append(self._Message(role="system", content=bg))
        # history
        for h in self.history:
            msgs.append(self._Message(role=h["role"], content=h["content"]))
        return msgs

    def chat(self, user_text: str) -> Tuple[str, Dict[str, Any]]:
        """发一条消息,返回 (assistant_reply, metadata)"""
        self.history.append({"role": "user", "content": user_text})
        msgs = self._build_messages()
        resp = self._client.chat(messages=msgs)
        self.history.append({"role": "assistant", "content": resp.content})
        meta = {
            "model": resp.model,
            "tokens": resp.usage.get("total_tokens", 0),
            "cost": resp.cost_usd,
            "latency_ms": resp.latency_ms,
        }
        self.total_tokens += meta["tokens"]
        self.total_cost += meta["cost"]
        self.total_latency += meta["latency_ms"]
        return resp.content, meta


# ============== 渲染辅助 ==============

def persona_banner(persona: Dict[str, Any]) -> str:
    """显示 persona 卡片"""
    traits = ", ".join(persona.get("traits", []))
    return (
        f"{C.BG_MAGENTA}{C.WHITE}{C.BOLD} {persona.get('name', '?')} ({persona.get('age', '?')}岁) "
        f"{persona.get('gender', '')} {C.RESET}\n"
        f"  {C.DIM}性格:{C.RESET} {C.CYAN}{traits}{C.RESET}\n"
        f"  {C.DIM}设定:{C.RESET} {persona.get('background', '')[:120]}"
    )


def format_assistant(name: str, text: str, meta: Dict[str, Any]) -> str:
    """渲染助手消息"""
    head = f"{C.BG_CYAN}{C.WHITE}{C.BOLD} {name} {C.RESET}"
    body = ""
    for line in text.split("\n"):
        body += f"  {C.WHITE}{line}{C.RESET}\n"
    footer = f"  {C.DIM}[{meta['model']} · {meta['tokens']} tokens · ${meta['cost']:.4f} · {meta['latency_ms']}ms]{C.RESET}"
    return f"{head}\n{body}{footer}"


def format_user(text: str) -> str:
    """渲染用户消息"""
    head = f"{C.BG_BLUE}{C.WHITE}{C.BOLD} 你 {C.RESET}"
    body = ""
    for line in text.split("\n"):
        body += f"  {C.WHITE}{line}{C.RESET}\n"
    return f"{head}\n{body}"


# ============== 主 REPL ==============

class AichatREPL(cmd.Cmd):
    """aichat-hub 交互式 REPL"""

    intro = None  # 我们自己打印
    prompt = ""
    ruler = "─" * 60

    def __init__(self, persona_id: str = "xiaoai", provider: str = "mock"):
        super().__init__()
        self.persona_id = persona_id
        self.provider = provider
        self.engine: Optional[ChatEngine] = None
        self.turn_count = 0

    def start(self) -> None:
        """主循环"""
        # 加载 engine
        try:
            self.engine = ChatEngine(self.persona_id, provider=self.provider)
        except Exception as e:
            print(f"{C.RED}✗ 初始化失败:{C.RESET} {e}")
            return

        # 欢迎
        self._print_banner()
        self._print_help_brief()

        # 启动 cmdloop
        try:
            self.cmdloop()
        except (KeyboardInterrupt, EOFError):
            print(f"\n{C.DIM}(Ctrl+C 退出){C.RESET}")
            self._print_summary()
            return

    def _print_banner(self) -> None:
        p = self.engine.persona
        name = p.get("display_name") or p.get("name", "?")
        print()
        print(f"{C.BOLD}{C.MAGENTA}╔════════════════════════════════════════════════════════════╗{C.RESET}")
        print(f"{C.BOLD}{C.MAGENTA}║{C.RESET}        {C.BOLD}{C.WHITE}aichat-hub v1.0.2  ·  交互式 REPL{C.RESET}                  {C.BOLD}{C.MAGENTA}║{C.RESET}")
        print(f"{C.BOLD}{C.MAGENTA}╚════════════════════════════════════════════════════════════╝{C.RESET}")
        print()
        print(persona_banner(p))
        # greeting
        greeting = p.get("greeting", "你好~")
        print()
        print(f"  {C.DIM}开场白:{C.RESET} {C.CYAN}{greeting}{C.RESET}")
        print(f"  {C.DIM}Provider:{C.RESET} {C.YELLOW}{self.provider}{C.RESET}")
        print()

    def _print_help_brief(self) -> None:
        print(f"  {C.DIM}命令:{C.RESET}  {C.GREEN}/help{C.RESET} 帮助 · {C.GREEN}/persona{C.RESET} 切换角色 · {C.GREEN}/history{C.RESET} 历史 · {C.GREEN}/quit{C.RESET} 退出")
        print(f"  {C.DIM}直接输入消息开始对话{C.RESET}")
        print()
        print(self.ruler)

    # cmd.Cmd 默认会处理一行输入 — 但 default() 太简单
    # 我们重写 cmdloop 自己控制
    def cmdloop(self, intro=None):
        """自定义 loop,处理空行 + 命令前缀"""
        self._print_intro_if_needed()
        while True:
            try:
                line = input(self._make_prompt())
            except EOFError:
                break
            except KeyboardInterrupt:
                print(f"\n{C.DIM}(Ctrl+C — 输入 /quit 退出){C.RESET}")
                continue
            line = line.strip()
            if not line:
                continue
            if line.startswith("/"):
                cmd_name = line[1:].split()[0].lower()
                args = line[len(cmd_name) + 2:] if len(line) > len(cmd_name) + 2 else ""
                should_continue = self._handle_command(cmd_name, args)
                if not should_continue:
                    break
            else:
                self._handle_user_message(line)
            print()

    def _print_intro_if_needed(self) -> None:
        pass  # banner 已打印

    def _make_prompt(self) -> str:
        p = self.engine.persona
        persona_name = p.get("display_name") or p.get("name", "?")
        return f"{C.BOLD}{C.GREEN}{persona_name} ❯{C.RESET} "

    def _handle_command(self, cmd_name: str, args: str) -> bool:
        """处理命令,返回 False 表示退出"""
        if cmd_name in ("quit", "exit", "q"):
            self._print_summary()
            return False
        if cmd_name == "help":
            self._print_full_help()
            return True
        if cmd_name == "persona" or cmd_name == "list":
            self._list_personas()
            return True
        if cmd_name == "switch" or cmd_name == "use":
            self._switch_persona(args.strip())
            return True
        if cmd_name == "clear" or cmd_name == "cls":
            os.system("clear" if os.name == "posix" else "cls")
            self._print_banner()
            return True
        if cmd_name == "history":
            self._print_history()
            return True
        if cmd_name == "cost" or cmd_name == "stats":
            self._print_stats()
            return True
        if cmd_name == "provider":
            self._switch_provider(args.strip())
            return True
        if cmd_name == "info":
            self._print_persona_info()
            return True
        print(f"{C.RED}✗ 未知命令:{C.RESET} /{cmd_name}    输入 {C.GREEN}/help{C.RESET} 看帮助")

    def _handle_user_message(self, text: str) -> None:
        """处理普通消息"""
        p = self.engine.persona
        name = p.get("display_name") or p.get("name", "AI")
        # 显示用户消息
        print(format_user(text))
        # 思考动画
        thinking_animation(0.4, name)
        # 调 LLM
        try:
            reply, meta = self.engine.chat(text)
            print(format_assistant(name, reply, meta))
            self.turn_count += 1
        except Exception as e:
            print(f"{C.RED}✗ 出错:{C.RESET} {e}")
            # 撤回最后一条 user
            if self.engine.history and self.engine.history[-1]["role"] == "user":
                self.engine.history.pop()

    # ============== 命令实现 ==============

    def _print_full_help(self) -> None:
        print()
        print(f"{C.BOLD}命令列表:{C.RESET}")
        print(f"  {C.GREEN}/help{C.RESET}              显示本帮助")
        print(f"  {C.GREEN}/persona{C.RESET}           列出所有可用 persona")
        print(f"  {C.GREEN}/switch NAME{C.RESET}      切到 NAME (xiaoai / dr_li / xiaozhi)")
        print(f"  {C.GREEN}/info{C.RESET}              显示当前 persona 详情")
        print(f"  {C.GREEN}/history{C.RESET}           显示对话历史")
        print(f"  {C.GREEN}/stats{C.RESET}             显示 token / cost 统计")
        print(f"  {C.GREEN}/provider NAME{C.RESET}    切 LLM provider (mock/openai/deepseek/...)")
        print(f"  {C.GREEN}/clear{C.RESET}             清屏(重新显示 banner)")
        print(f"  {C.GREEN}/quit{C.RESET}              退出(显示本次会话统计)")
        print()
        print(f"{C.DIM}直接输入消息即可对话。按 Ctrl+C 中断当前输入。{C.RESET}")

    def _list_personas(self) -> None:
        print()
        print(f"{C.BOLD}可用 persona:{C.RESET}")
        for pid in list_personas():
            p = load_persona(pid)
            mark = "→" if pid == self.persona_id else " "
            color = C.GREEN if pid == self.persona_id else C.DIM
            print(f"  {color}{mark} {pid:12s}  {p.get('name', '?')}  ({p.get('age', '?')}岁,{p.get('gender', '?')}){C.RESET}")
            print(f"      {C.DIM}{p.get('background', '')[:80]}...{C.RESET}")

    def _switch_persona(self, new_id: str) -> None:
        if not new_id:
            print(f"{C.RED}✗ 用法:{C.RESET} /switch <persona_id>")
            self._list_personas()
            return
        if new_id not in list_personas():
            print(f"{C.RED}✗ 未知 persona:{C.RESET} {new_id}")
            self._list_personas()
            return
        old = self.engine.persona.get("display_name") or self.engine.persona.get("name", "?")
        self.persona_id = new_id
        self.engine = ChatEngine(new_id, provider=self.provider)
        new = self.engine.persona.get("display_name") or self.engine.persona.get("name", "?")
        print(f"{C.GREEN}✓ 已切换:{C.RESET} {old} → {new}")
        # 显示新 persona 的 greeting
        greeting = self.engine.persona.get("greeting", "")
        if greeting:
            print(f"  {C.CYAN}{greeting}{C.RESET}")

    def _switch_provider(self, new_prov: str) -> None:
        if not new_prov:
            print(f"{C.RED}✗ 用法:{C.RESET} /provider <name>")
            print(f"  可用: mock, openai, deepseek, zhipu, dashscope, moonshot, anthropic")
            return
        try:
            self.provider = new_prov
            self.engine = ChatEngine(self.persona_id, provider=new_prov)
            print(f"{C.GREEN}✓ Provider 已切到:{C.RESET} {new_prov}")
        except Exception as e:
            print(f"{C.RED}✗ 切换失败:{C.RESET} {e}")

    def _print_history(self) -> None:
        if not self.engine or not self.engine.history:
            print(f"{C.DIM}(无历史){C.RESET}")
            return
        p = self.engine.persona
        name = p.get("display_name") or p.get("name", "AI")
        print()
        print(f"{C.BOLD}对话历史 ({len(self.engine.history)} 条):{C.RESET}")
        for i, h in enumerate(self.engine.history, 1):
            who = "你" if h["role"] == "user" else name
            color = C.BLUE if h["role"] == "user" else C.CYAN
            print(f"  {C.DIM}{i:2d}.{C.RESET} {color}{who}{C.RESET}: {h['content'][:80]}")

    def _print_stats(self) -> None:
        if not self.engine:
            return
        p = self.engine.persona
        name = p.get("display_name") or p.get("name", "?")
        print()
        print(f"{C.BOLD}本次会话统计:{C.RESET}")
        print(f"  Persona:      {C.CYAN}{name}{C.RESET}")
        print(f"  Provider:     {C.YELLOW}{self.provider}{C.RESET}")
        print(f"  轮数:         {self.turn_count}")
        print(f"  Token 总数:   {self.engine.total_tokens}")
        print(f"  累计 cost:    {C.GREEN}${self.engine.total_cost:.4f}{C.RESET}")
        print(f"  平均延迟:     {self.engine.total_latency / max(self.turn_count, 1):.0f}ms")

    def _print_persona_info(self) -> None:
        if not self.engine:
            return
        p = self.engine.persona
        name = p.get("display_name") or p.get("name", "?")
        print()
        print(f"{C.BOLD}当前 persona 详情:{C.RESET}")
        print(persona_banner(p))
        print()
        print(f"  {C.DIM}ID:{C.RESET}        {self.persona_id}")
        print(f"  {C.DIM}姓名:{C.RESET}      {name}")
        print(f"  {C.DIM}年龄:{C.RESET}      {p.get('age', '?')}")
        print(f"  {C.DIM}性别:{C.RESET}      {p.get('gender', '?')}")
        print(f"  {C.DIM}声音:{C.RESET}      {p.get('voice_id', '?')}")
        print(f"  {C.DIM}形象:{C.RESET}      {p.get('avatar_style', '?')}")

    def _print_summary(self) -> None:
        print()
        print(self.ruler)
        self._print_stats()
        print()
        print(f"{C.DIM}再见~ {C.CYAN}👋{C.RESET}")


# ============== CLI ==============

def main(argv: List[str]) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="aichat-hub 交互式 REPL")
    parser.add_argument("persona", nargs="?", default="xiaoai", help="初始 persona (xiaoai/dr_li/xiaozhi)")
    parser.add_argument("--provider", "-p", default="mock", help="LLM provider (mock/openai/...)")
    parser.add_argument("--list", action="store_true", help="列出所有 persona")
    args = parser.parse_args(argv)

    if args.list:
        print(f"{C.BOLD}可用 persona:{C.RESET}")
        for pid in list_personas():
            p = load_persona(pid)
            print(f"  {C.GREEN}{pid:12s}{C.RESET}  {p.get('name', '?')} ({p.get('age', '?')}岁) — {p.get('greeting', '')}")
        return 0

    if args.persona not in list_personas():
        print(f"{C.RED}✗ 未知 persona:{C.RESET} {args.persona}")
        print(f"  可用:{', '.join(list_personas())}")
        return 1

    repl = AichatREPL(persona_id=args.persona, provider=args.provider)
    repl.start()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
