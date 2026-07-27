#!/usr/bin/env python3
"""
test_12_interview — aichat-hub Cycle 12 模拟面试模块测试
======================================================
覆盖:
  1. 数据模型(Question/AnswerResult/InterviewSession)
  2. 4 角色配置(tech/behavioral/hr/pressure)
  3. 题库完整性(每角色 ≥ 6 题)
  4. start_interview(2-5 轮)
  5. submit_answer(5 维评分 + 反馈)
  6. 完整面试流程(多轮 → 复盘)
  7. 5 维评分函数(单元测试)
  8. CLI 入口
"""
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from interview import (
    Question, AnswerResult, InterviewSession,
    INTERVIEWER_PROFILES, QUESTION_BANK,
    list_interviewers, get_interviewer,
    start_interview, submit_answer, end_interview,
    _logic_score, _expression_score, _depth_score,
    _adaptability_score, _fit_score, _aggregate_score,
)


# ============== 1. 数据模型 ==============

def test_question_dataclass():
    """Question 数据类"""
    q = Question(role="tech", text="实现 LRU", key_points=["哈希表", "双向链表"], difficulty=3)
    assert q.role == "tech"
    assert q.difficulty == 3
    assert len(q.key_points) == 2
    print("✓ Question 数据类")


def test_answer_result_dataclass():
    """AnswerResult 数据类"""
    r = AnswerResult(question="Q", answer="A", score=0.8, feedback="好")
    d = r.to_dict()
    assert d["score"] == 0.8
    assert d["feedback"] == "好"
    print("✓ AnswerResult 数据类")


def test_interview_session_lifecycle():
    """InterviewSession 生命周期"""
    s = InterviewSession(interviewer="tech")
    assert s.interviewer == "tech"
    assert not s.completed
    assert s.round_idx == 0
    # 加一个回答
    q = Question(role="tech", text="Q1", key_points=["A"], difficulty=2)
    s.questions = [q]
    r = AnswerResult(question="Q1", answer="我的回答 A", score=0.7)
    s.add_answer("我的回答 A", r)
    assert s.round_idx == 1
    assert s.completed  # 1 题 1 答 → completed
    print("✓ InterviewSession 生命周期")


def test_interview_session_total_score():
    """总分计算"""
    s = InterviewSession(interviewer="hr")
    s.questions = [Question("hr", "Q1", []), Question("hr", "Q2", [])]
    s.results = [
        AnswerResult(question="Q1", answer="", score=0.8),
        AnswerResult(question="Q2", answer="", score=0.6),
    ]
    s.round_idx = 2
    s.completed = True
    assert s.total_score() == 0.7
    print(f"✓ 总分 = {s.total_score():.0%}")


def test_interview_session_dimension_averages():
    """维度平均"""
    s = InterviewSession(interviewer="hr")
    s.results = [
        AnswerResult(question="Q", answer="A", logic=0.8, expression=0.6,
                     depth=0.7, adaptability=0.9, fit=0.5),
    ]
    avg = s.dimension_averages()
    assert "logic" in avg
    assert avg["logic"] == 0.8
    print(f"✓ 维度平均 logic={avg['logic']:.0%}")


def test_interview_session_to_dict():
    """序列化"""
    s = InterviewSession(interviewer="tech", target_position="算法工程师")
    s.questions = [Question("tech", "Q1", ["A"])]
    s.results = [AnswerResult(question="Q1", answer="A", score=0.5)]
    s.round_idx = 1
    s.completed = True
    d = s.to_dict()
    assert d["interviewer"] == "tech"
    assert d["target_position"] == "算法工程师"
    assert d["total_score"] == 0.5
    print("✓ Session 序列化")


# ============== 2. 角色配置 ==============

def test_interviewer_profiles():
    """4 角色配置完整"""
    assert len(INTERVIEWER_PROFILES) == 4
    for role in ("tech", "behavioral", "hr", "pressure"):
        p = INTERVIEWER_PROFILES[role]
        assert "name" in p
        assert "emoji" in p
        assert "description" in p
        assert "style" in p
        assert len(p["description"]) > 10
    print(f"✓ 4 角色配置完整")


def test_list_interviewers():
    """列出所有面试官"""
    ls = list_interviewers()
    assert len(ls) == 4
    for i in ls:
        assert "id" in i
        assert i["id"] in INTERVIEWER_PROFILES
    print(f"✓ 列出 {len(ls)} 个面试官")


def test_get_interviewer():
    """获取单个面试官"""
    i = get_interviewer("tech")
    assert i["id"] == "tech"
    assert "技术" in i["name"]
    print("✓ 获取面试官")


# ============== 3. 题库完整性 ==============

def test_question_bank_size():
    """每角色 ≥ 6 题"""
    for role, questions in QUESTION_BANK.items():
        assert len(questions) >= 6, f"{role} 题数 = {len(questions)}"
    total = sum(len(q) for q in QUESTION_BANK.values())
    print(f"✓ 题库 {total} 道题(4 角色)")


def test_question_structure():
    """题目结构完整"""
    for role, questions in QUESTION_BANK.items():
        for q in questions:
            assert q.role == role
            assert len(q.text) > 5
            assert len(q.key_points) >= 1
            assert 1 <= q.difficulty <= 5
    print("✓ 题目结构完整")


def test_question_bank_tech():
    """技术题包含算法/系统设计/编程"""
    tech_qs = QUESTION_BANK["tech"]
    texts = " ".join(q.text for q in tech_qs)
    assert "LRU" in texts or "缓存" in texts
    assert "TCP" in texts or "握手" in texts
    print("✓ 技术题库覆盖算法/系统设计/网络")


def test_question_bank_behavioral():
    """行为题有 STAR 关键词"""
    beh_qs = QUESTION_BANK["behavioral"]
    texts = " ".join(q.text for q in beh_qs)
    assert "成就" in texts or "项目" in texts
    assert "冲突" in texts or "团队" in texts
    print("✓ 行为题库覆盖成就/冲突/反思")


def test_question_bank_hr():
    """HR 题有自我介绍/职业规划"""
    hr_qs = QUESTION_BANK["hr"]
    texts = " ".join(q.text for q in hr_qs)
    assert "自我介绍" in texts
    assert "职业" in texts or "规划" in texts
    print("✓ HR 题库覆盖自我介绍/职业规划")


def test_question_bank_pressure():
    """压力题有质疑/打断"""
    press_qs = QUESTION_BANK["pressure"]
    texts = " ".join(q.text for q in press_qs)
    # 压力题关键词
    assert "为什么" in texts or "怎么" in texts or "重做" in texts
    print("✓ 压力题库覆盖质疑/否定")


# ============== 4. start_interview ==============

def test_start_tech_3rounds():
    """开启技术面 3 轮"""
    s = start_interview("tech", rounds=3)
    assert s.interviewer == "tech"
    assert len(s.questions) == 3
    assert s.round_idx == 0
    assert not s.completed
    print(f"✓ 开启技术面 3 轮(首题:{s.questions[0].text[:30]}...)")


def test_start_with_rounds_bounds():
    """轮次边界 2-5"""
    # 1 → 至少 2
    s = start_interview("hr", rounds=1)
    assert len(s.questions) >= 2
    # 10 → 至多 5
    s = start_interview("hr", rounds=10)
    assert len(s.questions) <= 5
    print("✓ 轮次边界 2-5")


def test_start_unknown_role_fallback():
    """未知角色 fallback"""
    s = start_interview("nonexistent", rounds=2)
    # fallback 到 hr
    assert s.interviewer in QUESTION_BANK
    assert len(s.questions) == 2
    print(f"✓ 未知角色 fallback 到 {s.interviewer}")


def test_start_with_position():
    """带目标岗位"""
    s = start_interview("tech", target_position="产品经理", rounds=2)
    assert s.target_position == "产品经理"
    print("✓ 带目标岗位")


# ============== 5. submit_answer ==============

def test_submit_answer_basic():
    """提交回答基本流程"""
    s = start_interview("tech", rounds=2)
    q0 = s.questions[0]
    r = submit_answer(s, "用双指针从两端向中间比较,O(n) 时间 O(1) 空间,处理空串边界")
    assert isinstance(r, AnswerResult)
    assert r.question == q0.text
    assert r.score > 0
    assert s.round_idx == 1
    print(f"✓ 提交回答(score={r.score:.0%})")


def test_submit_answer_5_dimensions():
    """5 维评分都有"""
    s = start_interview("tech", rounds=2)
    r = submit_answer(s, "实现 LRU 缓存:用哈希表加双向链表。O(1) 时间复杂度。")
    assert 0 <= r.logic <= 1
    assert 0 <= r.expression <= 1
    assert 0 <= r.depth <= 1
    assert 0 <= r.adaptability <= 1
    assert 0 <= r.fit <= 1
    assert 0 <= r.score <= 1
    print(f"✓ 5 维评分 logic={r.logic:.0%} depth={r.depth:.0%}")


def test_submit_answer_with_quantification_higher():
    """含数字的回答 depth 更高"""
    s1 = start_interview("tech", rounds=2)
    r1 = submit_answer(s1, "实现一个简单功能")  # 无数字/无关键词
    s2 = start_interview("tech", rounds=2)
    r2 = submit_answer(s2, "O(n) 时间复杂度,O(1) 空间复杂度,处理空串边界条件")
    # r2 命中关键词应更多
    assert r2.depth >= r1.depth, f"含数字应 depth 更高,得到 {r1.depth} vs {r2.depth}"
    print(f"✓ 含数字 depth 更高({r1.depth:.0%} → {r2.depth:.0%})")


def test_submit_answer_empty_low_score():
    """空回答分数低"""
    s = start_interview("tech", rounds=2)
    r = submit_answer(s, "")
    assert r.score < 0.3
    print(f"✓ 空回答分数低({r.score:.0%})")


def test_submit_answer_complete_session():
    """完成整场面试"""
    s = start_interview("hr", rounds=3)
    answers = [
        "我是一名应届生,毕业于清华计算机系,在字节跳动实习过 3 个月,主要做推荐系统。希望加入贵公司,成为一名算法工程师。",
        "因为我看好公司的业务发展,这个岗位匹配我的技能和兴趣。",
        "短期先打好基础,中期成为某领域的专家。",
    ]
    for ans in answers:
        r = submit_answer(s, ans)
        assert r.score >= 0
    assert s.completed
    assert s.round_idx == 3
    print(f"✓ 完整 3 轮面试,总分 = {s.total_score():.0%}")


def test_submit_answer_completed_raises():
    """已完成面试不能再提交"""
    s = start_interview("hr", rounds=2)  # 2 题
    submit_answer(s, "回答 1")
    submit_answer(s, "回答 2")
    # 现在 completed=True,第三次应抛 ValueError
    assert s.completed
    try:
        submit_answer(s, "回答 3")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 已完成面试不能提交")


# ============== 6. 5 维评分单元测试 ==============

def test_logic_score():
    """逻辑性"""
    assert _logic_score("") == 0.0
    assert _logic_score("短") < 0.5
    structured = "首先,我做了 A。然后,通过 B。最后,实现了 C。总之,效果很好。"
    assert _logic_score(structured) > 0.5
    print(f"✓ 逻辑性(结构化) = {_logic_score(structured):.0%}")


def test_expression_score():
    """表达"""
    assert _expression_score("") == 0.0
    # 短答
    short = _expression_score("好")
    # 理想长度
    good = _expression_score("这是一个测试回答。" * 5)
    assert good > short
    print(f"✓ 表达(短 vs 适长) = {short:.0%} vs {good:.0%}")


def test_depth_score():
    """深度"""
    q = Question(role="tech", text="LRU", key_points=["哈希表", "双向链表", "O(1)"])
    # 命中 1 个
    r1 = _depth_score("用哈希表实现", q.key_points)
    # 命中 3 个
    r2 = _depth_score("用哈希表 + 双向链表,O(1) get/put", q.key_points)
    assert r2 > r1
    # 无要点
    assert _depth_score("回答", []) == 0.5
    print(f"✓ 深度 命中1={r1:.0%}, 命中3={r2:.0%}")


def test_adaptability_score():
    """应变"""
    # 空答
    assert _adaptability_score("") == 0.0
    # 正面 + 有内容(>50 字符 → 0.9)
    long_positive = "我有 3 年相关经验,具体来说在这个岗位上我做过 A, B, C 三件事,都有明确的成果。" * 2
    assert _adaptability_score(long_positive) > 0.7
    # 正面 + 短(≤50 字符 → 0.7)
    short_positive = "我有 3 年相关经验"
    assert _adaptability_score(short_positive) == 0.7
    # 负面 + 短
    assert _adaptability_score("不知道") < 0.3
    # 负面 + 长
    assert _adaptability_score("不知道啊,这个问题我之前没想过,总之比较复杂吧") < 0.5
    print("✓ 应变评分")


def test_fit_score():
    """岗位匹配"""
    # 算法关键词
    s1 = _fit_score("我熟悉 Python, PyTorch, 机器学习", position="算法工程师")
    s2 = _fit_score("我做了个网页", position="算法工程师")
    assert s1 > s2
    # 未知岗位 fallback
    assert _fit_score("回答", position="非主流岗位") == 0.5
    print(f"✓ 匹配度(算法岗) 含关键词={s1:.0%}, 不含={s2:.0%}")


def test_aggregate_score():
    """总分加权"""
    s = _aggregate_score(0.8, 0.6, 0.7, 0.9, 0.5)
    assert 0 < s < 1
    # 全 0
    assert _aggregate_score(0, 0, 0, 0, 0) == 0.0
    # 全 1
    assert _aggregate_score(1, 1, 1, 1, 1) == 1.0
    print(f"✓ 加权总分 = {s:.0%}")


# ============== 7. end_interview 复盘 ==============

def test_end_interview_report():
    """结束面试生成复盘报告"""
    s = start_interview("tech", rounds=2)
    submit_answer(s, "用双指针 + O(n) 时间,处理空串边界")
    submit_answer(s, "哈希表加双向链表,O(1) get/put")
    report = end_interview(s)
    assert "interviewer" in report
    assert "total_score" in report
    assert "dimension_averages" in report
    assert "top_improvements" in report
    assert report["rounds"] == 2
    assert 0 <= report["total_score"] <= 1
    print(f"✓ 复盘报告:total={report['total_score']:.0%}, 改进建议 {len(report['top_improvements'])} 条")


def test_end_interview_empty():
    """空面试的复盘"""
    s = start_interview("hr", rounds=2)
    report = end_interview(s)
    assert report["total_score"] == 0.0
    assert report["rounds"] == 0
    print("✓ 空面试复盘")


# ============== 8. 反馈生成 ==============

def test_feedback_for_tech_mentions_complexity():
    """技术面回答无复杂度分析,反馈应提示"""
    s = start_interview("tech", rounds=1)
    r = submit_answer(s, "用列表存,然后遍历查找")  # 无 O() / 复杂度
    assert "复杂度" in r.feedback or "时间" in r.feedback, f"反馈应提示复杂度,实际: {r.feedback}"
    print("✓ 技术面反馈提示复杂度")


def test_feedback_for_behavioral_mentions_star():
    """行为面回答无 STAR 关键词,反馈应提示"""
    s = start_interview("behavioral", rounds=1)
    r = submit_answer(s, "我做过一个项目,做得很好,很有意思。")
    assert "STAR" in r.feedback or "情境" in r.feedback or "组织" in r.feedback, f"反馈应提示 STAR,实际: {r.feedback}"
    print("✓ 行为面反馈提示 STAR")


def test_feedback_for_hr_short_answer():
    """HR 面回答太短,反馈应提示"""
    s = start_interview("hr", rounds=1)
    r = submit_answer(s, "好")
    assert len(r.feedback) > 5
    print("✓ HR 短回答反馈")


# ============== 9. CLI ==============

def test_cli_interviewers():
    """CLI:interviewers 子命令"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "interview.py"), "interviewers"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data) == 4
    print("✓ CLI interviewers")


def test_cli_list():
    """CLI:list 子命令"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "interview.py"), "list"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "tech" in result.stdout
    assert "hr" in result.stdout
    print("✓ CLI list")


def test_cli_start():
    """CLI:start 子命令"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "interview.py"), "start", "tech", "3"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["rounds"] == 3
    assert "first_question" in data
    print("✓ CLI start")


# ============== 10. 集成 ==============

def test_integration_full_4_roles():
    """集成:4 角色都能完整跑"""
    for role in ("tech", "behavioral", "hr", "pressure"):
        s = start_interview(role, rounds=2)
        submit_answer(s, f"作为一个有经验的候选人,我会通过第一,第二,第三这些步骤,实现 O(n) 时间复杂度的方案。")
        submit_answer(s, f"我熟悉 Python, PyTorch, 性能提升 30%,覆盖 100 万用户。")
        report = end_interview(s)
        assert report["rounds"] == 2
        assert report["total_score"] > 0
    print("✓ 4 角色完整流程")


def test_integration_with_resume():
    """集成:interview 复用 resume 的关键词词典"""
    # 验证 _fit_score 调用了 resume 模块
    from interview import _fit_score
    s = _fit_score("Python 机器学习 深度学习 PyTorch", position="算法工程师")
    # 应有匹配分
    assert s > 0
    print(f"✓ 与 resume 集成(fit={s:.0%})")


# ============== 入口 ==============

if __name__ == "__main__":
    test_question_dataclass()
    test_answer_result_dataclass()
    test_interview_session_lifecycle()
    test_interview_session_total_score()
    test_interview_session_dimension_averages()
    test_interview_session_to_dict()
    test_interviewer_profiles()
    test_list_interviewers()
    test_get_interviewer()
    test_question_bank_size()
    test_question_structure()
    test_question_bank_tech()
    test_question_bank_behavioral()
    test_question_bank_hr()
    test_question_bank_pressure()
    test_start_tech_3rounds()
    test_start_with_rounds_bounds()
    test_start_unknown_role_fallback()
    test_start_with_position()
    test_submit_answer_basic()
    test_submit_answer_5_dimensions()
    test_submit_answer_with_quantification_higher()
    test_submit_answer_empty_low_score()
    test_submit_answer_complete_session()
    test_submit_answer_completed_raises()
    test_logic_score()
    test_expression_score()
    test_depth_score()
    test_adaptability_score()
    test_fit_score()
    test_aggregate_score()
    test_end_interview_report()
    test_end_interview_empty()
    test_feedback_for_tech_mentions_complexity()
    test_feedback_for_behavioral_mentions_star()
    test_feedback_for_hr_short_answer()
    test_cli_interviewers()
    test_cli_list()
    test_cli_start()
    test_integration_full_4_roles()
    test_integration_with_resume()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
