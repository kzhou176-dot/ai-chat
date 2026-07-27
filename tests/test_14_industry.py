#!/usr/bin/env python3
"""
test_14_industry — aichat-hub Cycle 14 行业洞察模块测试
====================================================
覆盖:
  1. 9 行业画像完整
  2. FAQ 题库完整性(每行业 ≥ 20 题)
  3. start_industry_session(2-30 轮)
  4. submit_answer(5 维评分 + 反馈)
  5. 完整对话流程
  6. Holland Code 推荐行业
  7. answer_industry_question(基于规则问答)
  8. 5 维评分单元测试
  9. CLI 入口
"""
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from industry_insight import (
    INDUSTRY_PROFILES, FAQ_BANK,
    IndustryQuestion, AnswerResult, IndustrySession,
    list_industries, get_industry, get_industry_prompt,
    start_industry_session, submit_answer,
    recommend_industries_for_holland, answer_industry_question,
    _score_answer_logic, _score_answer_expression, _score_answer_depth,
)


# ============== 1. 9 行业画像 ==============

def test_nine_industries():
    """9 行业完整"""
    assert len(INDUSTRY_PROFILES) == 9
    expected = ["algorithm", "product", "operation", "design", "data",
                "finance", "consulting", "fmcg", "realestate"]
    for ind in expected:
        assert ind in INDUSTRY_PROFILES
    print(f"✓ 9 行业画像完整")


def test_industry_profile_structure():
    """行业画像结构"""
    for ind_id, profile in INDUSTRY_PROFILES.items():
        assert "name" in profile
        assert "emoji" in profile
        assert "category" in profile
        assert "entry_bar" in profile
        assert "top_companies" in profile and len(profile["top_companies"]) >= 3
        assert "salary_range_2025" in profile
        assert "holland_fit" in profile and len(profile["holland_fit"]) >= 2
        assert "skill_tree" in profile and len(profile["skill_tree"]) >= 5
        assert "career_path" in profile
        assert "typical_day" in profile
        assert "trends_2025" in profile
        assert "system_prompt" in profile
    print("✓ 行业画像结构完整")


def test_list_industries():
    """列出 9 行业"""
    ls = list_industries()
    assert len(ls) == 9
    for i in ls:
        assert "id" in i
        assert i["id"] in INDUSTRY_PROFILES
        assert "system_prompt" not in i  # 列表不暴露完整 prompt
    print(f"✓ 列出 {len(ls)} 行业")


def test_get_industry():
    """获取单个行业"""
    i = get_industry("algorithm")
    assert i["id"] == "algorithm"
    assert "算法" in i["name"]
    assert "🤖" in i["emoji"]
    print("✓ 获取单行业")


def test_get_industry_prompt():
    """获取行业 Prompt"""
    p = get_industry_prompt("product")
    assert "产品经理" in p
    assert "PRD" in p or "用户" in p
    print("✓ 行业 Prompt")


# ============== 2. FAQ 题库 ==============

def test_faq_bank_per_industry():
    """每行业 ≥ 20 题"""
    for ind, faqs in FAQ_BANK.items():
        assert len(faqs) >= 20, f"{ind} FAQ = {len(faqs)}"
    total = sum(len(f) for f in FAQ_BANK.values())
    print(f"✓ FAQ 总数 {total}(每行业 ≥ 20)")


def test_faq_bank_covers_all_industries():
    """9 行业都有 FAQ"""
    for ind in INDUSTRY_PROFILES:
        assert ind in FAQ_BANK
    print("✓ 9 行业都有 FAQ")


def test_faq_structure():
    """FAQ 结构"""
    for ind, faqs in FAQ_BANK.items():
        for faq in faqs:
            assert "q" in faq
            assert "kp" in faq
            assert len(faq["q"]) > 5
            assert len(faq["kp"]) >= 2
    print("✓ FAQ 结构完整")


def test_faq_no_duplicate():
    """FAQ 无重复题"""
    for ind, faqs in FAQ_BANK.items():
        questions = [f["q"] for f in faqs]
        assert len(questions) == len(set(questions)), f"{ind} 有重复题"
    print("✓ FAQ 无重复")


# ============== 3. start_industry_session ==============

def test_start_default_3rounds():
    """默认 3 轮"""
    s = start_industry_session("algorithm")
    assert s.industry == "algorithm"
    assert len(s.questions) == 3
    assert s.round_idx == 0
    assert not s.completed
    print(f"✓ 算法行业 3 轮(首题:{s.questions[0].text[:30]}...)")


def test_start_with_holland_code():
    """带 Holland Code"""
    s = start_industry_session("product", user_holland_code="EAS")
    assert s.user_holland_code == "EAS"
    print("✓ 带 Holland Code")


def test_start_unknown_industry_fallback():
    """未知行业 fallback"""
    s = start_industry_session("nonexistent", rounds=2)
    assert s.industry == "algorithm"  # fallback
    print(f"✓ 未知行业 fallback 到 {s.industry}")


def test_start_rounds_bounds():
    """轮次边界"""
    s = start_industry_session("design", rounds=1)
    assert len(s.questions) >= 1
    s = start_industry_session("design", rounds=100)
    assert len(s.questions) <= len(FAQ_BANK["design"])
    print("✓ 轮次边界")


def test_start_each_industry():
    """9 行业都能开 session"""
    for ind in INDUSTRY_PROFILES:
        s = start_industry_session(ind, rounds=2)
        assert s.industry == ind
        assert len(s.questions) == 2
    print("✓ 9 行业都能开 session")


# ============== 4. submit_answer ==============

def test_submit_basic():
    """提交基本回答"""
    s = start_industry_session("algorithm", rounds=2)
    q0 = s.questions[0]
    ans = "算法岗每天写 Python 代码调 PyTorch 模型,跑机器学习实验,然后开会写文档。"
    r = submit_answer(s, ans)
    assert isinstance(r, AnswerResult)
    assert r.question == q0.text
    assert r.score > 0
    assert s.round_idx == 1
    print(f"✓ 提交回答(score={r.score:.0%})")


def test_submit_with_hit_key_points():
    """回答命中关键要点"""
    s = start_industry_session("algorithm", rounds=1)
    q0 = s.questions[0]
    # 关键要点是 ["写代码", "调参", "跑实验", "开会", "文档"]
    ans = "首先写代码,然后调参,跑实验,最后开会讨论结果,写文档总结。"
    r = submit_answer(s, ans)
    # 至少命中 1 个
    assert len(r.key_points_hit) >= 1
    print(f"✓ 命中要点 {len(r.key_points_hit)}/{len(q0.key_points)}")


def test_submit_empty_low_score():
    """空答低分"""
    s = start_industry_session("product", rounds=1)
    r = submit_answer(s, "")
    assert r.score < 0.3
    print(f"✓ 空答低分({r.score:.0%})")


def test_submit_completed_raises():
    """已完成 session 不能提交"""
    s = start_industry_session("hr", rounds=1)  # 注意: industry_insight 没用 hr,fallback 到 algorithm
    s.questions = s.questions[:1]
    submit_answer(s, "回答 1")
    try:
        submit_answer(s, "回答 2")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 已完成 session 不能提交")


def test_submit_no_more_questions_raises():
    """无更多题抛错"""
    s = start_industry_session("data", rounds=1)
    submit_answer(s, "回答 1")
    try:
        submit_answer(s, "回答 2")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 无更多题抛错")


def test_submit_feedback():
    """反馈生成"""
    s = start_industry_session("finance", rounds=1)
    r = submit_answer(s, "金融行业每天用 Excel 做估值建模,做 PPT,开会议,出差见客户。")
    assert r.feedback
    assert any(c in r.feedback for c in ["👍", "✓", "⚠️"])
    print(f"✓ 反馈: {r.feedback[:50]}")


# ============== 5. 完整流程 ==============

def test_full_session_algorithm():
    """完整算法行业 3 轮"""
    s = start_industry_session("algorithm", rounds=3)
    answers = [
        "写 Python 代码用 PyTorch 调机器学习模型,跑深度学习实验,然后开会讨论,写文档。",
        "需要 Python/PyTorch/LeetCode/数学基础,顶会论文加分,ACM 竞赛获奖是亮点。",
        "选 offer 看业务场景、技术成长、WLB、薪资,团队也很重要。",
    ]
    for ans in answers:
        r = submit_answer(s, ans)
        assert r.score >= 0
    assert s.completed
    assert s.round_idx == 3
    print(f"✓ 完整 3 轮,总分 = {s.total_score():.0%}")


def test_total_score():
    """总分计算"""
    s = start_industry_session("product", rounds=2)
    submit_answer(s, "好的回答,首先分析用户需求,然后写 PRD,做 A/B 测试,持续优化。")
    submit_answer(s, "通过 SQL 数据分析用户行为,迭代产品功能。")
    assert 0 <= s.total_score() <= 1
    print(f"✓ 总分 = {s.total_score():.0%}")


def test_session_to_dict():
    """Session 序列化"""
    s = start_industry_session("design", rounds=2, user_holland_code="AIC")
    submit_answer(s, "设计师每天用 Figma 画 UI 规范,做交互设计,评审,偶尔做用户研究。")
    d = s.to_dict()
    assert d["industry"] == "design"
    assert d["user_holland_code"] == "AIC"
    assert "total_score" in d
    print("✓ Session 序列化")


# ============== 6. Holland Code 推荐 ==============

def test_recommend_ias():
    """IAS 代码推荐"""
    recs = recommend_industries_for_holland("IAS")
    assert len(recs) == 9
    # 按匹配度降序
    for i in range(len(recs) - 1):
        assert recs[i]["match_score"] >= recs[i + 1]["match_score"]
    # consulting (IES) 应该排前
    assert recs[0]["match_score"] > 0
    print(f"✓ IAS 推荐 Top 3: {[(r['name'], r['match_score']) for r in recs[:3]]}")


def test_recommend_empty():
    """空 code"""
    recs = recommend_industries_for_holland("")
    assert recs == []
    print("✓ 空 code 返回空")


def test_recommend_all_zero():
    """不相关 code"""
    recs = recommend_industries_for_holland("XXX")
    # 所有 match_score 应为 0
    assert all(r["match_score"] == 0.0 for r in recs)
    print("✓ 不相关 code 全 0")


def test_recommend_rie_to_algorithm():
    """RIE 匹配算法岗(算法 holland_fit = [I, R, A],RIE 命中 2)"""
    recs = recommend_industries_for_holland("RIE")
    # 找 algorithm 的 match_score
    algo_rec = next((r for r in recs if r["industry"] == "algorithm"), None)
    assert algo_rec is not None
    # RIE 命中 I+R = 2/3 = 0.667
    assert algo_rec["match_score"] >= 0.5
    print(f"✓ RIE 匹配算法 = {algo_rec['match_score']:.0%}")


# ============== 7. 行业问答 ==============

def test_answer_question_basic():
    """基本行业问答"""
    result = answer_industry_question("algorithm", "算法岗真实一天是什么样的?")
    assert result["industry"] == "algorithm"
    assert result["matched_faq"] is not None
    assert len(result["key_points"]) > 0
    assert "industry_profile" in result
    print(f"✓ 行业问答:{result['matched_faq'][:30]}")


def test_answer_question_no_match():
    """无匹配问答"""
    result = answer_industry_question("product", "完全不相关的问题 xyz123")
    assert result["matched_faq"] is None
    print("✓ 无匹配 fallback")


def test_answer_question_industry_profile():
    """行业画像在结果中"""
    result = answer_industry_question("finance", "金融薪资")
    assert "top_companies" in result["industry_profile"]
    assert "salary_range" in result["industry_profile"]
    print(f"✓ 行业画像:{result['industry_profile']['salary_range']}")


def test_answer_question_unknown_industry():
    """未知行业 fallback"""
    result = answer_industry_question("nonexistent", "问题")
    assert result["industry"] == "algorithm"  # fallback
    print(f"✓ 未知行业 fallback")


# ============== 8. 5 维评分单元 ==============

def test_score_logic():
    """逻辑评分"""
    assert _score_answer_logic("") == 0.0
    structured = "首先做 A。然后通过 B。最后实现 C。总之,效果很好。"
    assert _score_answer_logic(structured) > 0.5
    print(f"✓ 逻辑评分 = {_score_answer_logic(structured):.0%}")


def test_score_expression():
    """表达评分"""
    assert _score_answer_expression("") == 0.0
    # 真实场景:多句不同内容 + 长度适中
    good = (
        "首先分析用户需求,然后做产品设计,接着写技术方案。"
        "通过数据驱动持续优化。最后通过 A/B 测试验证效果。"
    )
    assert _score_answer_expression(good) > 0.5, f"good score 应 > 0.5,得到 {_score_answer_expression(good)}"
    print(f"✓ 表达评分 = {_score_answer_expression(good):.0%}")


def test_score_depth():
    """深度评分"""
    kp = ["Python", "PyTorch", "机器学习"]
    # 命中 2 个
    r = _score_answer_depth("我会 Python 和 PyTorch 写机器学习代码", kp)
    assert r >= 0.5
    # 无要点
    assert _score_answer_depth("回答", []) == 0.5
    print(f"✓ 深度评分 = {r:.0%}")


# ============== 9. CLI ==============

def test_cli_industries():
    """CLI:industries"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "industry_insight.py"), "industries"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "algorithm" in result.stdout
    assert "product" in result.stdout
    print("✓ CLI industries")


def test_cli_profile():
    """CLI:profile"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "industry_insight.py"), "profile", "algorithm"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["id"] == "algorithm"
    print("✓ CLI profile")


def test_cli_start():
    """CLI:start"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "industry_insight.py"), "start", "product", "3"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["rounds"] == 3
    print("✓ CLI start")


def test_cli_recommend():
    """CLI:recommend"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "industry_insight.py"), "recommend", "IAS"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "consulting" in result.stdout or "algorithm" in result.stdout
    print("✓ CLI recommend")


def test_cli_faq():
    """CLI:faq"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "industry_insight.py"), "faq", "data"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "SQL" in result.stdout
    print("✓ CLI faq")


# ============== 10. 集成 ==============

def test_integration_full_3_industries():
    """集成:3 行业完整流程"""
    for ind in ("algorithm", "product", "design"):
        s = start_industry_session(ind, rounds=2, user_holland_code="RIA")
        submit_answer(s, f"作为 {INDUSTRY_PROFILES[ind]['name']},我会通过技术成长和业务场景,实现团队目标。")
        submit_answer(s, "首先分析需求,然后执行,最后复盘总结,持续迭代优化。")
        assert s.completed
    print("✓ 3 行业完整流程")


def test_integration_holland_recommend_to_faq():
    """集成:Holland Code 推荐 → 选择行业 → FAQ"""
    code = "IAS"
    recs = recommend_industries_for_holland(code)
    # 取 Top 1
    top = recs[0]
    # 用 Top 1 行业
    result = answer_industry_question(top["industry"], f"{top['name']}真实一天")
    assert result["matched_faq"] is not None
    print(f"✓ {code} → {top['name']} → FAQ {result['matched_faq'][:30]}")


def test_integration_all_industries_questions():
    """集成:9 行业每行业至少 1 轮"""
    for ind in INDUSTRY_PROFILES:
        s = start_industry_session(ind, rounds=1)
        r = submit_answer(s, f"我作为 {INDUSTRY_PROFILES[ind]['name']},通过专业能力实现团队目标,带来价值。")
        assert r.score >= 0
    print("✓ 9 行业都能对话")


# ============== 入口 ==============

if __name__ == "__main__":
    test_nine_industries()
    test_industry_profile_structure()
    test_list_industries()
    test_get_industry()
    test_get_industry_prompt()
    test_faq_bank_per_industry()
    test_faq_bank_covers_all_industries()
    test_faq_structure()
    test_faq_no_duplicate()
    test_start_default_3rounds()
    test_start_with_holland_code()
    test_start_unknown_industry_fallback()
    test_start_rounds_bounds()
    test_start_each_industry()
    test_submit_basic()
    test_submit_with_hit_key_points()
    test_submit_empty_low_score()
    test_submit_completed_raises()
    test_submit_no_more_questions_raises()
    test_submit_feedback()
    test_full_session_algorithm()
    test_total_score()
    test_session_to_dict()
    test_recommend_ias()
    test_recommend_empty()
    test_recommend_all_zero()
    test_recommend_rie_to_algorithm()
    test_answer_question_basic()
    test_answer_question_no_match()
    test_answer_question_industry_profile()
    test_answer_question_unknown_industry()
    test_score_logic()
    test_score_expression()
    test_score_depth()
    test_cli_industries()
    test_cli_profile()
    test_cli_start()
    test_cli_recommend()
    test_cli_faq()
    test_integration_full_3_industries()
    test_integration_holland_recommend_to_faq()
    test_integration_all_industries_questions()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
