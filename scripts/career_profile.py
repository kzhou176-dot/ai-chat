#!/usr/bin/env python3
"""
aichat-Hub Career Profile (霍兰德职业兴趣测试) 模块
==================================================
基于 John Holland RIASEC 理论,大学生职业画像。

6 维:
  R(Realistic 实际型)— 动手 / 操作 / 工具
  I(Investigative 研究型)— 研究 / 分析 / 思考
  A(Artistic 艺术型)— 创造 / 表达 / 设计
  S(Social 社会型)— 助人 / 教育 / 服务
  E(Enterprising 企业型)— 领导 / 影响 / 说服
  C(Conventional 常规型)— 组织 / 数据 / 流程

60 题(每维 10 题),3 选 1:
  - 喜欢 (+2 分)
  - 中立 (+1 分)
  - 不喜欢 (0 分)

Holland Code:取 Top 3 维度的字母组合(例 "IAS")

数字人解读:
  - career_guide(职业规划师 🧭)— 引导式对话
  - 输出:6 维分数 + Holland Code + 推荐岗位 + 学习路径

沙箱安全:
  - 静态题库 + 规则评分
  - 不依赖 LLM API
  - 可选 LLM 解读(接 LLMClient)

Cycle 13 — 第三个职业辅导模块
"""
from __future__ import annotations
import json
import re
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


# ============== 维度定义 ==============

RIASEC_DIMENSIONS = {
    "R": {
        "name": "实际型",
        "name_en": "Realistic",
        "emoji": "🔧",
        "keywords": "动手 / 操作 / 工具 / 机械 / 户外",
        "careers": ["工程师", "技术员", "机械师", "建筑工人", "农林牧渔", "实验员"],
    },
    "I": {
        "name": "研究型",
        "name_en": "Investigative",
        "emoji": "🔬",
        "keywords": "研究 / 分析 / 思考 / 探索 / 数据",
        "careers": ["科学家", "算法工程师", "研究员", "数据分析师", "医生", "心理学者"],
    },
    "A": {
        "name": "艺术型",
        "name_en": "Artistic",
        "emoji": "🎨",
        "keywords": "创造 / 表达 / 艺术 / 设计 / 想象",
        "careers": ["设计师", "艺术家", "作家", "音乐家", "导演", "建筑师"],
    },
    "S": {
        "name": "社会型",
        "name_en": "Social",
        "emoji": "🤝",
        "keywords": "助人 / 教育 / 服务 / 社交 / 关怀",
        "careers": ["教师", "咨询师", "HR", "医生", "社工", "教练"],
    },
    "E": {
        "name": "企业型",
        "name_en": "Enterprising",
        "emoji": "📈",
        "keywords": "领导 / 影响 / 说服 / 管理 / 竞争",
        "careers": ["销售", "创业者", "管理者", "律师", "营销", "高管"],
    },
    "C": {
        "name": "常规型",
        "name_en": "Conventional",
        "emoji": "📋",
        "keywords": "组织 / 数据 / 流程 / 规范 / 细节",
        "careers": ["会计", "行政", "运营", "审计", "编辑", "客服"],
    },
}

# 答案选项分值
ANSWER_SCORES = {
    "like": 2,      # 喜欢
    "neutral": 1,   # 中立
    "dislike": 0,   # 不喜欢
}

ANSWER_LABELS = {
    "like": "👍 喜欢",
    "neutral": "😐 中立",
    "dislike": "👎 不喜欢",
}


# ============== 60 题题库(每维 10 题) ==============

QUESTION_BANK: List[Dict[str, str]] = [
    # ========== R(实际型)10 题 ==========
    {"id": "R01", "dim": "R", "text": "我喜欢动手操作机器或工具,比如组装硬件、维修设备。"},
    {"id": "R02", "dim": "R", "text": "比起在办公室,我更愿意在户外或现场工作。"},
    {"id": "R03", "dim": "R", "text": "我喜欢木工、电工、机械类 DIY 项目。"},
    {"id": "R04", "dim": "R", "text": "面对具体可见的成果(比如实物),我会比抽象的工作更有成就感。"},
    {"id": "R05", "dim": "R", "text": "我喜欢操作类的运动(如攀岩、滑雪、徒步)而不是纯脑力活动。"},
    {"id": "R06", "dim": "R", "text": "比起写报告,我更喜欢把东西做出来。"},
    {"id": "R07", "dim": "R", "text": "我对汽车、机械设备的工作原理感兴趣。"},
    {"id": "R08", "dim": "R", "text": "我喜欢按照明确的步骤和流程完成任务。"},
    {"id": "R09", "dim": "R", "text": "我愿意做农业、园艺、动物保护等贴近自然的工作。"},
    {"id": "R10", "dim": "R", "text": "比起开会讨论,我更喜欢直接动手解决。"},

    # ========== I(研究型)10 题 ==========
    {"id": "I01", "dim": "I", "text": "我喜欢研究一个问题直到找到根本原因。"},
    {"id": "I02", "dim": "I", "text": "我对数据分析和数学建模有强烈兴趣。"},
    {"id": "I03", "dim": "I", "text": "我喜欢阅读学术论文或技术博客。"},
    {"id": "I04", "dim": "I", "text": "我享受解出一道难题/谜题的成就感。"},
    {"id": "I05", "dim": "I", "text": "比起重复工作,我更喜欢探索新领域。"},
    {"id": "I06", "dim": "I", "text": "我喜欢做实验、验证假设、推演逻辑。"},
    {"id": "I07", "dim": "I", "text": "我对未知事物充满好奇心,愿意花时间钻研。"},
    {"id": "I08", "dim": "I", "text": "我享受一个人静下来思考问题的时间。"},
    {"id": "I09", "dim": "I", "text": "我倾向于用逻辑和证据而不是直觉做决定。"},
    {"id": "I10", "dim": "I", "text": "我对科学发现、新技术前沿感兴趣。"},

    # ========== A(艺术型)10 题 ==========
    {"id": "A01", "dim": "A", "text": "我喜欢用文字、绘画、音乐等方式表达自己。"},
    {"id": "A02", "dim": "A", "text": "我对美学、设计、艺术有强烈感受力。"},
    {"id": "A03", "dim": "A", "text": "比起按部就班,我更喜欢自由发挥的创作过程。"},
    {"id": "A04", "dim": "A", "text": "我会花大量时间在艺术爱好上(绘画/写作/摄影/音乐)。"},
    {"id": "A05", "dim": "A", "text": "我喜欢想象和构思新的东西,即使最终不一定能实现。"},
    {"id": "A06", "dim": "A", "text": "我喜欢打破常规、尝试非传统的解决方案。"},
    {"id": "A07", "dim": "A", "text": "我会被独特、有创意的事物吸引。"},
    {"id": "A08", "dim": "A", "text": "我喜欢没有标准答案的开放性问题。"},
    {"id": "A09", "dim": "A", "text": "我会关注产品的视觉设计、配色、字体等细节。"},
    {"id": "A10", "dim": "A", "text": "比起流程化的工作,我更喜欢有想象空间的任务。"},

    # ========== S(社会型)10 题 ==========
    {"id": "S01", "dim": "S", "text": "我喜欢帮助别人解决困难或痛苦。"},
    {"id": "S02", "dim": "S", "text": "我喜欢和人打交道,而不是整天对着电脑。"},
    {"id": "S03", "dim": "S", "text": "我愿意做老师、培训师、咨询师等助人职业。"},
    {"id": "S04", "dim": "S", "text": "团队合作比单打独斗更让我有成就感。"},
    {"id": "S05", "dim": "S", "text": "我擅长倾听他人并给出有同理心的反馈。"},
    {"id": "S06", "dim": "S", "text": "我关注社会问题,愿意参与志愿活动。"},
    {"id": "S07", "dim": "S", "text": "我喜欢和不同背景的人交流,从中学习。"},
    {"id": "S08", "dim": "S", "text": "我愿意花时间陪伴需要帮助的人。"},
    {"id": "S09", "dim": "S", "text": "比起追求个人成就,我更看重给他人带来的价值。"},
    {"id": "S10", "dim": "S", "text": "我喜欢组织活动让大家参与进来。"},

    # ========== E(企业型)10 题 ==========
    {"id": "E01", "dim": "E", "text": "我喜欢影响和说服别人接受我的想法。"},
    {"id": "E02", "dim": "E", "text": "我愿意承担领导责任,带领团队达成目标。"},
    {"id": "E03", "dim": "E", "text": "我对商业、创业、管理有强烈兴趣。"},
    {"id": "E04", "dim": "E", "text": "我追求成绩、地位和影响力。"},
    {"id": "E05", "dim": "E", "text": "我擅长在竞争中脱颖而出。"},
    {"id": "E06", "dim": "E", "text": "我愿意承担风险去追求更大的回报。"},
    {"id": "E07", "dim": "E", "text": "我喜欢制定策略,而不是执行细节。"},
    {"id": "E08", "dim": "E", "text": "我愿意做销售、谈判、推广类工作。"},
    {"id": "E09", "dim": "E", "text": "我倾向于主导讨论而不是被动跟随。"},
    {"id": "E10", "dim": "E", "text": "我愿意为了目标牺牲短期舒适。"},

    # ========== C(常规型)10 题 ==========
    {"id": "C01", "dim": "C", "text": "我喜欢处理数据和文档,有条理地整理信息。"},
    {"id": "C02", "dim": "C", "text": "我擅长遵守规则和流程,不喜欢模糊地带。"},
    {"id": "C03", "dim": "C", "text": "我倾向于把任务做成清单按计划执行。"},
    {"id": "C04", "dim": "C", "text": "我喜欢财务、统计、审计等精确性高的工作。"},
    {"id": "C05", "dim": "C", "text": "我会主动维护秩序和规范化。"},
    {"id": "C06", "dim": "C", "text": "我擅长在表格/数据库中查找和管理信息。"},
    {"id": "C07", "dim": "C", "text": "我喜欢可预测、有规律的工作环境。"},
    {"id": "C08", "dim": "C", "text": "我对细节敏感,容易发现别人忽略的错误。"},
    {"id": "C09", "dim": "C", "text": "我倾向于用系统/工具来提高效率。"},
    {"id": "C10", "dim": "C", "text": "我愿意做行政、运营、客服等流程化工作。"},
]


# ============== Holland Code 映射(精选 24 种) ==============

HOLLAND_CODE_MAP: Dict[str, Dict[str, str]] = {
    "RIA": {"careers": "工程师 / 建筑师 / 数据科学家", "advice": "实操+研究+艺术,适合做需要动手又需要创新的技术岗位。"},
    "RIS": {"careers": "医生 / 牙医 / 兽医 / 心理治疗师", "advice": "实操+研究+社会,助人型专业岗位很适合你。"},
    "RIE": {"careers": "项目经理 / 工程主管 / 技术经理", "advice": "技术 + 管理的结合,适合做技术领导。"},
    "RIC": {"careers": "实验室技术员 / 质量工程师", "advice": "实操+研究+常规,适合做规范化技术工作。"},
    "IAS": {"careers": "心理咨询师 / 作家 / UX 研究员", "advice": "研究+艺术+社会,适合做需要洞察人心的研究/创作岗位。"},
    "IAR": {"careers": "建筑师 / 产品设计师 / 算法工程师", "advice": "研究+艺术+实操,适合做有创造性的技术工作。"},
    "IES": {"careers": "管理咨询 / 律师 / 高管", "advice": "研究+企业+社会,适合做需要战略思考的高影响力岗位。"},
    "ISA": {"careers": "教育研究者 / 心理治疗师 / 课程设计", "advice": "研究+社会+艺术,适合做教育/心理类工作。"},
    "AIC": {"careers": "平面设计 / 文案策划 / 品牌策划", "advice": "艺术+研究+常规,适合做有创意但需规范的岗位。"},
    "ASE": {"careers": "演员 / 公关 / 市场总监", "advice": "艺术+社会+企业,适合做需要表达和影响力的工作。"},
    "SEC": {"careers": "HR / 销售主管 / 培训师", "advice": "社会+企业+常规,适合做需要协调和管理的岗位。"},
    "ESC": {"careers": "客户经理 / 运营管理 / 项目经理", "advice": "企业+社会+常规,适合做客户/运营管理类工作。"},
    "CES": {"careers": "财务 / 审计 / 行政主管", "advice": "常规+企业+社会,适合做规范化管理类工作。"},
    "ECI": {"careers": "投资分析师 / 战略顾问", "advice": "企业+常规+研究,适合做需要分析的金融/咨询岗位。"},
    "SIA": {"careers": "教师 / 课程设计 / 编辑", "advice": "社会+研究+艺术,适合做教育/内容类工作。"},
    "SAE": {"careers": "营销 / 公关 / 品牌经理", "advice": "社会+艺术+企业,适合做需要影响力和创意的市场工作。"},
    "CRI": {"careers": "数据库管理 / IT 运维", "advice": "常规+实操+研究,适合做 IT 基础设施类工作。"},
    "CRE": {"careers": "物流管理 / 采购主管", "advice": "常规+实操+企业,适合做供应链/运营管理工作。"},
    "CSE": {"careers": "行政助理 / 客服主管", "advice": "常规+社会+企业,适合做服务管理类工作。"},
    "ACS": {"careers": "插画师 / 编辑 / 校对", "advice": "艺术+常规+社会,适合做有创意的规范化工作。"},
    "AIS": {"careers": "艺术教育 / 策展人", "advice": "艺术+研究+社会,适合做艺术教育/文化传播。"},
    "EAS": {"careers": "销售总监 / 创业者 / 营销高管", "advice": "企业+艺术+社会,适合做高创造力的领导工作。"},
    "ERS": {"careers": "运营总监 / 业务负责人", "advice": "企业+实操+社会,适合做业务运营类管理。"},
    "ISR": {"careers": "学术研究 / 实验室研究员", "advice": "研究+社会+实操,适合做学术研究/技术研发。"},
    "IRA": {"careers": "数据科学家 / 实验室研究员 / 算法工程师", "advice": "研究+实操+艺术,适合做需要创新和动手的技术研究岗位。"},
}


# ============== 数据模型 ==============

@dataclass
class CareerTestSession:
    """一场霍兰德测试"""
    questions: List[Dict[str, str]] = field(default_factory=list)
    answers: Dict[str, str] = field(default_factory=dict)  # qid -> like/neutral/dislike
    round_idx: int = 0
    completed: bool = False
    started_at: float = field(default_factory=time.time)
    ended_at: float = 0.0
    target_position: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CareerProfile:
    """职业画像结果"""
    scores: Dict[str, int]         # R/I/A/S/E/C -> 0-20
    top3: List[Tuple[str, int]]    # [(dim, score), ...]
    holland_code: str              # 3 字母
    interpretation: str            # 解读
    careers: List[str]             # 推荐岗位
    advice: str                    # 建议
    target_position_match: float = 0.0  # 与目标岗位的匹配度(0-1)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scores": self.scores,
            "top3": self.top3,
            "holland_code": self.holland_code,
            "interpretation": self.interpretation,
            "careers": self.careers,
            "advice": self.advice,
            "target_position_match": self.target_position_match,
        }


# ============== 职业规划师 Prompt ==============

CAREER_GUIDE_PROMPTS = {
    "career_guide": {
        "name": "职业规划师",
        "emoji": "🧭",
        "system_prompt": (
            "你是一位资深职业规划师,精通霍兰德职业兴趣理论(RIASEC)。"
            "你会基于学生的 6 维分数和 Holland Code:"
            "1) 解读代码含义(3 字母代表什么组合)"
            "2) 推荐具体校招岗位(细到 BAT/TMD 等公司级别)"
            "3) 给出学习路径建议(该看哪些书/做哪些项目)"
            "4) 对比学生目标岗位(如有),给一致性建议"
        ),
    },
}


# ============== 核心 API ==============

def list_dimensions() -> List[Dict[str, str]]:
    """列出 6 维度"""
    return [
        {"id": k, **v} for k, v in RIASEC_DIMENSIONS.items()
    ]


def get_dimension(dim: str) -> Dict[str, str]:
    """获取单个维度"""
    return {"id": dim, **RIASEC_DIMENSIONS.get(dim, RIASEC_DIMENSIONS["I"])}


def start_career_test(
    target_position: str = "",
    question_count: int = 60,
) -> CareerTestSession:
    """开启一场霍兰德测试

    question_count: 题目数(默认 60 = 完整版,可调 30 = 简版)
    """
    # 按维度均匀抽样
    if question_count >= 60:
        questions = QUESTION_BANK[:]
    else:
        # 简化版:每维取 question_count/6 题
        per_dim = max(1, question_count // 6)
        questions = []
        for dim in ["R", "I", "A", "S", "E", "C"]:
            dim_questions = [q for q in QUESTION_BANK if q["dim"] == dim]
            questions.extend(dim_questions[:per_dim])
    return CareerTestSession(
        questions=questions,
        target_position=target_position,
    )


def submit_answer(
    session: CareerTestSession,
    qid: str,
    answer: str,
) -> Dict[str, Any]:
    """提交一个答案。

    answer: like / neutral / dislike
    返回:当前进度 + 下一题(若有)
    """
    if session.completed:
        raise ValueError("Test already completed")
    if answer not in ANSWER_SCORES:
        raise ValueError(f"Invalid answer: {answer}, must be one of {list(ANSWER_SCORES.keys())}")
    # 检查 qid 是否有效
    if not any(q["id"] == qid for q in session.questions):
        raise ValueError(f"Unknown question id: {qid}")
    session.answers[qid] = answer
    session.round_idx += 1
    if session.round_idx >= len(session.questions):
        session.completed = True
        session.ended_at = time.time()
    # 下一题
    next_q = None
    if not session.completed and session.round_idx < len(session.questions):
        next_q = session.questions[session.round_idx]
    return {
        "qid": qid,
        "answer": answer,
        "round_idx": session.round_idx,
        "completed": session.completed,
        "next_question": next_q,
    }


def compute_scores(session: CareerTestSession) -> Dict[str, int]:
    """计算 6 维分数(0-20)"""
    scores = {dim: 0 for dim in RIASEC_DIMENSIONS}
    for q in session.questions:
        ans = session.answers.get(q["id"])
        if ans is None:
            continue
        scores[q["dim"]] += ANSWER_SCORES[ans]
    return scores


def compute_profile(session: CareerTestSession) -> CareerProfile:
    """生成完整职业画像"""
    scores = compute_scores(session)
    # 排序,取 Top 3
    sorted_dims = sorted(scores.items(), key=lambda x: -x[1])
    top3 = sorted_dims[:3]
    # Holland Code(分数为 0 的维度不参与)
    nonzero = [(d, s) for d, s in sorted_dims if s > 0]
    if len(nonzero) >= 3:
        code = "".join(d for d, s in nonzero[:3])
    elif len(nonzero) >= 1:
        code = "".join(d for d, s in nonzero)
        code = code.ljust(3, "I")  # 不足 3 位用 I 补
    else:
        code = "III"  # 全 0,默认研究型
    # 查表
    info = HOLLAND_CODE_MAP.get(code, {
        "careers": "通用研究 / 探索类岗位",
        "advice": f"你的 Holland Code 是 {code},系统暂未收录精确映射,建议结合目标岗位和兴趣进一步探索。",
    })
    # 解读
    top_dim_names = [RIASEC_DIMENSIONS[d]["name"] for d, _ in top3]
    interpretation = (
        f"你的 Holland Code 是 {code},核心特质:{' / '.join(top_dim_names)}。\n"
        f"最高分维度:{RIASEC_DIMENSIONS[top3[0][0]]['name']}({top3[0][1]}/20),"
        f"次高分:{RIASEC_DIMENSIONS[top3[1][0]]['name']}({top3[1][1]}/20)。"
    )
    # 推荐岗位
    careers = [c.strip() for c in info["careers"].split("/")]
    # 目标岗位匹配度
    match_score = _position_match(scores, session.target_position)
    return CareerProfile(
        scores=scores,
        top3=top3,
        holland_code=code,
        interpretation=interpretation,
        careers=careers,
        advice=info["advice"],
        target_position_match=match_score,
    )


def _position_match(scores: Dict[str, int], target_position: str) -> float:
    """与目标岗位的匹配度(0-1)
    简化版:基于岗位推断 Holland 倾向,看用户分数是否对齐
    """
    if not target_position:
        return 0.0
    # 岗位 → RIASEC 期望(简化)
    position_holland = {
        "算法工程师": {"I": 15, "R": 10},
        "产品经理": {"E": 12, "S": 12, "I": 10},
        "运营": {"E": 12, "S": 10, "C": 10},
        "后端工程师": {"I": 15, "R": 10, "C": 10},
        "前端工程师": {"A": 10, "I": 12, "R": 10},
        "数据分析师": {"I": 18, "C": 12},
        "测试工程师": {"C": 15, "I": 12, "R": 10},
        "UI 设计师": {"A": 18, "I": 10, "S": 8},
        "咨询": {"I": 12, "E": 15, "S": 12},
        "金融": {"C": 15, "E": 12, "I": 12},
        "教师": {"S": 18, "I": 10, "A": 8},
        "销售": {"E": 18, "S": 10},
    }
    expected = position_holland.get(target_position)
    if not expected:
        return 0.5  # 未知岗位,中庸
    # 计算用户分数 vs 期望的余弦相似度(简化)
    total_match = 0
    for dim, exp_score in expected.items():
        user_score = scores.get(dim, 0)
        # 用户分数 >= 期望一半算命中
        if user_score >= exp_score * 0.6:
            total_match += 1
    return round(total_match / len(expected), 4)


def get_career_guide() -> Dict[str, str]:
    """获取职业规划师角色"""
    return {"id": "career_guide", **CAREER_GUIDE_PROMPTS["career_guide"]}


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 career_profile.py {dimensions|start|status|profile|list_codes}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "dimensions":
        print(json.dumps(list_dimensions(), ensure_ascii=False, indent=2))
    elif cmd == "list_codes":
        for code, info in HOLLAND_CODE_MAP.items():
            print(f"  {code}: {info['careers']}")
    elif cmd == "start":
        target = sys.argv[2] if len(sys.argv) > 2 else ""
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 60
        s = start_career_test(target_position=target, question_count=count)
        first = s.questions[0] if s.questions else None
        print(json.dumps({
            "total_questions": len(s.questions),
            "first_question": first,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
