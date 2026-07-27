#!/usr/bin/env python3
"""
aichat-hub Scene (场景/故事) 模块
==================================
为虚拟人设计多场景、多故事线,让对话有"剧情"。

设计元素(参考星野对话设计):
  - 人物:复用 Persona
  - 场景:时间/地点/氛围
  - 议程(Agenda):对话的核心目标
  - 开场白:进入场景的第一句话
  - 好感度事件:达成特定条件时触发的剧情

使用:
  scene = Scene(...)
  store.add(scene)
  prompt = store.to_system_prompt(persona_name="小爱")
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any


class SceneType(str, Enum):
    """场景类型"""
    DAILY = "daily"           # 日常(咖啡厅聊天)
    ROMANCE = "romance"       # 浪漫(海边散步)
    ADVENTURE = "adventure"   # 冒险(寻宝)
    FANTASY = "fantasy"       # 奇幻(魔法学院)
    SCIFI = "scifi"           # 科幻(太空站)
    HISTORICAL = "historical" # 历史(古代)
    MYSTERY = "mystery"       # 悬疑(侦探)


@dataclass
class AgendaItem:
    """议程项(对话话题)"""
    topic: str
    description: str
    trigger_keywords: List[str] = field(default_factory=list)  # 触发关键词
    completed: bool = False
    triggered_at: Optional[float] = None


@dataclass
class AffectionEvent:
    """好感度事件(达成触发条件时,剧情推进 + 关系升级)"""
    name: str  # 事件名
    condition: str  # 触发条件描述
    affection_delta: int  # 关系加成(0-10)
    script: str  # 触发后的剧情文本
    triggered: bool = False
    triggered_at: Optional[float] = None


@dataclass
class Scene:
    """场景定义"""
    id: str
    title: str
    scene_type: SceneType
    persona_name: str
    description: str
    setting: str  # 场景氛围
    opening_line: str  # 开场白
    agenda: List[AgendaItem] = field(default_factory=list)
    affection_events: List[AffectionEvent] = field(default_factory=list)
    background_music: Optional[str] = None  # 背景音乐(可选)
    tags: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["scene_type"] = self.scene_type.value
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Scene":
        d["scene_type"] = SceneType(d.get("scene_type", "daily"))
        d["agenda"] = [AgendaItem(**a) for a in d.get("agenda", [])]
        d["affection_events"] = [AffectionEvent(**e) for e in d.get("affection_events", [])]
        return cls(**d)

    def to_system_prompt(self) -> str:
        """生成可注入 system prompt 的场景上下文"""
        parts = [
            f"【当前场景】:{self.title}",
            f"类型:{self.scene_type.value} | 标签:{', '.join(self.tags) or '无'}",
            f"设定:{self.setting}",
            f"开场白:{self.opening_line}",
        ]
        if self.agenda:
            ag_items = "\n".join(
                f"  - [{'✓' if a.completed else '○'}] {a.topic}:{a.description}"
                for a in self.agenda
            )
            parts.append(f"\n对话议程(可围绕这些话题展开):\n{ag_items}")
        if self.affection_events:
            ev_items = "\n".join(
                f"  - [{'✓' if e.triggered else '○'}] {e.name}(触发:{e.condition} → +{e.affection_delta}好感)"
                for e in self.affection_events
            )
            parts.append(f"\n好感度事件:\n{ev_items}")
        return "\n".join(parts)


class SceneStore:
    """场景存储"""

    def __init__(self, root: Path = None):
        self.root = root or Path(
            "str(Path(__file__).parent.parent)/data/scenes"
        )
        self.root.mkdir(parents=True, exist_ok=True)
        self.scenes: Dict[str, Scene] = {}
        self._load()

    def _load(self):
        path = self.root / "scenes.json"
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            for sid, sdata in data.get("scenes", {}).items():
                self.scenes[sid] = Scene.from_dict(sdata)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[scene] load warning: {e}")

    def save(self):
        data = {
            "scenes": {sid: s.to_dict() for sid, s in self.scenes.items()},
            "saved_at": time.time(),
        }
        (self.root / "scenes.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def add(self, scene: Scene) -> None:
        self.scenes[scene.id] = scene

    def get(self, scene_id: str) -> Optional[Scene]:
        return self.scenes.get(scene_id)

    def list_by_persona(self, persona_name: str) -> List[Scene]:
        return [s for s in self.scenes.values() if s.persona_name == persona_name]

    def list_all(self) -> List[Scene]:
        return list(self.scenes.values())

    # ---------- 议程/事件推进 ----------

    def check_agenda(self, scene_id: str, user_msg: str) -> List[AgendaItem]:
        """检查用户消息触发了哪些议程项,标记为 completed"""
        scene = self.get(scene_id)
        if not scene:
            return []
        triggered = []
        msg_lower = user_msg.lower()
        for item in scene.agenda:
            if item.completed:
                continue
            for kw in item.trigger_keywords:
                if kw.lower() in msg_lower:
                    item.completed = True
                    item.triggered_at = time.time()
                    triggered.append(item)
                    break
        return triggered

    def check_affection_event(
        self, scene_id: str, condition_met: str
    ) -> Optional[AffectionEvent]:
        """检查是否触发好感度事件(condition_met: 'name1,name2,...')"""
        scene = self.get(scene_id)
        if not scene:
            return None
        conditions = {c.strip() for c in condition_met.split(",")}
        for ev in scene.affection_events:
            if ev.triggered:
                continue
            if ev.condition in conditions:
                ev.triggered = True
                ev.triggered_at = time.time()
                return ev
        return None

    def get_opening_line(self, scene_id: str) -> Optional[str]:
        scene = self.get(scene_id)
        return scene.opening_line if scene else None


# 内置示例场景
BUILTIN_SCENES = {
    "xiaoai_coffee": {
        "title": "午后咖啡馆",
        "scene_type": SceneType.DAILY,
        "persona_name": "小爱",
        "description": "阳光透过落地窗洒在原木桌面上,你和小爱在咖啡馆里对坐",
        "setting": "温馨、慢节奏、有咖啡香",
        "opening_line": "(微笑看着你)这家的拿铁很香呢,你要不要也来一杯?",
        "agenda": [
            {"topic": "分享近况", "description": "聊聊最近发生的事",
             "trigger_keywords": ["最近", "今天", "工作", "学习"]},
            {"topic": "聊音乐", "description": "听小爱推荐一首歌",
             "trigger_keywords": ["音乐", "歌", "听", "推荐"]},
            {"topic": "未来计划", "description": "聊聊周末想做什么",
             "trigger_keywords": ["周末", "计划", "想做", "打算"]},
        ],
        "affection_events": [
            {"name": "第一次叫出昵称", "condition": "first_nickname",
             "affection_delta": 2, "script": "你突然叫我「宝」,我脸有点红..."},
            {"name": "分享秘密", "condition": "share_secret",
             "affection_delta": 5, "script": "你告诉我了一个从没对别人说过的秘密,我好感动..."},
        ],
        "tags": ["日常", "温馨", "咖啡"],
    },
    "xiaozhi_hackathon": {
        "title": "深夜 Hackathon",
        "scene_type": SceneType.ADVENTURE,
        "persona_name": "小智",
        "description": "凌晨 2 点的办公室,只有键盘声和咖啡机嗡嗡响,你们在赶一个 AI 项目",
        "setting": "紧张、专注、肾上腺素",
        "opening_line": "Yo! 还醒着?还有 6 小时,我们能搞定的!",
        "agenda": [
            {"topic": "讨论架构", "description": "前后端怎么拆",
             "trigger_keywords": ["架构", "前后端", "api", "数据库"]},
            {"topic": "debug 紧急 bug", "description": "线上服务挂了",
             "trigger_keywords": ["bug", "挂", "错误", "报错"]},
            {"topic": "提交代码", "description": "最后冲刺",
             "trigger_keywords": ["commit", "push", "提交", "merge"]},
        ],
        "affection_events": [
            {"name": "一起解决难题", "condition": "solve_bug_together",
             "affection_delta": 3, "script": "卧槽搞定了! 你小子行啊!"},
            {"name": "提交前夜的咖啡", "condition": "midnight_coffee",
             "affection_delta": 1, "script": "这杯咖啡,敬我们的友谊!"},
        ],
        "tags": ["技术", "深夜", "冒险"],
    },
    "drli_consult": {
        "title": "门诊咨询",
        "scene_type": SceneType.DAILY,
        "persona_name": "李医生",
        "description": "在三甲医院的诊室里,你坐在李医生对面,有点紧张地描述症状",
        "setting": "专业、关切、有消毒水味",
        "opening_line": "您好,我是李医生,请坐。请问哪里不舒服?",
        "agenda": [
            {"topic": "了解症状", "description": "询问发病时间/位置/程度",
             "trigger_keywords": ["疼", "不舒服", "症状", "难受"]},
            {"topic": "过往病史", "description": "了解过敏/慢性病",
             "trigger_keywords": ["过敏", "病史", "慢性", "手术"]},
            {"topic": "给出建议", "description": "开检查/开药/转诊",
             "trigger_keywords": ["检查", "药", "治疗", "怎么办"]},
        ],
        "affection_events": [
            {"name": "建立信任", "condition": "patient_relieved",
             "affection_delta": 2, "script": "你能来就诊就对了,我们一起想办法。"},
        ],
        "tags": ["医疗", "专业", "关怀"],
    },
}


def seed_builtin_scenes(store: SceneStore):
    """把内置场景写进 store"""
    for sid, conf in BUILTIN_SCENES.items():
        if sid in store.scenes:
            continue
        # 转换 agenda/affection_events 字段
        agenda = [AgendaItem(**a) for a in conf.get("agenda", [])]
        evs = [AffectionEvent(**e) for e in conf.get("affection_events", [])]
        scene = Scene(
            id=sid,
            title=conf["title"],
            scene_type=conf["scene_type"],
            persona_name=conf["persona_name"],
            description=conf["description"],
            setting=conf["setting"],
            opening_line=conf["opening_line"],
            agenda=agenda,
            affection_events=evs,
            tags=conf.get("tags", []),
        )
        store.add(scene)


if __name__ == "__main__":
    # demo
    store = SceneStore()
    seed_builtin_scenes(store)
    store.save()

    print(f"=== 场景库(共 {len(store.scenes)} 个) ===\n")
    for sid, scene in store.scenes.items():
        print(f"[{sid}] {scene.title} ({scene.persona_name})")
        print(scene.to_system_prompt())
        print()
        print("---")

    # 模拟议程触发
    print("\n=== 议程触发测试 ===")
    triggered = store.check_agenda("xiaoai_coffee", "最近工作好累啊,想听歌放松一下")
    for t in triggered:
        print(f"  ✓ 触发议程:{t.topic} ({t.description})")

    # 好感度事件
    ev = store.check_affection_event("xiaoai_coffee", "first_nickname")
    if ev:
        print(f"  💕 触发事件:{ev.name} (+{ev.affection_delta} 好感)")
        print(f"     {ev.script}")
