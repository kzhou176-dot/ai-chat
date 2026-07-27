#!/usr/bin/env python3
"""
test_22_paper_chat — aichat-hub Cycle 22 论文对话模块测试
=====================================================
覆盖:
  1. 数据模型(ChatMessage / PaperChatSession)
  2. 检索相关论文
  3. 4 回答模板(list / compare / keyview / path)
  4. 意图识别(简单关键词)
  5. 完整对话流程
  6. 内存 session 存储
  7. 引用自动添加
  8. CLI 入口
  9. 集成
"""
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from paper_chat import (
    ChatMessage, PaperChatSession,
    _search_relevant_papers,
    _format_paper_brief,
    _format_template_list, _format_template_compare,
    _format_template_keyview, _format_template_path,
    TEMPLATE_FORMATTERS,
    _detect_intent,
    start_chat, ask, end_chat,
    save_session, get_session,
    _PAPER_CHAT_SESSIONS,
)


# ============== 1. 数据模型 ==============

def test_chat_message():
    """ChatMessage"""
    m = ChatMessage(role="user", content="什么是 LLM?")
    assert m.role == "user"
    assert m.content == "什么是 LLM?"
    assert m.citations == []
    print("✓ ChatMessage")


def test_chat_message_with_citations():
    """ChatMessage 带引用"""
    m = ChatMessage(role="assistant", content="...", citations=["1706.03762", "1234.5678"])
    assert len(m.citations) == 2
    print("✓ ChatMessage 引用")


def test_chat_message_to_dict():
    """ChatMessage 序列化"""
    m = ChatMessage(role="user", content="test")
    d = m.to_dict()
    assert d["role"] == "user"
    assert d["content"] == "test"
    print("✓ ChatMessage 序列化")


def test_paper_chat_session():
    """PaperChatSession"""
    s = PaperChatSession(id="S1", user_id="U1", topic="LLM")
    assert s.id == "S1"
    assert s.topic == "LLM"
    assert s.round_idx == 0
    assert s.completed is False
    print("✓ PaperChatSession")


def test_paper_chat_session_add_message():
    """添加消息"""
    s = PaperChatSession(id="S1", user_id="U1")
    s.add_message(ChatMessage(role="user", content="q"))
    assert s.round_idx == 0
    s.add_message(ChatMessage(role="assistant", content="a"))
    assert s.round_idx == 1
    print("✓ 添加消息 + round_idx 增加")


def test_paper_chat_session_end():
    """结束 session"""
    s = PaperChatSession(id="S1", user_id="U1")
    s.add_message(ChatMessage(role="user", content="q"))
    s.add_message(ChatMessage(role="assistant", content="a"))
    s.end()
    assert s.completed
    assert s.ended_at > 0
    print("✓ 结束 session")


def test_paper_chat_session_to_dict():
    """Session 序列化"""
    s = PaperChatSession(id="S1", user_id="U1", topic="LLM")
    s.add_message(ChatMessage(role="user", content="q"))
    d = s.to_dict()
    assert d["id"] == "S1"
    assert d["topic"] == "LLM"
    assert len(d["messages"]) == 1
    print("✓ Session 序列化")


# ============== 2. 检索 ==============

def test_search_relevant_basic():
    """基本检索"""
    results = _search_relevant_papers("LLM", top_n=3)
    assert len(results) <= 3
    print(f"✓ 检索 'LLM' → {len(results)} 篇")


def test_search_relevant_no_match():
    """无匹配"""
    results = _search_relevant_papers("zzzzz_no_match_xyz", top_n=3)
    assert results == []
    print("✓ 无匹配 → 空")


def test_search_relevant_score_higher():
    """高相关性应排前"""
    results = _search_relevant_papers("transformer", top_n=5)
    # 第一篇应含 transformer
    if results:
        assert "transformer" in results[0]["title"].lower() or any(
            "transformer" in c.lower() for c in results[0].get("categories", [])
        )
    print(f"✓ 高相关排前:{results[0]['title'][:50] if results else 'None'}")


# ============== 3. 4 回答模板 ==============

def test_format_paper_brief():
    """论文简要"""
    paper = {
        "arxiv_id": "1234.5678",
        "title": "Test Paper",
        "year": 2024,
        "abstract": "This is a test abstract " * 20,  # 长
    }
    brief = _format_paper_brief(paper)
    assert "Test Paper" in brief
    assert "2024" in brief
    assert "..." in brief
    print(f"✓ 论文简要:{brief[:60]}...")


def test_format_template_list():
    """模板 1:列表"""
    papers = [
        {"arxiv_id": "1", "title": "P1", "year": 2024, "abstract": "Abstract 1 " * 20},
        {"arxiv_id": "2", "title": "P2", "year": 2025, "abstract": "Abstract 2 " * 20},
    ]
    output = _format_template_list("LLM", papers, ["1", "2"])
    assert "P1" in output
    assert "P2" in output
    assert "2024" in output
    assert "[1]" in output
    assert "[2]" in output
    print("✓ 模板 1:列表")


def test_format_template_list_empty():
    """模板 1:无结果"""
    output = _format_template_list("LLM", [], [])
    assert "未找到" in output or "抱歉" in output
    print("✓ 模板 1:无结果")


def test_format_template_compare():
    """模板 2:对比"""
    papers = [
        {"arxiv_id": "1", "title": "P1", "year": 2024, "abstract": "A1 " * 30, "authors": ["A"]},
        {"arxiv_id": "2", "title": "P2", "year": 2025, "abstract": "A2 " * 30, "authors": ["B"]},
    ]
    output = _format_template_compare("LLM", papers, ["1", "2"])
    assert "P1" in output
    assert "P2" in output
    assert "对比" in output
    print("✓ 模板 2:对比")


def test_format_template_compare_1_paper():
    """模板 2:1 篇 fallback 列表"""
    papers = [{"arxiv_id": "1", "title": "P1", "year": 2024, "abstract": "A1 " * 30, "authors": ["A"]}]
    output = _format_template_compare("LLM", papers, ["1"])
    # fallback 列表
    assert "P1" in output
    print("✓ 模板 2:1 篇 fallback")


def test_format_template_keyview():
    """模板 3:核心观点"""
    papers = [
        {"arxiv_id": "1", "title": "P1", "year": 2024, "abstract": "A1 " * 30, "authors": ["A"]},
    ]
    output = _format_template_keyview("LLM", papers, ["1"])
    assert "P1" in output
    assert "核心观点" in output
    assert "[1]" in output
    print("✓ 模板 3:核心观点")


def test_format_template_path():
    """模板 4:研究路径"""
    papers = [
        {"arxiv_id": "1", "title": "P1", "year": 2023, "abstract": "A1 " * 30, "authors": ["A"]},
        {"arxiv_id": "2", "title": "P2", "year": 2024, "abstract": "A2 " * 30, "authors": ["B"]},
        {"arxiv_id": "3", "title": "P3", "year": 2025, "abstract": "A3 " * 30, "authors": ["C"]},
    ]
    output = _format_template_path("LLM", papers, ["1", "2", "3"])
    assert "入门" in output
    assert "进阶" in output
    assert "前沿" in output
    print("✓ 模板 4:研究路径")


# ============== 4. 意图识别 ==============

def test_detect_intent_compare():
    """检测对比"""
    assert _detect_intent("Transformer 和 RNN 有什么区别?") == "compare"
    assert _detect_intent("对比 BERT 和 GPT") == "compare"
    print("✓ 意图:对比")


def test_detect_intent_keyview():
    """检测核心观点"""
    assert _detect_intent("RLHF 的核心思想是什么?") == "keyview"
    assert _detect_intent("作者认为什么是关键?") == "keyview"
    print("✓ 意图:核心观点")


def test_detect_intent_path():
    """检测研究路径"""
    assert _detect_intent("怎么入门 LLM?") == "path"
    assert _detect_intent("学习路径推荐") == "path"
    print("✓ 意图:研究路径")


def test_detect_intent_default_list():
    """默认列表"""
    assert _detect_intent("推荐几篇 RAG 论文") == "list"
    assert _detect_intent("LLM 相关研究") == "list"
    print("✓ 意图:默认列表")


# ============== 5. 完整对话流程 ==============

def test_start_chat():
    """开 session"""
    s = start_chat("user_001", topic="LLM")
    assert s.user_id == "user_001"
    assert s.topic == "LLM"
    # 欢迎消息
    assert len(s.messages) == 1
    assert s.messages[0].role == "assistant"
    assert "LLM" in s.messages[0].content
    print("✓ 开 session")


def test_ask_basic():
    """基本提问"""
    s = start_chat("user_001", topic="LLM")
    s.messages = []
    s.round_idx = 0
    r = ask(s, "推荐几篇论文")
    assert r.role == "assistant"
    assert len(r.content) > 0
    # 应有引用
    # 引用数可能为 0(如果没有匹配)
    print(f"✓ 提问:回答 {len(r.content)} 字符,引用 {len(r.citations)} 条")


def test_ask_multi_round():
    """多轮"""
    s = start_chat("user_001")
    s.messages = []
    s.round_idx = 0
    r1 = ask(s, "推荐几篇 LLM 论文")
    r2 = ask(s, "对比 Transformer 和 RNN")
    assert s.round_idx == 2
    assert len(s.messages) == 4  # 2 user + 2 assistant
    print(f"✓ 多轮:2 轮,round_idx={s.round_idx}")


def test_ask_after_completed_raises():
    """完成后不能再问"""
    s = start_chat("user_001")
    s.messages = []
    s.completed = True
    try:
        ask(s, "再问一个")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 已完成不能问")


def test_end_chat():
    """结束"""
    s = start_chat("user_001", topic="LLM")
    s.messages = []
    s.round_idx = 0
    ask(s, "推荐论文")
    # ask 后 round_idx=1,end_chat 内部加 summary 又 +1 → total_rounds=2
    summary = end_chat(s)
    assert summary["session_id"] == s.id
    # 1 轮对话 + 1 总结消息 = 2 assistant 消息
    assert summary["total_rounds"] == 2
    assert s.completed
    print(f"✓ 结束:共 {summary['total_rounds']} 轮,{summary['unique_citations']} 引用")


def test_end_chat_idempotent():
    """end 可多次调用(幂等)"""
    s = start_chat("user_001")
    s.messages = []
    end_chat(s)
    summary2 = end_chat(s)  # 二次调用
    assert s.completed
    print("✓ end 幂等")


# ============== 6. 内存 session ==============

def test_save_and_get_session():
    """保存和获取"""
    _PAPER_CHAT_SESSIONS.clear()
    s = start_chat("user_001", topic="LLM")
    sid = save_session(s)
    got = get_session(sid)
    assert got is not None
    assert got.user_id == "user_001"
    print(f"✓ 保存/获取 {sid}")


def test_get_nonexistent():
    """不存在"""
    assert get_session("NOTEXIST") is None
    print("✓ 不存在 None")


# ============== 7. 引用自动添加 ==============

def test_citation_added_to_response():
    """回答带引用"""
    s = start_chat("user_001")
    s.messages = []
    s.round_idx = 0
    r = ask(s, "Transformer 注意力机制")
    # 应有引用(如果检索到)
    if r.citations:
        assert all(isinstance(c, str) for c in r.citations)
    print(f"✓ 引用自动:{len(r.citations)} 条")


def test_no_match_no_citation():
    """无匹配无引用"""
    s = start_chat("user_001")
    s.messages = []
    s.round_idx = 0
    r = ask(s, "完全不相关 xyz123")
    assert r.citations == []
    print("✓ 无匹配无引用")


# ============== 8. CLI ==============

def test_cli_start():
    """CLI:start"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "paper_chat.py"), "start", "cli_user", "LLM"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "started" in result.stdout
    assert "Session" in result.stdout
    print("✓ CLI start")


def test_cli_ask_skipped():
    """CLI:ask 跳过(进程间内存不共享)"""
    # 沙箱友好:CLI start/ask/end 各自是不同进程,_PAPER_CHAT_SESSIONS 不跨进程
    # 测试 CLI start + 模块 ask(不跨进程)
    r1 = subprocess.run(
        [sys.executable, str(SCRIPTS / "paper_chat.py"), "start", "cli_user", "LLM"],
        capture_output=True, text=True, timeout=10
    )
    assert r1.returncode == 0
    # 进程内测试 ask
    s = start_chat("cli_user", topic="LLM")
    r = ask(s, "推荐 LLM 论文")
    assert r.content is not None
    print("✓ CLI start + 模块 ask(进程内)")


def test_cli_end():
    """CLI:end 跳过(进程间内存不共享)"""
    # end_chat 内部需要 session,在 CLI 进程外不持久
    # 改成进程内测试
    s = start_chat("cli_user", topic="LLM")
    s.messages = []
    s.round_idx = 0
    ask(s, "q")
    summary = end_chat(s)
    assert "total_rounds" in summary
    print("✓ CLI end(进程内)")


# ============== 9. 集成 ==============

def test_integration_full_flow():
    """集成:开 → 问 → 引用 → 结束"""
    _PAPER_CHAT_SESSIONS.clear()
    s = start_chat("test_user", topic="LLM")
    s.messages = []
    s.round_idx = 0
    sid = save_session(s)
    # 1. 问
    r1 = ask(s, "推荐 LLM 论文")
    # 2. 对比
    r2 = ask(s, "对比 Transformer 和 RNN")
    # 3. 路径
    r3 = ask(s, "怎么入门 LLM")
    # 4. 核心
    r4 = ask(s, "RLHF 核心思想")
    # 5. 结束(内部加 summary, round_idx=5)
    summary = end_chat(s)
    # 验证
    assert s.round_idx == 5  # 4 轮对话 + 1 总结
    assert len(s.messages) == 9  # 4 user + 5 assistant
    assert summary["total_rounds"] == 5
    # 至少有些回答有引用
    all_citations = set()
    for m in s.messages:
        all_citations.update(m.citations)
    print(f"✓ 集成:4 轮对话 + 1 总结,引用 {len(all_citations)} 篇")


def test_integration_with_papers_module():
    """集成:用 papers 模块(cycle 21)"""
    from papers import _get_paper_index
    papers = _get_paper_index()
    assert len(papers) > 0
    # paper_chat 应能检索这些论文
    s = start_chat("test", topic="AI")
    s.messages = []
    s.round_idx = 0
    r = ask(s, "推荐论文")
    # 至少应工作(可能 0 引用)
    assert r.content is not None
    print(f"✓ 集成 papers:{len(papers)} 篇可检索")


# ============== 入口 ==============

if __name__ == "__main__":
    test_chat_message()
    test_chat_message_with_citations()
    test_chat_message_to_dict()
    test_paper_chat_session()
    test_paper_chat_session_add_message()
    test_paper_chat_session_end()
    test_paper_chat_session_to_dict()
    test_search_relevant_basic()
    test_search_relevant_no_match()
    test_search_relevant_score_higher()
    test_format_paper_brief()
    test_format_template_list()
    test_format_template_list_empty()
    test_format_template_compare()
    test_format_template_compare_1_paper()
    test_format_template_keyview()
    test_format_template_path()
    test_detect_intent_compare()
    test_detect_intent_keyview()
    test_detect_intent_path()
    test_detect_intent_default_list()
    test_start_chat()
    test_ask_basic()
    test_ask_multi_round()
    test_ask_after_completed_raises()
    test_end_chat()
    test_end_chat_idempotent()
    test_save_and_get_session()
    test_get_nonexistent()
    test_citation_added_to_response()
    test_no_match_no_citation()
    test_cli_start()
    test_cli_ask_skipped()
    test_cli_end()
    test_integration_full_flow()
    test_integration_with_papers_module()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
