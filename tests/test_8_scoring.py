"""
test_8_scoring — 5 维自动评分测试
==================================
测试 Scorer:
  - 5 维独立评分(length/format/relevance/diversity/latency)
  - 总分加权平均
  - 边界条件(空文本/极长/极短)
  - 批量评分
  - 不同理想长度区间
  - 集成:对 mock LLM 输出评分
  - HTTP 接入:/api/score
"""
import sys
import json
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from scoring import (
    Scorer, ScoreResult,
    score_from_dict, tokenize,
)


def test_tokenize():
    """tokenize 中英文"""
    zh = tokenize("我喜欢喝咖啡")
    en = tokenize("I love coffee")
    assert "喜欢" in zh and "咖啡" in zh
    assert "love" in en and "coffee" in en
    # 停用词不在
    assert "的" not in tokenize("我喜欢咖啡的口味")
    assert "the" not in en
    print(f"  ✓ tokenize: zh={zh}, en={en}")


def test_length_in_range():
    """长度在理想区间内 = 1.0"""
    s = Scorer(ideal_length_range=(50, 500))
    score, detail = s.length_score("这是一段测试文本,长度在 50-500 之间。" * 3)
    assert score == 1.0
    assert detail["in_range"] is True
    print(f"  ✓ length in range: {score}")


def test_length_too_short():
    """太短:线性低于 1.0"""
    s = Scorer(ideal_length_range=(50, 500))
    score, detail = s.length_score("很短")
    assert 0 < score < 1.0
    assert not detail["in_range"]
    print(f"  ✓ length too short: {score} (chars={detail['char_count']})")


def test_length_too_long():
    """太长:指数衰减"""
    s = Scorer(ideal_length_range=(50, 500))
    long_text = "x" * 2000
    score, detail = s.length_score(long_text)
    assert 0 < score < 1.0
    assert not detail["in_range"]
    print(f"  ✓ length too long: {score} (chars={detail['char_count']})")


def test_length_empty():
    """空文本 = 0"""
    s = Scorer()
    score, _ = s.length_score("")
    assert score == 0.0
    print("  ✓ length empty = 0")


def test_format_with_code():
    """代码块加分"""
    s = Scorer()
    text = "```python\nprint('hi')\n```"
    score, detail = s.format_score(text)
    assert score > 0.3
    assert detail.get("has_code_block") is True
    print(f"  ✓ format with code: {score}")


def test_format_with_heading_list():
    """标题 + 列表加分"""
    s = Scorer()
    text = "# 标题\n\n- 项目 1\n- 项目 2\n- 项目 3"
    score, detail = s.format_score(text)
    assert detail.get("has_heading") is True
    assert detail.get("has_list") is True
    assert score >= 0.4
    print(f"  ✓ format with heading+list: {score}")


def test_format_plain_text():
    """纯文本:分数较低"""
    s = Scorer()
    score, _ = s.format_score("just plain text without any structure")
    assert score < 0.3
    print(f"  ✓ format plain text: {score}")


def test_format_empty():
    """空文本 = 0"""
    s = Scorer()
    score, _ = s.format_score("")
    assert score == 0.0
    print("  ✓ format empty = 0")


def test_relevance_keywords_matched():
    """关键词命中"""
    s = Scorer()
    score, detail = s.relevance_score(
        "Python 是一种广泛使用的编程语言,适合初学者",
        "什么是 Python 编程语言",
    )
    # "python" "编程" "语言" 应该在 text 中
    assert score > 0.5
    assert detail["matched"] >= 2
    print(f"  ✓ relevance matched: {score} ({detail['matched']}/{detail['prompt_tokens']})")


def test_relevance_no_overlap():
    """完全不相关"""
    s = Scorer()
    score, detail = s.relevance_score(
        "今天天气真好",
        "解释机器学习算法",
    )
    assert score < 0.3
    print(f"  ✓ relevance no overlap: {score}")


def test_relevance_empty_prompt():
    """空 prompt = 0"""
    s = Scorer()
    score, detail = s.relevance_score("anything", "")
    assert score == 0.0
    assert detail["prompt_tokens"] == 0
    print("  ✓ relevance empty prompt = 0")


def test_diversity_high():
    """高多样性:unique 比例高"""
    s = Scorer()
    text = "今天我去了公园,看到很多花,红的黄的紫的,还遇到了一只猫"
    score, detail = s.diversity_score(text)
    assert score > 0.5
    print(f"  ✓ diversity high: {score} (unigram={detail['unigram_diversity']}, bigram={detail['bigram_diversity']})")


def test_diversity_repetitive():
    """重复文本:多样性低"""
    s = Scorer()
    text = "你好你好你好你好你好你好你好你好"
    score, detail = s.diversity_score(text)
    assert score < 0.5
    print(f"  ✓ diversity repetitive: {score} (unigram={detail['unigram_diversity']})")


def test_diversity_too_short():
    """太短(<2 token) = 0"""
    s = Scorer()
    score, _ = s.diversity_score("hi")
    assert score == 0.0
    print("  ✓ diversity too short = 0")


def test_latency_fast():
    """快速响应 = 高分"""
    s = Scorer(latency_budget_ms=3000)
    score, detail = s.latency_score(100)
    assert score > 0.9
    assert detail["within_budget"] is True
    print(f"  ✓ latency fast: {score}")


def test_latency_slow():
    """慢响应 = 低分"""
    s = Scorer(latency_budget_ms=3000)
    score, detail = s.latency_score(5000)
    assert score == 0.0
    assert not detail["within_budget"]
    print(f"  ✓ latency slow: {score}")


def test_latency_at_budget():
    """刚好 budget = 0"""
    s = Scorer(latency_budget_ms=3000)
    score, _ = s.latency_score(3000)
    assert score == 0.0
    print(f"  ✓ latency at budget: {score}")


def test_total_score():
    """5 维总分"""
    s = Scorer()
    r = s.score(
        "# 机器学习\n\n机器学习是 **AI 子领域**,包括深度学习、强化学习等。",
        "什么是机器学习",
        latency_ms=500,
    )
    assert 0 < r.total_score <= 1.0
    assert r.length_score > 0
    assert r.format_score > 0
    assert r.relevance_score > 0
    assert r.diversity_score > 0
    assert r.latency_score > 0
    print(f"  ✓ total: {r.total_score:.3f} (5 dim: {r.length_score}/{r.format_score}/{r.relevance_score}/{r.diversity_score}/{r.latency_score})")


def test_weights_applied():
    """权重影响总分"""
    s_default = Scorer()  # 等权
    s_zero = Scorer(weights={"length": 1.0, "format": 0, "relevance": 0, "diversity": 0, "latency": 0})
    r1 = s_default.score("hi", "hi", 100)
    r2 = s_zero.score("hi", "hi", 100)
    # 默认权重下总分 = 5 维等权
    # 零权重下总分 = 仅 length
    assert r1.total_score != r2.total_score
    print(f"  ✓ weights: default={r1.total_score}, length-only={r2.total_score}")


def test_score_batch():
    """批量评分"""
    s = Scorer()
    items = [
        {"text": "好的回答", "prompt": "ok?", "latency_ms": 200},
        {"text": "复杂的回答" * 50, "prompt": "test", "latency_ms": 1000},
    ]
    results = s.score_batch(items)
    assert len(results) == 2
    assert all(isinstance(r, ScoreResult) for r in results)
    print(f"  ✓ batch: {len(results)} results")


def test_custom_ideal_length():
    """自定义理想长度区间"""
    s = Scorer(ideal_length_range=(10, 100))
    score, _ = s.length_score("a" * 50)  # 在 10-100 内
    assert score == 1.0
    print(f"  ✓ custom ideal range: {score}")


def test_score_from_dict():
    """从 dict 评分(API helper)"""
    payload = {
        "text": "# 标题\n\n内容",
        "prompt": "标题",
        "latency_ms": 500,
    }
    r = score_from_dict(payload)
    assert r.total_score > 0
    assert r.prompt == "标题"
    print(f"  ✓ score_from_dict: {r.total_score}")


def test_score_to_dict():
    """ScoreResult 可序列化"""
    s = Scorer()
    r = s.score("hi", "hi", 100)
    d = r.to_dict()
    assert "length_score" in d
    assert "total_score" in d
    assert "details" in d
    json_str = json.dumps(d)
    parsed = json.loads(json_str)
    assert parsed["prompt"] == "hi"
    print(f"  ✓ to_dict: {len(d)} keys")


def test_integration_llm_response():
    """集成:对 LLM 风格输出评分"""
    sys.path.insert(0, str(SCRIPTS))
    from llm_client import LLMClient, Message

    client = LLMClient(provider="mock")
    scorer = Scorer()

    # mock LLM 输出
    resp = client.chat([Message("user", "用 Python 写个 hello world")])
    # mock 路径返回 sandbox 内容
    # 直接对响应评分
    r = scorer.score(resp.content, "用 Python 写个 hello world", resp.latency_ms)
    assert r.total_score > 0
    print(f"  ✓ integration LLM: total={r.total_score}, mock_content='{resp.content[:30]}...'")


def test_zero_weight_dimension():
    """某维度权重 = 0 不影响 total"""
    s = Scorer(weights={"length": 0, "format": 0, "relevance": 1.0, "diversity": 0, "latency": 0})
    r = s.score("机器学习是 AI 子领域", "什么是机器学习", 500)
    # total 应该 = relevance_score
    assert abs(r.total_score - r.relevance_score) < 0.001
    print(f"  ✓ zero-weight: total={r.total_score} = relevance={r.relevance_score}")


def test_all_zeros():
    """空输入 = 总分 0"""
    s = Scorer()
    r = s.score("", "", 0)
    assert r.total_score == 0.0
    assert r.length_score == 0
    assert r.format_score == 0
    assert r.relevance_score == 0
    assert r.diversity_score == 0
    assert r.latency_score == 0
    print("  ✓ empty inputs = 0")


if __name__ == "__main__":
    tests = [
        test_tokenize,
        test_length_in_range,
        test_length_too_short,
        test_length_too_long,
        test_length_empty,
        test_format_with_code,
        test_format_with_heading_list,
        test_format_plain_text,
        test_format_empty,
        test_relevance_keywords_matched,
        test_relevance_no_overlap,
        test_relevance_empty_prompt,
        test_diversity_high,
        test_diversity_repetitive,
        test_diversity_too_short,
        test_latency_fast,
        test_latency_slow,
        test_latency_at_budget,
        test_total_score,
        test_weights_applied,
        test_score_batch,
        test_custom_ideal_length,
        test_score_from_dict,
        test_score_to_dict,
        test_integration_llm_response,
        test_zero_weight_dimension,
        test_all_zeros,
    ]
    print(f"Running {len(tests)} scoring tests...\n")
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            import traceback
            print(f"  ✗ {t.__name__}: {e}")
            traceback.print_exc()
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
