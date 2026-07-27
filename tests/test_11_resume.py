#!/usr/bin/env python3
"""
test_11_resume — aichat-hub Cycle 11 简历模块测试
================================================
覆盖:
  1. 数据模型(Internship/Project/ResumeProfile)+ 序列化
  2. 简历生成(3 个变体)
  3. 简历改写(弱动词替换 + 量化 TODO + 3 角色)
  4. 5 维评分(完整性/量化/STAR/相关性/格式)
  5. 角色列表 + 变体列表
  6. CLI 入口可执行
  7. Profile 边界情况(空 profile / 高完整 profile)
"""
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from resume import (
    Internship, Project, ResumeProfile,
    generate_resume, rewrite_resume, score_resume,
    get_persona_info, list_personas, list_variants,
    PERSONA_PROMPTS, POSITION_KEYWORDS, WEAK_TO_STRONG,
    ScoreResult, _has_quantification, _star_compliance,
    _format_score, _relevance_score,
)


# ============== 1. 数据模型 ==============

def test_internship_dataclass():
    """Internship 数据类"""
    it = Internship(company="字节", role="算法实习生", period="2024.06 - 2024.09",
                    description="实现了推荐系统")
    assert it.company == "字节"
    assert it.role == "算法实习生"
    print("✓ Internship 数据类")


def test_project_dataclass():
    """Project 数据类"""
    p = Project(name="CubeSolver", role="核心开发", period="2024.03-2024.06",
                description="用 Q-Learning 解魔方", tech_stack=["Python", "NumPy"])
    assert p.name == "CubeSolver"
    assert "Python" in p.tech_stack
    print("✓ Project 数据类")


def test_resume_profile_minimal():
    """最小 Profile(只 name)"""
    p = ResumeProfile(name="小王")
    assert p.name == "小王"
    assert p.degree == "本科"
    assert p.target_position == "算法工程师"
    assert p.internships == []
    print("✓ ResumeProfile 默认值")


def test_resume_profile_serialization():
    """Profile 序列化 / 反序列化"""
    p = ResumeProfile(
        name="小王", school="清华大学", major="计算机",
        internships=[Internship(company="字节", role="算法实习生", period="2024.06",
                                description="实现推荐系统")],
        projects=[Project(name="Demo", description="做了一个 demo", tech_stack=["Python"])],
        skills=["Python", "PyTorch"],
    )
    d = p.to_dict()
    assert d["name"] == "小王"
    assert d["internships"][0]["company"] == "字节"
    assert d["projects"][0]["tech_stack"] == ["Python"]
    # 反序列化
    p2 = ResumeProfile.from_dict(d)
    assert p2.name == "小王"
    assert p2.internships[0].company == "字节"
    assert p2.projects[0].tech_stack == ["Python"]
    print("✓ Profile 序列化/反序列化")


def test_completeness_empty():
    """空 profile 完整性接近 0"""
    p = ResumeProfile(name="小王")
    comp = p.completeness_ratio()
    # name + degree + target_position 三个有默认值 → 至少 0.25
    assert comp < 0.4, f"空 profile 完整性应低,得到 {comp}"
    print(f"✓ 完整性(空 profile) = {comp:.2%}")


def test_completeness_full():
    """完整 profile 完整性接近 1"""
    p = ResumeProfile(
        name="小王", school="清华", major="CS", degree="硕士",
        target_position="算法工程师", email="a@b.com",
        internships=[Internship("字节", "算法", "2024.06", "实现推荐")],
        projects=[Project("Demo", "独立开发", "2024.03", "做了 demo", ["Python"])],
        skills=["Python"], awards=["国奖"],
        self_intro="我是一名学生",
    )
    comp = p.completeness_ratio()
    assert comp >= 0.95, f"完整 profile 完整性应高,得到 {comp}"
    print(f"✓ 完整性(完整 profile) = {comp:.2%}")


# ============== 2. 简历生成 ==============

def _make_full_profile() -> ResumeProfile:
    return ResumeProfile(
        name="小王", school="清华大学", major="计算机", degree="本科",
        graduation_year=2026, target_position="算法工程师",
        email="wang@tsinghua.edu.cn", phone="13800000000",
        internships=[
            Internship(company="字节跳动", role="算法实习生",
                       period="2024.06 - 2024.09",
                       description="负责推荐系统召回层优化,提升 DAU 5%"),
        ],
        projects=[
            Project(name="CubeSolver", role="核心开发", period="2024.03 - 2024.06",
                    description="用 Q-Learning 实现魔方求解器,平均 30 步解出",
                    tech_stack=["Python", "NumPy", "PyTorch"]),
        ],
        skills=["Python", "PyTorch", "SQL", "数据结构"],
        awards=["ACM 区域赛金奖", "国家奖学金"],
        self_intro="热爱算法,擅长数学建模,熟悉推荐系统全链路。",
    )


def test_generate_technical():
    """生成技术版简历"""
    p = _make_full_profile()
    text = generate_resume(p, "technical")
    assert "# 小王" in text
    assert "## 教育背景" in text
    assert "## 实习经历" in text
    assert "## 项目经历" in text
    assert "## 技能清单" in text  # 技术版特有
    assert "## 获奖经历" in text
    assert "Python" in text
    assert "ACM 区域赛金奖" in text
    print(f"✓ 技术版简历生成 ({len(text)} 字符)")


def test_generate_product():
    """生成产品版简历"""
    p = _make_full_profile()
    text = generate_resume(p, "product")
    assert "# 小王" in text
    assert "## 自我评价" in text  # 产品版强调
    assert "## 实习经历" in text
    assert "## 项目经历" in text
    print(f"✓ 产品版简历生成 ({len(text)} 字符)")


def test_generate_operation():
    """生成运营版简历"""
    p = _make_full_profile()
    text = generate_resume(p, "operation")
    assert "# 小王" in text
    assert "## 自我评价" in text
    assert "## 实习经历" in text
    print(f"✓ 运营版简历生成 ({len(text)} 字符)")


def test_generate_minimal_profile():
    """最小 profile(只有 name)生成"""
    p = ResumeProfile(name="无名氏")
    text = generate_resume(p, "technical")
    assert "# 无名氏" in text
    assert "## 实习经历" not in text  # 没有就不输出
    print("✓ 最小 profile 生成")


# ============== 3. 简历改写 ==============

def test_rewrite_weak_verb_replacement():
    """弱动词 → 强动词"""
    p = ResumeProfile(
        name="小王", school="清华", major="CS",
        internships=[Internship("A", "B", "2024.06", "负责了推荐系统的开发")],
    )
    text, notes = rewrite_resume(p, "technical", "mentor")
    # "负责" 应被替换成"主导"
    assert "负责了" not in text or "TODO" in text  # 改写后无原"负责"
    assert any("替换" in n for n in notes)
    print("✓ 弱动词替换")


def test_rewrite_quantification_todo():
    """无量化数据自动加 TODO"""
    p = ResumeProfile(
        name="小王", school="清华", major="CS",
        internships=[Internship("A", "B", "2024.06", "负责开发一个系统")],
    )
    text, notes = rewrite_resume(p, "technical", "mentor")
    assert "TODO" in text
    assert any("量化" in n for n in notes)
    print("✓ 量化 TODO 提示")


def test_rewrite_with_quantification_keeps():
    """已有量化数据,不再加 TODO"""
    p = ResumeProfile(
        name="小王", school="清华", major="CS",
        internships=[Internship("A", "B", "2024.06",
                                "负责推荐系统,性能提升 30%,覆盖 100 万用户")],
    )
    text, notes = rewrite_resume(p, "technical", "mentor")
    # 已有数字,不应加 TODO
    assert "TODO" not in text
    print("✓ 已有量化数据时不加 TODO")


def test_rewrite_three_personas():
    """3 个角色都能调用"""
    p = _make_full_profile()
    for persona in ("mentor", "hr", "senior"):
        text, notes = rewrite_resume(p, "technical", persona)
        assert isinstance(text, str)
        assert len(text) > 100
        # 角色 emoji 应在第一条 note
        assert PERSONA_PROMPTS[persona]["emoji"] in notes[0]
        # 角色名应在第一条 note
        assert PERSONA_PROMPTS[persona]["name"] in notes[0]
    print("✓ 3 角色改写")


# ============== 4. 5 维评分 ==============

def test_score_full_profile_high():
    """完整 profile 评分应较高"""
    p = _make_full_profile()
    r = score_resume(p)
    assert isinstance(r, ScoreResult)
    assert 0 <= r.completeness <= 1
    assert 0 <= r.quantification <= 1
    assert 0 <= r.star_compliance <= 1
    assert 0 <= r.relevance <= 1
    assert 0 <= r.format_score <= 1
    assert 0 <= r.total <= 1
    # 完整 profile 总分应 > 0.5
    assert r.total > 0.5, f"完整 profile 总分应较高,得到 {r.total}"
    print(f"✓ 完整 profile 评分 = {r.total:.2%}")


def test_score_minimal_profile_low():
    """最小 profile 评分应较低"""
    p = ResumeProfile(name="小王")
    r = score_resume(p)
    assert r.total < 0.5, f"最小 profile 总分应低,得到 {r.total}"
    assert len(r.suggestions) > 0  # 应有建议
    print(f"✓ 最小 profile 评分 = {r.total:.2%}, {len(r.suggestions)} 条建议")


def test_score_suggestions():
    """建议生成"""
    p = ResumeProfile(name="小王")  # 空白
    r = score_resume(p)
    sug_text = " ".join(r.suggestions)
    # 至少包含 完整性 / 量化 / STAR / 关键词 / 格式 中的几个
    assert any(kw in sug_text for kw in ["完整性", "量化", "STAR", "关键词", "格式"])
    print(f"✓ 评分建议 {len(r.suggestions)} 条")


def test_quantification_metric():
    """量化检测"""
    assert _has_quantification("用户 100 万") == 1.0  # 全部含数字
    assert _has_quantification("") == 0.0
    assert _has_quantification("没有数字") == 0.0
    # 混合:2 句含数字,2 句不含
    mixed = _has_quantification("用户 100 万。无数字句。有数字 5。纯文字。")
    assert 0.0 < mixed < 1.0, f"混合句量化分应介于 0-1,得到 {mixed}"
    # 纯数字句
    assert _has_quantification("性能提升 30%") == 1.0
    # 单句不含
    assert _has_quantification("负责开发系统") == 0.0
    print(f"✓ 量化检测(混合) = {mixed:.2%}")


def test_star_compliance_metric():
    """STAR 合规检测"""
    full_star = "在项目期间,需要优化推荐性能,通过引入缓存实现,降低延迟 50ms"
    score = _star_compliance(full_star)
    assert score == 1.0, f"完整 STAR 应 = 1.0,得到 {score}"
    assert _star_compliance("") == 0.0
    print(f"✓ STAR 检测(完整) = {score:.0%}")


def test_format_score_metric():
    """格式分"""
    good = "# 标题\n## 子标题\n- 列表项 1\n- 列表项 2\n" * 10  # 中等长度
    s = _format_score(good)
    assert s > 0.5
    assert _format_score("") == 0.0
    print(f"✓ 格式分 = {s:.2%}")


def test_relevance_score_algorithm():
    """算法岗关键词相关性"""
    p = _make_full_profile()  # 目标 = 算法工程师,含 PyTorch/Python
    r = _relevance_score(p)
    # 完整 profile 应有一定相关度
    assert r > 0.0
    print(f"✓ 关键词相关性(算法岗) = {r:.2%}")


def test_relevance_score_unknown_position():
    """未知岗位关键词相关性走 fallback"""
    p = ResumeProfile(name="小王", target_position="未知岗位")
    r = _relevance_score(p)
    assert r == 0.5  # fallback
    print(f"✓ 未知岗位关键词 fallback = {r:.2%}")


# ============== 5. 角色 / 变体 ==============

def test_list_personas():
    """列出 3 个角色"""
    ps = list_personas()
    assert len(ps) == 3
    ids = [p["id"] for p in ps]
    assert "mentor" in ids
    assert "hr" in ids
    assert "senior" in ids
    for p in ps:
        assert "name" in p
        assert "emoji" in p
        assert "system_prompt" in p
        assert len(p["system_prompt"]) > 50
    print(f"✓ 角色列表 ({len(ps)} 个)")


def test_get_persona_info():
    """获取单个角色"""
    info = get_persona_info("mentor")
    assert info["id"] == "mentor"
    assert "简历导师" in info["name"]
    assert "STAR" in info["system_prompt"]
    print("✓ 单角色信息")


def test_list_variants():
    """列出 3 个变体"""
    vs = list_variants()
    assert "technical" in vs
    assert "product" in vs
    assert "operation" in vs
    print(f"✓ 变体列表 ({len(vs)} 个)")


# ============== 6. 字典/数据 ==============

def test_weak_strong_verb_dict():
    """弱动词词典"""
    assert "负责" in WEAK_TO_STRONG
    assert WEAK_TO_STRONG["负责"] == "主导"
    assert len(WEAK_TO_STRONG) >= 5
    print(f"✓ 弱→强动词 {len(WEAK_TO_STRONG)} 条")


def test_position_keywords():
    """岗位关键词库"""
    assert "算法工程师" in POSITION_KEYWORDS
    assert "产品经理" in POSITION_KEYWORDS
    for pos, kws in POSITION_KEYWORDS.items():
        assert len(kws) >= 8, f"{pos} 关键词数 = {len(kws)}"
    print(f"✓ 岗位关键词 {len(POSITION_KEYWORDS)} 个岗位")


# ============== 7. CLI ==============

def test_cli_personas():
    """CLI:personas 子命令"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "resume.py"), "personas"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert len(data) == 3
    print("✓ CLI personas")


def test_cli_variants():
    """CLI:variants 子命令"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "resume.py"), "variants"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "technical" in result.stdout
    print("✓ CLI variants")


def test_cli_generate():
    """CLI:generate 子命令"""
    p = _make_full_profile()
    d = p.to_dict()
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "resume.py"), "generate",
         json.dumps(d, ensure_ascii=False), "technical"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "# 小王" in result.stdout
    assert "## 项目经历" in result.stdout
    print("✓ CLI generate")


def test_cli_rewrite():
    """CLI:rewrite 子命令"""
    p = _make_full_profile()
    d = p.to_dict()
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "resume.py"), "rewrite",
         json.dumps(d, ensure_ascii=False), "technical", "mentor"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "改写后" in result.stdout
    assert "改写说明" in result.stdout
    assert "简历导师" in result.stdout
    print("✓ CLI rewrite")


def test_cli_score():
    """CLI:score 子命令"""
    p = _make_full_profile()
    d = p.to_dict()
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "resume.py"), "score",
         json.dumps(d, ensure_ascii=False)],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "total" in data
    assert "completeness" in data
    assert 0 <= data["total"] <= 1
    print(f"✓ CLI score = {data['total']:.2%}")


# ============== 8. 集成 ==============

def test_integration_rewrite_then_score():
    """集成:改写后再评分"""
    p = _make_full_profile()
    text, notes = rewrite_resume(p, "technical", "mentor")
    # 改写后生成的 Profile 重新评分
    # 这里只验证 text 长度合理(改写不破坏结构)
    assert "##" in text  # 仍有标题
    assert len(text) > 300, f"改写后文本应 > 300 字符,得到 {len(text)}"
    # 改写说明应包含至少 1 条
    assert len(notes) >= 1
    print(f"✓ 改写集成 ({len(text)} 字符, {len(notes)} 条改写说明)")


# ============== 入口 ==============

if __name__ == "__main__":
    test_internship_dataclass()
    test_project_dataclass()
    test_resume_profile_minimal()
    test_resume_profile_serialization()
    test_completeness_empty()
    test_completeness_full()
    test_generate_technical()
    test_generate_product()
    test_generate_operation()
    test_generate_minimal_profile()
    test_rewrite_weak_verb_replacement()
    test_rewrite_quantification_todo()
    test_rewrite_with_quantification_keeps()
    test_rewrite_three_personas()
    test_score_full_profile_high()
    test_score_minimal_profile_low()
    test_score_suggestions()
    test_quantification_metric()
    test_star_compliance_metric()
    test_format_score_metric()
    test_relevance_score_algorithm()
    test_relevance_score_unknown_position()
    test_list_personas()
    test_get_persona_info()
    test_list_variants()
    test_weak_strong_verb_dict()
    test_position_keywords()
    test_cli_personas()
    test_cli_variants()
    test_cli_generate()
    test_cli_rewrite()
    test_cli_score()
    test_integration_rewrite_then_score()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
