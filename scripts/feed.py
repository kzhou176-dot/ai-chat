#!/usr/bin/env python3
"""
aichat-Hub Feed (时间线 / Feed 流) 模块
=====================================
大学生校友 + 行业 + 求职 + 校招 4 类内容流。

4 类 Feed:
  - alumni_post(校友动态):学长学姐发的内推/经验
  - industry_post(行业洞察):9 行业专家发的行业情报
  - career_post(求职技巧):简历/面试/职业规划
  - recruit_post(校招资讯):校招时间线/公司宣讲/笔试真题

核心能力:
  - 发布 / 点赞 / 评论 / 分享
  - 时间线(按时间倒序)
  - 个性化推荐(基于 Holland Code + 目标行业 + 学校)
  - 30+ 静态 Feed(混合 4 类)

沙箱安全:
  - 静态 Feed 池(30+)
  - 纯规则互动
  - 不依赖 LLM

Cycle 17 — 第二个 v0.4 模块
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


# ============== 4 类 Feed ==============

CATEGORIES = ["alumni_post", "industry_post", "career_post", "recruit_post"]
CATEGORY_LABELS = {
    "alumni_post": ("校友动态", "🎓"),
    "industry_post": ("行业洞察", "🏢"),
    "career_post": ("求职技巧", "💼"),
    "recruit_post": ("校招资讯", "📅"),
}


# ============== 数据模型 ==============

@dataclass
class Comment:
    """评论"""
    id: str
    author_id: str
    author_name: str
    content: str
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FeedItem:
    """一条 Feed"""
    id: str
    author_id: str
    author_name: str
    author_role: str            # persona / industry_expert / career_guide / alumni / hr / senior
    author_avatar: str = "👤"   # 头像 emoji
    author_school: str = ""     # 关联学校
    author_industry: str = ""   # 关联行业
    content: str = ""
    category: str = "career_post"
    tags: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)
    likes: int = 0
    comments: List[Comment] = field(default_factory=list)
    shares: int = 0
    liked_by: List[str] = field(default_factory=list)  # 哪些用户 id 点赞过

    def is_liked_by(self, user_id: str) -> bool:
        return user_id in self.liked_by

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # 加标签
        d["category_label"] = CATEGORY_LABELS.get(self.category, ("?", "?"))[0]
        d["category_emoji"] = CATEGORY_LABELS.get(self.category, ("?", "?"))[1]
        return d


# ============== 静态 Feed 池(30+) ==============

FEED_POOL: List[FeedItem] = [
    # ========== 校友动态(alumni_post)10 条 ==========
    FeedItem(
        id="FP001", author_id="TH001", author_name="张学长",
        author_role="alumni", author_avatar="👨‍💻",
        author_school="清华大学", author_industry="互联网",
        content="今天帮 3 个清华学弟推了字节算法岗,2 个拿到面试。Tips: 简历项目经历必须量化,比如'性能提升 30%'比'性能提升明显'有用 10 倍。",
        category="alumni_post", tags=["字节", "算法", "校招", "内推"],
        likes=42, shares=8, timestamp=time.time() - 3600 * 2,
    ),
    FeedItem(
        id="FP002", author_id="TH005", author_name="刘学长",
        author_role="alumni", author_avatar="🧑‍💻",
        author_school="清华大学", author_industry="互联网",
        content="美团 2025 校招提前批已开,找我内推! 重点提醒: 提前批比正式批好进 30%,别错过。",
        category="alumni_post", tags=["美团", "提前批", "内推"],
        likes=78, shares=15, timestamp=time.time() - 3600 * 5,
    ),
    FeedItem(
        id="FP003", author_id="TH004", author_name="陈学姐",
        author_role="alumni", author_avatar="👩‍💼",
        author_school="清华大学", author_industry="互联网",
        content="UX 设计师面试 5 道常见题: 1) 你最有成就感的项目 2) ux 研究方法 3) 跨部门协作 4) 设计 vs 商业 5) 你为什么选我们。准备 STAR 法则回答。",
        category="alumni_post", tags=["设计", "面试", "UX"],
        likes=55, shares=12, timestamp=time.time() - 3600 * 8,
    ),
    FeedItem(
        id="FP004", author_id="PKU001", author_name="赵学长",
        author_role="alumni", author_avatar="🧑‍💻",
        author_school="北京大学", author_industry="互联网",
        content="阿里淘宝推荐算法,5 年经验,做校招面试官 3 年。看简历的 3 个 priority: 1) 项目深度 2) 顶会论文 3) 实习含金量。",
        category="alumni_post", tags=["阿里", "推荐", "校招", "面试官"],
        likes=66, shares=10, timestamp=time.time() - 3600 * 12,
    ),
    FeedItem(
        id="FP005", author_id="FD001", author_name="郑学长",
        author_role="alumni", author_avatar="👨‍💻",
        author_school="复旦大学", author_industry="互联网",
        content="蚂蚁支付后端,校招生 1 年总结: Java + 分布式 + 高并发 + 业务理解。3 年后想跳甲方/投资/创业,都见过,选择比努力重要。",
        category="alumni_post", tags=["蚂蚁", "后端", "校招", "职业路径"],
        likes=88, shares=20, timestamp=time.time() - 3600 * 18,
    ),
    FeedItem(
        id="FP006", author_id="ZJU001", author_name="梁学姐",
        author_role="alumni", author_avatar="👩‍💼",
        author_school="浙江大学", author_industry="互联网",
        content="字节抖音 PM 3 年。AI 产品经理校招要求: 1) 懂 AI 技术(不必精通) 2) 有 0-1 产品经验 3) 用户思维 + 数据驱动。",
        category="alumni_post", tags=["字节", "PM", "AI产品"],
        likes=95, shares=22, timestamp=time.time() - 3600 * 24,
    ),
    FeedItem(
        id="FP007", author_id="FD002", author_name="钱学姐",
        author_role="alumni", author_avatar="👩‍💼",
        author_school="复旦大学", author_industry="快消",
        content="宝洁管培生,清扬品牌。3-5 年留存率 30% 的原因: 强度大 + 天花板 + 薪资 vs 互联网。退出路径: 品牌咨询 / 创业 / 互联网营销。",
        category="alumni_post", tags=["宝洁", "管培生", "快消", "职业路径"],
        likes=72, shares=15, timestamp=time.time() - 3600 * 30,
    ),
    FeedItem(
        id="FP008", author_id="PKU002", author_name="孙学姐",
        author_role="alumni", author_avatar="👩‍💼",
        author_school="北京大学", author_industry="金融",
        content="高盛 IBD VP,5 年经验。投行降薪是真的,但仍是顶薪。应届生选投行/PE/VC/咨询,看个人兴趣 + 退出路径,不要只看钱。",
        category="alumni_post", tags=["高盛", "投行", "金融"],
        likes=63, shares=12, timestamp=time.time() - 3600 * 36,
    ),
    FeedItem(
        id="FP009", author_id="USTC001", author_name="杨学长",
        author_role="alumni", author_avatar="🧑‍💻",
        author_school="中国科学技术大学", author_industry="互联网",
        content="华为天才少年,入职 1 年。技术深度决定上限,但 30 岁后工程能力 + 业务理解 + 软技能 同样重要。不要只刷题。",
        category="alumni_post", tags=["华为", "天才少年", "算法", "职业成长"],
        likes=110, shares=25, timestamp=time.time() - 3600 * 48,
    ),
    FeedItem(
        id="FP010", author_id="SJTU001", author_name="胡学姐",
        author_role="alumni", author_avatar="👩‍💻",
        author_school="上海交通大学", author_industry="互联网",
        content="美团前端,React/TypeScript/小程序。性能优化 3 个实战: 1) 路由懒加载 2) 图片压缩 3) 减少 setState 频率。",
        category="alumni_post", tags=["美团", "前端", "性能优化"],
        likes=45, shares=8, timestamp=time.time() - 3600 * 60,
    ),

    # ========== 行业洞察(industry_post)10 条 ==========
    FeedItem(
        id="FP011", author_id="industry_algorithm", author_name="算法行业专家",
        author_role="industry_expert", author_avatar="🤖",
        author_industry="互联网",
        content="2025 校招 LLM 方向最热,具身智能是下一个风口。算法岗薪资 30-60 万,但岗位减少 30%。要会 LLM 不只是 LeetCode。",
        category="industry_post", tags=["算法", "LLM", "具身智能", "2025校招"],
        likes=125, shares=30, timestamp=time.time() - 3600 * 3,
    ),
    FeedItem(
        id="FP012", author_id="industry_product", author_name="产品经理行业专家",
        author_role="industry_expert", author_avatar="📱",
        author_industry="互联网",
        content="B 端 PM 越来越值钱,2025 校招薪资 25-50 万。AI 产品经理新需求激增,缺口 50% 没人做。应届生想入行?做 1-2 个 AI Demo 项目。",
        category="industry_post", tags=["产品", "B端", "AI", "校招"],
        likes=98, shares=22, timestamp=time.time() - 3600 * 7,
    ),
    FeedItem(
        id="FP013", author_id="industry_data", author_name="数据分析师行业专家",
        author_role="industry_expert", author_avatar="📈",
        author_industry="互联网",
        content="数据分析师 3 必备技能: SQL + Python + 业务理解。SQL 刷到什么程度?窗口函数 + 复杂查询 + 性能优化。Python 数据分析 5 个常用库。",
        category="industry_post", tags=["数据", "SQL", "Python"],
        likes=82, shares=18, timestamp=time.time() - 3600 * 10,
    ),
    FeedItem(
        id="FP014", author_id="industry_design", author_name="UI/UX 设计行业专家",
        author_role="industry_expert", author_avatar="🎨",
        author_industry="互联网",
        content="设计师 2025 趋势: AI 辅助设计普及(效率 +50%),但 UX 研究 / 用户洞察更值钱。作品集 > 学历。3-5 个完整流程项目是硬通货。",
        category="industry_post", tags=["设计", "UX", "AI", "作品集"],
        likes=68, shares=15, timestamp=time.time() - 3600 * 14,
    ),
    FeedItem(
        id="FP015", author_id="industry_finance", author_name="金融行业专家",
        author_role="industry_expert", author_avatar="💰",
        author_industry="金融",
        content="金融 2025 趋势: 投行降薪 30-50%,资管/量化仍是香饽饽。证书方面 CFA/FRM 加分,但不是必须。头部实习 > 一切。",
        category="industry_post", tags=["金融", "投行", "量化"],
        likes=70, shares=16, timestamp=time.time() - 3600 * 22,
    ),
    FeedItem(
        id="FP016", author_id="industry_consulting", author_name="咨询行业专家",
        author_role="industry_expert", author_avatar="🏢",
        author_industry="咨询",
        content="MBB 校招看重: 1) 学校 2) 案例面试(50+ case) 3) 英语 4) 实习 5) 沟通。Case in Point + 每日 1 case,3 个月准备期。",
        category="industry_post", tags=["咨询", "MBB", "校招"],
        likes=55, shares=12, timestamp=time.time() - 3600 * 28,
    ),
    FeedItem(
        id="FP017", author_id="industry_operation", author_name="运营行业专家",
        author_role="industry_expert", author_avatar="📊",
        author_industry="互联网",
        content="运营 3 主流方向: 内容运营 / 短视频运营 / 增长运营。2025 校招起薪 15-30 万,小红书/B 站个人号 1 万粉是加分项。",
        category="industry_post", tags=["运营", "小红书", "B站"],
        likes=60, shares=14, timestamp=time.time() - 3600 * 35,
    ),
    FeedItem(
        id="FP018", author_id="industry_fmcg", author_name="快消行业专家",
        author_role="industry_expert", author_avatar="🛒",
        author_industry="快消",
        content="宝洁八大问: 领导力 / 创新 / 效率 / 执行力 / 团队 / 决策 / 服务 / 诚信。STAR 法则 + 具体例子 + 量化结果。准备 3 个月。",
        category="industry_post", tags=["快消", "宝洁", "八大问"],
        likes=48, shares=10, timestamp=time.time() - 3600 * 42,
    ),
    FeedItem(
        id="FP019", author_id="industry_realestate", author_name="地产行业专家",
        author_role="industry_expert", author_avatar="🏗️",
        author_industry="地产",
        content="地产行业现状: 整体收缩 30%,但代建/物业/商业细分还在招。万科/龙湖/华润 管培生项目仍是头部选择。",
        category="industry_post", tags=["地产", "管培生"],
        likes=32, shares=6, timestamp=time.time() - 3600 * 50,
    ),
    FeedItem(
        id="FP020", author_id="industry_algorithm", author_name="算法行业专家",
        author_role="industry_expert", author_avatar="🤖",
        author_industry="互联网",
        content="算法岗方向选择: CV/NLP/推荐/广告/LLM。LLM 风口但内卷,推荐稳定但成熟,具身智能新机会但不确定。建议:兴趣 + 团队 + 业务。",
        category="industry_post", tags=["算法", "方向", "选择"],
        likes=88, shares=18, timestamp=time.time() - 3600 * 72,
    ),

    # ========== 求职技巧(career_post)5 条 ==========
    FeedItem(
        id="FP021", author_id="career_mentor", author_name="简历导师",
        author_role="persona", author_avatar="📝",
        content="STAR 法则的 4 个关键点: 1) S 情境(背景/约束) 2) T 任务(目标) 3) A 行动(具体动作) 4) R 结果(量化数据)。每段项目经历都按这个写。",
        category="career_post", tags=["简历", "STAR", "改写"],
        likes=180, shares=45, timestamp=time.time() - 3600 * 1,
    ),
    FeedItem(
        id="FP022", author_id="career_hr", author_name="HR 顾问",
        author_role="persona", author_avatar="💼",
        content="大厂 HR 每天看 500+ 份简历,3 秒抓住眼球的 5 个关键: 1) 学校 + 学历 + 专业(顶部) 2) 量化数据(数字 30%+) 3) 关键词(岗位 JD) 4) 项目经历 5) 实习。",
        category="career_post", tags=["HR", "简历", "面试"],
        likes=150, shares=38, timestamp=time.time() - 3600 * 4,
    ),
    FeedItem(
        id="FP023", author_id="career_guide", author_name="职业规划师",
        author_role="persona", author_avatar="🧭",
        content="霍兰德 6 维,你的代码是? 测完看推荐: RIA(工程师/建筑师) / IAS(咨询/产品) / SEC(HR/销售)。基于代码选行业,而不是反过来。",
        category="career_post", tags=["霍兰德", "职业规划"],
        likes=135, shares=32, timestamp=time.time() - 3600 * 6,
    ),
    FeedItem(
        id="FP024", author_id="career_mentor", author_name="简历导师",
        author_role="persona", author_avatar="📝",
        content="简历 3 大常见错误: 1) '负责'/'参与'/'协助' 等弱动词太多 2) 没有量化数据 3) 自我评价太空洞。改:主导/推动 + 30% 提升 + 具体例子。",
        category="career_post", tags=["简历", "改写", "动词"],
        likes=160, shares=40, timestamp=time.time() - 3600 * 9,
    ),
    FeedItem(
        id="FP025", author_id="career_guide", author_name="职业规划师",
        author_role="persona", author_avatar="🧭",
        content="校招时间线: 6-7 月暑期实习 8-9 月提前批 9-10 月正式批 11 月补录。互联网公司一般提前批好进,不要等。",
        category="career_post", tags=["校招", "时间线"],
        likes=98, shares=22, timestamp=time.time() - 3600 * 16,
    ),

    # ========== 校招资讯(recruit_post)5 条 ==========
    FeedItem(
        id="FP026", author_id="recruit_news", author_name="校招资讯",
        author_role="persona", author_avatar="📅",
        content="【国家大学生就业服务平台】2025 届校招时间线: 7 月启动 → 8 月提前批 → 9-10 月正式批 → 11 月补录 → 12 月-2 月春招。",
        category="recruit_post", tags=["校招", "时间线", "官方"],
        likes=200, shares=55, timestamp=time.time() - 3600 * 0.5,
    ),
    FeedItem(
        id="FP027", author_id="recruit_news", author_name="校招资讯",
        author_role="persona", author_avatar="📅",
        content="【字节跳动】2025 秋招提前批 7-8 月,正式批 9-10 月。算法 / 后端 / 前端 / 产品 / 运营 / 设计 全岗位开放,找我内推。",
        category="recruit_post", tags=["字节", "校招", "秋招"],
        likes=178, shares=48, timestamp=time.time() - 3600 * 11,
    ),
    FeedItem(
        id="FP028", author_id="recruit_news", author_name="校招资讯",
        author_role="persona", author_avatar="📅",
        content="【阿里巴巴】2025 秋招 8 月 1 日启动,共开放 3000+ 岗位,覆盖算法/工程/产品/设计/数据/运营。面向 2025 届毕业生。",
        category="recruit_post", tags=["阿里", "秋招"],
        likes=165, shares=42, timestamp=time.time() - 3600 * 20,
    ),
    FeedItem(
        id="FP029", author_id="recruit_news", author_name="校招资讯",
        author_role="persona", author_avatar="📅",
        content="【腾讯】2025 校招提前批 7 月启动,微信/QQ/腾讯视频/腾讯云 全 BU 开放。算法岗特别多,LLM 方向需求激增。",
        category="recruit_post", tags=["腾讯", "校招", "LLM"],
        likes=145, shares=36, timestamp=time.time() - 3600 * 33,
    ),
    FeedItem(
        id="FP030", author_id="recruit_news", author_name="校招资讯",
        author_role="persona", author_avatar="📅",
        content="【中金公司】2025 暑期实习申请截止 4 月 30 日,投行/研究/资管 全赛道开放。清北复交 + 财经 985 是基本盘。",
        category="recruit_post", tags=["中金", "金融", "实习"],
        likes=88, shares=18, timestamp=time.time() - 3600 * 48,
    ),
]


# ============== FeedEngine ==============

class FeedEngine:
    """Feed 引擎"""
    def __init__(self):
        import copy
        self._pool: List[FeedItem] = copy.deepcopy(FEED_POOL)  # 深复制(独立 liked_by)
        self._user_actions: Dict[str, set] = {}  # user_id -> set of feed_ids(已点赞)

    def list_feed(
        self,
        category: Optional[str] = None,
        author_school: Optional[str] = None,
        author_industry: Optional[str] = None,
        limit: int = 20,
        sort: str = "time",
    ) -> List[Dict[str, Any]]:
        """列出 Feed(可筛选+排序)"""
        items = list(self._pool)
        if category:
            items = [x for x in items if x.category == category]
        if author_school:
            items = [x for x in items if x.author_school == author_school]
        if author_industry:
            items = [x for x in items if x.author_industry == author_industry]
        # 排序
        if sort == "time":
            items.sort(key=lambda x: -x.timestamp)
        elif sort == "hot":
            items.sort(key=lambda x: -(x.likes + x.shares * 2 + len(x.comments) * 3))
        return [x.to_dict() for x in items[:limit]]

    def get_post(self, post_id: str) -> Optional[Dict[str, Any]]:
        for p in self._pool:
            if p.id == post_id:
                return p.to_dict()
        return None

    def publish_post(
        self,
        author_id: str,
        author_name: str,
        author_role: str,
        content: str,
        category: str = "career_post",
        tags: Optional[List[str]] = None,
        author_avatar: str = "👤",
        author_school: str = "",
        author_industry: str = "",
    ) -> Dict[str, Any]:
        """发布 Feed"""
        if category not in CATEGORIES:
            category = "career_post"
        pid = str(uuid.uuid4())[:8]
        post = FeedItem(
            id=pid, author_id=author_id, author_name=author_name,
            author_role=author_role, author_avatar=author_avatar,
            author_school=author_school, author_industry=author_industry,
            content=content, category=category, tags=tags or [],
        )
        self._pool.insert(0, post)  # 最新置顶
        return post.to_dict()

    def like_post(self, post_id: str, user_id: str) -> Dict[str, Any]:
        """点赞"""
        for p in self._pool:
            if p.id == post_id:
                if user_id in p.liked_by:
                    # 已点赞,取消
                    p.liked_by.remove(user_id)
                    p.likes = max(0, p.likes - 1)
                    return {"post": p.to_dict(), "action": "unliked"}
                else:
                    p.liked_by.append(user_id)
                    p.likes += 1
                    return {"post": p.to_dict(), "action": "liked"}
        return {"error": "post not found"}

    def add_comment(self, post_id: str, user_id: str, user_name: str, content: str) -> Dict[str, Any]:
        """评论"""
        for p in self._pool:
            if p.id == post_id:
                cid = str(uuid.uuid4())[:8]
                p.comments.append(Comment(
                    id=cid, author_id=user_id, author_name=user_name, content=content,
                ))
                return {"post": p.to_dict(), "comment_id": cid}
        return {"error": "post not found"}

    def share_post(self, post_id: str) -> Dict[str, Any]:
        """分享"""
        for p in self._pool:
            if p.id == post_id:
                p.shares += 1
                return {"post": p.to_dict()}
        return {"error": "post not found"}

    def recommend_for_user(
        self,
        holland_code: str = "",
        target_industry: str = "",
        user_school: str = "",
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """个性化推荐"""
        items = list(self._pool)
        scored = []
        for item in items:
            score = 0
            # 学校匹配 +30
            if user_school and item.author_school == user_school:
                score += 30
            # 行业匹配 +20
            if target_industry and item.author_industry == target_industry:
                score += 20
            # Holland Code 匹配 +15(简化:基于 category)
            if holland_code and self._category_match_holland(item.category, holland_code):
                score += 15
            # 热度加分(likes + shares*2 + comments*3)
            score += min(30, item.likes + item.shares * 2 + len(item.comments) * 3)
            # 时间近加分
            age_hours = (time.time() - item.timestamp) / 3600
            if age_hours < 24:
                score += 10
            elif age_hours < 72:
                score += 5
            scored.append((score, item))
        # 按分数倒序
        scored.sort(key=lambda x: -x[0])
        return [item.to_dict() for _, item in scored[:limit]]

    def _category_match_holland(self, category: str, holland_code: str) -> bool:
        """简单映射:category 与 Holland Code 匹配度"""
        # 行业洞察 + 校友动态 = 强相关
        # 求职技巧 + 校招资讯 = 普适
        mapping = {
            "industry_post": "IARE",  # 研究/艺术/企业
            "alumni_post": "SRIE",    # 社会/实际/研究
            "career_post": "ESC",      # 企业/社会/常规
            "recruit_post": "CE",      # 常规/企业
        }
        if not holland_code:
            return False
        target = mapping.get(category, "")
        return any(c in target for c in holland_code.upper())


# ============== 核心 API(模块级) ==============

_ENGINE = FeedEngine()


def list_feed(
    category: Optional[str] = None,
    author_school: Optional[str] = "",
    author_industry: Optional[str] = "",
    limit: int = 20,
    sort: str = "time",
) -> List[Dict[str, Any]]:
    return _ENGINE.list_feed(
        category=category, author_school=author_school,
        author_industry=author_industry, limit=limit, sort=sort,
    )


def get_post(post_id: str) -> Optional[Dict[str, Any]]:
    return _ENGINE.get_post(post_id)


def publish_post(**kwargs) -> Dict[str, Any]:
    return _ENGINE.publish_post(**kwargs)


def like_post(post_id: str, user_id: str) -> Dict[str, Any]:
    return _ENGINE.like_post(post_id, user_id)


def add_comment(post_id: str, user_id: str, user_name: str, content: str) -> Dict[str, Any]:
    return _ENGINE.add_comment(post_id, user_id, user_name, content)


def share_post(post_id: str) -> Dict[str, Any]:
    return _ENGINE.share_post(post_id)


def recommend_for_user(
    holland_code: str = "",
    target_industry: str = "",
    user_school: str = "",
    limit: int = 10,
) -> List[Dict[str, Any]]:
    return _ENGINE.recommend_for_user(
        holland_code=holland_code,
        target_industry=target_industry,
        user_school=user_school,
        limit=limit,
    )


def list_categories() -> List[Dict[str, str]]:
    """列出 4 类 Feed"""
    return [
        {"id": k, "label": v[0], "emoji": v[1]}
        for k, v in CATEGORY_LABELS.items()
    ]


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 feed.py {list|categories|get|recommend|publish}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "list":
        cat = sys.argv[2] if len(sys.argv) > 2 else None
        items = list_feed(category=cat, limit=5)
        for i in items:
            print(f"  [{i['category_emoji']} {i['category_label']}] {i['author_name']}: {i['content'][:50]}...  👍{i['likes']}")
    elif cmd == "categories":
        for c in list_categories():
            print(f"  {c['emoji']} {c['id']} - {c['label']}")
    elif cmd == "get":
        if len(sys.argv) < 3:
            print("Usage: ... get <post_id>", file=sys.stderr)
            sys.exit(1)
        post = get_post(sys.argv[2])
        print(json.dumps(post, ensure_ascii=False, indent=2) if post else "Not found")
    elif cmd == "recommend":
        code = sys.argv[2] if len(sys.argv) > 2 else ""
        industry = sys.argv[3] if len(sys.argv) > 3 else ""
        school = sys.argv[4] if len(sys.argv) > 4 else ""
        items = recommend_for_user(holland_code=code, target_industry=industry, user_school=school, limit=5)
        for i in items:
            print(f"  {i['author_name']}: {i['content'][:50]}...")
    elif cmd == "publish":
        # python3 feed.py publish <author> <content> [category]
        if len(sys.argv) < 4:
            print("Usage: ... publish <author> <content> [category]", file=sys.stderr)
            sys.exit(1)
        post = publish_post(
            author_id="cli_user", author_name=sys.argv[2],
            author_role="user", content=sys.argv[3],
            category=sys.argv[4] if len(sys.argv) > 4 else "career_post",
        )
        print(f"发布成功:{post['id']}")
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
