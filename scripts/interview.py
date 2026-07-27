#!/usr/bin/env python3
"""
aichat-Hub Interview (模拟面试官) 模块
=====================================
大学生 AI 模拟面试 — 多角色 / 多轮对话 / 5 维评分 / 完整复盘。

4 角色面试官:
  - tech(技术面) ⚙️ — 算法 / 系统设计 / 编程,关注深度 + 边界
  - behavioral(行为面) 🧠 — STAR 法则,关注结构 + 量化
  - hr(HR 面) 💬 — 自我介绍 / 职业规划 / 文化匹配,关注表达 + 真诚
  - pressure(压力面) 🔥 — 故意打断 / 否定 / 追问,关注抗压 + 应变

5 维评分:
  1. logic(逻辑性)— 回答结构是否清晰
  2. expression(表达)— 语言流畅度(长度 + 句式)
  3. depth(技术深度)— 关键要点覆盖率
  4. adaptability(应变)— 是否正面回答追问
  5. fit(匹配度)— 与目标岗位关键词相关

核心能力:
  - 多轮对话(2-5 轮可配,默认 3 轮)
  - 追问/澄清(基于规则的 follow_up)
  - 具体反馈(每轮亮点 + 不足 + 改写建议)
  - 完整复盘(总分 + 各维曲线 + Top3 改进点)

沙箱安全:
  - 题库 + 评分用规则化(不依赖 LLM)
  - 4 角色 × 10+ 题 = 40+ 题目静态库
  - 评分用关键词匹配 + 长度 + 结构检测

Cycle 12 — 第二个职业辅导模块
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
class Question:
    """一道面试题"""
    role: str             # tech / behavioral / hr / pressure
    text: str             # 题面
    key_points: List[str] # 关键要点(评分依据)
    difficulty: int = 3   # 1-5
    follow_up: str = ""   # 追问(可选)


@dataclass
class AnswerResult:
    """一道题的回答结果"""
    question: str          # 题面
    answer: str           # 回答
    key_points_hit: List[str] = field(default_factory=list)  # 命中要点
    key_points_missed: List[str] = field(default_factory=list)
    score: float = 0.0    # 0-1
    feedback: str = ""    # 文本反馈
    logic: float = 0.0
    expression: float = 0.0
    depth: float = 0.0
    adaptability: float = 0.0
    fit: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class InterviewSession:
    """一场模拟面试"""
    interviewer: str                  # tech / behavioral / hr / pressure
    target_position: str = "算法工程师"
    questions: List[Question] = field(default_factory=list)
    answers: List[str] = field(default_factory=list)
    results: List[AnswerResult] = field(default_factory=list)
    round_idx: int = 0
    completed: bool = False
    started_at: float = field(default_factory=time.time)
    ended_at: float = 0.0

    def add_answer(self, answer: str, result: AnswerResult):
        """记录一次回答"""
        self.answers.append(answer)
        self.results.append(result)
        self.round_idx += 1
        if self.round_idx >= len(self.questions):
            self.completed = True
            self.ended_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interviewer": self.interviewer,
            "target_position": self.target_position,
            "questions": [asdict(q) for q in self.questions],
            "answers": self.answers,
            "results": [r.to_dict() for r in self.results],
            "round_idx": self.round_idx,
            "completed": self.completed,
            "total_score": self.total_score(),
        }

    def total_score(self) -> float:
        """总分(平均)"""
        if not self.results:
            return 0.0
        return round(sum(r.score for r in self.results) / len(self.results), 4)

    def dimension_averages(self) -> Dict[str, float]:
        """各维度平均分"""
        if not self.results:
            return {"logic": 0.0, "expression": 0.0, "depth": 0.0, "adaptability": 0.0, "fit": 0.0}
        return {
            "logic": round(sum(r.logic for r in self.results) / len(self.results), 4),
            "expression": round(sum(r.expression for r in self.results) / len(self.results), 4),
            "depth": round(sum(r.depth for r in self.results) / len(self.results), 4),
            "adaptability": round(sum(r.adaptability for r in self.results) / len(self.results), 4),
            "fit": round(sum(r.fit for r in self.results) / len(self.results), 4),
        }

    def top_improvements(self, top_n: int = 3) -> List[str]:
        """Top N 改进建议"""
        # 收集所有 feedback
        all_feedback: List[str] = []
        for r in self.results:
            if r.feedback:
                all_feedback.append(r.feedback)
        # 取后 N 条(最近的反馈)
        return all_feedback[-top_n:]


# ============== 角色配置 ==============

INTERVIEWER_PROFILES = {
    "tech": {
        "name": "技术面试官",
        "emoji": "⚙️",
        "description": "算法 / 系统设计 / 编程题,关注深度 + 边界 + 复杂度分析",
        "style": "理性、严谨、追问细节,会打断你说'这块我没听清,具体说说'",
    },
    "behavioral": {
        "name": "行为面试官",
        "emoji": "🧠",
        "description": "STAR 法则 / 项目复盘 / 团队协作,关注结构 + 量化 + 反思",
        "style": "温和但要求具体,会用 STAR 追问'那结果呢?有没有数据?'",
    },
    "hr": {
        "name": "HR 面试官",
        "emoji": "💬",
        "description": "自我介绍 / 职业规划 / 文化匹配,关注表达 + 真诚 + 稳定性",
        "style": "亲切但洞察力强,会观察你的表达细节和情绪",
    },
    "pressure": {
        "name": "压力面试官",
        "emoji": "🔥",
        "description": "故意打断 / 否定 / 追问极端情况,关注抗压 + 应变 + 自我调节",
        "style": "质疑、否定、追问,'这不太可能吧?'、'你确定?'",
    },
}


# ============== 题库(4 角色 × 多题) ==============

QUESTION_BANK: Dict[str, List[Question]] = {
    "tech": [
        Question(
            role="tech",
            text="请实现一个函数,判断一个字符串是否是回文。",
            key_points=["双指针", "O(n) 时间", "O(1) 空间", "边界处理(空串/单字符)"],
            difficulty=2,
            follow_up="如果输入是 Unicode 字符,你的方案还成立吗?",
        ),
        Question(
            role="tech",
            text="如何设计一个高并发的短链系统?从用户点击短链到跳转到长链的完整链路。",
            key_points=["短链生成(哈希/自增 ID)", "存储选型(Redis/DB)", "缓存策略", "限流", "301/302 跳转"],
            difficulty=5,
            follow_up="如果 QPS 是 10 万,你的方案瓶颈在哪?怎么优化?",
        ),
        Question(
            role="tech",
            text="LRU 缓存怎么实现?如果要支持 TTL 过期,如何改造?",
            key_points=["哈希表 + 双向链表", "O(1) get/put", "TTL 用额外堆/懒删除", "并发安全"],
            difficulty=4,
            follow_up="如果是分布式 LRU,方案有什么不同?",
        ),
        Question(
            role="tech",
            text="给定一个有序数组,找 target 的第一个和最后一个位置。",
            key_points=["二分查找", "两次二分找左右边界", "O(log n) 时间", "边界处理"],
            difficulty=3,
        ),
        Question(
            role="tech",
            text="解释下 TCP 三次握手和四次挥手,为什么不是两次?",
            key_points=["三次握手:SYN/SYN-ACK/ACK", "防止已失效请求", "四次挥手:FIN/ACK", "TIME_WAIT 状态"],
            difficulty=3,
        ),
        Question(
            role="tech",
            text="进程和线程的区别?协程呢?什么场景用协程?",
            key_points=["进程:独立地址空间", "线程:共享堆", "协程:用户态调度", "I/O 密集型适合协程"],
            difficulty=3,
        ),
        Question(
            role="tech",
            text="你熟悉的设计模式有哪些?举一个你在项目里用过的例子。",
            key_points=["具体模式名(策略/工厂/观察者/单例)", "实际项目场景", "解决了什么问题", "权衡/取舍"],
            difficulty=2,
        ),
        Question(
            role="tech",
            text="如何检测链表是否有环?进阶:找出环的入口?",
            key_points=["快慢指针", "Floyd 算法", "哈希表法(空间 O(n))", "数学证明"],
            difficulty=3,
        ),
        Question(
            role="tech",
            text="数据库索引为什么用 B+ 树而不是红黑树?",
            key_points=["磁盘 I/O 友好", "范围查询", "叶子节点链表", "高度平衡"],
            difficulty=4,
        ),
        Question(
            role="tech",
            text="如果让你重新设计 Git,你会改什么?",
            key_points=["明确说现状不足", "具体改进点", "权衡(兼容性/性能/学习曲线)", "不熟悉的不要硬编"],
            difficulty=5,
        ),
    ],
    "behavioral": [
        Question(
            role="behavioral",
            text="讲一个你最有成就感的项目,用了 STAR 法则描述。",
            key_points=["S 情境(背景/约束)", "T 任务(目标)", "A 行动(具体动作)", "R 结果(量化数据)"],
            difficulty=3,
        ),
        Question(
            role="behavioral",
            text="讲一次你和队友意见冲突的经历,你最后怎么处理的?",
            key_points=["具体冲突场景", "自己的立场 + 理由", "如何沟通", "最终结果 + 反思"],
            difficulty=3,
        ),
        Question(
            role="behavioral",
            text="你做过的最失败的一个决定是什么?为什么?",
            key_points=["诚实面对", "具体场景", "当时的判断逻辑", "事后反思 + 学到什么"],
            difficulty=4,
        ),
        Question(
            role="behavioral",
            text="你同时要应付 3 个 deadline 的时候,怎么排优先级?",
            key_points=["具体方法(优先级矩阵/MoSCoW)", "取舍逻辑", "沟通协调", "最终交付结果"],
            difficulty=3,
        ),
        Question(
            role="behavioral",
            text="讲一次你主动学习一个新技能/新领域的经历。",
            key_points=["学习目标", "方法(课程/项目/请教他人)", "遇到的困难", "成果"],
            difficulty=2,
        ),
        Question(
            role="behavioral",
            text="你被批评/否定过最狠的一次是什么?感受如何?后来呢?",
            key_points=["具体场景", "当时的情绪(真实)", "理性反思", "如何改进"],
            difficulty=4,
        ),
        Question(
            role="behavioral",
            text="讲一次你主动推动而非被动接受任务的事。",
            key_points=["主动性来源", "具体动作", "阻力 + 如何克服", "结果"],
            difficulty=3,
        ),
        Question(
            role="behavioral",
            text="你在团队里一般扮演什么角色?为什么?",
            key_points=["具体角色(leader/coach/executor)", "举例支撑", "反思自己的不足", "互补心态"],
            difficulty=2,
        ),
    ],
    "hr": [
        Question(
            role="hr",
            text="请做一个 1 分钟的自我介绍。",
            key_points=["学校 + 专业 + 年级", "1-2 个亮点(项目/实习)", "目标岗位 + 动机", "不超时"],
            difficulty=1,
        ),
        Question(
            role="hr",
            text="你为什么选择我们公司?为什么是这个岗位?",
            key_points=["对公司业务有了解", "岗位匹配度", "个人发展", "真诚不过度吹"],
            difficulty=2,
        ),
        Question(
            role="hr",
            text="你 5 年后的职业规划是什么?",
            key_points=["短期(1-2 年)", "中期(3-5 年)", "和公司发展结合", "不要过于天马行空"],
            difficulty=2,
        ),
        Question(
            role="hr",
            text="你有什么缺点?",
            key_points=["真实但可控的缺点", "自我认知", "改进措施", "不要套话(完美主义)"],
            difficulty=3,
        ),
        Question(
            role="hr",
            text="你目前的 offer 情况?为什么我们应该是你的第一选择?",
            key_points=["诚实", "不要撒谎(诚信红线)", "对比维度(业务/成长/文化)", "真诚表态"],
            difficulty=4,
        ),
        Question(
            role="hr",
            text="如果入职后发现自己不合适,你会怎么办?",
            key_points=["不轻易说跳槽", "先内部沟通", "主动学习", "止损判断"],
            difficulty=3,
        ),
        Question(
            role="hr",
            text="你的期望薪资是多少?怎么算出来的?",
            key_points=["市场行情(校招区间)", "个人能力定位", "不卑不亢", "可商量的空间"],
            difficulty=3,
        ),
        Question(
            role="hr",
            text="你有什么想问我的?",
            key_points=["不问薪资(最后一轮)", "问团队/业务/培养", "不查户口", "真诚互动"],
            difficulty=2,
        ),
    ],
    "pressure": [
        Question(
            role="pressure",
            text="我看了你的简历,说实话没什么亮点,你自己觉得为什么我们要录用你?",
            key_points=["不被激怒", "自信但不傲慢", "具体举 1-2 个亮点", "不卑不亢"],
            difficulty=4,
            follow_up="就这些?这听起来很普通啊。",
        ),
        Question(
            role="pressure",
            text="你刚才说的方案有严重问题,重做。",
            key_points=["不慌不乱", "承认可能的不足", "理性反驳", "给出修改方案"],
            difficulty=5,
            follow_up="你怎么证明你的修改是对的?",
        ),
        Question(
            role="pressure",
            text="你之前那段实习只做了 3 个月?是不是被劝退了?",
            key_points=["不被激怒", "诚实说明原因", "强调收获", "不要攻击前公司"],
            difficulty=5,
        ),
        Question(
            role="pressure",
            text="你 GPA 不高,是不是能力有问题?",
            key_points=["不被激怒", "其他维度补充(项目/竞赛)", "解释原因(非能力)", "不要撒谎"],
            difficulty=4,
        ),
        Question(
            role="pressure",
            text="你前面那个候选人明显比你优秀,你怎么看?",
            key_points=["不被激怒", "承认差距", "突出自己独特价值", "不贬低他人"],
            difficulty=4,
        ),
        Question(
            role="pressure",
            text="这个需求明天就要,你做不完怎么办?",
            key_points=["不被情绪带跑", "拆解优先级", "沟通协调", "实在做不完的兜底"],
            difficulty=3,
        ),
    ],
}


# ============== 评分函数(5 维,纯规则) ==============

def _logic_score(answer: str) -> float:
    """逻辑性:结构性 + 过渡词"""
    if not answer or len(answer.strip()) < 10:
        return 0.0
    s = answer.strip()
    # 结构化信号
    struct_signals = sum([
        bool(re.search(r"首先|第一|第二|第三|然后|接下来|最后|总之|综上", s)),  # 顺序词
        bool(re.search(r"因为|所以|因此|但是|不过|然而", s)),  # 因果/转折
        bool(re.search(r"\n[-*]\s|\n\d+[\.、]", s)),  # 列表
        s.count("。") + s.count(".") >= 3,  # 多句
    ])
    return round(min(1.0, struct_signals / 3.0), 4)


def _expression_score(answer: str) -> float:
    """表达:长度 + 句式多样性"""
    if not answer:
        return 0.0
    n = len(answer)
    # 理想长度 50-500 字符
    if 50 <= n <= 500:
        len_score = 1.0
    elif n < 50:
        len_score = n / 50
    else:
        len_score = max(0.4, 1.0 - (n - 500) / 1000)
    # 句式多样性(unique 句数 / 总句数)
    sents = re.split(r"[。.!?！？\n]", answer)
    sents = [x.strip() for x in sents if x.strip()]
    if len(sents) >= 2:
        uniq_ratio = len(set(sents)) / len(sents)
    else:
        uniq_ratio = 0.5
    return round(0.6 * len_score + 0.4 * uniq_ratio, 4)


def _depth_score(answer: str, key_points: List[str]) -> float:
    """技术/内容深度:关键要点覆盖率"""
    if not key_points:
        return 0.5  # 无要点定义,默认 0.5
    answer_lower = answer.lower()
    hit = 0
    for kp in key_points:
        kp_words = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+", kp)
        # 关键点至少 1 个词命中即算 hit
        if any(w.lower() in answer_lower for w in kp_words if len(w) > 1):
            hit += 1
    return round(hit / len(key_points), 4)


def _adaptability_score(answer: str, follow_up: str = "") -> float:
    """应变:正面回答 + 简洁(短答 vs 长答)"""
    if not answer:
        return 0.0
    # 不正面回答的信号(短答 + 含否定词)
    n = len(answer)
    negative = bool(re.search(r"不知道|不清楚|不会|没想过|随便|无所谓", answer))
    if negative and n < 30:
        return 0.2
    if negative:
        return 0.4
    # 正面 + 有内容
    if n > 50:
        return 0.9
    return 0.7


def _fit_score(answer: str, position: str = "算法工程师") -> float:
    """岗位匹配度:目标岗位的关键词在回答中的覆盖率(简化版)"""
    # 复用 resume.py 的关键词字典
    try:
        from resume import POSITION_KEYWORDS
    except ImportError:
        return 0.5
    keywords = POSITION_KEYWORDS.get(position, [])
    if not keywords:
        return 0.5
    answer_lower = answer.lower()
    hit = sum(1 for kw in keywords if kw.lower() in answer_lower)
    return round(min(1.0, hit / 3.0), 4)  # 命中 3 个即满分(回答短,关键词少)


def _aggregate_score(logic: float, expression: float, depth: float,
                     adaptability: float, fit: float) -> float:
    """加权总分"""
    return round(
        0.20 * logic
        + 0.15 * expression
        + 0.30 * depth
        + 0.15 * adaptability
        + 0.20 * fit,
        4
    )


# ============== 核心 API ==============

def list_interviewers() -> List[Dict[str, str]]:
    """列出所有面试官"""
    return [
        {"id": k, **v}
        for k, v in INTERVIEWER_PROFILES.items()
    ]


def get_interviewer(interviewer: str) -> Dict[str, str]:
    """获取单个面试官"""
    return {"id": interviewer, **INTERVIEWER_PROFILES.get(interviewer, INTERVIEWER_PROFILES["hr"])}


def start_interview(
    interviewer: str = "tech",
    target_position: str = "算法工程师",
    rounds: int = 3,
) -> InterviewSession:
    """
    开始一场模拟面试。

    rounds: 2-5 之间(默认 3 轮)
    """
    if interviewer not in QUESTION_BANK:
        interviewer = "hr"  # fallback
    questions = QUESTION_BANK[interviewer][:max(2, min(5, rounds))]
    return InterviewSession(
        interviewer=interviewer,
        target_position=target_position,
        questions=questions,
    )


def submit_answer(
    session: InterviewSession,
    answer: str,
) -> AnswerResult:
    """
    提交一次回答,返回评分结果 + 反馈。
    """
    if session.completed:
        raise ValueError("Interview already completed")
    if session.round_idx >= len(session.questions):
        raise ValueError("No more questions")

    q = session.questions[session.round_idx]
    # 5 维评分
    logic = _logic_score(answer)
    expression = _expression_score(answer)
    depth = _depth_score(answer, q.key_points)
    adaptability = _adaptability_score(answer, q.follow_up)
    fit = _fit_score(answer, session.target_position)
    score = _aggregate_score(logic, expression, depth, adaptability, fit)

    # 命中要点 / 漏掉要点
    answer_lower = answer.lower()
    hit, miss = [], []
    for kp in q.key_points:
        kp_words = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+", kp)
        if any(w.lower() in answer_lower for w in kp_words if len(w) > 1):
            hit.append(kp)
        else:
            miss.append(kp)

    # 反馈
    feedback = _generate_feedback(
        role=session.interviewer,
        question=q,
        answer=answer,
        score=score,
        hit=hit, miss=miss,
    )

    result = AnswerResult(
        question=q.text,
        answer=answer,
        key_points_hit=hit,
        key_points_missed=miss,
        score=score,
        feedback=feedback,
        logic=logic, expression=expression, depth=depth,
        adaptability=adaptability, fit=fit,
    )
    session.add_answer(answer, result)
    return result


def _generate_feedback(
    role: str,
    question: Question,
    answer: str,
    score: float,
    hit: List[str],
    miss: List[str],
) -> str:
    """生成反馈文本"""
    parts = []
    # 总评
    if score >= 0.8:
        parts.append(f"👍 优秀回答({score:.0%})。")
    elif score >= 0.6:
        parts.append(f"✓ 中等回答({score:.0%}),有亮点也有不足。")
    else:
        parts.append(f"⚠️ 较弱回答({score:.0%}),建议优化。")
    # 亮点
    if hit:
        parts.append(f"命中要点:{', '.join(hit[:3])}")
    # 不足
    if miss:
        parts.append(f"可补充:{', '.join(miss[:3])}")
    # 角色化建议
    profile = INTERVIEWER_PROFILES.get(role, INTERVIEWER_PROFILES["hr"])
    if role == "tech":
        if not any(w in answer for w in ["O(", "复杂度", "时间", "空间"]):
            parts.append("建议:主动分析时间/空间复杂度")
    elif role == "behavioral":
        star_hits = sum(1 for w in ["情境", "任务", "行动", "结果", "在", "通过", "提升"] if w in answer)
        if star_hits < 3:
            parts.append("建议:用 STAR 法则(情境/任务/行动/结果)组织回答")
    elif role == "hr":
        if len(answer) < 50:
            parts.append("建议:展开讲,具体例子比抽象描述更有说服力")
    elif role == "pressure":
        negative = any(w in answer for w in ["不知道", "不会", "随便", "无所谓"])
        if negative:
            parts.append("建议:压力面要稳住,不卑不亢,正面回应")
    return " ".join(parts)


def end_interview(session: InterviewSession) -> Dict[str, Any]:
    """结束面试,返回完整复盘报告"""
    if not session.completed and session.round_idx > 0:
        session.completed = True
        session.ended_at = time.time()
    return {
        "interviewer": get_interviewer(session.interviewer),
        "target_position": session.target_position,
        "rounds": session.round_idx,
        "total_score": session.total_score(),
        "dimension_averages": session.dimension_averages(),
        "top_improvements": session.top_improvements(top_n=3),
        "all_results": [r.to_dict() for r in session.results],
        "duration_seconds": round(session.ended_at - session.started_at, 2) if session.ended_at else 0,
    }


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 interview.py {interviewers|start|run|list}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "interviewers":
        print(json.dumps(list_interviewers(), ensure_ascii=False, indent=2))
    elif cmd == "list":
        for i in list_interviewers():
            print(f"  {i['emoji']} {i['id']:12s} - {i['name']}")
    elif cmd == "start":
        role = sys.argv[2] if len(sys.argv) > 2 else "tech"
        rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        s = start_interview(role, rounds=rounds)
        print(json.dumps({
            "interviewer": get_interviewer(role),
            "rounds": len(s.questions),
            "first_question": s.questions[0].text,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
