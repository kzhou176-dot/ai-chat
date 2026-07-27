#!/usr/bin/env python3
"""
aichat-Hub Industry Insight (行业洞察) 模块
==========================================
大学生 9 大行业专家虚拟人对话 — 行业画像 / 职业路径 / 技能树 / 常见问题。

9 大行业(2025 大学生求职热门):
  algorithm  算法工程师 🤖
  product    产品经理   📱
  operation  运营       📊
  design     UI/UX 设计 🎨
  data       数据分析师 📈
  finance    金融       💰
  consulting 咨询       🏢
  fmcg       快消       🛒
  realestate 地产       🏗️

每个行业提供:
  1. 行业画像(头部公司 / 校招薪资 / 入门门槛)
  2. 职业路径(3-5 年典型发展)
  3. 技能树(必备技能)
  4. 常见问题库(20-30 FAQ)
  5. 与 Holland Code 的匹配度(联动 career_profile)

与 interview.py 模式一致:
  - Question(role, text, key_points, difficulty)
  - IndustrySession(industry, questions, answers, results)
  - 5 维评分(复用 interview 的逻辑)

沙箱安全:9 行业 × 20-30 题 = 220+ 题目静态库,纯规则评分

Cycle 14 — 第四个职业辅导模块
"""
from __future__ import annotations
import json
import re
import time
from collections import Counter
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


# ============== 行业画像 ==============

INDUSTRY_PROFILES: Dict[str, Dict[str, Any]] = {
    "algorithm": {
        "name": "算法工程师",
        "emoji": "🤖",
        "category": "互联网技术",
        "entry_bar": "985/211 + ACM/数学建模/顶会论文",
        "top_companies": ["字节跳动", "阿里巴巴", "腾讯", "美团", "华为", "百度", "小米"],
        "salary_range_2025": "30-60 万(校招 P5-P6)",
        "holland_fit": ["I", "R", "A"],
        "skill_tree": ["Python", "PyTorch", "LeetCode", "机器学习", "深度学习", "数学基础", "顶会论文"],
        "career_path": "P5(校招)→ P6(3年)→ P7(5年)→ 资深/专家",
        "typical_day": "80% 写代码/调参/跑实验;20% 开会/写文档",
        "trends_2025": "LLM/多模态/AIGC/具身智能 是新风口",
        "system_prompt": (
            "你是一位资深的算法工程师,在 BAT 大厂工作 5-8 年。"
            "你精通 Python/PyTorch/机器学习,对 LLM/多模态/AIGC 趋势了如指掌。"
            "你会从过来人视角告诉学生:算法岗的真实一天、必备技能、校招准备路径、"
            "选 offer 的关键维度(技术成长/业务场景/WLB/薪资)。"
        ),
    },
    "product": {
        "name": "产品经理",
        "emoji": "📱",
        "category": "互联网产品",
        "entry_bar": "985/211 + 实习 + 产品案例(可演示的)",
        "top_companies": ["字节跳动", "腾讯", "阿里巴巴", "美团", "小红书", "快手", "京东"],
        "salary_range_2025": "25-50 万(校招 P5-P6)",
        "holland_fit": ["E", "A", "S"],
        "skill_tree": ["用户调研", "PRD 撰写", "Axure/墨刀", "数据 SQL", "竞品分析", "A/B 测试", "用户增长"],
        "career_path": "产品助理 → 产品经理 → 高级 → 产品总监",
        "typical_day": "50% 会议(对齐/评审)+ 30% 写 PRD + 20% 调研/数据分析",
        "trends_2025": "AI 产品经理需求激增(0-1 AI 应用)",
        "system_prompt": (
            "你是一位互联网大厂资深产品经理,5-8 年经验,做过 C 端/B 端/AI 多类产品。"
            "你会告诉学生:产品岗的核心能力(用户洞察 + 数据驱动 + 跨部门协作)、"
            "如何写一份高通过率的 PRD、校招选 offer 的关键维度。"
        ),
    },
    "operation": {
        "name": "运营",
        "emoji": "📊",
        "category": "互联网运营",
        "entry_bar": "学历较宽松 + 运营相关实习 + 运营案例(可量化)",
        "top_companies": ["阿里巴巴", "字节跳动", "美团", "小红书", "B 站", "拼多多", "快手"],
        "salary_range_2025": "15-30 万(校招)",
        "holland_fit": ["E", "S", "C"],
        "skill_tree": ["内容运营", "活动运营", "用户增长", "数据分析", "小红书/B 站", "短视频运营", "社群运营"],
        "career_path": "运营专员 → 运营经理 → 运营总监",
        "typical_day": "40% 数据分析 + 30% 写文案/活动 + 30% 沟通协调",
        "trends_2025": "内容运营 / 短视频 / 增长运营 三足鼎立",
        "system_prompt": (
            "你是一位互联网运营老兵,做过用户增长/内容运营/活动运营多条线。"
            "你会告诉学生:运营岗的真实工作、校招准备(小红书/B 站个人号)、"
            "如何从执行岗走向策略岗、运营转产品的可能性。"
        ),
    },
    "design": {
        "name": "UI/UX 设计",
        "emoji": "🎨",
        "category": "互联网设计",
        "entry_bar": "作品集(实习 + 个人项目)",
        "top_companies": ["字节跳动", "腾讯", "阿里巴巴", "小米", "美团", "京东", "蚂蚁"],
        "salary_range_2025": "20-40 万(校招)",
        "holland_fit": ["A", "I", "C"],
        "skill_tree": ["Figma", "Sketch", "UI 规范", "交互设计", "动效", "UX 研究", "用户访谈"],
        "career_path": "初级设计师 → 高级 → 设计专家 / 设计总监",
        "typical_day": "60% 画图 + 30% 评审 + 10% 用户研究",
        "trends_2025": "AI 辅助设计普及;UX 研究/用户洞察更值钱",
        "system_prompt": (
            "你是一位互联网资深设计师,8 年经验,做过 UX/UI/品牌多类设计。"
            "你会告诉学生:作品集如何准备、设计岗面试如何展示、"
            "C 端/B 端/品牌设计的差异、AI 工具对设计师的影响。"
        ),
    },
    "data": {
        "name": "数据分析师",
        "emoji": "📈",
        "category": "互联网数据",
        "entry_bar": "统计学/计算机/数学背景 + SQL/Python 熟练",
        "top_companies": ["字节跳动", "美团", "京东", "蚂蚁", "腾讯", "拼多多", "滴滴"],
        "salary_range_2025": "25-45 万(校招)",
        "holland_fit": ["I", "C", "E"],
        "skill_tree": ["SQL", "Python", "Excel", "Tableau/Power BI", "A/B 测试", "统计学", "业务理解"],
        "career_path": "分析师 → 高级分析师 → 数据科学家 / 经理",
        "typical_day": "50% 写 SQL/Python + 30% 报告 + 20% 业务沟通",
        "trends_2025": "与算法边界模糊;数据 + 业务复合型人才更受欢迎",
        "system_prompt": (
            "你是一位资深数据分析师,在大厂数据团队工作 5-8 年。"
            "你会告诉学生:数据岗的核心能力(业务理解 + 技术 + 沟通)、"
            "如何从取数机器变成业务伙伴、数据分析师的转型路径。"
        ),
    },
    "finance": {
        "name": "金融",
        "emoji": "💰",
        "category": "金融",
        "entry_bar": "985 + 头部实习 + CFA/FRM 加分",
        "top_companies": ["中金", "中信证券", "华泰证券", "高盛", "摩根士丹利", "中金基金", "桥水"],
        "salary_range_2025": "30-80 万(投行/资管/量化)",
        "holland_fit": ["C", "E", "I"],
        "skill_tree": ["Excel", "Wind", "Bloomberg", "估值建模", "行业研究", "CFA/FRM", "财务分析"],
        "career_path": "分析师 → VP → MD(投行);或基金/资管路径",
        "typical_day": "60% Excel/PPT + 30% 会议 + 10% 客户沟通",
        "trends_2025": "投行降薪;资管/量化仍是香饽饽",
        "system_prompt": (
            "你是一位金融行业资深从业者,在头部投行/资管工作 8-10 年。"
            "你会告诉学生:金融细分赛道(投行/券商/基金/银行/保险)的差异、"
            "校招准备路径(实习/证书/技能)、选 offer 关键维度、真实工作强度。"
        ),
    },
    "consulting": {
        "name": "咨询",
        "emoji": "🏢",
        "category": "咨询",
        "entry_bar": "清北复交 + MBB 案例面试",
        "top_companies": ["麦肯锡", "贝恩", "BCG", "罗兰贝格", "埃森哲", "德勤", "PwC"],
        "salary_range_2025": "25-50 万(MBB 校招)",
        "holland_fit": ["I", "E", "S"],
        "skill_tree": ["PPT", "Excel", "案例分析", "行业研究", "用户访谈", "结构化思维", "英语"],
        "career_path": "Consultant → Manager → Senior Manager → Partner",
        "typical_day": "70% PPT + 25% 客户访谈 + 5% 数据",
        "trends_2025": "战略咨询仍卷;数字化咨询是新增量",
        "system_prompt": (
            "你是一位 MBB 资深咨询顾问,7 年经验,做过多个行业项目。"
            "你会告诉学生:咨询校招准备(案例面试/PPT/英语)、"
            "咨询的真实工作强度(出差/加班/项目周期)、"
            "咨询的退出路径(转甲方/投资/创业)。"
        ),
    },
    "fmcg": {
        "name": "快消",
        "emoji": "🛒",
        "category": "快消",
        "entry_bar": "985/211 + 商业思维 + 英语",
        "top_companies": ["宝洁", "联合利华", "欧莱雅", "可口可乐", "百威", "亿滋", "玛氏"],
        "salary_range_2025": "18-35 万(管培生)",
        "holland_fit": ["S", "A", "E"],
        "skill_tree": ["商业思维", "宝洁八大问", "英语", "数字营销", "跨部门协作", "项目管理", "数据分析"],
        "career_path": "管培生 → 品牌经理 → 高级经理 → 市场总监",
        "typical_day": "30% 会议 + 30% 跨部门 + 20% 数据 + 20% 活动",
        "trends_2025": "管培生项目仍是顶级,但 3-5 年留存率 < 30%",
        "system_prompt": (
            "你是一位宝洁/联合利华资深品牌经理,管培生项目出身。"
            "你会告诉学生:宝洁八大问怎么准备、快消管培的优劣势、"
            "快消 vs 互联网的差异、退出路径(品牌咨询/创业)。"
        ),
    },
    "realestate": {
        "name": "地产",
        "emoji": "🏗️",
        "category": "地产",
        "entry_bar": "985/211 + 工程/管理类背景",
        "top_companies": ["万科", "龙湖", "华润", "中海", "招商蛇口", "保利", "碧桂园"],
        "salary_range_2025": "15-30 万(校招)",
        "holland_fit": ["E", "S", "C"],
        "skill_tree": ["成本管理", "工程管理", "营销策划", "投融资", "项目管理", "客户关系"],
        "career_path": "管培生 → 项目经理 → 项目总 → 区域总",
        "typical_day": "40% 现场 + 30% 会议 + 20% 文档 + 10% 销售",
        "trends_2025": "整体收缩;代建/物业/商业细分还在招",
        "system_prompt": (
            "你是一位头部地产公司区域项目总,管培生出身。"
            "你会告诉学生:地产行业现状(整体收缩)、细分赛道选择(代建/物业/商业)、"
            "校招选 offer 关键维度、行业转型路径。"
        ),
    },
}


# ============== 9 行业常见问题库(每行业 20-30 题) ==============

FAQ_BANK: Dict[str, List[Dict[str, Any]]] = {
    "algorithm": [
        {"q": "算法岗真实一天是什么样的?", "kp": ["写代码", "调参", "跑实验", "开会", "文档"]},
        {"q": "校招算法岗的必备技能是什么?", "kp": ["Python", "PyTorch", "LeetCode", "机器学习", "顶会论文", "数学"]},
        {"q": "算法岗分哪些方向?哪个方向好?", "kp": ["CV", "NLP", "推荐", "广告", "LLM", "AIGC"]},
        {"q": "校招算法岗需要论文吗?", "kp": ["顶会加分", "A 类期刊", "比赛获奖", "实际项目"]},
        {"q": "LeetCode 刷多少题够用?", "kp": ["200-300 中等", "覆盖高频题", "每日一题", "分类练习"]},
        {"q": "实习 vs 论文,校招哪个更重要?", "kp": ["大厂实习加分", "顶会论文更强", "两者皆有最佳"]},
        {"q": "算法岗会被 AI 取代吗?", "kp": ["不会取代", "工具进化", "工程能力更重要", "研究型人才稀缺"]},
        {"q": "如何选算法岗 offer?", "kp": ["业务场景", "技术成长", "WLB", "薪资", "团队"]},
        {"q": "算法岗晋升路径是什么?", "kp": ["P5 校招", "P6 3 年", "P7 5 年", "P8 资深"]},
        {"q": "算法岗需要读研/读博吗?", "kp": ["本科可就业", "研究岗要博士", "硕士是主流"]},
        {"q": "应届算法岗薪资 30-60 万是真的吗?", "kp": ["30-60 万正常", "看公司", "看评级", "看股票"]},
        {"q": "如何准备算法岗的简历?", "kp": ["项目经历", "竞赛奖项", "顶会论文", "实习经历", "技术栈"]},
        {"q": "算法岗的面试流程是什么?", "kp": ["笔试", "技术面 1-2 轮", "系统设计", "HR 面", "Leader 面"]},
        {"q": "算法岗面试会考什么?", "kp": ["算法题", "机器学习基础", "项目深挖", "系统设计"]},
        {"q": "如何入门 LLM 方向?", "kp": ["Hugging Face", "Transformer 论文", "开源项目", "动手实践"]},
        {"q": "顶会论文怎么发?周期多长?", "kp": ["NeurIPS/ICML/ICLR/CVPR", "周期 1-2 年", "需要好 idea"]},
        {"q": "推荐系统方向还有前景吗?", "kp": ["传统推荐成熟", "LLM+推荐", "工业界需求大", "迭代快"]},
        {"q": "AIGC 是风口吗?值得入吗?", "kp": ["2024-2025 风口", "技术栈变化快", "创业机会多", "竞争激烈"]},
        {"q": "如何选研究方向?热门还是兴趣?", "kp": ["兴趣优先", "结合就业", "看导师", "看实验室"]},
        {"q": "算法岗转产品/管理可行吗?", "kp": ["完全可行", "技术 + 产品思维", "有优势", "后期管理"]},
        {"q": "BAT 算法岗校招看重什么?", "kp": ["基础功", "项目深度", "论文", "竞赛", "实习"]},
        {"q": "算法岗 35 岁危机是真的吗?", "kp": ["存在", "技术专家", "管理路径", "持续学习"]},
    ],
    "product": [
        {"q": "产品岗真实一天是什么样的?", "kp": ["会议", "写 PRD", "数据", "调研", "评审"]},
        {"q": "校招产品岗必备能力是什么?", "kp": ["用户洞察", "数据驱动", "PRD 撰写", "竞品分析", "沟通"]},
        {"q": "没有产品实习,如何准备校招?", "kp": ["个人产品项目", "产品分析文章", "竞品分析报告", "PRD 练习"]},
        {"q": "产品岗面试会问什么?", "kp": ["产品设计题", "产品分析题", "行为面试", "数据题"]},
        {"q": "如何写一份高质量 PRD?", "kp": ["背景", "目标", "需求", "流程", "指标"]},
        {"q": "C 端 vs B 端产品,选哪个?", "kp": ["C 端用户多", "B 端商业深", "看兴趣", "看背景"]},
        {"q": "AI 产品经理是什么?和传统 PM 区别?", "kp": ["懂 AI 技术", "0-1 应用", "算法理解", "数据敏感"]},
        {"q": "产品岗需要会写代码吗?", "kp": ["不要求精通", "能看懂技术", "会 SQL 加分", "能画原型"]},
        {"q": "如何选产品岗 offer?", "kp": ["业务", "成长空间", "团队", "薪资", "公司平台"]},
        {"q": "产品岗晋升路径?", "kp": ["产品助理", "产品经理", "高级", "产品总监", "VP"]},
        {"q": "校招产品岗薪资范围?", "kp": ["25-50 万", "看公司", "看评级"]},
        {"q": "产品岗如何转管理?", "kp": ["带人", "带项目", "战略思维", "沟通能力"]},
        {"q": "产品岗的 35 岁危机?", "kp": ["存在", "专家路径", "管理路径", "创业"]},
        {"q": "如何判断自己适合产品岗?", "kp": ["用户思维", "数据敏感", "沟通强", "逻辑清晰", "好奇心"]},
        {"q": "产品岗面试的产品设计题怎么做?", "kp": ["明确目标用户", "核心场景", "关键功能", "指标"]},
        {"q": "数据敏感度怎么培养?", "kp": ["看 SQL 教程", "拆解指标", "A/B 测试", "看 DAU/MAU/留存"]},
        {"q": "产品岗的入门书籍推荐?", "kp": ["俞军产品方法论", "启示录", "用户体验要素", "简约至上"]},
        {"q": "如何做一份高质量的竞品分析?", "kp": ["选对标", "拆解功能", "对比维度", "结论建议"]},
        {"q": "产品岗和运营岗如何选?", "kp": ["产品偏策略", "运营偏执行", "看兴趣", "都接触"]},
        {"q": "产品岗需要 MBA 吗?", "kp": ["不必须", "有加分", "外企更看", "字节阿里不要求"]},
    ],
    "operation": [
        {"q": "运营岗真实一天是什么样的?", "kp": ["数据分析", "写文案", "活动", "沟通"]},
        {"q": "运营分哪几类?", "kp": ["内容运营", "用户运营", "活动运营", "增长运营", "社群运营", "短视频"]},
        {"q": "校招运营岗必备能力?", "kp": ["执行力", "数据分析", "文案", "沟通", "抗压"]},
        {"q": "小红书/B 站个人号要做吗?", "kp": ["强烈推荐", "加分项", "案例展示", "垂直深耕"]},
        {"q": "运营岗如何写简历?", "kp": ["量化结果", "项目案例", "数据指标", "增长曲线"]},
        {"q": "运营岗的薪资范围?", "kp": ["15-30 万", "看公司", "看赛道"]},
        {"q": "运营如何转产品?", "kp": ["产品感", "数据驱动", "完整闭环", "案例积累"]},
        {"q": "内容运营怎么做?", "kp": ["选题", "文案", "渠道", "数据复盘"]},
        {"q": "用户增长怎么做?", "kp": ["AARRR 漏斗", "拉新", "激活", "留存", "变现", "传播"]},
        {"q": "活动运营的关键点?", "kp": ["目标", "预算", "流程", "复盘", "数据"]},
        {"q": "如何选运营岗 offer?", "kp": ["业务", "增长空间", "团队", "薪资", "公司"]},
        {"q": "运营岗 35 岁危机?", "kp": ["存在", "转管理", "转营销", "创业"]},
        {"q": "校招运营岗的面试流程?", "kp": ["笔试", "业务面", "Leader 面", "HR 面"]},
        {"q": "运营岗面试会问什么?", "kp": ["案例分析", "活动策划", "数据复盘", "行业理解"]},
        {"q": "如何判断自己适合运营岗?", "kp": ["执行力强", "数据敏感", "沟通", "抗压", "好奇心"]},
        {"q": "运营岗的入门书籍?", "kp": ["运营之光", "增长黑客", "精益创业"]},
        {"q": "短视频运营需要什么技能?", "kp": ["拍摄", "剪辑", "脚本", "投放", "数据分析"]},
        {"q": "如何从执行岗走向策略岗?", "kp": ["主动思考", "数据复盘", "案例总结", "复利"]},
        {"q": "运营岗和市场的区别?", "kp": ["运营偏内", "市场偏外", "都重数据", "场景不同"]},
        {"q": "运营管培生值得去吗?", "kp": ["头部值得", "小公司慎选", "看项目", "看培养"]},
    ],
    "design": [
        {"q": "设计岗真实一天是什么样的?", "kp": ["画图", "评审", "用户研究", "协作"]},
        {"q": "设计岗分哪几类?", "kp": ["UI", "UX", "品牌", "插画", "动效", "交互"]},
        {"q": "校招设计岗必备能力?", "kp": ["Figma/Sketch", "UI 规范", "作品集", "沟通"]},
        {"q": "作品集如何准备?", "kp": ["3-5 个项目", "流程完整", "问题-方案", "数据验证"]},
        {"q": "没有实习经验,如何做作品集?", "kp": ["重设计项目", "完整流程", "个人项目", "开源贡献"]},
        {"q": "设计岗面试会问什么?", "kp": ["作品集介绍", "设计思路", "UX 题", "沟通"]},
        {"q": "C 端 vs B 端设计,选哪个?", "kp": ["C 端视觉重", "B 端逻辑重", "看兴趣"]},
        {"q": "AI 工具对设计师的影响?", "kp": ["工具进化", "效率提升", "UX 更值钱", "创意思维"]},
        {"q": "设计岗薪资范围?", "kp": ["20-40 万", "看公司", "看方向"]},
        {"q": "设计师需要学代码吗?", "kp": ["HTML/CSS", "动效代码", "加分项", "不强制"]},
        {"q": "如何选设计岗 offer?", "kp": ["业务", "设计团队", "成长空间", "薪资"]},
        {"q": "设计岗晋升路径?", "kp": ["初级", "高级", "专家", "设计总监"]},
        {"q": "设计岗 35 岁危机?", "kp": ["存在", "专家路径", "管理路径", "创业"]},
        {"q": "如何判断自己适合设计岗?", "kp": ["审美", "同理心", "用户视角", "细节敏感"]},
        {"q": "UX 设计师做什么?", "kp": ["用户调研", "信息架构", "原型设计", "可用性测试"]},
        {"q": "UI 设计师和 UX 设计师区别?", "kp": ["UI 视觉", "UX 逻辑", "现代融合", "全链路设计"]},
        {"q": "动效设计需要什么技能?", "kp": ["After Effects", "Principle", "Figma", "Lottie"]},
        {"q": "品牌设计 vs 互联网设计?", "kp": ["品牌传统", "互联网迭代快", "都重审美"]},
        {"q": "设计岗的入门书籍?", "kp": ["设计心理学", "简约至上", "用户体验要素", "About Face"]},
        {"q": "校招设计岗的简历如何写?", "kp": ["作品集链接", "项目", "实习", "技能"]},
    ],
    "data": [
        {"q": "数据分析师真实一天是什么样的?", "kp": ["SQL/Python", "报告", "业务沟通", "会议"]},
        {"q": "数据岗分哪几类?", "kp": ["业务分析", "数据科学", "算法", "数据工程", "BI"]},
        {"q": "校招数据岗必备技能?", "kp": ["SQL", "Python", "统计学", "业务理解", "沟通"]},
        {"q": "SQL 刷到什么程度够用?", "kp": ["窗口函数", "复杂查询", "性能优化", "每日一题"]},
        {"q": "数据分析师需要会算法吗?", "kp": ["基础统计", "传统 ML", "不需要深度学习", "业务理解"]},
        {"q": "数据岗薪资范围?", "kp": ["25-45 万", "看公司", "看方向"]},
        {"q": "数据分析师和数据科学家区别?", "kp": ["分析师业务", "科学家算法", "技能栈不同"]},
        {"q": "如何从取数机器变业务伙伴?", "kp": ["懂业务", "主动思考", "数据故事", "沟通"]},
        {"q": "A/B 测试怎么做?", "kp": ["假设", "分流", "指标", "统计显著", "结论"]},
        {"q": "数据可视化用什么工具?", "kp": ["Tableau", "Power BI", "Superset", "Python 可视化"]},
        {"q": "数据岗晋升路径?", "kp": ["分析师", "高级", "科学家", "经理", "总监"]},
        {"q": "数据岗 35 岁危机?", "kp": ["存在", "业务专家", "管理路径", "创业"]},
        {"q": "如何选数据岗 offer?", "kp": ["业务", "数据量", "团队", "成长", "薪资"]},
        {"q": "数据岗面试会问什么?", "kp": ["SQL 题", "统计学", "案例分析", "业务理解"]},
        {"q": "统计学需要学到什么程度?", "kp": ["假设检验", "回归", "AB 测试", "因果推断"]},
        {"q": "Python 数据分析需要哪些库?", "kp": ["Pandas", "NumPy", "Matplotlib", "Scikit-learn"]},
        {"q": "业务理解怎么培养?", "kp": ["看行业报告", "拆解指标", "主动问业务", "看研报"]},
        {"q": "数据仓库需要了解吗?", "kp": ["加分项", "不强制", "Hive/Spark"]},
        {"q": "数据岗的入门书籍?", "kp": ["深入浅出数据分析", "统计学", "精益数据分析"]},
        {"q": "数据分析师如何转算法?", "kp": ["补 ML", "刷题", "论文", "项目"]},
    ],
    "finance": [
        {"q": "金融行业真实一天是什么样的?", "kp": ["Excel", "PPT", "会议", "客户", "出差"]},
        {"q": "金融细分赛道有哪些?", "kp": ["投行", "券商", "基金", "银行", "保险", "PE/VC", "咨询"]},
        {"q": "投行降薪是真的吗?", "kp": ["是", "降 30-50%", "但仍是顶薪", "应届仍香"]},
        {"q": "校招金融岗必备技能?", "kp": ["Excel", "估值建模", "行业研究", "Wind", "英语"]},
        {"q": "金融岗薪资范围?", "kp": ["30-80 万", "投行顶薪", "基金高", "银行中"]},
        {"q": "CFA/FRM 证书有用吗?", "kp": ["加分项", "不强制", "看岗位", "考证周期长"]},
        {"q": "金融行业 35 岁危机?", "kp": ["存在", "MD 前淘汰", "转型", "或坚持"]},
        {"q": "如何选金融岗 offer?", "kp": ["平台", "业务", "团队", "薪资", "退出路径"]},
        {"q": "投行的工作强度?", "kp": ["高", "加班多", "项目制", "WLB 差"]},
        {"q": "量化方向值得入吗?", "kp": ["高薪", "门槛高", "数学+编程", "竞争激烈"]},
        {"q": "PE/VC 和投行区别?", "kp": ["PE/VC 投资", "投行融资", "都高薪", "PE/VC 退出少"]},
        {"q": "金融行业校招看重什么?", "kp": ["学校", "实习", "证书", "技能", "性格"]},
        {"q": "金融行业需要 MBA 吗?", "kp": ["投行 PE 有用", "券商基金不必须"]},
        {"q": "如何准备金融行业校招?", "kp": ["头部实习", "证书", "建模比赛", "案例分析"]},
        {"q": "银行 vs 投行 vs 基金?", "kp": ["银行稳", "投行累", "基金高薪", "看个人"]},
        {"q": "金融行业转行容易吗?", "kp": ["难", "退出路径窄", "可转咨询/投资/创业"]},
        {"q": "金融行业英语要求?", "kp": ["外资高", "内资中", "雅思托福加分"]},
        {"q": "金融行业的入门书籍?", "kp": ["公司金融", "投资学", "估值", "行业研究"]},
        {"q": "金融行业女性友好吗?", "kp": ["投行累但女性不少", "基金研究女性多", "看岗位"]},
        {"q": "金融行业未来 5 年趋势?", "kp": ["资管崛起", "投行降薪", "数字化", "监管严"]},
    ],
    "consulting": [
        {"q": "咨询行业真实一天?", "kp": ["PPT", "客户访谈", "出差", "数据", "会议"]},
        {"q": "MBB 校招看重什么?", "kp": ["学校", "案例面试", "英语", "实习", "沟通"]},
        {"q": "案例面试怎么准备?", "kp": ["Case in Point", "练 50+ case", "market sizing", "profitability"]},
        {"q": "咨询的晋升路径?", "kp": ["Consultant", "Manager", "Senior Manager", "Partner"]},
        {"q": "咨询薪资范围?", "kp": ["25-50 万 MBB 校招", "看公司", "看地区"]},
        {"q": "咨询行业 35 岁危机?", "kp": ["存在", "转 MD 难", "退出路径广"]},
        {"q": "咨询的退出路径?", "kp": ["转甲方", "PE/VC", "创业", "投行"]},
        {"q": "咨询行业工作强度?", "kp": ["高", "项目制", "加班多", "出差多"]},
        {"q": "如何选咨询 offer?", "kp": ["MBB > 其他", "战略 > 数字化", "项目", "团队"]},
        {"q": "MBB 校招案例面试怎么练?", "kp": ["每日 1 case", "找伙伴", "mock", "结构化"]},
        {"q": "咨询和投行怎么选?", "kp": ["看兴趣", "看 WLB", "看退出", "都累"]},
        {"q": "咨询行业需要 MBA 吗?", "kp": ["MBB 强需求", "必备", "MBA 后跳甲方"]},
        {"q": "咨询行业英语要求?", "kp": ["MBB 必备", "口语流利", "写作专业"]},
        {"q": "战略咨询和数字化咨询区别?", "kp": ["战略偏业务", "数字化偏技术", "都高薪"]},
        {"q": "咨询行业入门书籍?", "kp": ["Case in Point", "咨询的奥秘", "麦肯锡方法"]},
        {"q": "咨询行业校招流程?", "kp": ["网申", "笔试", "案例面试", "Superday", "Offer"]},
        {"q": "咨询行业需要什么样的特质?", "kp": ["结构化思维", "沟通", "抗压", "学习快", "好奇"]},
        {"q": "咨询行业未来趋势?", "kp": ["数字化", "ESG", "中国本土咨询崛起", "AI 工具"]},
        {"q": "咨询行业女性友好吗?", "kp": ["MBB 友好", "晋升透明", "Work-Life 改善中"]},
        {"q": "咨询转甲方合适吗?", "kp": ["很常见", "战略部", "PMO", "CEO 办公室"]},
    ],
    "fmcg": [
        {"q": "快消行业真实一天?", "kp": ["会议", "跨部门", "数据", "活动", "营销"]},
        {"q": "快消管培生值得去吗?", "kp": ["值得", "培养体系", "快成长", "但 3-5 年留存率低"]},
        {"q": "宝洁八大问是什么?", "kp": ["领导力", "创新", "效率", "执行力", "团队", "决策", "服务", "诚信"]},
        {"q": "如何准备宝洁八大问?", "kp": ["STAR 法则", "具体例子", "量化结果", "真实"]},
        {"q": "快消和互联网怎么选?", "kp": ["快消稳", "互联网累但快", "看 WLB", "看薪资"]},
        {"q": "快消薪资范围?", "kp": ["18-35 万管培", "看公司", "看品牌"]},
        {"q": "快消管培的轮岗?", "kp": ["销售", "市场", "供应链", "财务", "2-3 年"]},
        {"q": "快消 35 岁危机?", "kp": ["存在", "品牌总监", "CMO", "退出创业"]},
        {"q": "如何选快消 offer?", "kp": ["品牌", "公司", "培养", "薪资", "团队"]},
        {"q": "快消管培留存率低的原因?", "kp": ["强度大", "天花板", "薪资", "机会成本", "个人选择"]},
        {"q": "宝洁 vs 联合利华?", "kp": ["宝洁传统强", "联合利华数字化", "都顶"]},
        {"q": "快消转互联网容易吗?", "kp": ["可以", "市场→营销", "品牌→产品", "供应链→运营"]},
        {"q": "快消校招看重什么?", "kp": ["学校", "英语", "商业思维", "领导力", "实习"]},
        {"q": "快消行业入门书籍?", "kp": ["品牌洗脑", "定位", "营销管理"]},
        {"q": "数字营销在快消行业的重要性?", "kp": ["越来越重要", "DTC 趋势", "数据驱动", "新机会"]},
        {"q": "快消行业晋升路径?", "kp": ["管培", "品牌经理", "高级", "市场总监", "CMO"]},
        {"q": "快消行业工作强度?", "kp": ["中等", "项目制", "加班", "WLB 中"]},
        {"q": "快消行业需要 MBA 吗?", "kp": ["不必须", "MKT 总监有加分"]},
        {"q": "快消行业的退出路径?", "kp": ["品牌咨询", "创业", "互联网营销", "投资"]},
        {"q": "快消管培 3-5 年后会怎样?", "kp": ["品牌经理", "转行", "读 MBA", "创业"]},
    ],
    "realestate": [
        {"q": "地产行业真实一天?", "kp": ["现场", "会议", "文档", "销售", "客户"]},
        {"q": "地产行业现状?", "kp": ["整体收缩", "分化", "代建/物业/商业还在招"]},
        {"q": "地产细分赛道怎么选?", "kp": ["代建稳", "物业需求", "商业高端", "看兴趣"]},
        {"q": "校招地产岗必备能力?", "kp": ["工程/管理背景", "沟通", "抗压", "项目感"]},
        {"q": "地产薪资范围?", "kp": ["15-30 万", "看公司", "看区域"]},
        {"q": "地产 35 岁危机?", "kp": ["严重", "项目总难", "转型", "退出"]},
        {"q": "如何选地产 offer?", "kp": ["公司", "业务", "区域", "薪资", "退出"]},
        {"q": "地产管培生项目?", "kp": ["万科/龙湖/华润/中海 强", "培养体系", "2-3 年轮岗"]},
        {"q": "地产和互联网怎么选?", "kp": ["地产传统", "互联网新", "看 WLB", "看行业"]},
        {"q": "地产行业未来 5 年?", "kp": ["整体收缩", "分化", "代建崛起", "数字化"]},
        {"q": "地产转行容易吗?", "kp": ["可以", "转建筑/物业/投资"]},
        {"q": "地产行业入门书籍?", "kp": ["地产行业研究", "项目运营"]},
        {"q": "地产行业需要什么证书?", "kp": ["不强制", "建造师/造价师 加分"]},
        {"q": "地产行业英语要求?", "kp": ["低", "本土化强", "外资有要求"]},
        {"q": "地产校招看重什么?", "kp": ["学校", "专业", "实习", "性格", "稳定性"]},
        {"q": "地产行业工作强度?", "kp": ["高", "项目制", "加班", "应酬"]},
        {"q": "地产晋升路径?", "kp": ["管培", "项目经理", "项目总", "区域总", "集团"]},
        {"q": "地产行业女性友好吗?", "kp": ["设计/营销/人力友好", "工程/项目偏男性"]},
        {"q": "代建赛道怎么样?", "kp": ["新兴", "轻资产", "WLB 好", "发展稳"]},
        {"q": "地产退出路径?", "kp": ["物业", "建筑", "投资", "创业", "公务员"]},
    ],
}


# ============== 数据模型 ==============

@dataclass
class IndustryQuestion:
    """行业问题"""
    industry: str         # industry id
    text: str
    key_points: List[str]
    difficulty: int = 2


@dataclass
class AnswerResult:
    """回答结果(简化版,复用 interview 的逻辑)"""
    question: str
    answer: str
    key_points_hit: List[str] = field(default_factory=list)
    key_points_missed: List[str] = field(default_factory=list)
    score: float = 0.0
    feedback: str = ""
    logic: float = 0.0
    expression: float = 0.0
    depth: float = 0.0
    adaptability: float = 0.0
    fit: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IndustrySession:
    """行业洞察对话 session"""
    industry: str
    questions: List[IndustryQuestion] = field(default_factory=list)
    answers: List[str] = field(default_factory=list)
    results: List[AnswerResult] = field(default_factory=list)
    round_idx: int = 0
    completed: bool = False
    started_at: float = field(default_factory=time.time)
    ended_at: float = 0.0
    user_holland_code: str = ""  # 用户 Holland Code(联动)

    def add_answer(self, answer: str, result: AnswerResult):
        self.answers.append(answer)
        self.results.append(result)
        self.round_idx += 1
        if self.round_idx >= len(self.questions):
            self.completed = True
            self.ended_at = time.time()

    def total_score(self) -> float:
        if not self.results:
            return 0.0
        return round(sum(r.score for r in self.results) / len(self.results), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "industry": self.industry,
            "user_holland_code": self.user_holland_code,
            "questions": [asdict(q) for q in self.questions],
            "answers": self.answers,
            "results": [r.to_dict() for r in self.results],
            "round_idx": self.round_idx,
            "completed": self.completed,
            "total_score": self.total_score(),
        }


# ============== 核心 API ==============

def list_industries() -> List[Dict[str, Any]]:
    """列出 9 大行业"""
    return [
        {"id": k, **{kk: vv for kk, vv in v.items() if kk != "system_prompt"}}
        for k, v in INDUSTRY_PROFILES.items()
    ]


def get_industry(industry: str) -> Dict[str, Any]:
    """获取单个行业"""
    profile = INDUSTRY_PROFILES.get(industry, INDUSTRY_PROFILES["algorithm"])
    return {"id": industry, **profile}


def get_industry_prompt(industry: str) -> str:
    """获取行业系统 Prompt"""
    return INDUSTRY_PROFILES.get(industry, INDUSTRY_PROFILES["algorithm"])["system_prompt"]


def start_industry_session(
    industry: str = "algorithm",
    rounds: int = 3,
    user_holland_code: str = "",
) -> IndustrySession:
    """开启行业洞察对话"""
    if industry not in FAQ_BANK:
        industry = "algorithm"
    # 抽取 rounds 道题
    available = FAQ_BANK[industry]
    questions = [
        IndustryQuestion(
            industry=industry,
            text=q["q"],
            key_points=q["kp"],
            difficulty=2,
        )
        for q in available[:max(1, min(rounds, len(available)))]
    ]
    return IndustrySession(
        industry=industry,
        questions=questions,
        user_holland_code=user_holland_code,
    )


def _score_answer_logic(answer: str) -> float:
    """逻辑性(复用 interview 逻辑)"""
    if not answer or len(answer.strip()) < 10:
        return 0.0
    s = answer.strip()
    struct = sum([
        bool(re.search(r"首先|第一|第二|第三|然后|接下来|最后|总之|综上", s)),
        bool(re.search(r"因为|所以|因此|但是|不过|然而", s)),
        bool(re.search(r"\n[-*]\s|\n\d+[\.、]", s)),
        s.count("。") + s.count(".") >= 3,
    ])
    return round(min(1.0, struct / 3.0), 4)


def _score_answer_expression(answer: str) -> float:
    """表达(复用 interview 逻辑)"""
    if not answer:
        return 0.0
    n = len(answer)
    if 50 <= n <= 500:
        len_score = 1.0
    elif n < 50:
        len_score = n / 50
    else:
        len_score = max(0.4, 1.0 - (n - 500) / 1000)
    sents = re.split(r"[。.!?！？\n]", answer)
    sents = [x.strip() for x in sents if x.strip()]
    if len(sents) >= 2:
        uniq = len(set(sents)) / len(sents)
    else:
        uniq = 0.5
    return round(0.6 * len_score + 0.4 * uniq, 4)


def _score_answer_depth(answer: str, key_points: List[str]) -> float:
    """深度:关键要点覆盖"""
    if not key_points:
        return 0.5
    answer_lower = answer.lower()
    hit = 0
    for kp in key_points:
        kp_words = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+", kp)
        if any(w.lower() in answer_lower for w in kp_words if len(w) > 1):
            hit += 1
    return round(hit / len(key_points), 4)


def submit_answer(
    session: IndustrySession,
    answer: str,
) -> AnswerResult:
    """提交回答 + 5 维评分"""
    if session.completed:
        raise ValueError("Session already completed")
    if session.round_idx >= len(session.questions):
        raise ValueError("No more questions")
    q = session.questions[session.round_idx]
    # 5 维
    logic = _score_answer_logic(answer)
    expression = _score_answer_expression(answer)
    depth = _score_answer_depth(answer, q.key_points)
    # 应变 + 匹配度(简化:应变=0.7 默认,匹配度=0.5 默认)
    adaptability = 0.7 if answer else 0.0
    fit = 0.5
    # 加权
    score = round(
        0.20 * logic + 0.15 * expression + 0.30 * depth
        + 0.15 * adaptability + 0.20 * fit,
        4,
    )
    # 命中/漏掉
    answer_lower = answer.lower()
    hit, miss = [], []
    for kp in q.key_points:
        kp_words = re.findall(r"[\u4e00-\u9fff]+|[a-zA-Z]+", kp)
        if any(w.lower() in answer_lower for w in kp_words if len(w) > 1):
            hit.append(kp)
        else:
            miss.append(kp)
    # 反馈
    if score >= 0.8:
        fb = f"👍 优秀回答({score:.0%})。"
    elif score >= 0.6:
        fb = f"✓ 中等回答({score:.0%})。"
    else:
        fb = f"⚠️ 较弱回答({score:.0%})。"
    if hit:
        fb += f" 命中:{' / '.join(hit[:3])}"
    if miss:
        fb += f" 补充:{' / '.join(miss[:3])}"
    result = AnswerResult(
        question=q.text,
        answer=answer,
        key_points_hit=hit,
        key_points_missed=miss,
        score=score,
        feedback=fb,
        logic=logic, expression=expression, depth=depth,
        adaptability=adaptability, fit=fit,
    )
    session.add_answer(answer, result)
    return result


# ============== Holland Code 匹配 ==============

def recommend_industries_for_holland(holland_code: str) -> List[Dict[str, Any]]:
    """基于 Holland Code 推荐行业(按匹配度排序)"""
    if not holland_code:
        return []
    code_set = set(holland_code.upper())
    scored = []
    for ind_id, profile in INDUSTRY_PROFILES.items():
        fit_dims = profile.get("holland_fit", [])
        # 计算 code ∩ fit_dims 的比例
        overlap = len(code_set & set(fit_dims))
        match = overlap / max(1, len(fit_dims))
        scored.append({
            "industry": ind_id,
            "name": profile["name"],
            "emoji": profile["emoji"],
            "match_score": round(match, 4),
        })
    # 按匹配度降序
    scored.sort(key=lambda x: -x["match_score"])
    return scored


# ============== 行业问答(无 LLM 模式) ==============

def answer_industry_question(
    industry: str,
    question: str,
) -> Dict[str, Any]:
    """
    行业问答(基于规则 + FAQ 匹配)。
    返回:匹配的 FAQ + 行业画像 + 建议
    """
    if industry not in INDUSTRY_PROFILES:
        industry = "algorithm"
    profile = INDUSTRY_PROFILES[industry]
    # FAQ 匹配
    faqs = FAQ_BANK.get(industry, [])
    matched = None
    best_score = 0
    # 中文 2-gram + 英文单词
    def tokenize(s: str) -> set:
        zh = re.findall(r"[\u4e00-\u9fff]+", s)
        en = re.findall(r"[a-zA-Z]+", s.lower())
        grams = set()
        for s_zh in zh:
            for i in range(len(s_zh) - 1):
                grams.add(s_zh[i:i+2])
        grams.update(en)
        return grams
    for faq in faqs:
        q_tokens = tokenize(faq["q"])
        in_tokens = tokenize(question)
        overlap = len(q_tokens & in_tokens)
        if overlap > best_score:
            best_score = overlap
            matched = faq
    return {
        "industry": industry,
        "industry_name": profile["name"],
        "question": question,
        "matched_faq": matched["q"] if matched else None,
        "key_points": matched["kp"] if matched else [],
        "suggestion": (
            f"建议从以下角度回答:{', '.join(matched['kp'])}"
            if matched else "未找到匹配 FAQ,建议看行业画像"
        ),
        "industry_profile": {
            "top_companies": profile["top_companies"][:3],
            "salary_range": profile["salary_range_2025"],
            "career_path": profile["career_path"],
            "typical_day": profile["typical_day"],
        },
    }


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 industry_insight.py {industries|profile|start|recommend|faq <industry>}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "industries":
        for i in list_industries():
            print(f"  {i['emoji']} {i['id']:12s} - {i['name']}")
    elif cmd == "profile":
        if len(sys.argv) < 3:
            print("Need industry id", file=sys.stderr)
            sys.exit(1)
        print(json.dumps(get_industry(sys.argv[2]), ensure_ascii=False, indent=2))
    elif cmd == "start":
        ind = sys.argv[2] if len(sys.argv) > 2 else "algorithm"
        rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 3
        s = start_industry_session(ind, rounds=rounds)
        print(json.dumps({
            "industry": ind,
            "rounds": len(s.questions),
            "first_question": s.questions[0].text if s.questions else None,
        }, ensure_ascii=False, indent=2))
    elif cmd == "recommend":
        code = sys.argv[2] if len(sys.argv) > 2 else ""
        recs = recommend_industries_for_holland(code)
        for r in recs:
            print(f"  {r['emoji']} {r['industry']:12s} - {r['name']}  匹配度 {r['match_score']:.0%}")
    elif cmd == "faq":
        ind = sys.argv[2] if len(sys.argv) > 2 else "algorithm"
        for faq in FAQ_BANK.get(ind, []):
            print(f"  Q: {faq['q']}")
            print(f"     KP: {' / '.join(faq['kp'])}")
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
