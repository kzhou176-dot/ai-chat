#!/usr/bin/env python3
"""
aichat-hub TTS (Text-to-Speech) 抽象层
======================================
为 Persona.voice_id 提供统一语音合成接口。

设计:
  - TTSProvider 抽象基类(synthesize / list_voices)
  - MockProvider 默认实现(返回合成元数据,不实际播放)
  - EdgeTTSProvider 占位(需要 edge-tts 包)
  - 工厂函数 get_provider(name) 按需返回

注意:
  - 沙盒环境**不实际播放音频**(user 偏好)
  - 实际部署时接入 edge-tts / Azure / 讯飞 TTS
  - 所有 provider 都返回 SynthResult(包含 text/voice/duration_estimate/format)

Cycle 5 - 基础版
"""
from __future__ import annotations
import json
import time
import hashlib
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import List, Dict, Optional, Any


class AudioFormat(str, Enum):
    """音频格式"""
    MP3 = "mp3"
    WAV = "wav"
    PCM = "pcm"
    OGG = "ogg"


@dataclass
class Voice:
    """声音定义"""
    id: str
    name: str
    language: str = "zh-CN"  # BCP-47
    gender: str = "female"  # male/female/neutral
    age_range: str = "young"  # child/young/middle/mature
    style: str = "neutral"  # neutral/cheerful/sad/angry/whisper
    provider: str = "mock"
    sample_text: str = ""


@dataclass
class SynthResult:
    """合成结果(不包含实际音频字节,只元数据)"""
    text: str
    voice_id: str
    provider: str
    format: AudioFormat
    duration_estimate_s: float  # 估算时长(秒)
    sample_rate: int
    char_count: int
    cost_estimate: float  # 估算费用(元)
    cache_key: str
    created_at: float = field(default_factory=time.time)
    audio_path: Optional[str] = None  # 如果保存了文件,这里是路径

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["format"] = self.format.value
        return d


class TTSProvider(ABC):
    """TTS 提供方抽象基类"""

    name: str = "abstract"

    @abstractmethod
    def list_voices(self, language: Optional[str] = None) -> List[Voice]:
        """列出可用声音"""
        raise NotImplementedError

    @abstractmethod
    def synthesize(
        self,
        text: str,
        voice_id: str,
        audio_format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
        pitch: float = 0.0,
    ) -> SynthResult:
        """合成语音(返回元数据,不返回实际音频)"""
        raise NotImplementedError

    def _cache_key(self, text: str, voice_id: str, **kwargs) -> str:
        """生成缓存 key"""
        content = f"{text}|{voice_id}|{sorted(kwargs.items())}"
        return hashlib.md5(content.encode("utf-8")).hexdigest()[:16]

    def _estimate_duration(self, text: str, speed: float = 1.0) -> float:
        """估算时长(中文 ~3 字/秒, 英文 ~150 词/分)"""
        if not text:
            return 0.0
        # 简化:中英混合,约 2.5 字符/秒
        chars_per_sec = 2.5 * speed
        return round(len(text) / chars_per_sec, 2)


class MockProvider(TTSProvider):
    """Mock TTS — 不实际合成,只返回元数据"""

    name = "mock"

    VOICES = [
        Voice("female-young", "年轻女声", "zh-CN", "female", "young", "neutral", "mock", "你好,我是小爱。"),
        Voice("female-soft", "温柔女声", "zh-CN", "female", "young", "cheerful", "mock", "今天天气真不错呀~"),
        Voice("female-mature", "成熟女声", "zh-CN", "female", "middle", "neutral", "mock", "您好,我是李医生。"),
        Voice("male-young", "年轻男声", "zh-CN", "male", "young", "neutral", "mock", "Yo~ 我是小智!"),
        Voice("male-mature", "成熟男声", "zh-CN", "male", "mature", "neutral", "mock", "请坐,有什么可以帮您?"),
        Voice("en-female-1", "English Female 1", "en-US", "female", "young", "neutral", "mock", "Hi, I'm here to help."),
        Voice("en-male-1", "English Male 1", "en-US", "male", "middle", "neutral", "mock", "Hello, how can I assist?"),
    ]

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or Path(
            "/Users/yuefeng/.mavis/agents/mavis/workspace/aichat-hub/data/tts_cache"
        )
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # mock 计费(元/千字符)
        self.cost_per_1k_chars = 0.0  # 免费

    def list_voices(self, language: Optional[str] = None) -> List[Voice]:
        if language is None:
            return self.VOICES
        return [v for v in self.VOICES if v.language.startswith(language)]

    def synthesize(
        self,
        text: str,
        voice_id: str,
        audio_format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
        pitch: float = 0.0,
    ) -> SynthResult:
        voice = self._get_voice(voice_id)
        duration = self._estimate_duration(text, speed)
        cost = len(text) / 1000 * self.cost_per_1k_chars
        cache_key = self._cache_key(text, voice_id, audio_format=audio_format.value, speed=speed, pitch=pitch)
        return SynthResult(
            text=text,
            voice_id=voice_id,
            provider=self.name,
            format=audio_format,
            duration_estimate_s=duration,
            sample_rate=24000,
            char_count=len(text),
            cost_estimate=cost,
            cache_key=cache_key,
        )

    def _get_voice(self, voice_id: str) -> Optional[Voice]:
        for v in self.VOICES:
            if v.id == voice_id:
                return v
        return None


class EdgeTTSProvider(TTSProvider):
    """Microsoft Edge TTS(免费,基于 edge-tts 包)— 沙盒不实际调用"""

    name = "edge"

    def __init__(self):
        # 检查 edge-tts 是否安装
        try:
            import edge_tts  # noqa: F401
            self._available = True
        except ImportError:
            self._available = False

    def list_voices(self, language: Optional[str] = None) -> List[Voice]:
        # Edge TTS 有 300+ 中文/英文声音
        # 返回推荐的中英文声音(无论 edge-tts 是否可用,都作为占位)
        voices = [
            Voice("zh-CN-XiaoxiaoNeural", "晓晓", "zh-CN", "female", "young", "neutral", "edge"),
            Voice("zh-CN-YunxiNeural", "云希", "zh-CN", "male", "young", "neutral", "edge"),
            Voice("zh-CN-YunjianNeural", "云健", "zh-CN", "male", "middle", "neutral", "edge"),
            Voice("en-US-JennyNeural", "Jenny", "en-US", "female", "young", "neutral", "edge"),
            Voice("en-US-GuyNeural", "Guy", "en-US", "male", "middle", "neutral", "edge"),
        ]
        if language is None:
            return voices
        return [v for v in voices if v.language.startswith(language)]

    def synthesize(
        self,
        text: str,
        voice_id: str,
        audio_format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
        pitch: float = 0.0,
    ) -> SynthResult:
        if not self._available:
            # 沙盒 fallback:返回 mock 结果
            mock = MockProvider()
            return mock.synthesize(text, voice_id, audio_format, speed, pitch)
        # 实际部署时调用 edge-tts
        # 这里是占位
        return SynthResult(
            text=text,
            voice_id=voice_id,
            provider=self.name,
            format=audio_format,
            duration_estimate_s=self._estimate_duration(text, speed),
            sample_rate=24000,
            char_count=len(text),
            cost_estimate=0.0,  # Edge TTS 免费
            cache_key=self._cache_key(text, voice_id),
        )


class XunfeiTTSProvider(TTSProvider):
    """科大讯飞 TTS(国内,企业级)— 占位"""

    name = "xunfei"

    def __init__(self, api_key: str = None):
        self.api_key = api_key

    def list_voices(self, language: Optional[str] = None) -> List[Voice]:
        return [
            Voice("xiaoyan", "小燕", "zh-CN", "female", "young", "neutral", "xunfei"),
            Voice("aisjiuxu", "许久", "zh-CN", "male", "middle", "neutral", "xunfei"),
            Voice("aisxping", "小萍", "zh-CN", "female", "middle", "neutral", "xunfei"),
        ]

    def synthesize(
        self,
        text: str,
        voice_id: str,
        audio_format: AudioFormat = AudioFormat.MP3,
        speed: float = 1.0,
        pitch: float = 0.0,
    ) -> SynthResult:
        return SynthResult(
            text=text,
            voice_id=voice_id,
            provider=self.name,
            format=audio_format,
            duration_estimate_s=self._estimate_duration(text, speed),
            sample_rate=16000,
            char_count=len(text),
            cost_estimate=len(text) / 1000 * 0.02,  # ¥0.02/千字符(估算)
            cache_key=self._cache_key(text, voice_id),
        )


# 工厂
_PROVIDERS: Dict[str, type] = {
    "mock": MockProvider,
    "edge": EdgeTTSProvider,
    "xunfei": XunfeiTTSProvider,
}


def get_provider(name: str = "mock", **kwargs) -> TTSProvider:
    """按名称获取 provider(默认 mock)"""
    cls = _PROVIDERS.get(name)
    if cls is None:
        return MockProvider()
    return cls(**kwargs)


def list_providers() -> List[Dict[str, str]]:
    """列出所有可用 provider"""
    return [
        {"id": name, "class": cls.__name__, "description": cls.__doc__ or ""}
        for name, cls in _PROVIDERS.items()
    ]


# Persona voice_id → TTS voice 映射(对应 persona.py 里的 voice_id)
PERSONA_VOICE_MAP = {
    "xiaoai": "female-soft",
    "dr_li": "male-mature",
    "xiaozhi": "male-young",
    # 默认 fallback
    "default": "female-young",
}


def get_voice_for_persona(persona_name: str) -> str:
    """根据虚拟人名字获取对应 voice_id"""
    return PERSONA_VOICE_MAP.get(persona_name, PERSONA_VOICE_MAP["default"])


if __name__ == "__main__":
    print("=== aichat-hub TTS Providers ===\n")
    for p in list_providers():
        print(f"  [{p['id']}] {p['class']}")

    print("\n=== Mock voices ===")
    mock = MockProvider()
    for v in mock.list_voices():
        print(f"  {v.id:20s} {v.gender}/{v.age_range}/{v.style} ({v.language})")

    print("\n=== Synthesize demo (mock, no actual audio) ===")
    for text, persona in [
        ("你好,我是小爱~", "xiaoai"),
        ("您好,我是李医生", "dr_li"),
        ("Yo~ 我是小智!", "xiaozhi"),
    ]:
        voice_id = get_voice_for_persona(persona)
        result = mock.synthesize(text, voice_id)
        print(f"  [{persona}] voice={voice_id}, "
              f"duration={result.duration_estimate_s}s, "
              f"chars={result.char_count}, "
              f"cache_key={result.cache_key}")
