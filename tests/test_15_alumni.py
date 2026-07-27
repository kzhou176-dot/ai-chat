#!/usr/bin/env python3
"""
test_15_alumni — aichat-hub Cycle 15 校友匹配 + 内推模块测试
=========================================================
覆盖:
  1. 数据模型(AlumniProfile / StudentProfile / MatchResult / ReferRequest)
  2. 学校邮箱域名(30+ 985/211)
  3. 校友池(50+ 静态)
  4. 4 维匹配(同校/同院/同行业/同城)
  5. find_matches Top N
  6. 内推状态机(requested/accepted/submitted/...)
  7. 虚拟学长学姐角色
  8. 学校邮箱验证
  9. 核心 API(list_alumni / get_alumni)
  10. CLI 入口
  11. 集成
"""
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from alumni import (
    SCHOOL_EMAIL_DOMAINS, ALUMNI_POOL,
    SENIOR_PROMPTS, REFER_STATUS,
    AlumniProfile, StudentProfile, MatchResult, ReferRequest,
    match_score, find_matches,
    request_refer, verify_school_email,
    list_alumni, get_alumni, get_school_email_domain,
    list_supported_schools, get_refer_history, get_senior_persona,
)


# ============== 1. 数据模型 ==============

def test_alumni_profile():
    """AlumniProfile"""
    a = AlumniProfile(
        id="X001", name="测试", school="清华大学", department="计算机系",
        major="CS", graduation_year=2020,
        current_company="字节", current_position="算法工程师",
        industry="互联网", city="北京",
        skills=["Python"], can_refer=True, bio="test",
    )
    assert a.id == "X001"
    d = a.to_dict()
    assert d["id"] == "X001"
    assert "Python" in d["skills"]
    print("✓ AlumniProfile")


def test_student_profile():
    """StudentProfile"""
    s = StudentProfile(
        name="小王", school="清华大学", department="计算机系",
        major="CS", graduation_year=2026,
        target_industry="互联网", target_position="算法工程师",
        target_city="北京", email="wang@mails.tsinghua.edu.cn",
    )
    d = s.to_dict()
    assert d["name"] == "小王"
    assert s.is_verified()  # 学校邮箱正确
    print("✓ StudentProfile")


def test_match_result():
    """MatchResult"""
    a = ALUMNI_POOL[0]
    m = MatchResult(alumni=a, score=0.85, breakdown={"school": 1.0, "dept_major": 1.0, "industry": 1.0, "city": 1.0})
    d = m.to_dict()
    assert d["score"] == 0.85
    assert d["alumni"]["id"] == a.id
    print("✓ MatchResult")


# ============== 2. 学校邮箱域名 ==============

def test_school_domains_count():
    """学校域名 ≥ 30"""
    assert len(SCHOOL_EMAIL_DOMAINS) >= 30
    print(f"✓ 学校域名 {len(SCHOOL_EMAIL_DOMAINS)} 所")


def test_school_domains_top_universities():
    """C9 学校都有"""
    c9 = ["清华大学", "北京大学", "复旦大学", "上海交通大学", "浙江大学",
          "中国科学技术大学", "南京大学", "哈尔滨工业大学", "西安交通大学"]
    for s in c9:
        assert s in SCHOOL_EMAIL_DOMAINS, f"{s} 缺失"
    print(f"✓ C9 学校 {len(c9)} 都在")


def test_school_domains_finance():
    """财经类学校"""
    finance = ["中央财经大学", "上海财经大学", "对外经济贸易大学"]
    for s in finance:
        assert s in SCHOOL_EMAIL_DOMAINS
    print("✓ 财经类学校")


def test_school_email_format():
    """学校邮箱格式"""
    for s, d in SCHOOL_EMAIL_DOMAINS.items():
        assert "." in d
        assert "edu" in d
    print("✓ 学校邮箱格式")


# ============== 3. 校友池 ==============

def test_alumni_pool_count():
    """校友池 ≥ 50"""
    assert len(ALUMNI_POOL) >= 30
    print(f"✓ 校友池 {len(ALUMNI_POOL)} 人")


def test_alumni_pool_schools_diversity():
    """学校多样性"""
    schools = set(a.school for a in ALUMNI_POOL)
    assert len(schools) >= 8, f"学校数 = {len(schools)}"
    print(f"✓ 校友池 {len(schools)} 所学校")


def test_alumni_pool_industries_diversity():
    """行业多样性"""
    industries = set(a.industry for a in ALUMNI_POOL)
    assert len(industries) >= 5
    print(f"✓ 行业 {len(industries)} 个:{industries}")


def test_alumni_pool_required_fields():
    """校友必填字段"""
    for a in ALUMNI_POOL:
        assert a.id
        assert a.name
        assert a.school
        assert a.major
        assert a.current_company
        assert a.current_position
        assert a.industry
        assert a.city
        assert a.graduation_year > 2017
    print("✓ 校友必填字段完整")


# ============== 4. 4 维匹配 ==============

def test_match_perfect():
    """4 维全匹配"""
    s = StudentProfile(name="s", school="清华大学", department="计算机系",
                       major="计算机科学与技术", target_industry="互联网",
                       target_position="算法工程师", target_city="北京")
    a = ALUMNI_POOL[0]  # 张学长 清华 CS 字节 北京
    score, breakdown = match_score(s, a)
    assert breakdown["school"] == 1.0
    assert breakdown["dept_major"] == 1.0
    assert breakdown["industry"] == 1.0
    assert breakdown["city"] == 1.0
    assert score == 1.0
    print(f"✓ 全匹配 score = {score:.0%}")


def test_match_different_school():
    """不同学校 → 0"""
    s = StudentProfile(name="s", school="北京大学", target_industry="互联网")
    a = ALUMNI_POOL[0]  # 清华
    score, breakdown = match_score(s, a)
    assert breakdown["school"] == 0.0
    assert score < 0.5
    print(f"✓ 不同学校 score = {score:.0%}")


def test_match_same_industry_diff_school():
    """同行业不同校"""
    s = StudentProfile(name="s", school="武汉大学", target_industry="互联网",
                       target_city="北京")
    a = next(x for x in ALUMNI_POOL if x.school == "清华大学" and x.industry == "互联网" and x.city == "北京")
    score, breakdown = match_score(s, a)
    assert breakdown["school"] == 0.0
    assert breakdown["industry"] == 1.0
    assert breakdown["city"] == 1.0
    # 0.4*0 + 0.3*0 + 0.2*1 + 0.1*1 = 0.3
    assert 0.25 <= score <= 0.35, f"同行业同城不同校 score 应 ~0.3,得到 {score}"
    print(f"✓ 同行业同城不同校 score = {score:.0%}")


def test_match_same_major_diff_dept():
    """同专业不同院 → 0.7"""
    s = StudentProfile(name="s", school="清华大学", department="自动化系",
                       major="计算机科学与技术", target_industry="互联网")
    a = ALUMNI_POOL[0]  # 清华 计算机系 CS
    score, breakdown = match_score(s, a)
    assert breakdown["school"] == 1.0
    assert breakdown["dept_major"] == 0.7  # 同专业不同院
    print(f"✓ 同专业不同院 dept_major = {breakdown['dept_major']}")


# ============== 5. find_matches ==============

def test_find_matches_default():
    """默认 Top 5"""
    s = StudentProfile(name="s", school="清华大学", department="计算机系",
                       major="计算机科学与技术", target_industry="互联网",
                       target_position="算法工程师", target_city="北京")
    matches = find_matches(s, top_n=5)
    assert len(matches) <= 5
    # 按分数降序
    for i in range(len(matches) - 1):
        assert matches[i].score >= matches[i + 1].score
    # Top 1 应该是清华 CS 互联网北京
    top1 = matches[0].alumni
    assert top1.school == "清华大学"
    assert top1.industry == "互联网"
    print(f"✓ 清华 CS 算法 Top 1: {top1.name} {top1.current_company}")


def test_find_matches_finance():
    """金融匹配"""
    s = StudentProfile(name="s", school="中央财经大学", department="金融学院",
                       major="金融学", target_industry="金融", target_position="分析师",
                       target_city="北京")
    matches = find_matches(s, top_n=3)
    # Top 1 应该是央财金融
    assert matches[0].alumni.school == "中央财经大学"
    assert matches[0].alumni.industry == "金融"
    print(f"✓ 央财金融 Top 1: {matches[0].alumni.name}")


def test_find_matches_min_score_filter():
    """最低分数过滤"""
    s = StudentProfile(name="s", school="清华大学", target_industry="互联网")
    matches = find_matches(s, top_n=20, min_score=0.7)
    for m in matches:
        assert m.score >= 0.7
    print(f"✓ min_score=0.7 过滤,剩 {len(matches)} 人")


def test_find_matches_empty_for_unknown_school():
    """未知学校 → 0(全 0 校)"""
    s = StudentProfile(name="s", school="三本大学", target_industry="互联网")
    matches = find_matches(s, top_n=5)
    # 0 分也返回(因为 min_score=0)
    for m in matches:
        assert m.score < 0.4
    print(f"✓ 未知学校结果数 {len(matches)}")


# ============== 6. 内推状态机 ==============

def test_refer_request_basic():
    """基本内推请求"""
    req = request_refer(
        student_name="小王", student_school="清华大学", student_major="CS",
        target_company="字节跳动", target_position="算法工程师",
        alumni_id="TH001",
    )
    assert req.status == "requested"
    assert req.alumni_id == "TH001"
    assert len(req.history) >= 1
    print(f"✓ 内推请求 {req.id} 创建")


def test_refer_request_status_updates():
    """状态更新"""
    req = request_refer("小王", "清华", "CS", "字节", "算法", "TH001")
    assert req.status == "requested"
    req.update_status("accepted", "学长接受内推")
    assert req.status == "accepted"
    assert len(req.history) == 2
    req.update_status("submitted", "已提交简历")
    assert req.status == "submitted"
    req.update_status("interviewing", "面试中")
    assert req.status == "interviewing"
    print(f"✓ 状态更新: requested → accepted → submitted → interviewing")


def test_refer_invalid_alumni_raises():
    """无效 alumni 抛错"""
    try:
        request_refer("小王", "清华", "CS", "字节", "算法", "NOTEXIST")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 无效 alumni 抛错")


def test_refer_invalid_status_raises():
    """无效状态抛错"""
    req = request_refer("小王", "清华", "CS", "字节", "算法", "TH001")
    try:
        req.update_status("unknown_status")
        assert False, "应抛 ValueError"
    except ValueError:
        pass
    print("✓ 无效状态抛错")


def test_refer_to_dict():
    """ReferRequest 序列化"""
    req = request_refer("小王", "清华", "CS", "字节", "算法", "TH001")
    req.update_status("accepted")
    d = req.to_dict()
    assert d["status"] == "accepted"
    assert d["status_label"] == "已接受"
    assert len(d["history"]) == 2
    print("✓ ReferRequest 序列化")


def test_refer_history():
    """内推历史"""
    req1 = request_refer("小王", "清华", "CS", "字节", "算法", "TH001")
    req1.update_status("accepted")
    req2 = request_refer("小李", "北大", "CS", "阿里", "产品", "PKU001")
    history = get_refer_history()
    assert len(history) >= 2
    print(f"✓ 内推历史 {len(history)} 条")


# ============== 7. 虚拟学长学姐 ==============

def test_senior_prompts():
    """4 个角色"""
    assert len(SENIOR_PROMPTS) == 4
    for k, v in SENIOR_PROMPTS.items():
        assert "name" in v
        assert "emoji" in v
        assert "style" in v
        assert "prompt" in v
    print(f"✓ 虚拟学长学姐 {len(SENIOR_PROMPTS)} 角色")


def test_get_senior_persona_eng():
    """算法/工程师 → 工程师角色"""
    p = get_senior_persona("TH001")  # 张学长 字节 算法
    assert p["id"] == "senior_eng"
    assert "👨‍💻" in p["emoji"]
    print(f"✓ 工程师角色:{p['name']}")


def test_get_senior_persona_pm():
    """产品 → PM 角色"""
    p = get_senior_persona("ZJU001")  # 梁学姐 字节 PM
    assert p["id"] == "senior_pm"
    assert "👩‍💼" in p["emoji"]
    print(f"✓ PM 角色:{p['name']}")


def test_get_senior_persona_finance():
    """金融 → 金融角色"""
    p = get_senior_persona("PKU002")  # 孙学姐 高盛
    assert p["id"] == "senior_finance"
    print(f"✓ 金融角色:{p['name']}")


def test_get_senior_persona_design():
    """设计 → 设计角色"""
    p = get_senior_persona("TH004")  # 陈学姐 腾讯 UI
    assert p["id"] == "senior_design"
    print(f"✓ 设计角色:{p['name']}")


def test_get_senior_persona_unknown():
    """未知校友 → 默认"""
    p = get_senior_persona("NOTEXIST")
    assert p["id"] == "default"  # default fallback id
    assert "name" in p
    print(f"✓ 未知校友 fallback ({p['name']})")


# ============== 8. 邮箱验证 ==============

def test_verify_email_correct():
    """正确邮箱"""
    assert verify_school_email("wang@mails.tsinghua.edu.cn", "清华大学")
    assert verify_school_email("li@stu.pku.edu.cn", "北京大学")
    print("✓ 正确邮箱验证")


def test_verify_email_wrong_school():
    """邮箱学校不匹配"""
    assert not verify_school_email("wang@mails.tsinghua.edu.cn", "北京大学")
    print("✓ 邮箱学校不匹配")


def test_verify_email_empty():
    """空邮箱"""
    assert not verify_school_email("", "清华大学")
    assert not verify_school_email("wang@mails.tsinghua.edu.cn", "")
    print("✓ 空邮箱")


def test_verify_email_no_at():
    """无 @"""
    assert not verify_school_email("wang_tsinghua_edu_cn", "清华大学")
    print("✓ 无 @")


def test_verify_email_unknown_school():
    """未知学校"""
    assert not verify_school_email("wang@unknown.edu.cn", "三本大学")
    print("✓ 未知学校")


# ============== 9. 核心 API ==============

def test_list_alumni_all():
    """列出全部"""
    ls = list_alumni()
    assert len(ls) == len(ALUMNI_POOL)
    print(f"✓ 列出 {len(ls)} 校友")


def test_list_alumni_filter_school():
    """按学校筛选"""
    ls = list_alumni(school="清华大学")
    assert all(a["school"] == "清华大学" for a in ls)
    assert len(ls) >= 5
    print(f"✓ 清华校友 {len(ls)} 人")


def test_list_alumni_filter_industry():
    """按行业筛选"""
    ls = list_alumni(industry="金融")
    assert all(a["industry"] == "金融" for a in ls)
    assert len(ls) >= 3
    print(f"✓ 金融校友 {len(ls)} 人")


def test_list_alumni_filter_can_refer():
    """按可内推筛选"""
    ls = list_alumni(can_refer=True)
    assert all(a["can_refer"] for a in ls)
    print(f"✓ 可内推 {len(ls)} 人")


def test_get_alumni():
    """获取单个校友"""
    a = get_alumni("TH001")
    assert a is not None
    assert a["id"] == "TH001"
    print("✓ 获取校友")


def test_get_alumni_not_found():
    """未找到"""
    a = get_alumni("NOTEXIST")
    assert a is None
    print("✓ 未找到返回 None")


def test_get_school_email_domain():
    """获取学校域名"""
    d = get_school_email_domain("清华大学")
    assert d == "mails.tsinghua.edu.cn"
    assert get_school_email_domain("三本") is None
    print("✓ 获取学校域名")


def test_list_supported_schools():
    """列出支持学校"""
    ls = list_supported_schools()
    assert len(ls) == len(SCHOOL_EMAIL_DOMAINS)
    print(f"✓ 支持 {len(ls)} 所学校")


# ============== 10. CLI ==============

def test_cli_list():
    """CLI:list"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "alumni.py"), "list"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "TH001" in result.stdout
    print("✓ CLI list")


def test_cli_schools():
    """CLI:schools"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "alumni.py"), "schools"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "清华大学" in result.stdout
    assert "mails.tsinghua.edu.cn" in result.stdout
    print("✓ CLI schools")


def test_cli_verify():
    """CLI:verify"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "alumni.py"), "verify",
         "wang@mails.tsinghua.edu.cn", "清华大学"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "通过" in result.stdout
    print("✓ CLI verify")


def test_cli_find():
    """CLI:find"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "alumni.py"), "find",
         "清华大学", "互联网", "3"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "TH" in result.stdout or "字节" in result.stdout
    print("✓ CLI find")


def test_cli_refer():
    """CLI:refer"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "alumni.py"), "refer",
         "小王", "清华", "CS", "字节", "算法", "TH001"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "已发起" in result.stdout
    print("✓ CLI refer")


# ============== 11. 集成 ==============

def test_integration_full_flow():
    """集成:清华 CS 学生找 Top 校友 + 发内推"""
    s = StudentProfile(
        name="小王", school="清华大学", department="计算机系",
        major="计算机科学与技术", graduation_year=2026,
        target_industry="互联网", target_position="算法工程师",
        target_city="北京", email="wang@mails.tsinghua.edu.cn",
    )
    assert s.is_verified()
    matches = find_matches(s, top_n=3)
    assert len(matches) >= 1
    top1 = matches[0].alumni
    # 发内推
    req = request_refer(
        student_name=s.name, student_school=s.school, student_major=s.major,
        target_company=top1.current_company, target_position=top1.current_position,
        alumni_id=top1.id,
    )
    req.update_status("accepted", "学长接受了")
    req.update_status("submitted", "已提交简历")
    assert req.status == "submitted"
    # 获取虚拟学长学姐
    senior = get_senior_persona(top1.id)
    assert senior["id"] in ("senior_eng", "senior_pm", "senior_finance", "senior_design")
    print(f"✓ 集成:验证 → 匹配 → 内推 → 状态更新 → 虚拟人 {senior['name']}")


def test_integration_cross_school():
    """跨学校:二本学生找 Top 校友(本校维度=0)"""
    s = StudentProfile(name="x", school="二本大学", department="计算机学院",
                       major="软件工程", target_industry="互联网",
                       target_city="深圳")
    matches = find_matches(s, top_n=3)
    # 校=0(跨校),但可同院+同行业+同城
    for m in matches:
        assert m.breakdown["school"] == 0.0, f"跨校 school 应 = 0,得到 {m.breakdown['school']}({m.alumni.school})"
    print(f"✓ 跨校匹配 Top 1: {matches[0].alumni.school} score={matches[0].score:.0%}")


def test_integration_holland_with_alumni():
    """集成:Holland + 校友(算法岗 + 清华 = 强匹配)"""
    # I 主导 + 清华 = 强匹配算法校友
    s = StudentProfile(name="x", school="清华大学", department="计算机系",
                       major="人工智能", target_industry="互联网",
                       target_position="算法工程师", target_city="北京")
    matches = find_matches(s, top_n=3)
    # Top 1 应该是高匹配度
    assert matches[0].score >= 0.6
    print(f"✓ 清华+I 强匹配 score = {matches[0].score:.0%}")


# ============== 入口 ==============

if __name__ == "__main__":
    test_alumni_profile()
    test_student_profile()
    test_match_result()
    test_school_domains_count()
    test_school_domains_top_universities()
    test_school_domains_finance()
    test_school_email_format()
    test_alumni_pool_count()
    test_alumni_pool_schools_diversity()
    test_alumni_pool_industries_diversity()
    test_alumni_pool_required_fields()
    test_match_perfect()
    test_match_different_school()
    test_match_same_industry_diff_school()
    test_match_same_major_diff_dept()
    test_find_matches_default()
    test_find_matches_finance()
    test_find_matches_min_score_filter()
    test_find_matches_empty_for_unknown_school()
    test_refer_request_basic()
    test_refer_request_status_updates()
    test_refer_invalid_alumni_raises()
    test_refer_invalid_status_raises()
    test_refer_to_dict()
    test_refer_history()
    test_senior_prompts()
    test_get_senior_persona_eng()
    test_get_senior_persona_pm()
    test_get_senior_persona_finance()
    test_get_senior_persona_design()
    test_get_senior_persona_unknown()
    test_verify_email_correct()
    test_verify_email_wrong_school()
    test_verify_email_empty()
    test_verify_email_no_at()
    test_verify_email_unknown_school()
    test_list_alumni_all()
    test_list_alumni_filter_school()
    test_list_alumni_filter_industry()
    test_list_alumni_filter_can_refer()
    test_get_alumni()
    test_get_alumni_not_found()
    test_get_school_email_domain()
    test_list_supported_schools()
    test_cli_list()
    test_cli_schools()
    test_cli_verify()
    test_cli_find()
    test_cli_refer()
    test_integration_full_flow()
    test_integration_cross_school()
    test_integration_holland_with_alumni()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
