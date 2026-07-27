#!/usr/bin/env python3
"""
aichat-hub Resume (简历) 模块
=============================
大学生 AI 改简历 — 简历生成 / 改写 / 评分。

3 角色(虚拟人化):
  - 简历导师(mentor) — 通用改写建议 + STAR 法则 + 量化数据
  - 行业 HR(hr) — 关键词匹配 + ATS 兼容性 + 行业侧重
  - 学长学姐(senior) — 实战经验 + 面试官关心点 + 口语化建议

3 简历变体(同 Profile 多版本):
  - technical(技术版)— 突出技术栈、GitHub、竞赛、项目
  - product(产品版)— 突出用户思维、数据驱动、PRD 案例、实习
  - operation(运营版)— 突出用户增长、活动策划、内容运营

5 维评分:
  1. 完整性 completeness — Profile 必填字段覆盖率
  2. 量化 quantification — 动词 + 数字密度
  3. STAR 合规 star_compliance — 关键项四要素覆盖
  4. 关键词相关性 relevance — 与目标岗位的关键词匹配度
  5. 格式 format — Markdown 结构 + 长度合理性

沙箱安全:
  - 不依赖 LLM API(规则 + 模板)
  - 可选 LLM 模式:接 LLMClient(provider="mock") 给建议,无 key 也 OK

Cycle 11 — 第一个职业辅导模块
"""
from __future__ import annotations
import json
import re
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


# ============== 数据模型 ==============

@dataclass
class Internship:
    """一段实习"""
    company: str
    role: str
    period: str            # "2024.06 - 2024.09"
    description: str       # 一段描述(可能空,待改写)


@dataclass
class Project:
    """一个项目"""
    name: str
    role: str = ""         # "个人项目" / "团队 leader" / "核心开发"
    period: str = ""       # "2024.03 - 2024.06"
    description: str = ""  # 一段描述
    tech_stack: List[str] = field(default_factory=list)


@dataclass
class ResumeProfile:
    """简历基础信息"""
    name: str
    school: str = ""
    major: str = ""
    degree: str = "本科"   # 本科 / 硕士 / 博士
    graduation_year: int = 2026
    target_position: str = "算法工程师"
    phone: str = ""
    email: str = ""
    internships: List[Internship] = field(default_factory=list)
    projects: List[Project] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    awards: List[str] = field(default_factory=list)
    self_intro: str = ""

    def completeness_ratio(self) -> float:
        """完整性:必填字段的填充率(0-1)"""
        fields_required = [
            self.name, self.school, self.major, self.degree,
            self.target_position, self.email,
        ]
        # 至少 1 段实习或 1 个项目,记 1/3 权重
        list_filled = sum([
            1.0 if self.internships else 0.0,
            1.0 if self.projects else 0.0,
            1.0 if self.skills else 0.0,
            1.0 if self.awards else 0.0,
            1.0 if self.self_intro else 0.0,
        ]) / 5.0
        basic_filled = sum(1.0 for f in fields_required if f) / len(fields_required)
        # 基础字段 0.5 + 列表字段 0.5
        return round(0.5 * basic_filled + 0.5 * list_filled, 4)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "ResumeProfile":
        """从 dict 构造(支持嵌套 internship/project)"""
        internships = [Internship(**x) for x in d.get("internships", [])]
        projects = [Project(**x) for x in d.get("projects", [])]
        return cls(
            **{k: v for k, v in d.items() if k not in ("internships", "projects")},
            internships=internships,
            projects=projects,
        )


# ============== 角色 Prompt 模板 ==============

PERSONA_PROMPTS = {
    "mentor": {
        "name": "简历导师",
        "emoji": "📝",
        "system_prompt": (
            "你是一位资深简历导师,精通 STAR 法则(情境/任务/行动/结果)。"
            "你会针对学生的简历,给出具体可执行的改写建议:"
            "1) 补全量化数据(用户量、性能提升、覆盖率等)"
            "2) 用动词开头(实现/优化/设计/主导/推动)"
            "3) 结构化成 STAR 四要素"
            "4) 删掉所有无意义副词('负责'/'参与'/'协助')"
        ),
    },
    "hr": {
        "name": "行业 HR",
        "emoji": "💼",
        "system_prompt": (
            "你是一位互联网大厂 HR,熟悉 ATS(简历自动筛选系统)。"
            "你的关注点:"
            "1) 关键词匹配(目标岗位的技能词必须出现)"
            "2) 项目深度(3 句话以内必须讲清楚做什么/怎么做的/效果)"
            "3) 实习含金量(大厂 > 创业 > 中小厂,核心岗 > 边缘岗)"
            "4) 稳定性(学校 GPA / 实习时长 / 跳槽频率)"
        ),
    },
    "senior": {
        "name": "学长学姐",
        "emoji": "🎓",
        "system_prompt": (
            "你是一位刚从大厂校招上岸的学长/学姐,愿意分享实战经验。"
            "你会用口语化、过来人的视角告诉学生:"
            "1) 面试官真正关心什么(不是简历上写什么)"
            "2) 哪些实习 / 项目经验最加分(亲历者视角)"
            "3) 校招时间线(提前批/正式批/秋招补录)"
            "4) 怎么选 offer(钱、成长、平台、WLB)"
        ),
    },
}


# ============== 量化词典(改写用) ==============

# 弱动词 → 强动词
WEAK_TO_STRONG = {
    "负责": "主导",
    "参与": "核心开发",
    "协助": "独立完成",
    "帮助": "推动",
    "做": "实现",
    "写了": "开发",
    "搞了": "构建",
    "弄了": "搭建",
}

# 量化模板(根据描述自动补全)
QUANT_TEMPLATES = [
    "覆盖 {N}+ 用户",
    "性能提升 {N}%",
    "降低延迟 {N}ms",
    "日均处理 {N} 万条",
    "代码覆盖率 {N}%",
    "QPS 提升 {N} 倍",
    "DAU 增长 {N}%",
    "转化率提升 {N} 个百分点",
    "节省 {N} 小时/周",
    "成本降低 {N}%",
]


# ============== 简历生成 ==============

def generate_resume(profile: ResumeProfile, variant: str = "technical") -> str:
    """
    生成 Markdown 简历。

    variant:
      - technical: 技术版(项目 + 技能 + 实习)
      - product: 产品版(实习 + 项目 + 自我评价)
      - operation: 运营版(实习 + 获奖 + 自我评价)
    """
    lines: List[str] = []
    # 头部
    lines.append(f"# {profile.name}")
    contact_parts = []
    if profile.school:
        contact_parts.append(f"📚 {profile.school} · {profile.major} · {profile.degree} · {profile.graduation_year}")
    if profile.target_position:
        contact_parts.append(f"🎯 目标:{profile.target_position}")
    if profile.email:
        contact_parts.append(f"📧 {profile.email}")
    if profile.phone:
        contact_parts.append(f"📱 {profile.phone}")
    if contact_parts:
        lines.append("  |  ".join(contact_parts))
    lines.append("")

    # 教育背景(永远显示)
    if profile.school:
        lines.append("## 教育背景")
        lines.append(f"- **{profile.school}** · {profile.major} · {profile.degree} · 预计 {profile.graduation_year} 毕业")
        lines.append("")

    # 实习(永远显示,有就放)
    if profile.internships:
        lines.append("## 实习经历")
        for it in profile.internships:
            lines.append(f"### {it.company} · {it.role}  `{it.period}`")
            if it.description:
                lines.append(f"- {it.description}")
            lines.append("")
        lines.append("")

    # 项目:根据 variant 决定详细度
    if profile.projects:
        lines.append("## 项目经历")
        for p in profile.projects:
            head = f"### {p.name}"
            if p.role:
                head += f" · {p.role}"
            if p.period:
                head += f"  `{p.period}`"
            lines.append(head)
            if variant == "technical" and p.tech_stack:
                lines.append(f"- **技术栈**:{', '.join(p.tech_stack)}")
            if p.description:
                lines.append(f"- {p.description}")
            lines.append("")

    # 技能:技术版最详细
    if profile.skills and variant == "technical":
        lines.append("## 技能清单")
        lines.append("- " + " · ".join(profile.skills))
        lines.append("")

    # 获奖
    if profile.awards:
        lines.append("## 获奖经历")
        for a in profile.awards:
            lines.append(f"- {a}")
        lines.append("")

    # 自我评价:产品/运营版强调
    if profile.self_intro and variant in ("product", "operation"):
        lines.append("## 自我评价")
        lines.append(profile.self_intro)
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ============== 简历改写 ==============

def rewrite_resume(
    profile: ResumeProfile,
    variant: str = "technical",
    persona: str = "mentor",
) -> Tuple[str, List[str]]:
    """
    改写简历(规则化):
      1. 弱动词 → 强动词
      2. 描述为空时,补充模板化占位(待 LLM 后续填)
      3. 量化数据补全(若描述中无数字,加 TODO 标记)

    返回 (改写后简历, 改写说明列表)
    """
    notes: List[str] = []
    new_interns: List[Internship] = []
    for it in profile.internships:
        desc = it.description
        old_desc = desc
        # 1) 弱动词替换
        for weak, strong in WEAK_TO_STRONG.items():
            if weak in desc:
                desc = desc.replace(weak, strong)
        # 2) 量化检测
        has_number = bool(re.search(r"\d+(\.\d+)?", desc))
        if not has_number and desc:
            desc += " [TODO: 补充量化数据,如用户量/性能提升/节省成本]"
            notes.append(f"实习「{it.company} · {it.role}」无量化数据,已添加 TODO")
        if desc != old_desc:
            notes.append(f"实习「{it.company} · {it.role}」弱动词已替换")
        new_interns.append(Internship(company=it.company, role=it.role, period=it.period, description=desc))

    new_projs: List[Project] = []
    for p in profile.projects:
        desc = p.description
        old_desc = desc
        for weak, strong in WEAK_TO_STRONG.items():
            if weak in desc:
                desc = desc.replace(weak, strong)
        has_number = bool(re.search(r"\d+(\.\d+)?", desc))
        if not has_number and desc:
            desc += " [TODO: 补充量化数据,如性能提升 N%]"
            notes.append(f"项目「{p.name}」无量化数据,已添加 TODO")
        if desc != old_desc:
            notes.append(f"项目「{p.name}」弱动词已替换")
        new_projs.append(Project(
            name=p.name, role=p.role, period=p.period,
            description=desc, tech_stack=p.tech_stack,
        ))

    new_profile = ResumeProfile(
        name=profile.name, school=profile.school, major=profile.major,
        degree=profile.degree, graduation_year=profile.graduation_year,
        target_position=profile.target_position, phone=profile.phone,
        email=profile.email, internships=new_interns, projects=new_projs,
        skills=profile.skills, awards=profile.awards,
        self_intro=profile.self_intro,
    )
    rewritten = generate_resume(new_profile, variant=variant)

    # 角色化评语(轻量)
    persona_info = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["mentor"])
    notes.insert(0, f"由 {persona_info['emoji']} {persona_info['name']} 改写")
    return rewritten, notes


# ============== 5 维评分 ==============

# 目标岗位的关键词词典(简版)
POSITION_KEYWORDS = {
    "算法工程师": ["机器学习", "深度学习", "Python", "PyTorch", "TensorFlow", "论文", "ACM", "数学建模", "LeetCode", "数据挖掘"],
    "产品经理": ["用户调研", "PRD", "竞品分析", "Axure", "数据驱动", "需求文档", "A/B 测试", "用户增长", "MVP", "原型设计"],
    "运营": ["用户增长", "社群运营", "内容运营", "活动策划", "转化率", "DAU", "MAU", "新媒体", "短视频", "小红书"],
    "后端工程师": ["Java", "Python", "Go", "MySQL", "Redis", "Kafka", "微服务", "Docker", "Linux", "高并发"],
    "前端工程师": ["JavaScript", "TypeScript", "React", "Vue", "Webpack", "CSS", "HTML5", "Node.js", "小程序", "性能优化"],
    "数据分析师": ["SQL", "Python", "Excel", "Tableau", "Power BI", "数据可视化", "AB 测试", "统计学", "业务分析", "埋点"],
    "测试工程师": ["自动化测试", "Selenium", "JMeter", "接口测试", "Python", "性能测试", "测试用例", "CI/CD", "黑盒", "白盒"],
    "UI 设计师": ["Figma", "Sketch", "Photoshop", "设计规范", "用户研究", "交互设计", "视觉设计", "动效", "图标", "UI Kit"],
    "咨询": ["行业研究", "PPT", "Excel", "案例分析", "麦肯锡", "贝恩", "BCG", "战略", "用户访谈", "数据建模"],
    "金融": ["CFA", "FRM", "Wind", "Bloomberg", "Excel", "估值", "财务建模", "行业研究", "投资", "IPO"],
}


def _has_quantification(text: str) -> float:
    """量化分:含数字的句子 / 总句子(0-1)"""
    if not text:
        return 0.0
    sents = re.split(r"[。.!?！？\n]", text)
    sents = [s for s in sents if s.strip()]
    if not sents:
        return 0.0
    n_with_num = sum(1 for s in sents if re.search(r"\d+(\.\d+)?", s))
    return round(n_with_num / len(sents), 4)


def _star_compliance(text: str) -> float:
    """STAR 合规:四要素关键词覆盖(0-1)
       S=情境, T=任务, A=行动, R=结果
       简化:检测"在...期间 / 通过...实现 / 优化 / 提升 / 降低"等模式
    """
    if not text:
        return 0.0
    s_pattern = bool(re.search(r"(在|当).{0,10}(期间|时|场景下|情况下)", text))
    t_pattern = bool(re.search(r"(需要|目标|任务|要求|为了)", text))
    a_pattern = bool(re.search(r"(通过|采用|利用|基于|实现|设计|开发|构建|优化|推动)", text))
    r_pattern = bool(re.search(r"(提升|降低|增长|增加|减少|节省|达到|完成|实现.*\d|性能)", text))
    return round(sum([s_pattern, t_pattern, a_pattern, r_pattern]) / 4.0, 4)


def _format_score(text: str) -> float:
    """格式分:Markdown 结构 + 长度合理性(0-1)"""
    if not text:
        return 0.0
    has_heading = text.count("##") >= 2
    has_list = text.count("\n- ") >= 2
    length = len(text)
    # 理想长度 500-2500 字符
    if 500 <= length <= 2500:
        len_score = 1.0
    elif length < 500:
        len_score = length / 500
    else:
        len_score = max(0.0, 1.0 - (length - 2500) / 2500)
    return round(0.3 * (1.0 if has_heading else 0.0) + 0.3 * (1.0 if has_list else 0.0) + 0.4 * len_score, 4)


def _relevance_score(profile: ResumeProfile) -> float:
    """关键词相关性:目标岗位的关键词在简历中的覆盖率(0-1)"""
    pos = profile.target_position
    keywords = POSITION_KEYWORDS.get(pos)
    if not keywords:
        return 0.5  # 未知岗位,中庸
    # 拼所有文本
    text_parts = [profile.major, profile.self_intro]
    for it in profile.internships:
        text_parts.append(it.description)
    for p in profile.projects:
        text_parts.append(p.description)
        text_parts.extend(p.tech_stack)
    text_parts.extend(profile.skills)
    text = " ".join(text_parts).lower()
    hit = sum(1 for kw in keywords if kw.lower() in text)
    return round(hit / len(keywords), 4)


@dataclass
class ScoreResult:
    """5 维评分结果"""
    completeness: float = 0.0
    quantification: float = 0.0
    star_compliance: float = 0.0
    relevance: float = 0.0
    format_score: float = 0.0
    total: float = 0.0
    suggestions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def score_resume(profile: ResumeProfile) -> ScoreResult:
    """5 维评分(不依赖 LLM)"""
    comp = profile.completeness_ratio()
    # 拼所有描述文本
    descs = []
    for it in profile.internships:
        descs.append(it.description)
    for p in profile.projects:
        descs.append(p.description)
    all_desc = " ".join(descs)
    quant = _has_quantification(all_desc)
    star = _star_compliance(all_desc)
    rel = _relevance_score(profile)
    fmt = _format_score(generate_resume(profile))

    # 加权平均
    total = round(
        0.20 * comp + 0.20 * quant + 0.20 * star + 0.25 * rel + 0.15 * fmt,
        4
    )
    # 建议
    suggestions: List[str] = []
    if comp < 0.7:
        suggestions.append(f"完整性 {comp:.0%}:补全学校/邮箱/技能/项目等字段")
    if quant < 0.4:
        suggestions.append(f"量化 {quant:.0%}:每个项目/实习都加 1-2 个数字(用户量/性能/节省)")
    if star < 0.5:
        suggestions.append(f"STAR 合规 {star:.0%}:按 情境/任务/行动/结果 四要素重写")
    if rel < 0.3:
        suggestions.append(f"关键词相关 {rel:.0%}:补全 {profile.target_position} 岗位关键词")
    if fmt < 0.6:
        suggestions.append(f"格式 {fmt:.0%}:增加 ## 标题和 - 列表,长度 500-2500 字符")
    if total < 0.6:
        suggestions.append("总评分较低,建议从最高分维度优先优化")

    return ScoreResult(
        completeness=comp, quantification=quant, star_compliance=star,
        relevance=rel, format_score=fmt, total=total,
        suggestions=suggestions,
    )


# ============== 便捷函数(高阶 API) ==============

def get_persona_info(persona: str) -> Dict[str, str]:
    """获取角色信息"""
    p = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["mentor"])
    return {"id": persona, **p}


def list_personas() -> List[Dict[str, str]]:
    """列出所有角色"""
    return [get_persona_info(k) for k in PERSONA_PROMPTS.keys()]


def list_variants() -> List[str]:
    """列出所有简历变体"""
    return ["technical", "product", "operation"]


# ============== CLI ==============

def main():
    """CLI 入口"""
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 resume.py {generate|rewrite|score|personas|variants}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "personas":
        print(json.dumps(list_personas(), ensure_ascii=False, indent=2))
    elif cmd == "variants":
        print(list_variants())
    else:
        # 其他命令需要 stdin 输入 profile JSON
        if len(sys.argv) < 3:
            print("Need profile JSON as argument (or stdin)", file=sys.stderr)
            sys.exit(1)
        try:
            d = json.loads(sys.argv[2])
        except json.JSONDecodeError:
            d = json.loads(sys.stdin.read())
        profile = ResumeProfile.from_dict(d)
        if cmd == "generate":
            variant = sys.argv[3] if len(sys.argv) > 3 else "technical"
            print(generate_resume(profile, variant))
        elif cmd == "rewrite":
            variant = sys.argv[3] if len(sys.argv) > 3 else "technical"
            persona = sys.argv[4] if len(sys.argv) > 4 else "mentor"
            text, notes = rewrite_resume(profile, variant, persona)
            print("=== 改写后 ===")
            print(text)
            print("\n=== 改写说明 ===")
            for n in notes:
                print(f"- {n}")
        elif cmd == "score":
            r = score_resume(profile)
            print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))
        else:
            print(f"Unknown command: {cmd}", file=sys.stderr)
            sys.exit(1)


if __name__ == "__main__":
    main()
