"""
desktop_app.py — aichat-hub 桌面应用 (原生 macOS / Linux / Windows GUI)

特点:
  - 100% stdlib(tkinter)+ python3.13
  - 原生 macOS aqua 主题
  - 真实窗口:侧边栏(3 persona)+ chat 区域 + 输入框
  - 异步 chat(线程 + queue,UI 不卡)
  - 菜单栏(File/Edit/View/Persona/Help)
  - 快捷键:Cmd+N 新对话,Cmd+K 清空,Cmd+1/2/3 切 persona
  - 聊天历史持久化(~/Library/Application Support/aichat-hub/history.json)
  - Persona 头像/颜色 / 消息气泡 / 打字动画

用法:
  python3 scripts/desktop_app.py                    # 启动 GUI
  或
  aichat desktop
"""
from __future__ import annotations

import json
import os
import queue
import sys
import threading
import time
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import font as tkfont
from tkinter import ttk
from typing import Any, Dict, List, Optional, Tuple

# 路径
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)


# ============== Persona 配色 ==============

PERSONAS_META = {
    "xiaoai": {
        "name": "小爱",
        "subtitle": "22岁 · 文学少女",
        "emoji": "🌸",
        "color": "#e91e63",  # pink
        "bg_gradient": ("#fce4ec", "#ffffff"),
    },
    "dr_li": {
        "name": "李医生",
        "subtitle": "45岁 · 主任医师",
        "emoji": "🩺",
        "color": "#1976d2",  # blue
        "bg_gradient": ("#e3f2fd", "#ffffff"),
    },
    "xiaozhi": {
        "name": "小智",
        "subtitle": "18岁 · 极客 hacker",
        "emoji": "💻",
        "color": "#388e3c",  # green
        "bg_gradient": ("#e8f5e9", "#ffffff"),
    },
}

APP_NAME = "aichat-hub"
APP_VERSION = "1.0.2"
WINDOW_TITLE = f"{APP_NAME} v{APP_VERSION}"


# ============== 配置 / 持久化 ==============

def get_history_path() -> Path:
    """聊天历史存储路径"""
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_NAME
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))) / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base / "history.json"


def get_settings_path() -> Path:
    if sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support" / APP_NAME
    elif sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", str(Path.home()))) / APP_NAME
    else:
        base = Path.home() / ".config" / APP_NAME
    base.mkdir(parents=True, exist_ok=True)
    return base / "settings.json"


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def save_json(path: Path, data: Any) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[warn] save {path} failed: {e}")


# ============== 异步 chat worker ==============

class ChatWorker(threading.Thread):
    """后台线程调 LLM,通过 queue 把结果送回 UI"""

    def __init__(self, persona_id: str, message: str, history: List[Dict[str, str]],
                 provider: str, result_queue: queue.Queue):
        super().__init__(daemon=True)
        self.persona_id = persona_id
        self.message = message
        self.history = history
        self.provider = provider
        self.result_queue = result_queue

    def run(self) -> None:
        try:
            # 导入 LLM
            from llm_client import LLMClient, Message
            client = LLMClient(provider=self.provider)
            # 加载 persona(优先 builtin 中文名)
            persona_path = os.path.join(ROOT, "data", "personas", f"{self.persona_id}.json")
            bg = ""
            with open(persona_path, "r", encoding="utf-8") as f:
                pdata = json.load(f)
            try:
                from persona import BUILTIN_PERSONAS
                if self.persona_id in BUILTIN_PERSONAS:
                    bg = BUILTIN_PERSONAS[self.persona_id].get("background", "")
            except ImportError:
                pass
            if not bg:
                bg = pdata.get("background", "")
            # 构造 messages
            msgs = []
            if bg:
                msgs.append(Message(role="system", content=bg))
            for h in self.history:
                msgs.append(Message(role=h["role"], content=h["content"]))
            msgs.append(Message(role="user", content=self.message))
            # 调 LLM
            t0 = time.time()
            resp = client.chat(messages=msgs)
            latency_ms = int((time.time() - t0) * 1000)
            self.result_queue.put({
                "ok": True,
                "content": resp.content,
                "model": resp.model,
                "tokens": resp.usage.get("total_tokens", 0),
                "cost": resp.cost_usd,
                "latency_ms": latency_ms,
            })
        except Exception as e:
            self.result_queue.put({"ok": False, "error": str(e)})


# ============== UI 组件 ==============

class PersonaCard(tk.Frame):
    """侧边栏里的 persona 卡片"""

    def __init__(self, parent, persona_id: str, on_click, **kwargs):
        super().__init__(parent, **kwargs)
        self.persona_id = persona_id
        self.on_click = on_click
        meta = PERSONAS_META[persona_id]

        # 头像 + 名字
        self.avatar = tk.Label(self, text=meta["emoji"], font=("Helvetica", 28),
                               bg=kwargs.get("bg", "#f5f5f7"), padx=8, pady=4)
        self.avatar.pack(side=tk.LEFT)

        info = tk.Frame(self, bg=kwargs.get("bg", "#f5f5f7"))
        info.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 8))
        tk.Label(info, text=meta["name"], font=("Helvetica", 13, "bold"),
                 bg=kwargs.get("bg", "#f5f5f7"), anchor="w").pack(fill=tk.X)
        tk.Label(info, text=meta["subtitle"], font=("Helvetica", 10),
                 bg=kwargs.get("bg", "#f5f5f7"), fg="#666", anchor="w").pack(fill=tk.X)

        # 整卡片可点
        for w in (self, self.avatar, info, *info.winfo_children()):
            w.bind("<Button-1>", self._click)
            w.bind("<Enter>", self._on_enter)
            w.bind("<Leave>", self._on_leave)

        self.default_bg = kwargs.get("bg", "#f5f5f7")
        self.hover_bg = "#e8e8ed"

    def _click(self, _evt=None):
        self.on_click(self.persona_id)

    def _on_enter(self, _evt=None):
        if not getattr(self, "active", False):
            self._set_bg(self.hover_bg)

    def _on_leave(self, _evt=None):
        if not getattr(self, "active", False):
            self._set_bg(self.default_bg)

    def _set_bg(self, color):
        self.configure(bg=color)
        for child in self.winfo_children():
            try:
                child.configure(bg=color)
            except tk.TclError:
                pass

    def set_active(self, active: bool):
        self.active = active
        if active:
            self._set_bg(PERSONAS_META[self.persona_id]["color"])
        else:
            self._set_bg(self.default_bg)


class MessageBubble(tk.Frame):
    """聊天气泡"""

    def __init__(self, parent, role: str, text: str, meta: Optional[Dict[str, Any]] = None, **kwargs):
        # 提取自定义参数,不传给 Frame
        container_bg = kwargs.pop("container_bg", "#fafafa")
        persona_name = kwargs.pop("persona_name", "AI")
        persona_color = kwargs.pop("persona_color", "#666")
        super().__init__(parent, **kwargs)
        self.role = role
        self.bg = "#f0f4f8" if role == "user" else "#ffffff"
        # 名字 + 气泡
        if role == "user":
            name = "我"
            color = "#1976d2"
            anchor = tk.E
        else:
            name = persona_name
            color = persona_color
            anchor = tk.W
        # 名字
        name_lbl = tk.Label(self, text=name, font=("Helvetica", 10, "bold"),
                            fg=color, bg=container_bg, anchor=anchor)
        name_lbl.pack(fill=tk.X, padx=8, pady=(4, 0))
        # 气泡
        bubble = tk.Label(self, text=text, font=("Helvetica", 12),
                          bg=self.bg, fg="#222", wraplength=480, justify=tk.LEFT,
                          padx=12, pady=8, anchor=tk.W, relief=tk.FLAT)
        bubble.pack(fill=tk.X, padx=8, pady=(0, 2))
        # meta
        if meta:
            mtxt = f"{meta.get('model', '')} · {meta.get('tokens', 0)} tokens · ${meta.get('cost', 0):.4f} · {meta.get('latency_ms', 0)}ms"
            meta_lbl = tk.Label(self, text=mtxt, font=("Helvetica", 9),
                                fg="#999", bg=container_bg, anchor=anchor)
            meta_lbl.pack(fill=tk.X, padx=8, pady=(0, 6))


# ============== 主应用 ==============

class AichatApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(WINDOW_TITLE)
        self.root.geometry("960x640")
        self.root.minsize(720, 480)

        # macOS 专用设置
        if sys.platform == "darwin":
            try:
                self.root.createcommand("::tk::mac::ShowPreferences", self._open_settings)
            except tk.TclError:
                pass

        # 状态
        self.current_persona = "xiaoai"
        self.history: List[Dict[str, str]] = []  # 当前 session 历史
        self.all_history: Dict[str, List[Dict[str, str]]] = {}  # 按 persona 存
        self.result_queue: queue.Queue = queue.Queue()
        self.is_thinking = False
        self.worker: Optional[ChatWorker] = None

        # 加载
        self.settings = load_json(get_settings_path(), {"provider": "mock"})
        self.all_history = load_json(get_history_path(), {
            "xiaoai": [], "dr_li": [], "xiaozhi": []
        })
        self.history = list(self.all_history.get(self.current_persona, []))

        # 字体
        self.font_default = tkfont.Font(family="Helvetica", size=12)
        self.font_bold = tkfont.Font(family="Helvetica", size=12, weight="bold")

        # 样式
        self._setup_styles()
        # 构建 UI
        self._build_layout()
        self._build_menu()

        # 启动 queue 检查
        self.root.after(100, self._poll_queue)
        # 关闭处理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # 启动时:历史已加载,直接渲染
        self._render_history()

    # ---------- 样式 ----------

    def _setup_styles(self) -> None:
        style = ttk.Style()
        # 尝试 native theme
        if sys.platform == "darwin":
            try:
                style.theme_use("aqua")
            except tk.TclError:
                style.theme_use("default")
        else:
            try:
                style.theme_use("clam")
            except tk.TclError:
                pass
        # 自定义
        style.configure("Send.TButton", font=("Helvetica", 11, "bold"), padding=(20, 8))
        style.configure("Sidebar.TFrame", background="#f5f5f7")

    # ---------- 菜单 ----------

    def _build_menu(self) -> None:
        menubar = tk.Menu(self.root)

        # File
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建对话", accelerator="Cmd+N",
                              command=self._new_chat)
        file_menu.add_command(label="清空当前对话", accelerator="Cmd+K",
                              command=self._clear_chat)
        file_menu.add_separator()
        file_menu.add_command(label="打开 Web Dashboard…", command=self._open_dashboard)
        file_menu.add_separator()
        if sys.platform == "darwin":
            file_menu.add_command(label="设置…", accelerator="Cmd+,", command=self._open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="退出 aichat-hub", accelerator="Cmd+Q",
                              command=self._on_close)
        menubar.add_cascade(label="File", menu=file_menu)

        # Edit
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="清空", command=self._clear_chat)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        # Persona
        persona_menu = tk.Menu(menubar, tearoff=0)
        persona_menu.add_command(label="小爱 🌸", accelerator="Cmd+1",
                                 command=lambda: self._switch_persona("xiaoai"))
        persona_menu.add_command(label="李医生 🩺", accelerator="Cmd+2",
                                 command=lambda: self._switch_persona("dr_li"))
        persona_menu.add_command(label="小智 💻", accelerator="Cmd+3",
                                 command=lambda: self._switch_persona("xiaozhi"))
        menubar.add_cascade(label="Persona", menu=persona_menu)

        # View
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="Dashboard", command=self._open_dashboard)
        menubar.add_cascade(label="View", menu=view_menu)

        # Help
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于 aichat-hub", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

        # 快捷键
        self.root.bind_all("<Command-n>", lambda e: self._new_chat())
        self.root.bind_all("<Command-k>", lambda e: self._clear_chat())
        self.root.bind_all("<Command-q>", lambda e: self._on_close())
        self.root.bind_all("<Command-1>", lambda e: self._switch_persona("xiaoai"))
        self.root.bind_all("<Command-2>", lambda e: self._switch_persona("dr_li"))
        self.root.bind_all("<Command-3>", lambda e: self._switch_persona("xiaozhi"))
        # Return 发送
        self.input_text.bind("<Return>", self._on_enter_key)
        self.input_text.bind("<Shift-Return>", lambda e: None)  # 允许换行

    # ---------- 布局 ----------

    def _build_layout(self) -> None:
        # 整体:左右两栏
        self.root.configure(bg="#fafafa")
        container = tk.Frame(self.root, bg="#fafafa")
        container.pack(fill=tk.BOTH, expand=True)

        # ---- 左侧 sidebar ----
        sidebar = tk.Frame(container, bg="#f5f5f7", width=240)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # 标题
        tk.Label(sidebar, text="🤖 aichat-hub", font=("Helvetica", 16, "bold"),
                 bg="#f5f5f7", fg="#222", anchor="w").pack(fill=tk.X, padx=16, pady=(16, 4))
        tk.Label(sidebar, text=f"v{APP_VERSION}", font=("Helvetica", 10),
                 bg="#f5f5f7", fg="#999", anchor="w").pack(fill=tk.X, padx=16, pady=(0, 12))

        tk.Label(sidebar, text="选择 Persona", font=("Helvetica", 11, "bold"),
                 bg="#f5f5f7", fg="#666", anchor="w").pack(fill=tk.X, padx=16, pady=(8, 8))

        self.persona_cards = {}
        for pid in ["xiaoai", "dr_li", "xiaozhi"]:
            card = PersonaCard(sidebar, persona_id=pid, on_click=self._switch_persona, bg="#f5f5f7")
            card.pack(fill=tk.X, padx=8, pady=4)
            self.persona_cards[pid] = card
        self.persona_cards[self.current_persona].set_active(True)

        # 底部:provider + dashboard 链接
        bottom = tk.Frame(sidebar, bg="#f5f5f7")
        bottom.pack(side=tk.BOTTOM, fill=tk.X, padx=16, pady=16)
        tk.Label(bottom, text="Provider:", font=("Helvetica", 9),
                 bg="#f5f5f7", fg="#666", anchor="w").pack(fill=tk.X)
        self.provider_var = tk.StringVar(value=self.settings.get("provider", "mock"))
        prov_combo = ttk.Combobox(bottom, textvariable=self.provider_var,
                                   values=["mock", "openai", "deepseek", "zhipu",
                                           "dashscope", "moonshot", "anthropic"],
                                   state="readonly", width=20)
        prov_combo.pack(fill=tk.X, pady=(2, 8))
        prov_combo.bind("<<ComboboxSelected>>", lambda e: self._save_settings())

        # ---- 右侧 main ----
        main = tk.Frame(container, bg="#fafafa")
        main.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 顶部:persona 标题
        topbar = tk.Frame(main, bg="#ffffff", height=56)
        topbar.pack(fill=tk.X)
        topbar.pack_propagate(False)
        self.title_label = tk.Label(topbar, text="", font=("Helvetica", 16, "bold"),
                                     bg="#ffffff", anchor="w", padx=20)
        self.title_label.pack(side=tk.LEFT, fill=tk.Y)
        self.status_label = tk.Label(topbar, text="● 在线", font=("Helvetica", 10),
                                      bg="#ffffff", fg="#3fb950", padx=20)
        self.status_label.pack(side=tk.RIGHT, fill=tk.Y)
        # separator
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(fill=tk.X)

        # 中间:chat 滚动区
        chat_container = tk.Frame(main, bg="#fafafa")
        chat_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)

        self.canvas = tk.Canvas(chat_container, bg="#fafafa", highlightthickness=0)
        scrollbar = ttk.Scrollbar(chat_container, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#fafafa")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        # 宽度跟随
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # 鼠标滚轮
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        # 底部:输入区
        input_bar = tk.Frame(main, bg="#ffffff", height=80)
        input_bar.pack(fill=tk.X, side=tk.BOTTOM)
        input_bar.pack_propagate(False)
        ttk.Separator(main, orient=tk.HORIZONTAL).pack(side=tk.BOTTOM, fill=tk.X)
        input_inner = tk.Frame(input_bar, bg="#ffffff")
        input_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=12)

        self.input_text = tk.Text(input_inner, font=("Helvetica", 13), height=2,
                                   wrap=tk.WORD, bd=0, bg="#f5f5f7", relief=tk.FLAT,
                                   padx=12, pady=10)
        self.input_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.input_text.focus_set()

        self.send_btn = tk.Button(input_inner, text="发送 ↩", font=("Helvetica", 12, "bold"),
                                   bg="#1976d2", fg="white", activebackground="#1565c0",
                                   activeforeground="white", relief=tk.FLAT, bd=0,
                                   padx=20, pady=8, cursor="hand2",
                                   command=self._on_send)
        self.send_btn.pack(side=tk.RIGHT, padx=(12, 0))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        if sys.platform == "darwin":
            self.canvas.yview_scroll(int(-event.delta), "units")
        else:
            self.canvas.yview_scroll(int(-event.delta / 120), "units")

    # ---------- 行为 ----------

    def _switch_persona(self, persona_id: str) -> None:
        if persona_id not in PERSONAS_META:
            return
        if persona_id == self.current_persona:
            return
        # 保存当前
        self.all_history[self.current_persona] = self.history
        # 切换
        self.current_persona = persona_id
        self.history = list(self.all_history.get(persona_id, []))
        # 更新 UI
        for pid, card in self.persona_cards.items():
            card.set_active(pid == persona_id)
        self._refresh_title()
        self._render_history()
        self._save_history()

    def _refresh_title(self) -> None:
        meta = PERSONAS_META[self.current_persona]
        self.title_label.config(text=f"{meta['emoji']} {meta['name']}")

    def _render_history(self) -> None:
        # 清空
        for w in self.scrollable_frame.winfo_children():
            w.destroy()
        if not self.history:
            self._render_empty_state()
            return
        meta = PERSONAS_META[self.current_persona]
        for h in self.history:
            self._add_bubble(h["role"], h["content"],
                             persona_name=meta["name"], persona_color=meta["color"])
        self.canvas.yview_moveto(1.0)

    def _render_empty_state(self) -> None:
        meta = PERSONAS_META[self.current_persona]
        frame = tk.Frame(self.scrollable_frame, bg="#fafafa", pady=60)
        frame.pack(fill=tk.X, expand=True)
        tk.Label(frame, text=meta["emoji"], font=("Helvetica", 60), bg="#fafafa").pack()
        tk.Label(frame, text=meta["name"], font=("Helvetica", 22, "bold"),
                 bg="#fafafa", fg="#333").pack(pady=(8, 4))
        tk.Label(frame, text=meta["subtitle"], font=("Helvetica", 12),
                 bg="#fafafa", fg="#999").pack()
        greeting_path = os.path.join(ROOT, "data", "personas", f"{self.current_persona}.json")
        try:
            with open(greeting_path, "r", encoding="utf-8") as f:
                pd = json.load(f)
            greeting = pd.get("greeting", "")
        except Exception:
            greeting = ""
        if greeting:
            tk.Label(frame, text=greeting, font=("Helvetica", 13),
                     bg="#fafafa", fg="#666", wraplength=480, pady=20).pack()
        tk.Label(frame, text="↓ 在下面输入消息开始对话",
                 font=("Helvetica", 11), bg="#fafafa", fg="#bbb").pack(pady=10)

    def _add_bubble(self, role: str, text: str, meta: Optional[Dict[str, Any]] = None,
                    persona_name: str = "AI", persona_color: str = "#666") -> None:
        bubble = MessageBubble(self.scrollable_frame, role=role, text=text, meta=meta,
                                persona_name=persona_name, persona_color=persona_color,
                                container_bg="#fafafa")
        bubble.pack(fill=tk.X, pady=4)
        self.canvas.yview_moveto(1.0)
        return bubble

    def _on_enter_key(self, event):
        # Shift+Enter 换行,Enter 发送
        if event.state & 0x1:  # shift
            return None
        self._on_send()
        return "break"

    def _on_send(self) -> None:
        if self.is_thinking:
            return
        text = self.input_text.get("1.0", tk.END).strip()
        if not text:
            return
        self.input_text.delete("1.0", tk.END)
        # 加 user 气泡
        self._add_bubble("user", text)
        self.history.append({"role": "user", "content": text})
        self.all_history[self.current_persona] = self.history
        # 思考中
        self._set_thinking(True)
        self._add_thinking_bubble()
        # 后台 worker
        self.worker = ChatWorker(
            persona_id=self.current_persona,
            message=text,
            history=self.history[:-1],  # worker 自己会加 user
            provider=self.provider_var.get(),
            result_queue=self.result_queue,
        )
        self.worker.start()

    def _add_thinking_bubble(self) -> None:
        meta = PERSONAS_META[self.current_persona]
        # 用 emoji 当 typing indicator
        self.thinking_frame = tk.Frame(self.scrollable_frame, bg="#fafafa")
        self.thinking_frame.pack(fill=tk.X, pady=4)
        tk.Label(self.thinking_frame, text=meta["name"], font=("Helvetica", 10, "bold"),
                 fg=meta["color"], bg="#fafafa", anchor="w").pack(fill=tk.X, padx=8)
        self.thinking_label = tk.Label(
            self.thinking_frame,
            text=f"{meta['emoji']} 思考中.",
            font=("Helvetica", 12), bg="#ffffff", fg="#666",
            padx=12, pady=8, anchor=tk.W,
        )
        self.thinking_label.pack(fill=tk.X, padx=8)
        self.canvas.yview_moveto(1.0)
        self._animate_thinking(0)

    def _animate_thinking(self, dot: int) -> None:
        if not hasattr(self, "thinking_label") or not self.thinking_label.winfo_exists():
            return
        meta = PERSONAS_META[self.current_persona]
        dots = "." * (dot % 4)
        self.thinking_label.config(text=f"{meta['emoji']} 思考中{dots}")
        self.root.after(300, self._animate_thinking, dot + 1)

    def _set_thinking(self, thinking: bool) -> None:
        self.is_thinking = thinking
        if thinking:
            self.send_btn.config(state=tk.DISABLED, text="思考中...", bg="#999")
        else:
            self.send_btn.config(state=tk.NORMAL, text="发送 ↩", bg="#1976d2")

    def _poll_queue(self) -> None:
        try:
            result = self.result_queue.get_nowait()
        except queue.Empty:
            self.root.after(100, self._poll_queue)
            return
        # 移除 thinking
        if hasattr(self, "thinking_frame") and self.thinking_frame.winfo_exists():
            self.thinking_frame.destroy()
        self._set_thinking(False)
        # 处理结果
        meta = PERSONAS_META[self.current_persona]
        if result.get("ok"):
            content = result["content"]
            self._add_bubble("assistant", content, meta={
                "model": result.get("model", ""),
                "tokens": result.get("tokens", 0),
                "cost": result.get("cost", 0),
                "latency_ms": result.get("latency_ms", 0),
            }, persona_name=meta["name"], persona_color=meta["color"])
            self.history.append({"role": "assistant", "content": content})
            self.all_history[self.current_persona] = self.history
            self._save_history()
            self._update_status(f"● 在线 · {result.get('tokens', 0)} tokens · ${result.get('cost', 0):.4f} · {result.get('latency_ms', 0)}ms")
        else:
            err = result.get("error", "未知错误")
            self._add_bubble("assistant", f"❌ {err}", persona_name="错误", persona_color="#da3633")
            self._update_status(f"● 出错", "#da3633")
        self.root.after(100, self._poll_queue)

    def _update_status(self, text: str, color: str = "#3fb950") -> None:
        self.status_label.config(text=text, fg=color)

    # ---------- 操作 ----------

    def _new_chat(self) -> None:
        self._clear_chat()

    def _clear_chat(self) -> None:
        self.history = []
        self.all_history[self.current_persona] = []
        self._save_history()
        self._render_history()

    def _open_dashboard(self) -> None:
        webbrowser.open("http://127.0.0.1:8765/api/dashboard/html")

    def _open_settings(self) -> None:
        # macOS 标准 Cmd+, 打开设置(简化:弹个 info)
        self._show_about()

    def _show_about(self) -> None:
        top = tk.Toplevel(self.root)
        top.title("关于 aichat-hub")
        top.geometry("420x320")
        top.resizable(False, False)
        if sys.platform == "darwin":
            top.wait_visibility()
            top.transient(self.root)
        f = tk.Frame(top, padx=24, pady=24)
        f.pack(fill=tk.BOTH, expand=True)
        tk.Label(f, text="🤖 aichat-hub", font=("Helvetica", 24, "bold")).pack(pady=(0, 4))
        tk.Label(f, text=f"v{APP_VERSION}", font=("Helvetica", 12), fg="#666").pack()
        tk.Label(f, text="中国大学生职业领英替代 + 数字虚拟人界面",
                 font=("Helvetica", 11), wraplength=360, justify=tk.CENTER).pack(pady=(16, 8))
        tk.Label(f, text="26 scripts · 26 tests · 74 endpoints\n60 arxiv papers · 28 market research",
                 font=("Helvetica", 10), fg="#888", justify=tk.CENTER).pack(pady=8)
        tk.Label(f, text="纯 Python stdlib · MIT License",
                 font=("Helvetica", 10), fg="#aaa").pack(pady=(16, 0))
        tk.Button(f, text="关闭", command=top.destroy, padx=20).pack(pady=(16, 0))

    def _save_settings(self) -> None:
        self.settings["provider"] = self.provider_var.get()
        save_json(get_settings_path(), self.settings)

    def _save_history(self) -> None:
        save_json(get_history_path(), self.all_history)

    def _on_close(self) -> None:
        self._save_history()
        self._save_settings()
        self.root.destroy()

    def run(self) -> None:
        self._refresh_title()
        self._update_status(f"● 在线 · Provider: {self.provider_var.get()}")
        self.root.mainloop()


# ============== CLI ==============

def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="aichat-hub 桌面 app")
    parser.add_argument("--provider", default=None, help="LLM provider (mock/openai/...)")
    parser.add_argument("--persona", default=None, help="初始 persona (xiaoai/dr_li/xiaozhi)")
    args = parser.parse_args()

    if sys.platform == "darwin":
        # macOS 激活策略:作为独立 app 而非命令行工具
        try:
            from tkinter import _default_root
            # 让 Dock 看到图标
            import subprocess
            subprocess.Popen(["defaults", "write", "com.apple.dt.TinkerTool", "DTPath", "1"])
        except Exception:
            pass

    # 确保 python3.13+ (老 python 的 tk 在 macOS 15 崩)
    if sys.version_info < (3, 12):
        print(f"⚠️  python {sys.version_info[:2]} 太老,macOS 15+ 上的 tkinter 会崩")
        print(f"    建议:python3.13 scripts/desktop_app.py")
        print(f"    当前仍尝试启动...")

    app = AichatApp()
    if args.provider:
        app.provider_var.set(args.provider)
        app._save_settings()
    if args.persona and args.persona in PERSONAS_META:
        app._switch_persona(args.persona)
    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
