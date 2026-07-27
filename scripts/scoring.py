#!/usr/bin/env python3
"""
aichat-hub Scoring (5 维自动评分) 模块
=====================================
对 LLM 输出做 5 维自动评分,无 LLM Judge 依赖。

5 维:
  1. 长度(length_score):0-1,基于"理想长度区间"
  2. 格式(format_score):0-1,基于 markdown/code/list 结构
  3. 相关性(relevance_score):0-1,基于 prompt 关键词在 output 中覆盖度
  4. 多样性(diversity_score):0-1,基于 unique n-gram / total n-gram
  5. 响应时间(latency_score):0-1,基于 latency 倒数(快 = 高分)

总分 = 5 维加权平均(默认等权)

Cycle 8 - 基础版
"""
from __future__ import annotations
import json
import re
import time
import math
from collections import Counter
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any, Tuple


# 中文停用词(简化)
STOPWORDS_ZH = set("的 了 是 在 我 你 他 她 它 我们 你们 他们 和 与 或 但 因为 所以 一个 一些 这 那".split())
STOPWORDS_EN = set("a an the is are was were i you he she it we they and or but because so this that".split())


def tokenize(text: str) -> List[str]:
    """简化分词:中文 2-gram + 英文单词"""
    if not text:
        return []
    text = text.lower()
    en_words = re.findall(r"[a-z]+", text)
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
class ScoreResult:
    """5 维评分结果"""
    text: str
    prompt: str = ""
    length_score: float = 0.0      # 0-1
    format_score: float = 0.0     # 0-1
    relevance_score: float = 0.0  # 0-1
    diversity_score: float = 0.0  # 0-1
    latency_score: float = 0.0    # 0-1
    total_score: float = 0.0      # 加权平均
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class Scorer:
    """5 维自动评分器"""

    # 默认理想长度区间
    DEFAULT_IDEAL_LEN = (50, 500)  # 字符数

    def __init__(
        self,
        ideal_length_range: Tuple[int, int] = None,
        weights: Dict[str, float] = None,
        latency_budget_ms: float = 3000.0,  # 超过此值 lat_score 接近 0
    ):
        self.ideal_length_range = ideal_length_range or self.DEFAULT_IDEAL_LEN
        self.weights = weights or {
            "length": 0.2,
            "format": 0.15,
            "relevance": 0.3,
            "diversity": 0.15,
            "latency": 0.2,
        }
        self.latency_budget_ms = latency_budget_ms

    # ---------- 各维度评分 ----------

    def length_score(self, text: str) -> Tuple[float, Dict[str, Any]]:
        """长度评分:理想区间内 = 1.0,偏离衰减"""
        if not text:
            return 0.0, {"char_count": 0, "in_range": False}
        n = len(text)
        lo, hi = self.ideal_length_range
        if lo <= n <= hi:
            score = 1.0
        elif n < lo:
            # 短:线性增长
            score = n / lo
        else:
            # 长:指数衰减
            score = math.exp(-(n - hi) / hi)
        return round(score, 4), {"char_count": n, "in_range": lo <= n <= hi}

    def format_score(self, text: str) -> Tuple[float, Dict[str, Any]]:
        """格式评分:有 markdown/代码/列表/标题 加分"""
        if not text:
            return 0.0, {}
        score = 0.0
        signals = {}

        # Markdown 结构
        if "```" in text:
            score += 0.4
            signals["has_code_block"] = True
        if re.search(r"^#{1,6}\s+", text, re.MULTILINE):
            score += 0.2
            signals["has_heading"] = True
        if re.search(r"^[-*+]\s+", text, re.MULTILINE) or re.search(r"^\d+\.\s+", text, re.MULTILINE):
            score += 0.2
            signals["has_list"] = True
        if "**" in text or "__" in text:
            score += 0.1
            signals["has_bold"] = True
        if re.search(r"\[.+\]\(.+\)", text):
            score += 0.1
            signals["has_link"] = True
        # 完整段落(>=3 行)
        lines = [l for l in text.split("\n") if l.strip()]
        if len(lines) >= 3:
            score += 0.1
            signals["has_paragraphs"] = True

        return min(1.0, round(score, 4)), signals

    def relevance_score(self, text: str, prompt: str) -> Tuple[float, Dict[str, Any]]:
        """相关性评分:prompt 关键词在 output 中覆盖度"""
        if not text or not prompt:
            return 0.0, {"prompt_tokens": 0, "matched": 0, "coverage": 0.0}
        prompt_tokens = tokenize(prompt)
        if not prompt_tokens:
            return 0.0, {"prompt_tokens": 0, "matched": 0, "coverage": 0.0}
        text_token_set = set(tokenize(text))
        matched = sum(1 for t in prompt_tokens if t in text_token_set)
        coverage = matched / len(prompt_tokens)
        return round(coverage, 4), {
            "prompt_tokens": len(prompt_tokens),
            "matched": matched,
            "coverage": coverage,
        }

    def diversity_score(self, text: str) -> Tuple[float, Dict[str, Any]]:
        """多样性评分:unique n-gram / total n-gram(Distinct-N 思想)"""
        if not text:
            return 0.0, {}
        tokens = tokenize(text)
        if len(tokens) < 2:
            return 0.0, {"tokens": len(tokens), "distinct_ratio": 0.0}
        # unigram diversity
        uniq = set(tokens)
        unigram_div = len(uniq) / len(tokens)
        # bigram diversity
        bigrams = [(tokens[i], tokens[i+1]) for i in range(len(tokens) - 1)]
        bigram_div = len(set(bigrams)) / max(1, len(bigrams)) if bigrams else 0.0
        # 综合(unigram 0.4 + bigram 0.6)
        score = 0.4 * unigram_div + 0.6 * bigram_div
        return round(score, 4), {
            "tokens": len(tokens),
            "unique": len(uniq),
            "unigram_diversity": round(unigram_div, 4),
            "bigram_diversity": round(bigram_div, 4),
        }

    def latency_score(self, latency_ms: float) -> Tuple[float, Dict[str, Any]]:
        """响应时间评分:越快越高,超过 budget 接近 0"""
        if latency_ms <= 0:
            return 0.0, {"latency_ms": latency_ms, "within_budget": False}
        # 线性衰减:0ms → 1.0, budget → 0
        score = max(0.0, 1.0 - latency_ms / self.latency_budget_ms)
        return round(score, 4), {
            "latency_ms": latency_ms,
            "within_budget": latency_ms <= self.latency_budget_ms,
        }

    # ---------- 总分 ----------

    def score(
        self,
        text: str,
        prompt: str = "",
        latency_ms: float = 0.0,
    ) -> ScoreResult:
        """计算 5 维总分"""
        ls, ld = self.length_score(text)
        fs, fd = self.format_score(text)
        rs, rd = self.relevance_score(text, prompt)
        ds, dd = self.diversity_score(text)
        lts, ltd = self.latency_score(latency_ms)

        total = (
            self.weights["length"] * ls
            + self.weights["format"] * fs
            + self.weights["relevance"] * rs
            + self.weights["diversity"] * ds
            + self.weights["latency"] * lts
        )
        return ScoreResult(
            text=text,
            prompt=prompt,
            length_score=ls,
            format_score=fs,
            relevance_score=rs,
            diversity_score=ds,
            latency_score=lts,
            total_score=round(total, 4),
            details={
                "length": ld,
                "format": fd,
                "relevance": rd,
                "diversity": dd,
                "latency": ltd,
            },
        )

    def score_batch(
        self,
        items: List[Dict[str, Any]],
    ) -> List[ScoreResult]:
        """批量评分,每个 item 至少含 text 字段"""
        results = []
        for item in items:
            results.append(self.score(
                text=item.get("text", ""),
                prompt=item.get("prompt", ""),
                latency_ms=item.get("latency_ms", 0.0),
            ))
        return results


# ============== /api/score endpoint helper ==============

def score_from_dict(payload: Dict[str, Any]) -> ScoreResult:
    """从 webhook/web payload 生成 ScoreResult"""
    text = payload.get("text", "")
    prompt = payload.get("prompt", "")
    latency_ms = float(payload.get("latency_ms", 0.0))
    scorer = Scorer()
    return scorer.score(text, prompt, latency_ms)


if __name__ == "__main__":
    # demo
    scorer = Scorer()
    samples = [
        {
            "prompt": "解释什么是机器学习,举 3 个例子",
            "text": """# 机器学习简介

机器学习是 AI 的子领域,核心是**从数据中学习规律**。

## 例子

1. **图像识别**:训练 CNN 识别猫狗
2. **推荐系统**:协同过滤预测用户喜好
3. **自然语言处理**:BERT/GPT 等大模型

机器学习让计算机**自动改进**而不需要明确编程。""",
            "latency_ms": 850.0,
        },
        {
            "prompt": "你好",
            "text": "你好啊",
            "latency_ms": 200.0,
        },
        {
            "prompt": "Python 教程",
            "text": "```python\nprint('hello world')\n```",
            "latency_ms": 100.0,
        },
    ]
    print("=== 5 维自动评分 demo ===\n")
    for s in scorer.score_batch(samples):
        print(f"prompt: {s.prompt[:30]}...")
        print(f"  length:    {s.length_score:.3f}")
        print(f"  format:    {s.format_score:.3f}")
        print(f"  relevance: {s.relevance_score:.3f}")
        print(f"  diversity: {s.diversity_score:.3f}")
        print(f"  latency:   {s.latency_score:.3f}")
        print(f"  TOTAL:     {s.total_score:.3f}")
        print()
