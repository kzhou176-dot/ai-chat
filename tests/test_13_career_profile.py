#!/usr/bin/env python3
"""
test_13_career_profile — aichat-hub Cycle 13 霍兰德职业测试模块测试
============================================================
覆盖:
  1. 6 维度定义(RIASEC)
  2. 60 题题库(每维 10 题)
  3. start_career_test(60/30 题)
  4. submit_answer(3 选项 + 进度 + 完成)
  5. compute_scores(6 维分数)
  6. compute_profile(画像 + Holland Code + 解读)
  7. Holland Code 映射(24 种精选)
  8. 岗位匹配度(_position_match)
  9. 数字人角色(career_guide)
  10. CLI 入口
  11. 集成:完整流程(60 题 → 画像)
"""
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from career_profile import (
    RIASEC_DIMENSIONS, QUESTION_BANK, ANSWER_SCORES, ANSWER_LABELS,
    HOLLAND_CODE_MAP, CAREER_GUIDE_PROMPTS,
    CareerTestSession, CareerProfile,
    list_dimensions, get_dimension,
    start_career_test, submit_answer,
    compute_scores, compute_profile,
    get_career_guide, _position_match,
)


# ============== 1. 6 维度定义 ==============

def test_six_dimensions():
    """6 维 RIASEC 完整"""
    assert len(RIASEC_DIMENSIONS) == 6
    for dim_id in ("R", "I", "A", "S", "E", "C"):
        d = RIASEC_DIMENSIONS[dim_id]
        assert "name" in d
        assert "name_en" in d
        assert "emoji" in d
        assert "keywords" in d
        assert "careers" in d
        assert len(d["careers"]) > 5
    print("✓ 6 维 RIASEC 定义完整")


def test_dimensions_in_order():
    """6 维按 RIASEC 顺序"""
    assert list(RIASEC_DIMENSIONS.keys()) == ["R", "I", "A", "S", "E", "C"]
    print("✓ 6 维按 RIASEC 顺序")


def test_list_dimensions():
    """列出 6 维"""
    ds = list_dimensions()
    assert len(ds) == 6
    for d in ds:
        assert "id" in d
    print(f"✓ 列出 {len(ds)} 维")


def test_get_dimension():
    """获取单维"""
    d = get_dimension("I")
    assert d["id"] == "I"
    assert "研究" in d["name"]
    assert "Investigative" in d["name_en"]
    print("✓ 获取单维度")


# ============== 2. 题库 ==============

def test_question_bank_count():
    """题库总数 60"""
    assert len(QUESTION_BANK) == 60
    print(f"✓ 题库 {len(QUESTION_BANK)} 道")


def test_question_bank_per_dimension():
    """每维 10 题"""
    counts = {d: 0 for d in RIASEC_DIMENSIONS}
    for q in QUESTION_BANK:
        counts[q["dim"]] += 1
    for dim, count in counts.items():
        assert count == 10, f"{dim} 题数 = {count}"
    print(f"✓ 每维 10 题 {counts}")


def test_question_structure():
    """题目结构完整"""
    for q in QUESTION_BANK:
        assert "id" in q
        assert "dim" in q
        assert "text" in q
        assert q["dim"] in RIASEC_DIMENSIONS
        assert q["id"].startswith(q["dim"])
        assert len(q["text"]) > 10
    print("✓ 题目结构完整")


def test_question_ids_unique():
    """题 ID 唯一"""
    ids = [q["id"] for q in QUESTION_BANK]
    assert len(set(ids)) == 60
    print("✓ 题 ID 唯一")


# ============== 3. 答题选项 ==============

def test_answer_scores():
    """3 选 1 分值"""
    assert ANSWER_SCORES["like"] == 2
    assert ANSWER_SCORES["neutral"] == 1
    assert ANSWER_SCORES["dislike"] == 0
    print("✓ 3 选项分值")


def test_answer_labels():
    """3 选项标签"""
    assert "喜欢" in ANSWER_LABELS["like"]
    assert "中立" in ANSWER_LABELS["neutral"]
    assert "不喜欢" in ANSWER_LABELS["dislike"]
    print("✓ 3 选项标签")


# ============== 4. start_career_test ==============

def test_start_default_60():
    """默认 60 题"""
    s = start_career_test()
    assert len(s.questions) == 60
    assert s.round_idx == 0
    assert not s.completed
    print(f"✓ 默认 60 题")


def test_start_with_target_position():
    """带目标岗位"""
    s = start_career_test(target_position="算法工程师")
    assert s.target_position == "算法工程师"
    print("✓ 带目标岗位")


def test_start_short_version():
    """简版 30 题"""
    s = start_career_test(question_count=30)
    assert len(s.questions) == 30
    # 每维 5 题
    counts = {d: 0 for d in RIASEC_DIMENSIONS}
    for q in s.questions:
        counts[q["dim"]] += 1
    for c in counts.values():
        assert c == 5
    print(f"✓ 简版 30 题(每维 5 题)")


def test_start_to_dict():
    """Session 序列化"""
    s = start_career_test()
    d = s.to_dict()
    assert "questions" in d
    assert "answers" in d
    assert d["round_idx"] == 0
    print("✓ Session 序列化")


# ============== 5. submit_answer ==============

def test_submit_basic():
    """提交 1 个答案"""
    s = start_career_test(question_count=6)  # 简版 6 题
    q0 = s.questions[0]
    result = submit_answer(s, q0["id"], "like")
    assert result["qid"] == q0["id"]
    assert result["answer"] == "like"
    assert result["round_idx"] == 1
    print(f"✓ 提交答案(round_idx=1)")


def test_submit_invalid_answer_raises():
    """无效答案抛错"""
    s = start_career_test(question_count=6)
    q0 = s.questions[0]
    try:
        submit_answer(s, q0["id"], "yes")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 无效答案抛错")


def test_submit_invalid_qid_raises():
    """无效 qid 抛错"""
    s = start_career_test(question_count=6)
    try:
        submit_answer(s, "R99", "like")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 无效 qid 抛错")


def test_submit_completed_raises():
    """已完成测试不能再提交"""
    s = start_career_test(question_count=6)
    for q in s.questions:
        submit_answer(s, q["id"], "neutral")
    assert s.completed
    try:
        submit_answer(s, s.questions[0]["id"], "like")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 已完成不能提交")


def test_submit_next_question():
    """返回下一题"""
    s = start_career_test(question_count=6)
    q0 = s.questions[0]
    result = submit_answer(s, q0["id"], "like")
    assert result["next_question"] is not None
    assert result["next_question"]["id"] == s.questions[1]["id"]
    print("✓ 下一题返回正确")


def test_submit_no_next_after_last():
    """最后一题无下一题"""
    s = start_career_test(question_count=6)
    for i, q in enumerate(s.questions):
        result = submit_answer(s, q["id"], "like")
        if i == len(s.questions) - 1:
            assert result["next_question"] is None
            assert result["completed"]
    print("✓ 最后一题无下一题")


# ============== 6. compute_scores ==============

def test_compute_scores_all_like():
    """全 like → 每维 20 分"""
    s = start_career_test()
    for q in s.questions:
        submit_answer(s, q["id"], "like")
    scores = compute_scores(s)
    for dim, score in scores.items():
        assert score == 20, f"{dim} = {score}"
    print("✓ 全 like → 每维 20")


def test_compute_scores_all_dislike():
    """全 dislike → 每维 0"""
    s = start_career_test()
    for q in s.questions:
        submit_answer(s, q["id"], "dislike")
    scores = compute_scores(s)
    for score in scores.values():
        assert score == 0
    print("✓ 全 dislike → 每维 0")


def test_compute_scores_partial():
    """部分答 → 部分分数"""
    s = start_career_test()
    # 只答 R 维 5 题 like
    r_questions = [q for q in s.questions if q["dim"] == "R"][:5]
    for q in r_questions:
        submit_answer(s, q["id"], "like")
    scores = compute_scores(s)
    assert scores["R"] == 10  # 5 题 * 2 分
    assert scores["I"] == 0   # 没答
    print(f"✓ 部分答 R={scores['R']}, I={scores['I']}")


# ============== 7. compute_profile ==============

def test_compute_profile_all_like():
    """全 like profile(可能 6 维并列第一)"""
    s = start_career_test()
    for q in s.questions:
        submit_answer(s, q["id"], "like")
    p = compute_profile(s)
    assert isinstance(p, CareerProfile)
    assert all(score == 20 for score in p.scores.values())
    assert len(p.top3) == 3
    assert len(p.holland_code) == 3
    assert len(p.interpretation) > 10
    print(f"✓ 全 like profile, code={p.holland_code}")


def test_compute_profile_investigator():
    """全 I → 研究型主导"""
    s = start_career_test()
    for q in s.questions:
        if q["dim"] == "I":
            submit_answer(s, q["id"], "like")
        else:
            submit_answer(s, q["id"], "dislike")
    p = compute_profile(s)
    assert p.scores["I"] == 20
    assert p.scores["R"] == 0
    # I 应该在 top3 第一
    assert p.top3[0][0] == "I"
    # 解读包含"研究型"
    assert "研究" in p.interpretation
    print(f"✓ 全 I profile, code={p.holland_code}, top={p.top3[0]}")


def test_compute_profile_artistic():
    """全 A → 艺术型主导"""
    s = start_career_test()
    for q in s.questions:
        if q["dim"] == "A":
            submit_answer(s, q["id"], "like")
        else:
            submit_answer(s, q["id"], "dislike")
    p = compute_profile(s)
    assert p.top3[0][0] == "A"
    assert "艺术" in p.interpretation
    print(f"✓ 全 A profile, code={p.holland_code}")


def test_compute_profile_to_dict():
    """Profile 序列化"""
    s = start_career_test()
    for q in s.questions:
        submit_answer(s, q["id"], "like")
    p = compute_profile(s)
    d = p.to_dict()
    assert "scores" in d
    assert "holland_code" in d
    assert "interpretation" in d
    assert "careers" in d
    assert "advice" in d
    assert "target_position_match" in d
    print("✓ Profile 序列化")


# ============== 8. Holland Code 映射 ==============

def test_holland_code_map_count():
    """映射表 ≥ 24 种"""
    assert len(HOLLAND_CODE_MAP) >= 24
    print(f"✓ Holland Code 映射 {len(HOLLAND_CODE_MAP)} 种")


def test_holland_code_map_structure():
    """映射结构"""
    for code, info in HOLLAND_CODE_MAP.items():
        assert len(code) == 3
        assert all(c in RIASEC_DIMENSIONS for c in code)
        assert "careers" in info
        assert "advice" in info
        assert len(info["careers"]) > 3
        assert len(info["advice"]) > 5
    print("✓ 映射结构完整")


def test_known_codes_present():
    """经典代码都在"""
    classic = ["RIA", "IAS", "IES", "ASE", "SEC", "ESC", "SIA", "SAE", "IAR", "IRA"]
    for code in classic:
        assert code in HOLLAND_CODE_MAP, f"{code} 缺失"
    print(f"✓ 10 个经典代码都在")


# ============== 9. 岗位匹配度 ==============

def test_position_match_known():
    """已知岗位"""
    s = start_career_test(target_position="算法工程师")
    for q in s.questions:
        if q["dim"] == "I":
            submit_answer(s, q["id"], "like")
        else:
            submit_answer(s, q["id"], "dislike")
    p = compute_profile(s)
    # I 主导,匹配算法工程师
    match = p.target_position_match
    assert match > 0, f"全 I 应匹配算法岗,得到 {match}"
    print(f"✓ 全 I 匹配算法岗 = {match:.0%}")


def test_position_match_unknown():
    """未知岗位中庸"""
    m = _position_match({"I": 20}, "未知岗位")
    assert m == 0.5
    print("✓ 未知岗位 fallback = 0.5")


def test_position_match_empty():
    """空岗位 0"""
    m = _position_match({"I": 20}, "")
    assert m == 0.0
    print("✓ 空岗位 = 0")


def test_position_match_full_investigator_to_algorithm():
    """全 I 匹配算法岗,匹配度应较高"""
    scores = {d: 0 for d in RIASEC_DIMENSIONS}
    scores["I"] = 20
    scores["R"] = 16
    m = _position_match(scores, "算法工程师")
    assert m > 0.5, f"全 I + R 应与算法岗高度匹配,得到 {m}"
    print(f"✓ 全 I+R 匹配算法岗 = {m:.0%}")


# ============== 10. 数字人角色 ==============

def test_career_guide_prompts():
    """职业规划师 Prompt"""
    assert "career_guide" in CAREER_GUIDE_PROMPTS
    info = CAREER_GUIDE_PROMPTS["career_guide"]
    assert "职业规划师" in info["name"]
    assert "🧭" in info["emoji"]
    assert "RIASEC" in info["system_prompt"]
    print("✓ 职业规划师 Prompt")


def test_get_career_guide():
    """获取职业规划师"""
    g = get_career_guide()
    assert g["id"] == "career_guide"
    assert "职业规划师" in g["name"]
    print("✓ 获取职业规划师")


# ============== 11. CLI ==============

def test_cli_dimensions():
    """CLI:dimensions 子命令"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "career_profile.py"), "dimensions"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data) == 6
    print("✓ CLI dimensions")


def test_cli_list_codes():
    """CLI:list_codes 子命令"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "career_profile.py"), "list_codes"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "RIA" in result.stdout
    assert "IAS" in result.stdout
    print("✓ CLI list_codes")


def test_cli_start():
    """CLI:start 子命令"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "career_profile.py"), "start", "算法工程师", "60"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["total_questions"] == 60
    assert "first_question" in data
    print("✓ CLI start")


# ============== 12. 集成 ==============

def test_integration_full_60q():
    """集成:完整 60 题 → 画像"""
    s = start_career_test(target_position="算法工程师")
    # 模拟 I+R 主导(算法岗典型画像)
    for q in s.questions:
        if q["dim"] in ("I", "R"):
            submit_answer(s, q["id"], "like")
        elif q["dim"] in ("A", "C"):
            submit_answer(s, q["id"], "neutral")
        else:
            submit_answer(s, q["id"], "dislike")
    assert s.completed
    p = compute_profile(s)
    assert p.holland_code[0] in ("I", "R")
    assert p.scores["I"] == 20
    assert p.scores["R"] == 20
    # 算法岗匹配度高
    assert p.target_position_match >= 0.5
    print(f"✓ 60 题完整流程: code={p.holland_code}, 匹配算法={p.target_position_match:.0%}")


def test_integration_no_answer():
    """集成:无任何答题"""
    s = start_career_test()
    p = compute_profile(s)
    # 全 0 → 默认 III
    assert p.holland_code == "III"
    print(f"✓ 无答题 fallback code={p.holland_code}")


def test_integration_30q_short():
    """集成:简版 30 题"""
    s = start_career_test(question_count=30)
    for q in s.questions:
        submit_answer(s, q["id"], "like")
    p = compute_profile(s)
    # 全 like 简版
    assert len(p.top3) == 3
    print(f"✓ 30 题简版, code={p.holland_code}")


# ============== 入口 ==============

if __name__ == "__main__":
    test_six_dimensions()
    test_dimensions_in_order()
    test_list_dimensions()
    test_get_dimension()
    test_question_bank_count()
    test_question_bank_per_dimension()
    test_question_structure()
    test_question_ids_unique()
    test_answer_scores()
    test_answer_labels()
    test_start_default_60()
    test_start_with_target_position()
    test_start_short_version()
    test_start_to_dict()
    test_submit_basic()
    test_submit_invalid_answer_raises()
    test_submit_invalid_qid_raises()
    test_submit_completed_raises()
    test_submit_next_question()
    test_submit_no_next_after_last()
    test_compute_scores_all_like()
    test_compute_scores_all_dislike()
    test_compute_scores_partial()
    test_compute_profile_all_like()
    test_compute_profile_investigator()
    test_compute_profile_artistic()
    test_compute_profile_to_dict()
    test_holland_code_map_count()
    test_holland_code_map_structure()
    test_known_codes_present()
    test_position_match_known()
    test_position_match_unknown()
    test_position_match_empty()
    test_position_match_full_investigator_to_algorithm()
    test_career_guide_prompts()
    test_get_career_guide()
    test_cli_dimensions()
    test_cli_list_codes()
    test_cli_start()
    test_integration_full_60q()
    test_integration_no_answer()
    test_integration_30q_short()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
