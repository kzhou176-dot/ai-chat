#!/usr/bin/env python3
"""
aichat-hub Memory (长期记忆) 模块
=================================
为虚拟人提供长期记忆能力,包含:
  - episodic memory: 带时间戳的事件(对话摘要)
  - semantic memory: 事实/偏好(用户信息)
  - 简单 RAG 检索: 基于关键词 + 时间衰减的相关度打分
  - 自动衰减: 重要度随时间衰减,低重要度事件被压缩

设计目标:
  - 零外部依赖(标准库 only)
  - 单文件 < 200 行
  - 可与 Persona 集成(自动 recall 进 system prompt)

Cycle 2 - 基础版
"""
from __future__ import annotations
import json
import math
import re
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any


# 中文停用词(简化版,够 demo 用)
STOPWORDS_ZH = set("的 了 是 在 我 你 他 她 它 我们 你们 他们 和 与 或 但 因为 所以 一个 一些 这 那 啊 呢 吗 吧 嗯 哦 哈 哎".split())
STOPWORDS_EN = set("a an the is are was were i you he she it we they and or but because so this that".split())


def tokenize(text: str) -> List[str]:
    """简化分词:中文按字符 2-gram,英文按单词"""
    if not text:
        return []
    text = text.lower()
    # 英文部分按词
    en_words = re.findall(r"[a-z]+", text)
    # 中文部分按字符 2-gram
    zh_chars = re.findall(r"[\u4e00-\u9fff]+", text)
    tokens = []
    for w in en_words:
        if w not in STOPWORDS_EN and len(w) > 1:
            tokens.append(w)
    for s in zh_chars:
        for i in range(len(s) - 1):
            bg = s[i:i+2]
            if bg not in STOPWORDS_ZH:
                tokens.append(bg)
    return tokens


@dataclass
class Episode:
    """一个事件(对话摘要)"""
    ts: float  # unix time
    summary: str  # 一句话摘要
    importance: int = 5  # 1-10
    emotion: str = "neutral"  # happy/sad/angry/neutral/surprised
    participants: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def age_days(self, now: float = None) -> float:
        return ((now or time.time()) - self.ts) / 86400


@dataclass
class Fact:
    """一个事实(用户信息)"""
    text: str  # "用户喜欢喝咖啡"
    confidence: float = 1.0  # 0-1
    source: str = "user_told"  # user_told/inferred/observed
    ts: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)


@dataclass
class RecallResult:
    """检索结果"""
    episodes: List[Tuple[Episode, float]] = field(default_factory=list)  # (ep, score)
    facts: List[Tuple[Fact, float]] = field(default_factory=list)

    def to_context(self, max_eps: int = 5, max_facts: int = 5) -> str:
        """格式化为可注入 system prompt 的文本"""
        parts = []
        if self.facts[:max_facts]:
            facts_str = "\n".join(
                f"- (可信度{f.confidence:.0%}) {f.text}"
                for f, _ in self.facts[:max_facts]
            )
            parts.append(f"你记住的关于用户的事实:\n{facts_str}")
        if self.episodes[:max_eps]:
            eps_str = "\n".join(
                f"- [{time.strftime('%Y-%m-%d', time.localtime(e.ts))}] "
                f"(重要度{e.importance}) {e.summary}"
                for e, _ in self.episodes[:max_eps]
            )
            parts.append(f"相关回忆:\n{eps_str}")
        return "\n\n".join(parts)


class MemoryStore:
    """长期记忆存储(每个 Persona 一个)"""

    def __init__(self, persona_name: str, root: Path = None):
        self.persona_name = persona_name
        self.root = root or Path(
            "str(Path(__file__).parent.parent)/data/memory"
        )
        self.root.mkdir(parents=True, exist_ok=True)
        self.episodes: List[Episode] = []
        self.facts: List[Fact] = []
        self._load()

    def _path(self) -> Path:
        return self.root / f"{self.persona_name}.json"

    def _load(self):
        path = self._path()
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.episodes = [Episode(**e) for e in data.get("episodes", [])]
            self.facts = [Fact(**f) for f in data.get("facts", [])]
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[memory] load warning: {e}")

    def save(self):
        data = {
            "persona_name": self.persona_name,
            "episodes": [asdict(e) for e in self.episodes],
            "facts": [asdict(f) for f in self.facts],
            "saved_at": time.time(),
        }
        self._path().write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---------- 写入 ----------

    def add_episode(self, summary: str, importance: int = 5,
                    emotion: str = "neutral", tags: List[str] = None) -> Episode:
        ep = Episode(
            ts=time.time(),
            summary=summary,
            importance=max(1, min(10, importance)),
            emotion=emotion,
            tags=tags or [],
        )
        self.episodes.append(ep)
        # 保留最近 200 个,按重要度剪枝
        if len(self.episodes) > 200:
            self.episodes.sort(key=lambda e: e.importance, reverse=True)
            self.episodes = self.episodes[:200]
        return ep

    def add_fact(self, text: str, confidence: float = 1.0,
                 source: str = "user_told", tags: List[str] = None) -> Fact:
        # 去重:已有相同 text 则更新 confidence(取最高)
        for f in self.facts:
            if f.text == text:
                f.confidence = max(f.confidence, confidence)
                f.ts = time.time()
                return f
        fact = Fact(
            text=text,
            confidence=max(0.0, min(1.0, confidence)),
            source=source,
            tags=tags or [],
        )
        self.facts.append(fact)
        return fact

    # ---------- 检索(简单 RAG) ----------

    def recall(self, query: str, top_k: int = 5,
               now: float = None, time_decay: bool = True) -> RecallResult:
        """基于关键词相关度 + 时间衰减的检索"""
        now = now or time.time()
        q_tokens = set(tokenize(query))
        if not q_tokens:
            return RecallResult()

        # 打分 episodes
        ep_scores = []
        for ep in self.episodes:
            ep_tokens = set(tokenize(ep.summary + " ".join(ep.tags)))
            if not ep_tokens:
                continue
            overlap = len(q_tokens & ep_tokens) / len(q_tokens | ep_tokens)
            # Jaccard + 重要度加权 + 时间衰减
            score = overlap * (ep.importance / 10.0)
            if time_decay:
                age = ep.age_days(now)
                decay = math.exp(-age / 30.0)  # 30 天半衰期
                score *= decay
            if score > 0.01:
                ep_scores.append((ep, score))
        ep_scores.sort(key=lambda x: x[1], reverse=True)

        # 打分 facts
        fact_scores = []
        for f in self.facts:
            f_tokens = set(tokenize(f.text + " ".join(f.tags)))
            if not f_tokens:
                continue
            overlap = len(q_tokens & f_tokens) / len(q_tokens | f_tokens)
            score = overlap * f.confidence
            if time_decay:
                age = ((now - f.ts) / 86400)
                decay = math.exp(-age / 60.0)  # 事实 60 天半衰期
                score *= decay
            if score > 0.01:
                fact_scores.append((f, score))
        fact_scores.sort(key=lambda x: x[1], reverse=True)

        return RecallResult(
            episodes=ep_scores[:top_k],
            facts=fact_scores[:top_k],
        )

    # ---------- 摘要(对话后处理) ----------

    def summarize_recent(self, n: int = 10, now: float = None) -> str:
        """总结最近 n 个事件"""
        now = now or time.time()
        recent = sorted(self.episodes, key=lambda e: e.ts, reverse=True)[:n]
        if not recent:
            return "(无近期记忆)"
        lines = []
        for e in recent:
            date = time.strftime("%m-%d", time.localtime(e.ts))
            lines.append(f"[{date}] (重要度{e.importance}) {e.summary}")
        return "\n".join(lines)

    # ---------- 统计 ----------

    def stats(self) -> Dict[str, Any]:
        return {
            "persona": self.persona_name,
            "episodes": len(self.episodes),
            "facts": len(self.facts),
            "avg_importance": (
                sum(e.importance for e in self.episodes) / len(self.episodes)
                if self.episodes else 0
            ),
            "oldest_episode_days": (
                max(e.age_days() for e in self.episodes) if self.episodes else 0
            ),
        }


if __name__ == "__main__":
    # demo
    m = MemoryStore("xiaoai")
    m.add_fact("用户叫小李", confidence=1.0, tags=["用户", "姓名"])
    m.add_fact("用户喜欢喝美式咖啡", confidence=0.9, tags=["偏好", "饮食"])
    m.add_fact("用户是程序员", confidence=0.8, tags=["用户", "职业"])
    m.add_episode("用户分享了今天的工作压力", importance=7, emotion="sad", tags=["工作"])
    m.add_episode("用户说周末想去爬山", importance=4, emotion="happy", tags=["周末", "运动"])
    m.add_episode("用户提到妈妈身体不太好", importance=8, emotion="sad", tags=["家庭"])
    m.save()

    print("=== Stats ===")
    print(json.dumps(m.stats(), ensure_ascii=False, indent=2))

    print("\n=== Recall: 工作 ===")
    r = m.recall("工作压力")
    print(r.to_context())

    print("\n=== Recall: 咖啡 ===")
    r = m.recall("喝什么饮料")
    print(r.to_context())
