#!/usr/bin/env python3
"""
aichat-Hub Paper Chat (论文对话) 模块
=====================================
基于已有 50+ arXiv 论文(cycle 21)的多轮对话系统。

核心能力:
  1. 多轮对话 session(类似 cycle 12 interview)
  2. 检索增强:从 50+ 论文找相关
  3. 4 回答模板:列表 / 对比 / 核心观点 / 研究路径
  4. 自动引用:APA / IEEE / BibTeX / 自然语言
  5. 沙箱安全:无 LLM 依赖,纯规则化

Cycle 22 — v0.6 学术模式核心模块
"""
from __future__ import annotations
import json
import re
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


# ============== 数据模型 ==============

@dataclass
class ChatMessage:
    """对话消息"""
    role: str             # "user" / "assistant"
    content: str
    citations: List[str] = field(default_factory=list)  # 引用的 arxiv_id
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PaperChatSession:
    """论文对话 session"""
    id: str
    user_id: str
    topic: str = ""
    messages: List[ChatMessage] = field(default_factory=list)
    round_idx: int = 0
    completed: bool = False
    started_at: float = field(default_factory=time.time)
    ended_at: float = 0.0

    def add_message(self, message: ChatMessage):
        self.messages.append(message)
        if message.role == "assistant":
            self.round_idx += 1

    def end(self):
        self.completed = True
        self.ended_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "topic": self.topic,
            "messages": [m.to_dict() for m in self.messages],
            "round_idx": self.round_idx,
            "completed": self.completed,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
        }


# ============== 检索 ==============

def _search_relevant_papers(keyword: str, top_n: int = 5) -> List[Dict[str, Any]]:
    """检索相关论文(基于关键词 + 摘要匹配)"""
    from papers import _get_paper_index
    kw = keyword.lower()
    # 评分:title 命中 +3 / abstract 命中 +2 / category 命中 +1
    scored = []
    for p in _get_paper_index():
        score = 0
        title_lower = p.title.lower()
        abstract_lower = p.abstract.lower()
        if kw in title_lower:
            score += 3
        if kw in abstract_lower:
            score += 2
        if any(kw in c.lower() for c in p.categories):
            score += 1
        # 多关键词分割
        for word in kw.split():
            if word in title_lower:
                score += 1
            if word in abstract_lower:
                score += 0.5
        if score > 0:
            scored.append((score, p))
    scored.sort(key=lambda x: -x[0])
    return [p.to_dict() for _, p in scored[:top_n]]


# ============== 回答模板 ==============

def _format_paper_brief(paper: Dict[str, Any]) -> str:
    """格式化论文简要"""
    title = paper.get("title", "Untitled")
    year = paper.get("year", "")
    abstract = paper.get("abstract", "")
    brief = abstract[:100].strip()
    if len(abstract) > 100:
        brief += "..."
    return f"《{title}》({year}) - {brief}"


def _format_template_list(keyword: str, papers: List[Dict[str, Any]], citations: List[str]) -> str:
    """模板 1:相关论文列表"""
    if not papers:
        return f"抱歉,关于「{keyword}」未找到相关论文。"
    parts = [f"关于「{keyword}」,推荐以下 {len(papers)} 篇相关论文:\n"]
    for i, p in enumerate(papers, 1):
        title = p.get("title", "Untitled")
        year = p.get("year", "")
        abstract = p.get("abstract", "")
        brief = abstract[:80].strip()
        if len(abstract) > 80:
            brief += "..."
        parts.append(f"{i}. 《{title}》({year}) - {brief} [{i}]")
    parts.append(f"\n引用:共 {len(papers)} 篇")
    return "\n".join(parts)


def _format_template_compare(keyword: str, papers: List[Dict[str, Any]], citations: List[str]) -> str:
    """模板 2:对比分析(2-3 篇)"""
    if len(papers) < 2:
        return _format_template_list(keyword, papers, citations)
    parts = [f"关于「{keyword}」,对比 {len(papers)} 篇代表性论文:\n"]
    for i, p in enumerate(papers[:3], 1):
        title = p.get("title", "Untitled")
        authors = p.get("authors", [])
        author = authors[0] if authors else "Unknown"
        year = p.get("year", "")
        abstract = p.get("abstract", "")
        parts.append(f"**{i}. {title}**")
        parts.append(f"   作者:{author} et al. ({year})")
        parts.append(f"   摘要:{abstract[:150].strip()}{'...' if len(abstract) > 150 else ''}")
        parts.append(f"   [{i}]")
        parts.append("")
    parts.append("**对比建议**:")
    parts.append(f"- 共 {len(papers[:3])} 篇核心论文")
    parts.append("- 建议先读第 1 篇入门,再读后续深入")
    return "\n".join(parts)


def _format_template_keyview(keyword: str, papers: List[Dict[str, Any]], citations: List[str]) -> str:
    """模板 3:核心观点(单篇深入)"""
    if not papers:
        return f"抱歉,关于「{keyword}」未找到相关论文。"
    p = papers[0]  # 最相关 1 篇
    parts = []
    title = p.get("title", "Untitled")
    authors = p.get("authors", [])
    author_str = authors[0] if authors else "Unknown"
    year = p.get("year", "")
    abstract = p.get("abstract", "")
    parts.append(f"关于「{keyword}」,最相关的论文是:\n")
    parts.append(f"**《{title}》**")
    parts.append(f"作者:{author_str} et al. ({year})")
    parts.append(f"\n**核心观点**:")
    parts.append(f"{abstract}\n")
    parts.append(f"[1] {author_str} et al. ({year}). {title}. arXiv:{p.get('arxiv_id', '')}.")
    return "\n".join(parts)


def _format_template_path(keyword: str, papers: List[Dict[str, Any]], citations: List[str]) -> str:
    """模板 4:研究路径(入门 → 进阶 → 前沿)"""
    if not papers:
        return f"抱歉,关于「{keyword}」未找到相关论文。"
    parts = [f"学习「{keyword}」,建议按以下研究路径:\n"]
    stages = ["入门(基础概念)", "进阶(核心方法)", "前沿(最新进展)"]
    # 简单分桶:按年份分(老 → 新)
    sorted_papers = sorted(papers, key=lambda x: x.get("year", 0))
    for i, (stage, paper) in enumerate(zip(stages, sorted_papers[:3]), 1):
        title = paper.get("title", "Untitled")
        year = paper.get("year", "")
        abstract = paper.get("abstract", "")
        parts.append(f"**{i}. {stage}**")
        parts.append(f"   《{title}》({year})")
        parts.append(f"   {abstract[:80].strip()}{'...' if len(abstract) > 80 else ''}")
        parts.append(f"   [{i}]")
        parts.append("")
    return "\n".join(parts)


TEMPLATE_FORMATTERS = {
    "list": _format_template_list,
    "compare": _format_template_compare,
    "keyview": _format_template_keyview,
    "path": _format_template_path,
}


# ============== 意图识别(简单) ==============

def _detect_intent(question: str) -> str:
    """检测问题意图(选择模板)"""
    q = question.lower()
    if any(w in q for w in ["对比", "区别", "比较", "vs", "difference"]):
        return "compare"
    if any(w in q for w in ["核心", "观点", "看法", "认为", "思想"]):
        return "keyview"
    if any(w in q for w in ["路径", "怎么学", "入门", "怎么开始", "学习"]):
        return "path"
    # 默认列表
    return "list"


# ============== 核心 API ==============

def start_chat(user_id: str, topic: str = "") -> PaperChatSession:
    """开启论文对话"""
    sid = str(uuid.uuid4())[:8]
    session = PaperChatSession(id=sid, user_id=user_id, topic=topic)
    # 添加欢迎消息
    if topic:
        welcome = f"欢迎来到论文对话!主题:{topic}。请问您想了解什么?"
    else:
        welcome = "欢迎来到论文对话!请问您想了解什么主题?"
    session.add_message(ChatMessage(role="assistant", content=welcome))
    return session


def ask(session: PaperChatSession, question: str) -> ChatMessage:
    """提问并返回回答 + 引用"""
    if session.completed:
        raise ValueError("Chat already completed")
    # 记录用户问题
    session.add_message(ChatMessage(role="user", content=question))
    # 检索相关论文
    papers = _search_relevant_papers(question, top_n=5)
    citations = [p.get("arxiv_id", "") for p in papers if p.get("arxiv_id")]
    # 检测意图,选择模板
    intent = _detect_intent(question)
    formatter = TEMPLATE_FORMATTERS.get(intent, _format_template_list)
    answer = formatter(question, papers, citations)
    # 记录助手回答
    response = ChatMessage(role="assistant", content=answer, citations=citations)
    session.add_message(response)
    return response


def end_chat(session: PaperChatSession) -> Dict[str, Any]:
    """结束对话,返回总结"""
    if not session.completed:
        # 添加结束消息
        summary = f"本次对话共 {session.round_idx} 轮,引用了 {len(set(c for m in session.messages for c in m.citations))} 篇论文。"
        session.add_message(ChatMessage(role="assistant", content=summary))
        session.end()
    return {
        "session_id": session.id,
        "total_rounds": session.round_idx,
        "total_messages": len(session.messages),
        "unique_citations": len(set(c for m in session.messages for c in m.citations)),
        "duration_seconds": round(session.ended_at - session.started_at, 2) if session.ended_at else 0,
    }


# ============== 内存 session ==============

_PAPER_CHAT_SESSIONS: Dict[str, PaperChatSession] = {}


def save_session(session: PaperChatSession) -> str:
    _PAPER_CHAT_SESSIONS[session.id] = session
    return session.id


def get_session(session_id: str) -> Optional[PaperChatSession]:
    return _PAPER_CHAT_SESSIONS.get(session_id)


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 paper_chat.py {start|ask|end}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "start":
        user_id = sys.argv[2] if len(sys.argv) > 2 else "cli_user"
        topic = sys.argv[3] if len(sys.argv) > 3 else ""
        s = start_chat(user_id, topic)
        save_session(s)
        print(f"Session {s.id} started, topic: {topic or '(none)'}")
        print(f"Welcome: {s.messages[0].content}")
    elif cmd == "ask":
        if len(sys.argv) < 4:
            print("Usage: ... ask <session_id> <question>", file=sys.stderr)
            sys.exit(1)
        sid = sys.argv[2]
        s = get_session(sid)
        if s is None:
            print("Session not found", file=sys.stderr)
            sys.exit(1)
        question = " ".join(sys.argv[3:])
        r = ask(s, question)
        print(f"\n回答:\n{r.content}")
        if r.citations:
            print(f"\n引用:{' / '.join(r.citations)}")
    elif cmd == "end":
        if len(sys.argv) < 3:
            print("Usage: ... end <session_id>", file=sys.stderr)
            sys.exit(1)
        s = get_session(sys.argv[2])
        if s is None:
            print("Session not found", file=sys.stderr)
            sys.exit(1)
        summary = end_chat(s)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
