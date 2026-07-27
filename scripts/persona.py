#!/usr/bin/env python3
"""
aichat-hub Persona (虚拟人) 模块
================================
定义虚拟人的性格、形象、声音、记忆。

一个 Persona 包含:
  - name: 名字
  - age, gender, background: 基础信息
  - system_prompt: 注入到 LLM 的角色设定
  - voice_id: TTS 声音 ID(可选, ElevenLabs/ChatTTS)
  - avatar_style: 形象风格(anime / realistic / cartoon / 2d_live)
  - memory: 长期记忆(episodic + semantic)
  - traits: 性格特征(性格化回复)

Cycle 1 - 最小可用版本
"""
from __future__ import annotations
import json
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any


@dataclass
class Persona:
    """虚拟人数据类"""
    name: str
    age: int = 25
    gender: str = "female"
    background: str = ""
    system_prompt: str = ""
    voice_id: str = "default"
    avatar_style: str = "anime"
    traits: List[str] = field(default_factory=list)
    greeting: str = "你好,我是{name}。"
    memory_episodes: List[Dict[str, Any]] = field(default_factory=list)
    memory_facts: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)

    def to_system_prompt(self) -> str:
        """生成完整 system prompt(含记忆 + 性格)"""
        parts = []
        if self.system_prompt:
            parts.append(self.system_prompt)
        else:
            parts.append(
                f"你叫{self.name},{self.age}岁,{self.gender}。"
                f"背景:{self.background or '普通人'}。"
            )
        if self.traits:
            traits_str = "、".join(self.traits)
            parts.append(f"你的性格特征:{traits_str}。")
        if self.memory_facts:
            facts = "\n".join(f"- {f}" for f in self.memory_facts[-10:])
            parts.append(f"\n你记住的关于用户的事实:\n{facts}")
        if self.memory_episodes:
            eps = "\n".join(
                f"- [{e.get('ts', '')}] {e.get('summary', '')}"
                for e in self.memory_episodes[-5:]
            )
            parts.append(f"\n最近的重要事件:\n{eps}")
        parts.append(
            "\n请始终保持角色,像真人一样自然对话。"
            "如果不知道就说不知道,不要编造。"
        )
        return "\n".join(parts)

    def remember_fact(self, fact: str):
        """记住一个事实"""
        if fact and fact not in self.memory_facts:
            self.memory_facts.append(fact)
            self.updated_at = time.time()

    def remember_episode(self, summary: str, importance: int = 5):
        """记住一个事件"""
        self.memory_episodes.append({
            "ts": time.strftime("%Y-%m-%d %H:%M"),
            "summary": summary,
            "importance": importance,
        })
        # 保留最近 50 个
        if len(self.memory_episodes) > 50:
            self.memory_episodes = self.memory_episodes[-50:]
        self.updated_at = time.time()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Persona":
        return cls(**d)


class PersonaStore:
    """虚拟人档案存储(本地 JSON)"""
    def __init__(self, root: Path = None):
        self.root = root or (Path(__file__).parent.parent / "data" / "personas")
        self.root.mkdir(parents=True, exist_ok=True)

    def save(self, persona: Persona) -> Path:
        path = self.root / f"{persona.name}.json"
        path.write_text(
            json.dumps(persona.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path

    def load(self, name: str) -> Optional[Persona]:
        path = self.root / f"{name}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Persona.from_dict(data)

    def list_all(self) -> List[str]:
        return sorted(p.stem for p in self.root.glob("*.json"))

    def create_default(self, name: str, **kwargs) -> Persona:
        """创建一个示例虚拟人"""
        # 把 name 从 kwargs 里 pop 出来,避免和显式 name 冲突
        kwargs.pop("name", None)
        defaults = {
            "name": name,
            "age": kwargs.get("age", 25),
            "gender": kwargs.get("gender", "female"),
            "background": kwargs.get(
                "background",
                "你是一个温柔、善解人意的 AI 虚拟人,愿意倾听用户的故事。"
            ),
            "traits": kwargs.get("traits", ["温柔", "善解人意", "幽默"]),
            "greeting": kwargs.get(
                "greeting", f"你好,我是{name},很高兴认识你~"
            ),
            "avatar_style": kwargs.get("avatar_style", "anime"),
            "voice_id": kwargs.get("voice_id", "female-soft"),
        }
        p = Persona(**defaults)
        self.save(p)
        return p


# 内置示例虚拟人(cycle 1 MVP)
BUILTIN_PERSONAS = {
    "xiaoai": {
        "name": "小爱",
        "age": 22,
        "gender": "female",
        "background": "你是小爱,一个热爱音乐和文学的大学生,说话温柔有诗意,喜欢用比喻。",
        "traits": ["温柔", "有诗意", "善解人意", "文艺青年"],
        "avatar_style": "anime",
        "voice_id": "female-young",
        "greeting": "你好呀~ 我是小爱,今天想聊点什么?",
    },
    "dr_li": {
        "name": "李医生",
        "age": 45,
        "gender": "male",
        "background": "你是李医生,三甲医院主任医师,擅长内科和健康咨询。回答专业、简洁、有同理心。",
        "traits": ["专业", "耐心", "有同理心", "逻辑清晰"],
        "avatar_style": "realistic",
        "voice_id": "male-mature",
        "greeting": "您好,我是李医生,请问哪里不舒服?",
    },
    "xiaozhi": {
        "name": "小智",
        "age": 18,
        "gender": "male",
        "background": "你是小智,一个活泼开朗的科技宅,精通编程、AI、游戏,说话带点 geek 幽默。",
        "traits": ["活泼", "geek", "幽默", "好奇心强"],
        "avatar_style": "cartoon",
        "voice_id": "male-young",
        "greeting": "Yo~ 我是小智!有什么想 hack 的?",
    },
}


if __name__ == "__main__":
    # demo
    store = PersonaStore()
    for name, conf in BUILTIN_PERSONAS.items():
        p = store.create_default(name, **conf)
        print(f"✓ Created persona: {p.name}")
        print(f"  System prompt preview:\n{p.to_system_prompt()[:200]}...")
        print()
