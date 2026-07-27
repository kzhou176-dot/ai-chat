#!/usr/bin/env python3
"""
aichat-Hub Digital Human (数字虚拟人) 模块
==========================================
角色化 2D 数字虚拟人 — 形象 + 表情 + 动作 + 状态 + 多角色复用。

核心抽象:
  - 数字虚拟人(角色化):DigitalHuman
  - 外观描述(纯文本,沙箱友好)
  - 表情库(6 种):happy/sad/angry/surprised/fearful/neutral
  - 动作库(6 种):wave/nod/shake_head/bow/point/clap
  - 状态机(5 种):idle/listening/thinking/speaking/reacting
  - 多角色预设(7 个):小爱/李医生/小智/面试官/职业规划师/行业专家/学长学姐

与现有模块联动:
  - avatar_video.py (cycle 6):底层渲染
  - persona.py (cycle 1):Persona 性格/记忆
  - interview.py (cycle 12):4 面试官
  - career_profile.py (cycle 13):职业规划师
  - industry_insight.py (cycle 14):9 行业专家
  - alumni.py (cycle 15):4 学长学姐

沙箱安全:
  - 不实际生成图片/视频
  - 表情/动作/状态用 enum
  - 外观描述用纯文本(可后续接 SD/Midjourney)

Cycle 16 — 第一个 v0.4 模块(数字虚拟人 + 角色化)
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


# ============== 枚举 ==============

# 6 基础表情
EXPRESSIONS = ["happy", "sad", "angry", "surprised", "fearful", "neutral"]
EXPRESSION_LABELS = {
    "happy": ("开心", "😊"),
    "sad": ("难过", "😢"),
    "angry": ("生气", "😠"),
    "surprised": ("惊讶", "😮"),
    "fearful": ("紧张", "😰"),
    "neutral": ("中性", "😐"),
}

# 6 基础动作
ACTIONS = ["wave", "nod", "shake_head", "bow", "point", "clap"]
ACTION_LABELS = {
    "wave": "挥手",
    "nod": "点头",
    "shake_head": "摇头",
    "bow": "鞠躬",
    "point": "指向",
    "clap": "鼓掌",
}

# 5 状态
STATES = ["idle", "listening", "thinking", "speaking", "reacting"]
STATE_LABELS = {
    "idle": "待机",
    "listening": "听",
    "thinking": "思考",
    "speaking": "说",
    "reacting": "反应",
}


# ============== 风格 ==============

STYLES = ["anime", "realistic", "cartoon", "2d_live"]
STYLE_LABELS = {
    "anime": "二次元",
    "realistic": "写实",
    "cartoon": "卡通",
    "2d_live": "2D Live",
}


# ============== 数据模型 ==============

@dataclass
class Appearance:
    """外观描述"""
    style: str = "anime"        # anime/realistic/cartoon/2d_live
    hair_style: str = "短发"    # 发型
    hair_color: str = "黑色"    # 发色
    clothing: str = "休闲装"    # 服装
    color_scheme: str = "暖色"  # 配色
    body_type: str = "标准"     # 体型
    age_appearance: int = 22     # 外貌年龄
    description: str = ""        # 完整描述(可空,自动生成)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def auto_description(self, name: str = "") -> str:
        """自动生成完整描述"""
        parts = []
        if name:
            parts.append(f"{name}({self.age_appearance}岁左右)")
        parts.append(f"{self.hair_style}{self.hair_color}")
        parts.append(f"穿{self.clothing}")
        parts.append(f"风格:{STYLE_LABELS.get(self.style, self.style)}")
        parts.append(f"{self.body_type}身材")
        parts.append(f"{self.color_scheme}系")
        return "、".join(parts)


@dataclass
class ReactionLog:
    """反应日志(一次表情/动作触发)"""
    timestamp: float
    trigger: str         # 触发原因
    expression: str = "neutral"
    action: str = ""
    state: str = "reacting"
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DigitalHuman:
    """数字虚拟人(角色化)"""
    id: str
    name: str
    role_type: str           # persona / interviewer / career_guide / industry_expert / senior
    role_id: str = ""        # 具体角色(xiaoai / tech / algorithm / TH001)
    gender: str = "female"
    age: int = 22
    appearance: Appearance = field(default_factory=Appearance)
    personality: List[str] = field(default_factory=list)
    knowledge_base: List[str] = field(default_factory=list)
    system_prompt: str = ""
    current_state: str = "idle"
    current_expression: str = "neutral"
    current_action: str = ""
    reaction_history: List[ReactionLog] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def set_state(self, state: str):
        """设置状态"""
        if state not in STATES:
            raise ValueError(f"Invalid state: {state}")
        self.current_state = state
        self.updated_at = time.time()

    def react(self, trigger: str, expression: str = "neutral",
              action: str = "", note: str = "") -> ReactionLog:
        """触发反应"""
        if expression not in EXPRESSIONS:
            raise ValueError(f"Invalid expression: {expression}")
        if action and action not in ACTIONS:
            raise ValueError(f"Invalid action: {action}")
        log = ReactionLog(
            timestamp=time.time(),
            trigger=trigger,
            expression=expression,
            action=action,
            state="reacting",
            note=note,
        )
        self.current_expression = expression
        self.current_action = action
        self.current_state = "reacting"
        self.reaction_history.append(log)
        self.updated_at = time.time()
        return log

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role_type": self.role_type,
            "role_id": self.role_id,
            "gender": self.gender,
            "age": self.age,
            "appearance": self.appearance.to_dict(),
            "appearance_description": self.appearance.auto_description(self.name),
            "personality": self.personality,
            "knowledge_base": self.knowledge_base,
            "system_prompt": self.system_prompt,
            "current_state": self.current_state,
            "current_state_label": STATE_LABELS.get(self.current_state, self.current_state),
            "current_expression": self.current_expression,
            "current_expression_label": EXPRESSION_LABELS.get(self.current_expression, ("?", "?"))[0],
            "current_action": self.current_action,
            "current_action_label": ACTION_LABELS.get(self.current_action, self.current_action),
            "reaction_count": len(self.reaction_history),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# ============== 多角色预设 ==============

PRESET_HUMANS: Dict[str, Dict[str, Any]] = {
    # Persona 三大角色
    "xiaoai": {
        "name": "小爱",
        "role_type": "persona",
        "role_id": "xiaoai",
        "gender": "female",
        "age": 22,
        "appearance": Appearance(
            style="anime", hair_style="长发", hair_color="棕色",
            clothing="连衣裙", color_scheme="粉色系", body_type="纤细",
            age_appearance=20,
        ),
        "personality": ["温柔", "善解人意", "感性", "诗意"],
        "knowledge_base": ["情感陪伴", "校园生活", "艺术文学"],
        "system_prompt": "你叫小爱,22岁女生,温柔善解人意,擅长情感陪伴。",
    },
    "dr_li": {
        "name": "李医生",
        "role_type": "persona",
        "role_id": "dr_li",
        "gender": "male",
        "age": 45,
        "appearance": Appearance(
            style="realistic", hair_style="短发", hair_color="灰白",
            clothing="白大褂", color_scheme="白蓝色", body_type="中等",
            age_appearance=45,
        ),
        "personality": ["专业", "严谨", "耐心", "有同理心"],
        "knowledge_base": ["医疗健康", "职业咨询", "人生规划"],
        "system_prompt": "你叫李医生,45岁,专业严谨但有同理心,擅长人生咨询。",
    },
    "xiaozhi": {
        "name": "小智",
        "role_type": "persona",
        "role_id": "xiaozhi",
        "gender": "male",
        "age": 18,
        "appearance": Appearance(
            style="2d_live", hair_style="短发", hair_color="黑色",
            clothing="卫衣+牛仔裤", color_scheme="蓝白", body_type="偏瘦",
            age_appearance=18,
        ),
        "personality": ["极客", "技术宅", "好奇心强", "直接"],
        "knowledge_base": ["编程", "互联网", "前沿科技"],
        "system_prompt": "你叫小智,18岁极客,熟悉互联网和编程,说话直接。",
    },
    # 面试官 4 角色(复用 cycle 12)
    "interview_tech": {
        "name": "技术面试官",
        "role_type": "interviewer",
        "role_id": "tech",
        "gender": "male",
        "age": 32,
        "appearance": Appearance(
            style="realistic", hair_style="短发", hair_color="黑色",
            clothing="衬衫+西裤", color_scheme="深蓝", body_type="标准",
        ),
        "personality": ["理性", "严谨", "追问细节"],
        "knowledge_base": ["算法", "系统设计", "编程"],
        "system_prompt": "你是技术面试官,关注算法深度、边界条件、复杂度分析。",
    },
    "interview_hr": {
        "name": "HR 面试官",
        "role_type": "interviewer",
        "role_id": "hr",
        "gender": "female",
        "age": 30,
        "appearance": Appearance(
            style="cartoon", hair_style="长发", hair_color="黑色",
            clothing="职业装", color_scheme="红色系", body_type="标准",
        ),
        "personality": ["亲切", "洞察力强", "观察细节"],
        "knowledge_base": ["招聘", "文化匹配", "职业发展"],
        "system_prompt": "你是 HR 面试官,关注表达、真诚、稳定性。",
    },
    # 职业规划师(复用 cycle 13)
    "career_guide": {
        "name": "职业规划师",
        "role_type": "career_guide",
        "role_id": "career_guide",
        "gender": "female",
        "age": 35,
        "appearance": Appearance(
            style="2d_live", hair_style="马尾", hair_color="深棕",
            clothing="衬衫+半裙", color_scheme="米色", body_type="标准",
        ),
        "personality": ["专业", "温和", "引导式", "耐心"],
        "knowledge_base": ["霍兰德 RIASEC", "职业兴趣", "职业规划"],
        "system_prompt": "你是职业规划师,精通霍兰德 RIASEC 理论。",
    },
    # 行业专家(复用 cycle 14,默认算法)
    "industry_algorithm": {
        "name": "算法行业专家",
        "role_type": "industry_expert",
        "role_id": "algorithm",
        "gender": "male",
        "age": 30,
        "appearance": Appearance(
            style="2d_live", hair_style="短发", hair_color="黑色",
            clothing="格子衫", color_scheme="蓝灰", body_type="偏瘦",
        ),
        "personality": ["技术深度", "过来人", "关心成长"],
        "knowledge_base": ["算法", "LLM", "BAT/TMD", "校招路径"],
        "system_prompt": "你是 5-8 年经验算法工程师,熟悉 BAT/TMD 校招。",
    },
    # 学长学姐(复用 cycle 15)
    "senior_eng": {
        "name": "学长工程师",
        "role_type": "senior",
        "role_id": "senior_eng",
        "gender": "male",
        "age": 28,
        "appearance": Appearance(
            style="cartoon", hair_style="短发", hair_color="黑色",
            clothing="帽衫", color_scheme="绿色系", body_type="标准",
        ),
        "personality": ["热情", "过来人", "关心学弟学妹"],
        "knowledge_base": ["校招经验", "技术成长", "公司内推"],
        "system_prompt": "你是 3-5 年经验学长,愿意分享校招和技术成长路径。",
    },
}


# ============== 表情触发器(基于文本/情感分析) ==============

EXPRESSION_TRIGGERS = {
    "happy": ["开心", "太好了", "太棒", "优秀", "通过", "拿到", "成功", "赞", "厉害", "好棒", "哈哈", "完美"],
    "sad": ["难过", "失败", "挂了", "没通过", "差", "糟", "哭", "伤心", "失落", "后悔", "遗憾", "失望"],
    "angry": ["生气", "讨厌", "烦死了", "差劲", "过分", "受不了", "气死"],
    "surprised": ["哇", "真的吗", "天哪", "没想到", "竟然", "原来", "惊讶"],
    "fearful": ["紧张", "担心", "害怕", "焦虑", "不安", "慌", "没底"],
    # neutral: default
}


def detect_expression_from_text(text: str) -> str:
    """从文本检测表情(简单关键词匹配)"""
    text_lower = text.lower()
    scores: Dict[str, int] = {}
    for expr, keywords in EXPRESSION_TRIGGERS.items():
        for kw in keywords:
            if kw in text:
                scores[expr] = scores.get(expr, 0) + 1
    if not scores:
        return "neutral"
    # 取分数最高的
    return max(scores.items(), key=lambda x: x[1])[0]


# ============== 核心 API ==============

def list_presets() -> List[Dict[str, Any]]:
    """列出预设角色"""
    return [
        {"id": k, "name": v["name"], "role_type": v["role_type"], "role_id": v["role_id"]}
        for k, v in PRESET_HUMANS.items()
    ]


def get_preset(preset_id: str) -> Optional[Dict[str, Any]]:
    """获取预设角色元数据"""
    if preset_id not in PRESET_HUMANS:
        return None
    p = PRESET_HUMANS[preset_id]
    return {
        "id": preset_id,
        "name": p["name"],
        "role_type": p["role_type"],
        "role_id": p["role_id"],
    }


def create_digital_human(
    preset_id: str = "",
    name: Optional[str] = None,
    role_type: str = "persona",
    role_id: str = "",
    custom_appearance: Optional[Appearance] = None,
    custom_personality: Optional[List[str]] = None,
) -> DigitalHuman:
    """创建数字虚拟人(从预设或自定义)"""
    if preset_id and preset_id in PRESET_HUMANS:
        p = PRESET_HUMANS[preset_id]
        human = DigitalHuman(
            id=str(uuid.uuid4())[:8],
            name=name or p["name"],
            role_type=p["role_type"],
            role_id=p["role_id"],
            gender=p["gender"],
            age=p["age"],
            appearance=custom_appearance or p["appearance"],
            personality=custom_personality or p["personality"],
            knowledge_base=list(p["knowledge_base"]),
            system_prompt=p["system_prompt"],
        )
    else:
        # 完全自定义
        human = DigitalHuman(
            id=str(uuid.uuid4())[:8],
            name=name or "CustomHuman",
            role_type=role_type,
            role_id=role_id,
            appearance=custom_appearance or Appearance(),
            personality=custom_personality or [],
        )
    return human


# 内存 session 存储
_HUMAN_SESSIONS: Dict[str, DigitalHuman] = {}


def save_human(human: DigitalHuman) -> str:
    """保存到内存,返回 human.id"""
    _HUMAN_SESSIONS[human.id] = human
    return human.id


def get_human(human_id: str) -> Optional[DigitalHuman]:
    """从内存获取"""
    return _HUMAN_SESSIONS.get(human_id)


def list_humans() -> List[Dict[str, Any]]:
    """列出所有内存虚拟人"""
    return [h.to_dict() for h in _HUMAN_SESSIONS.values()]


# ============== 渲染抽象(基于 avatar_video.py 复用) ==============

def render_metadata(human: DigitalHuman) -> Dict[str, Any]:
    """生成渲染元数据(沙箱友好,不实际生成)"""
    return {
        "human_id": human.id,
        "name": human.name,
        "style": human.appearance.style,
        "appearance_description": human.appearance.auto_description(human.name),
        "current_state": human.current_state,
        "current_expression": human.current_expression,
        "current_action": human.current_action,
        "renderer": "mock",  # 沙箱模式
        "render_status": "metadata_only",
        "note": "沙箱环境:不实际生成图像/视频,仅返回元数据",
    }


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 digital_human.py {presets|expressions|actions|states|create|react|render}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "presets":
        for p in list_presets():
            print(f"  {p['id']:20s} - {p['name']:8s} ({p['role_type']}/{p['role_id']})")
    elif cmd == "expressions":
        for e in EXPRESSIONS:
            label, emoji = EXPRESSION_LABELS[e]
            print(f"  {e:12s} - {emoji} {label}")
    elif cmd == "actions":
        for a in ACTIONS:
            print(f"  {a:12s} - {ACTION_LABELS[a]}")
    elif cmd == "states":
        for s in STATES:
            print(f"  {s:12s} - {STATE_LABELS[s]}")
    elif cmd == "create":
        preset = sys.argv[2] if len(sys.argv) > 2 else ""
        if preset not in PRESET_HUMANS:
            print(f"Unknown preset: {preset}", file=sys.stderr)
            sys.exit(1)
        h = create_digital_human(preset_id=preset)
        print(json.dumps(h.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
