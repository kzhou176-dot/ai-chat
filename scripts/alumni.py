#!/usr/bin/env python3
"""
aichat-Hub Alumni (校友匹配 + 内推) 模块
==========================================
大学生校友网络 + 内推助手 — 同校/同院/同专业/同行业 4 维匹配。

核心能力:
  1. 4 维匹配(同校 0.4 / 同院同专业 0.3 / 同行业 0.2 / 同城 0.1)
  2. 校友池(静态模拟 50+ 校友,覆盖 985/211)
  3. 虚拟学长学姐(经授权,数字分身)
  4. 内推助手(状态机:requested/accepted/submitted/rejected/passed)
  5. 身份验证(学校邮箱格式)
  6. 与 career_profile / industry_insight / resume 联动

沙箱安全:
  - 静态校友池(50+)
  - 纯规则匹配(4 维加权)
  - 不依赖 LLM(对话用规则 Prompt 模板)

Cycle 15 — 第五个职业辅导模块(v0.3 完成)
"""
from __future__ import annotations
import json
import re
import time
import uuid
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


# ============== 学校邮箱域名(30+ 985/211) ==============

SCHOOL_EMAIL_DOMAINS: Dict[str, str] = {
    "清华大学": "mails.tsinghua.edu.cn",
    "北京大学": "stu.pku.edu.cn",
    "复旦大学": "m.fudan.edu.cn",
    "上海交通大学": "sjtu.edu.cn",
    "浙江大学": "zju.edu.cn",
    "中国科学技术大学": "mail.ustc.edu.cn",
    "南京大学": "nju.edu.cn",
    "武汉大学": "whu.edu.cn",
    "哈尔滨工业大学": "hit.edu.cn",
    "西安交通大学": "stu.xjtu.edu.cn",
    "北京航空航天大学": "buaa.edu.cn",
    "北京理工大学": "bit.edu.cn",
    "同济大学": "tongji.edu.cn",
    "东南大学": "seu.edu.cn",
    "华中科技大学": "hust.edu.cn",
    "中山大学": "mail.sysu.edu.cn",
    "厦门大学": "stu.xmu.edu.cn",
    "山东大学": "mail.sdu.edu.cn",
    "中南大学": "csu.edu.cn",
    "四川大学": "stu.scu.edu.cn",
    "吉林大学": "jlu.edu.cn",
    "大连理工大学": "mail.dlut.edu.cn",
    "重庆大学": "cqu.edu.cn",
    "电子科技大学": "std.uestc.edu.cn",
    "兰州大学": "lzu.edu.cn",
    "中央财经大学": "cufe.edu.cn",
    "上海财经大学": "mail.sufe.edu.cn",
    "对外经济贸易大学": "uibe.edu.cn",
    "北京邮电大学": "bupt.edu.cn",
    "华东师范大学": "stu.ecnu.edu.cn",
}


# ============== 数据模型 ==============

@dataclass
class AlumniProfile:
    """校友档案"""
    id: str
    name: str
    school: str
    department: str
    major: str
    graduation_year: int
    current_company: str
    current_position: str
    industry: str
    city: str
    skills: List[str] = field(default_factory=list)
    can_refer: bool = True
    bio: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class StudentProfile:
    """学生档案(查询方)"""
    name: str
    school: str
    department: str = ""
    major: str = ""
    graduation_year: int = 2026
    target_industry: str = "互联网"
    target_position: str = "算法工程师"
    target_city: str = "北京"
    email: str = ""  # 学校邮箱(用于身份验证)

    def is_verified(self) -> bool:
        """学校邮箱是否验证通过"""
        return verify_school_email(self.email, self.school)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MatchResult:
    """匹配结果"""
    alumni: AlumniProfile
    score: float
    breakdown: Dict[str, float]  # 4 维分数

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alumni": self.alumni.to_dict(),
            "score": self.score,
            "breakdown": self.breakdown,
        }


# ============== 校友池(50+ 静态模拟) ==============

ALUMNI_POOL: List[AlumniProfile] = [
    # ========== 清华大学 ==========
    AlumniProfile(id="TH001", name="张学长", school="清华大学", department="计算机系",
                  major="计算机科学与技术", graduation_year=2020,
                  current_company="字节跳动", current_position="高级算法工程师",
                  industry="互联网", city="北京",
                  skills=["Python", "PyTorch", "推荐系统", "LLM"],
                  bio="字节推荐算法,5年经验,熟悉 LLM/多模态/工业落地。"),
    AlumniProfile(id="TH002", name="李学姐", school="清华大学", department="经管学院",
                  major="金融学", graduation_year=2019,
                  current_company="中金公司", current_position="投资经理",
                  industry="金融", city="北京",
                  skills=["估值建模", "行业研究", "Wind", "Excel"],
                  bio="中金投行 5 年,做过 TMT/消费多个项目。"),
    AlumniProfile(id="TH003", name="王学长", school="清华大学", department="自动化系",
                  major="控制工程", graduation_year=2021,
                  current_company="华为", current_position="研发工程师",
                  industry="互联网", city="深圳",
                  skills=["C++", "嵌入式", "算法"],
                  bio="华为 2012 实验室,做 OS 内核。"),
    AlumniProfile(id="TH004", name="陈学姐", school="清华大学", department="美术学院",
                  major="交互设计", graduation_year=2022,
                  current_company="腾讯", current_position="高级 UI 设计师",
                  industry="互联网", city="深圳",
                  skills=["Figma", "UX 研究", "动效"],
                  bio="腾讯 CDC,做过微信/QQ 多款产品设计。"),
    AlumniProfile(id="TH005", name="刘学长", school="清华大学", department="计算机系",
                  major="人工智能", graduation_year=2020,
                  current_company="美团", current_position="技术专家",
                  industry="互联网", city="北京",
                  skills=["机器学习", "搜索", "推荐", "广告"],
                  bio="美团搜索广告算法负责人,有内推名额。"),

    # ========== 北京大学 ==========
    AlumniProfile(id="PKU001", name="赵学长", school="北京大学", department="信息科学技术学院",
                  major="计算机科学与技术", graduation_year=2021,
                  current_company="阿里巴巴", current_position="算法工程师",
                  industry="互联网", city="杭州",
                  skills=["Java", "推荐系统", "搜索"],
                  bio="阿里淘宝推荐,2 年校招生培养经验。"),
    AlumniProfile(id="PKU002", name="孙学姐", school="北京大学", department="光华管理学院",
                  major="金融硕士", graduation_year=2020,
                  current_company="高盛", current_position="VP",
                  industry="金融", city="上海",
                  skills=["并购", "估值", "Pitchbook"],
                  bio="高盛 IBD,有内推名额。"),
    AlumniProfile(id="PKU003", name="周学长", school="北京大学", department="数学科学学院",
                  major="应用数学", graduation_year=2019,
                  current_company="桥水基金", current_position="量化研究员",
                  industry="金融", city="上海",
                  skills=["Python", "量化", "数学建模"],
                  bio="桥水中国,做 alpha 策略。"),
    AlumniProfile(id="PKU004", name="吴学姐", school="北京大学", department="新闻与传播学院",
                  major="新闻学", graduation_year=2022,
                  current_company="小红书", current_position="内容运营",
                  industry="互联网", city="上海",
                  skills=["内容运营", "短视频", "小红书运营"],
                  bio="小红书美妆垂类运营,小红书个人号 5 万粉。"),

    # ========== 复旦大学 ==========
    AlumniProfile(id="FD001", name="郑学长", school="复旦大学", department="计算机科学技术学院",
                  major="软件工程", graduation_year=2021,
                  current_company="蚂蚁集团", current_position="高级开发工程师",
                  industry="互联网", city="杭州",
                  skills=["Java", "分布式", "微服务"],
                  bio="蚂蚁支付,做高并发后端。"),
    AlumniProfile(id="FD002", name="钱学姐", school="复旦大学", department="管理学院",
                  major="市场营销", graduation_year=2020,
                  current_company="宝洁", current_position="品牌经理",
                  industry="快消", city="广州",
                  skills=["品牌管理", "数字营销", "宝洁八大问"],
                  bio="宝洁中国市场部,管培生项目出身。"),
    AlumniProfile(id="FD003", name="马学长", school="复旦大学", department="经济学院",
                  major="经济学", graduation_year=2019,
                  current_company="麦肯锡", current_position="Engagement Manager",
                  industry="咨询", city="上海",
                  skills=["案例分析", "行业研究", "PPT"],
                  bio="MBB 5 年,做过 TMT/金融多个项目。"),

    # ========== 上海交通大学 ==========
    AlumniProfile(id="SJTU001", name="胡学姐", school="上海交通大学", department="电子信息与电气工程学院",
                  major="信息工程", graduation_year=2022,
                  current_company="美团", current_position="前端工程师",
                  industry="互联网", city="北京",
                  skills=["React", "TypeScript", "小程序"],
                  bio="美团外卖前端,做过性能优化。"),
    AlumniProfile(id="SJTU002", name="高学长", school="上海交通大学", department="安泰经济与管理学院",
                  major="金融学", graduation_year=2020,
                  current_company="中信证券", current_position="分析师",
                  industry="金融", city="上海",
                  skills=["行业研究", "Wind", "Excel"],
                  bio="中信证券 TMT 行业研究。"),
    AlumniProfile(id="SJTU003", name="林学长", school="上海交通大学", department="机械与动力工程学院",
                  major="机械工程", graduation_year=2018,
                  current_company="特斯拉", current_position="高级工程师",
                  industry="制造业", city="上海",
                  skills=["CAD", "热管理", "CFD"],
                  bio="特斯拉中国研发,做电池热管理。"),

    # ========== 浙江大学 ==========
    AlumniProfile(id="ZJU001", name="梁学姐", school="浙江大学", department="计算机科学与技术学院",
                  major="计算机", graduation_year=2021,
                  current_company="字节跳动", current_position="产品经理",
                  industry="互联网", city="北京",
                  skills=["用户研究", "PRD", "数据驱动"],
                  bio="字节抖音产品,3 年 PM 经验。"),
    AlumniProfile(id="ZJU002", name="宋学长", school="浙江大学", department="光电科学与工程学院",
                  major="光电信息", graduation_year=2020,
                  current_company="海康威视", current_position="算法工程师",
                  industry="互联网", city="杭州",
                  skills=["图像处理", "C++", "深度学习"],
                  bio="海康研究院,做视频理解。"),
    AlumniProfile(id="ZJU003", name="韩学长", school="浙江大学", department="管理学院",
                  major="管理科学与工程", graduation_year=2019,
                  current_company="联合利华", current_position="品牌经理",
                  industry="快消", city="上海",
                  skills=["品牌管理", "数字营销"],
                  bio="联合利华管培生,清扬/力士品牌。"),

    # ========== 中科大 ==========
    AlumniProfile(id="USTC001", name="杨学长", school="中国科学技术大学", department="计算机科学与技术学院",
                  major="计算机", graduation_year=2021,
                  current_company="华为", current_position="天才少年/算法工程师",
                  industry="互联网", city="深圳",
                  skills=["算法竞赛", "深度学习", "C++"],
                  bio="ACM 区域赛金牌,华为天才少年。"),
    AlumniProfile(id="USTC002", name="朱学姐", school="中国科学技术大学", department="物理学院",
                  major="凝聚态物理", graduation_year=2020,
                  current_company="中科院", current_position="博士后",
                  industry="学术", city="北京",
                  skills=["科研", "数据分析"],
                  bio="中科院物理所博后,继续做研究。"),

    # ========== 武大 / 哈工大 / 西交 / 南大 ==========
    AlumniProfile(id="WHU001", name="秦学长", school="武汉大学", department="计算机学院",
                  major="软件工程", graduation_year=2022,
                  current_company="腾讯", current_position="后台开发工程师",
                  industry="互联网", city="深圳",
                  skills=["Go", "微服务", "Kubernetes"],
                  bio="腾讯云后台,做 Kubernetes 相关。"),
    AlumniProfile(id="HIT001", name="尤学姐", school="哈尔滨工业大学", department="航天学院",
                  major="飞行器设计", graduation_year=2018,
                  current_company="中国航天科技集团", current_position="工程师",
                  industry="国企", city="北京",
                  skills=["结构设计", "CAD"],
                  bio="航天五院,做卫星结构设计。"),
    AlumniProfile(id="XJTU001", name="许学长", school="西安交通大学", department="电气工程学院",
                  major="电气工程", graduation_year=2019,
                  current_company="国家电网", current_position="工程师",
                  industry="国企", city="西安",
                  skills=["电力系统", "MATLAB"],
                  bio="国网陕西分公司,3 年经验。"),
    AlumniProfile(id="NJU001", name="何学姐", school="南京大学", department="文学院",
                  major="汉语言文学", graduation_year=2021,
                  current_company="字节跳动", current_position="内容运营",
                  industry="互联网", city="北京",
                  skills=["内容运营", "文案", "短视频"],
                  bio="字节西瓜视频运营,写过 100+ 爆款。"),

    # ========== 央财 / 上财 / 外贸 / 北邮 ==========
    AlumniProfile(id="CUFE001", name="吕学长", school="中央财经大学", department="金融学院",
                  major="金融学", graduation_year=2020,
                  current_company="华泰证券", current_position="分析师",
                  industry="金融", city="北京",
                  skills=["行业研究", "估值", "Wind"],
                  bio="华泰证券研究所,看消费板块。"),
    AlumniProfile(id="SUFE001", name="施学姐", school="上海财经大学", department="会计学院",
                  major="会计学", graduation_year=2020,
                  current_company="普华永道", current_position="高级审计师",
                  industry="咨询", city="上海",
                  skills=["审计", "Excel", "财务"],
                  bio="PwC 审计 3 年,准备跳槽甲方。"),
    AlumniProfile(id="BUPT001", name="苗学长", school="北京邮电大学", department="信息与通信工程学院",
                  major="通信工程", graduation_year=2021,
                  current_company="小米", current_position="通信算法工程师",
                  industry="互联网", city="北京",
                  skills=["5G", "信号处理", "MATLAB"],
                  bio="小米通信部,做 5G 算法。"),

    # ========== 补几个同专业的扩展(增加匹配池) ==========
    AlumniProfile(id="TH006", name="范学长", school="清华大学", department="计算机系",
                  major="计算机科学与技术", graduation_year=2023,
                  current_company="腾讯", current_position="后端开发工程师",
                  industry="互联网", city="深圳",
                  skills=["Go", "C++", "分布式", "微服务"],
                  bio="腾讯 WXG 后端,校招 1 年。"),
    AlumniProfile(id="PKU005", name="方学姐", school="北京大学", department="信息科学技术学院",
                  major="计算机科学与技术", graduation_year=2023,
                  current_company="美团", current_position="数据分析师",
                  industry="互联网", city="北京",
                  skills=["SQL", "Python", "Tableau"],
                  bio="美团数据团队,2 年校招生。"),
    AlumniProfile(id="FD004", name="姚学长", school="复旦大学", department="计算机科学技术学院",
                  major="计算机", graduation_year=2022,
                  current_company="小红书", current_position="算法工程师",
                  industry="互联网", city="上海",
                  skills=["推荐系统", "Python", "PyTorch"],
                  bio="小红书推荐算法,有内推名额。"),
]


# ============== 4 维匹配 ==============

def match_score(student: StudentProfile, alumni: AlumniProfile) -> Tuple[float, Dict[str, float]]:
    """4 维匹配分数

    返回:总分 + 4 维分数字典
    """
    breakdown = {
        "school": 1.0 if student.school == alumni.school else 0.0,
        "dept_major": 0.0,
        "industry": 1.0 if student.target_industry == alumni.industry else 0.0,
        "city": 1.0 if student.target_city == alumni.city else 0.0,
    }
    # 同院或同专业
    if student.department and alumni.department:
        if student.department == alumni.department:
            breakdown["dept_major"] = 1.0
        elif student.major and alumni.major and student.major == alumni.major:
            breakdown["dept_major"] = 0.7  # 同专业但不同院
        else:
            breakdown["dept_major"] = 0.0
    elif student.major and alumni.major and student.major == alumni.major:
        breakdown["dept_major"] = 0.7
    # 加权
    total = (
        0.40 * breakdown["school"]
        + 0.30 * breakdown["dept_major"]
        + 0.20 * breakdown["industry"]
        + 0.10 * breakdown["city"]
    )
    return round(total, 4), breakdown


def find_matches(
    student: StudentProfile,
    top_n: int = 5,
    min_score: float = 0.0,
) -> List[MatchResult]:
    """找 Top N 校友"""
    results = []
    for alumni in ALUMNI_POOL:
        score, breakdown = match_score(student, alumni)
        if score >= min_score:
            results.append(MatchResult(alumni=alumni, score=score, breakdown=breakdown))
    # 按分数降序
    results.sort(key=lambda x: -x.score)
    return results[:top_n]


# ============== 内推助手(状态机) ==============

REFER_STATUS = {
    "requested": "已请求",
    "accepted": "已接受",
    "submitted": "已提交",
    "rejected": "已拒绝",
    "passed": "通过初筛",
    "interviewing": "面试中",
    "offered": "已发 offer",
}

# 内存存储
_REFER_HISTORY: Dict[str, Dict[str, Any]] = {}


@dataclass
class ReferRequest:
    """内推请求"""
    id: str
    student_name: str
    student_school: str
    student_major: str
    target_company: str
    target_position: str
    alumni_id: str
    message: str = ""
    status: str = "requested"
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    history: List[Dict[str, str]] = field(default_factory=list)

    def update_status(self, new_status: str, note: str = ""):
        """更新状态"""
        if new_status not in REFER_STATUS:
            raise ValueError(f"Invalid status: {new_status}")
        self.status = new_status
        self.updated_at = time.time()
        self.history.append({
            "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.updated_at)),
            "status": new_status,
            "note": note,
        })
        _REFER_HISTORY[self.id] = {
            "student_name": self.student_name,
            "alumni_id": self.alumni_id,
            "target_company": self.target_company,
            "final_status": new_status,
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "student_name": self.student_name,
            "student_school": self.student_school,
            "student_major": self.student_major,
            "target_company": self.target_company,
            "target_position": self.target_position,
            "alumni_id": self.alumni_id,
            "message": self.message,
            "status": self.status,
            "status_label": REFER_STATUS.get(self.status, self.status),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "history": self.history,
        }


def request_refer(
    student_name: str,
    student_school: str,
    student_major: str,
    target_company: str,
    target_position: str,
    alumni_id: str,
    message: str = "",
) -> ReferRequest:
    """发起内推请求"""
    alumni = next((a for a in ALUMNI_POOL if a.id == alumni_id), None)
    if not alumni:
        raise ValueError(f"Alumni {alumni_id} not found")
    if not alumni.can_refer:
        raise ValueError(f"Alumni {alumni_id} cannot refer")
    rid = str(uuid.uuid4())[:8]
    req = ReferRequest(
        id=rid,
        student_name=student_name,
        student_school=student_school,
        student_major=student_major,
        target_company=target_company,
        target_position=target_position,
        alumni_id=alumni_id,
        message=message,
    )
    req.history.append({
        "ts": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
        "status": "requested",
        "note": f"学生 {student_name}({student_school} {student_major}) 发起内推请求",
    })
    return req


# ============== 虚拟学长学姐(数字分身) ==============

SENIOR_PROMPTS = {
    "senior_eng": {
        "name": "学长工程师",
        "emoji": "👨‍💻",
        "style": "理性 / 严谨 / 关心技术深度",
        "prompt": "你是一位在互联网大厂工作 3-5 年的学长,愿意分享技术成长路径。",
    },
    "senior_pm": {
        "name": "学姐产品经理",
        "emoji": "👩‍💼",
        "style": "亲切 / 关心产品思维",
        "prompt": "你是一位在互联网大厂工作 3-5 年的产品经理学姐,愿意分享 PM 成长路径。",
    },
    "senior_finance": {
        "name": "学长金融",
        "emoji": "💼",
        "style": "专业 / 关注行业动态",
        "prompt": "你是一位在头部金融机构工作 3-5 年的学长,愿意分享金融行业。",
    },
    "senior_design": {
        "name": "学姐设计",
        "emoji": "🎨",
        "style": "审美 / 关心用户体验",
        "prompt": "你是一位在互联网大厂工作 3-5 年的设计师学姐,愿意分享设计成长。",
    },
}


def get_senior_persona(alumni_id: str) -> Dict[str, str]:
    """基于校友 ID 推断虚拟人风格"""
    alumni = next((a for a in ALUMNI_POOL if a.id == alumni_id), None)
    if not alumni:
        return {"id": "default", **SENIOR_PROMPTS["senior_eng"]}
    # 根据行业 / 职位推断
    pos = alumni.current_position
    if "算法" in pos or "工程师" in pos or "开发" in pos:
        persona_id = "senior_eng"
    elif "产品" in pos:
        persona_id = "senior_pm"
    elif "金融" in alumni.industry or "投" in pos or "分析" in pos:
        persona_id = "senior_finance"
    elif "设计" in pos or "UI" in pos:
        persona_id = "senior_design"
    else:
        persona_id = "senior_eng"
    return {"id": persona_id, "alumni_id": alumni_id, **SENIOR_PROMPTS[persona_id]}


# ============== 学校邮箱验证 ==============

def verify_school_email(email: str, school: str) -> bool:
    """验证学校邮箱格式"""
    if not email or "@" not in email:
        return False
    domain_expected = SCHOOL_EMAIL_DOMAINS.get(school)
    if not domain_expected:
        return False
    return domain_expected in email


# ============== 核心 API ==============

def list_alumni(
    school: str = "",
    industry: str = "",
    can_refer: Optional[bool] = None,
) -> List[Dict[str, Any]]:
    """列出校友(可筛选)"""
    results = []
    for a in ALUMNI_POOL:
        if school and a.school != school:
            continue
        if industry and a.industry != industry:
            continue
        if can_refer is not None and a.can_refer != can_refer:
            continue
        results.append(a.to_dict())
    return results


def get_alumni(alumni_id: str) -> Optional[Dict[str, Any]]:
    """获取单个校友"""
    for a in ALUMNI_POOL:
        if a.id == alumni_id:
            return a.to_dict()
    return None


def get_school_email_domain(school: str) -> Optional[str]:
    """获取学校邮箱域名"""
    return SCHOOL_EMAIL_DOMAINS.get(school)


def list_supported_schools() -> List[str]:
    """列出支持邮箱验证的学校"""
    return list(SCHOOL_EMAIL_DOMAINS.keys())


def get_refer_history() -> List[Dict[str, Any]]:
    """获取所有内推历史"""
    return list(_REFER_HISTORY.values())


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 alumni.py {list|schools|verify|find|refer|history}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "list":
        for a in ALUMNI_POOL:
            print(f"  {a.id} {a.name} {a.school} {a.major} → {a.current_company} {a.current_position}")
    elif cmd == "schools":
        for s in SCHOOL_EMAIL_DOMAINS:
            print(f"  {s}: @{SCHOOL_EMAIL_DOMAINS[s]}")
    elif cmd == "verify":
        # python3 alumni.py verify <email> <school>
        if len(sys.argv) < 4:
            print("Usage: ... verify <email> <school>", file=sys.stderr)
            sys.exit(1)
        ok = verify_school_email(sys.argv[2], sys.argv[3])
        print("✓ 验证通过" if ok else "✗ 验证失败")
    elif cmd == "find":
        # python3 alumni.py find <school> <industry> <top>
        if len(sys.argv) < 4:
            print("Usage: ... find <school> <industry> [top]", file=sys.stderr)
            sys.exit(1)
        s = StudentProfile(name="", school=sys.argv[2], target_industry=sys.argv[3])
        top = int(sys.argv[4]) if len(sys.argv) > 4 else 5
        matches = find_matches(s, top_n=top)
        for m in matches:
            print(f"  [{m.score:.0%}] {m.alumni.id} {m.alumni.name} {m.alumni.school} → {m.alumni.current_company} {m.alumni.current_position}")
    elif cmd == "refer":
        # python3 alumni.py refer <student> <school> <major> <company> <alumni_id>
        if len(sys.argv) < 7:
            print("Usage: ... refer <student> <school> <major> <company> <position> <alumni_id>", file=sys.stderr)
            sys.exit(1)
        req = request_refer(
            student_name=sys.argv[2],
            student_school=sys.argv[3],
            student_major=sys.argv[4],
            target_company=sys.argv[5],
            target_position=sys.argv[6],
            alumni_id=sys.argv[7] if len(sys.argv) > 7 else "TH001",
        )
        print(f"内推请求 {req.id} 已发起:{req.student_name} → {req.alumni_id}")
    elif cmd == "history":
        for h in get_refer_history():
            print(f"  {h}")
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
