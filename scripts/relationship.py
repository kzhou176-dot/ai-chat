#!/usr/bin/env python3
"""
aichat-hub Relationship (关系阶段) 模块
======================================
为虚拟人提供"关系深度"建模,影响:
  - 称呼(您→你→宝贝)
  - 互动风格(礼貌→随意→亲昵)
  - 记忆 recall 阈值(陌生人召回少,亲密召回多)
  - 解锁的互动(拥抱/亲吻/私密话题)

设计目标:
  - 4 阶段:stranger → acquaintance → friend → intimate
  - 基于互动信号(消息数/深度对话次数/天数/情感得分)自动晋升
  - 可与 Persona 集成(to_system_prompt 注入关系上下文)

Cycle 3 - 基础版
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any


class Stage(str, Enum):
    """关系阶段"""
    STRANGER = "stranger"           # 陌生人
    ACQUAINTANCE = "acquaintance"   # 熟人
    FRIEND = "friend"               # 朋友
    INTIMATE = "intimate"           # 亲密

    @classmethod
    def from_int(cls, level: int) -> "Stage":
        """level 0-30 映射到阶段"""
        if level < 5:
            return cls.STRANGER
        elif level < 15:
            return cls.ACQUAINTANCE
        elif level < 25:
            return cls.FRIEND
        else:
            return cls.INTIMATE


# 阶段元数据
STAGE_META = {
    Stage.STRANGER: {
        "level_range": (0, 5),
        "label_zh": "陌生人",
        "address": "您",
        "tone": "礼貌、正式、保持距离",
        "memory_threshold": 0.3,  # 记忆 recall 阈值高(只记重要)
        "unlocked": ["基础对话", "自我介绍"],
        "color": "🔵",
    },
    Stage.ACQUAINTANCE: {
        "level_range": (5, 15),
        "label_zh": "熟人",
        "address": "你",
        "tone": "友好、轻松、开始关心",
        "memory_threshold": 0.15,
        "unlocked": ["日常问候", "分享兴趣", "记住对方基本信息"],
        "color": "🟢",
    },
    Stage.FRIEND: {
        "level_range": (15, 25),
        "label_zh": "朋友",
        "address": "你",
        "tone": "随意、互怼、分享心事",
        "memory_threshold": 0.08,
        "unlocked": ["深度话题", "情感支持", "记住历史事件", "开玩笑"],
        "color": "🟡",
    },
    Stage.INTIMATE: {
        "level_range": (25, 30),
        "label_zh": "亲密",
        "address": "亲爱的 / 宝贝 / 名字",
        "tone": "亲昵、撒娇、深度共情",
        "memory_threshold": 0.03,
        "unlocked": ["私密话题", "情感宣泄", "未来规划", "昵称"],
        "color": "🔴",
    },
}


@dataclass
class Interaction:
    """一次互动记录"""
    ts: float
    user_msg: str
    bot_msg: str
    emotion: str = "neutral"  # happy/sad/angry/neutral/surprised/loving
    depth: int = 1  # 1-5(5=最深)
    topics: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Relationship:
    """关系状态"""
    user_id: str
    persona_name: str
    level: int = 0  # 0-30
    total_messages: int = 0
    days_together: int = 0
    deep_conversations: int = 0  # depth >= 3 的次数
    positive_emotions: int = 0   # happy/loving
    negative_emotions: int = 0   # sad/angry
    nickname_given: Optional[str] = None  # 用户给虚拟人起的昵称
    special_moments: List[str] = field(default_factory=list)  # 关键时刻
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    @property
    def stage(self) -> Stage:
        return Stage.from_int(self.level)

    @property
    def meta(self) -> Dict[str, Any]:
        return STAGE_META[self.stage]

    @property
    def progress_pct(self) -> float:
        """当前阶段内进度 0-100"""
        lo, hi = STAGE_META[self.stage]["level_range"]
        if hi == lo:
            return 100.0
        return min(100.0, (self.level - lo) / (hi - lo) * 100)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["stage"] = self.stage.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Relationship":
        d.pop("stage", None)
        return cls(**d)


class RelationshipEngine:
    """关系推进引擎"""

    def __init__(self, persona_name: str, user_id: str = "default",
                 root: Path = None):
        self.persona_name = persona_name
        self.user_id = user_id
        self.root = root or Path(
            "str(Path(__file__).parent.parent)/data/relationships"
        )
        self.root.mkdir(parents=True, exist_ok=True)
        self.rel = self._load()
        self.interactions: List[Interaction] = []

    def _path(self) -> Path:
        safe_user = "".join(c for c in self.user_id if c.isalnum() or c in "-_")
        return self.root / f"{self.persona_name}__{safe_user}.json"

    def _load(self) -> Relationship:
        path = self._path()
        if not path.exists():
            return Relationship(user_id=self.user_id, persona_name=self.persona_name)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rel = Relationship.from_dict(data.get("relationship", {}))
            self.interactions = [
                Interaction(**i) for i in data.get("interactions", [])
            ]
            return rel
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[relationship] load warning: {e}")
            return Relationship(user_id=self.user_id, persona_name=self.persona_name)

    def save(self):
        data = {
            "persona_name": self.persona_name,
            "user_id": self.user_id,
            "relationship": self.rel.to_dict(),
            "interactions": [i.to_dict() for i in self.interactions[-100:]],
            "saved_at": time.time(),
        }
        self._path().write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---------- 信号打分 ----------

    def record_interaction(
        self, user_msg: str, bot_msg: str,
        emotion: str = "neutral", depth: int = 1, topics: List[str] = None
    ) -> Dict[str, Any]:
        """记录一次互动,自动计算关系变化"""
        before_stage = self.rel.stage

        inter = Interaction(
            ts=time.time(),
            user_msg=user_msg[:500],
            bot_msg=bot_msg[:500],
            emotion=emotion,
            depth=max(1, min(5, depth)),
            topics=topics or [],
        )
        self.interactions.append(inter)
        self.rel.total_messages += 1

        # 情感统计
        if emotion in ("happy", "loving"):
            self.rel.positive_emotions += 1
        elif emotion in ("sad", "angry"):
            self.rel.negative_emotions += 1

        if depth >= 3:
            self.rel.deep_conversations += 1

        # 计算 level 增量
        delta = self._calc_delta(inter)
        old_level = self.rel.level
        self.rel.level = min(30, max(0, self.rel.level + delta))
        self.rel.updated_at = time.time()

        after_stage = self.rel.stage
        promoted = before_stage != after_stage

        return {
            "delta": delta,
            "old_level": old_level,
            "new_level": self.rel.level,
            "stage": self.rel.stage.value,
            "promoted": promoted,
            "stage_label": self.rel.meta["label_zh"],
        }

    def _calc_delta(self, inter: Interaction) -> int:
        """根据互动信号计算 level 增量(正向或负向)"""
        delta = 0

        # 基础:每条消息 +0.1,深度对话额外加分
        delta += 0.1
        if inter.depth >= 2:
            delta += (inter.depth - 1) * 0.3  # depth 2→+0.3, depth 5→+1.2

        # 情感加成
        if inter.emotion == "loving":
            delta += 0.5
        elif inter.emotion == "happy":
            delta += 0.2
        elif inter.emotion == "sad":
            delta += 0.1  # 安慰也是亲密
        elif inter.emotion == "angry":
            delta -= 0.2  # 吵架扣分

        # 话题加成(私人话题)
        private_topics = {"感情", "家庭", "秘密", "未来", "梦想",
                         "love", "family", "secret", "future", "dream"}
        if any(t in private_topics for t in inter.topics):
            delta += 0.4

        return round(delta, 2)

    # ---------- 关系阶段输出 ----------

    def to_system_prompt(self) -> str:
        """生成可注入 system prompt 的关系上下文"""
        m = self.rel.meta
        parts = [
            f"【与用户的关系】:{m['color']} {m['label_zh']}({self.rel.level}/30, 阶段进度 {self.rel.progress_pct:.0f}%)",
            f"称呼:{m['address']}",
            f"语气:{m['tone']}",
            f"已解锁:{', '.join(m['unlocked'])}",
        ]
        if self.rel.nickname_given:
            parts.append(f"用户给你起的昵称:{self.rel.nickname_given}")
        if self.rel.special_moments:
            parts.append(f"共同记忆的时刻:{'; '.join(self.rel.special_moments[-3:])}")
        parts.append(
            f"统计:共 {self.rel.total_messages} 条消息, "
            f"{self.rel.deep_conversations} 次深度对话, "
            f"已相处 {self.rel.days_together} 天"
        )
        return "\n".join(parts)

    def set_nickname(self, nickname: str):
        """用户给虚拟人起昵称"""
        self.rel.nickname_given = nickname.strip()[:20]
        self.rel.updated_at = time.time()

    def add_special_moment(self, moment: str):
        """记录关键时刻"""
        if moment and moment not in self.rel.special_moments:
            self.rel.special_moments.append(moment)
            self.rel.special_moments = self.rel.special_moments[-10:]
            self.rel.updated_at = time.time()

    def stats(self) -> Dict[str, Any]:
        return {
            "persona": self.persona_name,
            "user": self.user_id,
            "level": self.rel.level,
            "stage": self.rel.stage.value,
            "stage_label": self.rel.meta["label_zh"],
            "progress_pct": round(self.rel.progress_pct, 1),
            "total_messages": self.rel.total_messages,
            "deep_conversations": self.rel.deep_conversations,
            "positive_emotions": self.rel.positive_emotions,
            "negative_emotions": self.rel.negative_emotions,
        }


if __name__ == "__main__":
    # demo
    eng = RelationshipEngine("xiaoai", "demo_user")
    print("=== Initial ===")
    print(eng.to_system_prompt())
    print()

    # 模拟 5 次互动
    print("=== After 5 interactions ===")
    for i, (msg, emo, depth) in enumerate([
        ("你好", "neutral", 1),
        ("今天工作好累", "sad", 3),
        ("想听你说说话", "loving", 4),
        ("我喜欢你", "loving", 5),
        ("周末想和你去看电影", "happy", 3),
    ]):
        result = eng.record_interaction(msg, f"reply {i}", emotion=emo, depth=depth)
        print(f"  [{i+1}] {msg[:20]} → +{result['delta']} → level {result['new_level']} ({result['stage_label']})")
        if result["promoted"]:
            print(f"      🎉 关系晋升:{result['stage']}")
    eng.save()
    print()
    print("=== Final ===")
    print(eng.to_system_prompt())
    print()
    print("Stats:", json.dumps(eng.stats(), ensure_ascii=False, indent=2))
