"""
test_5_tts — TTS 抽象层测试
===========================
测试:
  - MockProvider.list_voices() 7 个声音
  - synthesize() 返回 SynthResult(不返回实际音频)
  - duration 估算
  - cost 估算
  - cache_key 一致性
  - 3 个 provider 注册(mocks/edge/xunfei)
  - get_provider() 工厂
  - persona voice_id 映射
  - EdgeTTSProvider 在沙盒(无 edge-tts 包)下优雅 fallback
  - 集成:Persona → TTS
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from tts import (
    TTSProvider, MockProvider, EdgeTTSProvider, XunfeiTTSProvider,
    SynthResult, Voice, AudioFormat,
    get_provider, list_providers, get_voice_for_persona, PERSONA_VOICE_MAP,
)


def test_mock_provider_voices():
    """Mock provider 至少 5 个声音,含中英"""
    mock = MockProvider()
    voices = mock.list_voices()
    assert len(voices) >= 5
    # 必须有中文 + 英文
    langs = {v.language for v in voices}
    assert any(l.startswith("zh") for l in langs)
    assert any(l.startswith("en") for l in langs)
    # 性别均衡
    genders = {v.gender for v in voices}
    assert "male" in genders and "female" in genders
    print(f"  ✓ mock voices: {len(voices)} ({len(langs)} langs)")


def test_synthesize_returns_metadata():
    """synthesize 返回 SynthResult,不抛异常"""
    mock = MockProvider()
    result = mock.synthesize("你好世界", "female-young")
    assert isinstance(result, SynthResult)
    assert result.text == "你好世界"
    assert result.voice_id == "female-young"
    assert result.provider == "mock"
    assert result.format == AudioFormat.MP3
    assert result.char_count == 4
    assert result.duration_estimate_s > 0
    assert result.sample_rate > 0
    assert result.cache_key  # 非空
    print(f"  ✓ synthesize: {result.char_count} chars, {result.duration_estimate_s}s")


def test_synthesize_no_actual_audio():
    """确认不返回实际音频字节(沙盒友好)"""
    mock = MockProvider()
    result = mock.synthesize("hello", "en-female-1")
    # SynthResult 不应有 raw 音频字段
    assert not hasattr(result, "audio_bytes")
    assert not hasattr(result, "audio_data")
    # audio_path 应该是 None(没存)
    assert result.audio_path is None
    print("  ✓ no actual audio bytes returned (sandbox safe)")


def test_duration_estimate():
    """时长估算合理"""
    mock = MockProvider()
    # 10 个中文字符,速度 1.0 → 约 4 秒
    r1 = mock.synthesize("你好世界你好世界你好世界你好世界你好世界", "female-young", speed=1.0)
    # 速度 2.0 → 时长减半
    r2 = mock.synthesize("你好世界你好世界你好世界你好世界你好世界", "female-young", speed=2.0)
    assert r1.duration_estimate_s > r2.duration_estimate_s, \
        f"faster speed should give shorter duration: {r1.duration_estimate_s} vs {r2.duration_estimate_s}"
    # 速度 0.5 → 时长翻倍
    r3 = mock.synthesize("你好世界你好世界你好世界你好世界你好世界", "female-young", speed=0.5)
    assert r3.duration_estimate_s > r1.duration_estimate_s
    print(f"  ✓ duration: speed 1.0={r1.duration_estimate_s}s, 2.0={r2.duration_estimate_s}s, 0.5={r3.duration_estimate_s}s")


def test_cost_estimate_zero_for_mock():
    """mock provider 成本为 0"""
    mock = MockProvider()
    r = mock.synthesize("anything", "female-young")
    assert r.cost_estimate == 0.0
    print("  ✓ mock cost = 0")


def test_cost_for_xunfei():
    """讯飞有具体价格"""
    xf = XunfeiTTSProvider()
    r = xf.synthesize("a" * 1000, "xiaoyan")
    # ¥0.02/千字符,1000 字符 = ¥0.02
    assert r.cost_estimate > 0
    print(f"  ✓ xunfei cost for 1000 chars = ¥{r.cost_estimate:.4f}")


def test_cache_key_consistency():
    """相同输入产生相同 cache_key"""
    mock = MockProvider()
    r1 = mock.synthesize("hi", "female-young", speed=1.0, pitch=0.0)
    r2 = mock.synthesize("hi", "female-young", speed=1.0, pitch=0.0)
    assert r1.cache_key == r2.cache_key
    # 不同参数应不同
    r3 = mock.synthesize("hi", "female-young", speed=2.0, pitch=0.0)
    assert r1.cache_key != r3.cache_key
    print(f"  ✓ cache_key: same input → same key, diff param → diff key")


def test_cache_key_different_for_different_voices():
    """不同 voice 不同 cache_key"""
    mock = MockProvider()
    r1 = mock.synthesize("hi", "female-young")
    r2 = mock.synthesize("hi", "male-young")
    assert r1.cache_key != r2.cache_key
    print("  ✓ different voice → different cache_key")


def test_audio_format_options():
    """支持多种音频格式"""
    mock = MockProvider()
    for fmt in [AudioFormat.MP3, AudioFormat.WAV, AudioFormat.PCM, AudioFormat.OGG]:
        r = mock.synthesize("hi", "female-young", audio_format=fmt)
        assert r.format == fmt
    print(f"  ✓ formats: {[f.value for f in AudioFormat]}")


def test_get_provider_mock():
    """get_provider('mock') 返回 MockProvider"""
    p = get_provider("mock")
    assert isinstance(p, MockProvider)
    assert p.name == "mock"
    print("  ✓ get_provider('mock') → MockProvider")


def test_get_provider_unknown_fallback():
    """未知 provider fallback 到 mock"""
    p = get_provider("nonexistent_provider")
    assert isinstance(p, MockProvider)
    print("  ✓ unknown provider → mock fallback")


def test_list_providers():
    """列出所有注册 provider"""
    providers = list_providers()
    assert len(providers) >= 3
    ids = {p["id"] for p in providers}
    assert "mock" in ids
    assert "edge" in ids
    assert "xunfei" in ids
    print(f"  ✓ list_providers: {len(providers)} registered")


def test_edge_tts_fallback_in_sandbox():
    """Edge TTS 在无包时 fallback(沙盒环境)"""
    edge = EdgeTTSProvider()
    # 检查 _available 属性(实际取决于环境)
    if not edge._available:
        # fallback 测试
        r = edge.synthesize("test", "zh-CN-XiaoxiaoNeural")
        assert r.provider == "mock", \
            f"should fallback to mock, got {r.provider}"
        print("  ✓ edge-tts not installed → mock fallback")
    else:
        r = edge.synthesize("test", "zh-CN-XiaoxiaoNeural")
        assert r.provider == "edge"
        print("  ✓ edge-tts available → edge provider")


def test_edge_tts_voice_list():
    """Edge TTS 返回声音列表(沙盒下 5 个)"""
    edge = EdgeTTSProvider()
    voices = edge.list_voices()
    assert len(voices) >= 3
    print(f"  ✓ edge voices: {len(voices)}")


def test_persona_voice_mapping():
    """3 个内置虚拟人都有 voice_id 映射"""
    assert "xiaoai" in PERSONA_VOICE_MAP
    assert "dr_li" in PERSONA_VOICE_MAP
    assert "xiaozhi" in PERSONA_VOICE_MAP
    print(f"  ✓ persona voice map: {PERSONA_VOICE_MAP}")


def test_get_voice_for_persona():
    """get_voice_for_persona 正确返回"""
    assert get_voice_for_persona("xiaoai") == "female-soft"
    assert get_voice_for_persona("dr_li") == "male-mature"
    assert get_voice_for_persona("xiaozhi") == "male-young"
    # 未知 fallback
    assert get_voice_for_persona("nonexistent") == "female-young"
    print("  ✓ get_voice_for_persona")


def test_synth_result_to_dict():
    """SynthResult 可序列化"""
    mock = MockProvider()
    r = mock.synthesize("hi", "female-young")
    d = r.to_dict()
    assert d["text"] == "hi"
    assert d["provider"] == "mock"
    assert d["format"] == "mp3"  # enum 序列化为 value
    # 可以 JSON 序列化
    json_str = json.dumps(d)
    parsed = json.loads(json_str)
    assert parsed["text"] == "hi"
    print(f"  ✓ SynthResult to_dict ({len(d)} keys)")


def test_integration_with_persona():
    """完整流程:Persona → voice_id → TTS synthesize"""
    sys.path.insert(0, str(SCRIPTS))
    from persona import PersonaStore, BUILTIN_PERSONAS

    pstore = PersonaStore(root=ROOT / "data" / "test_tts_personas")
    pstore.root.mkdir(parents=True, exist_ok=True)

    for pname in ["xiaoai", "dr_li", "xiaozhi"]:
        pconf = dict(BUILTIN_PERSONAS[pname])
        pconf.pop("name", None)
        persona = pstore.create_default(pname, **pconf)
        # persona 有 voice_id 属性
        assert hasattr(persona, "voice_id")

        voice_id = get_voice_for_persona(pname)
        mock = MockProvider()
        result = mock.synthesize(
            f"你好,我是{persona.name}",
            voice_id,
        )
        assert result.voice_id == voice_id
        print(f"    [{pname}] voice={voice_id}, dur={result.duration_estimate_s}s")

    print("  ✓ integration: Persona → TTS synthesize")


def test_empty_text():
    """空文本不抛"""
    mock = MockProvider()
    r = mock.synthesize("", "female-young")
    assert r.char_count == 0
    assert r.duration_estimate_s == 0.0
    print("  ✓ empty text handled")


def test_voice_filter_by_language():
    """list_voices 支持按语言筛选"""
    mock = MockProvider()
    zh_voices = mock.list_voices("zh")
    en_voices = mock.list_voices("en")
    assert len(zh_voices) >= 3
    assert len(en_voices) >= 2
    assert all(v.language.startswith("zh") for v in zh_voices)
    assert all(v.language.startswith("en") for v in en_voices)
    print(f"  ✓ filter: zh={len(zh_voices)}, en={len(en_voices)}")


if __name__ == "__main__":
    tests = [
        test_mock_provider_voices,
        test_synthesize_returns_metadata,
        test_synthesize_no_actual_audio,
        test_duration_estimate,
        test_cost_estimate_zero_for_mock,
        test_cost_for_xunfei,
        test_cache_key_consistency,
        test_cache_key_different_for_different_voices,
        test_audio_format_options,
        test_get_provider_mock,
        test_get_provider_unknown_fallback,
        test_list_providers,
        test_edge_tts_fallback_in_sandbox,
        test_edge_tts_voice_list,
        test_persona_voice_mapping,
        test_get_voice_for_persona,
        test_synth_result_to_dict,
        test_integration_with_persona,
        test_empty_text,
        test_voice_filter_by_language,
    ]
    print(f"Running {len(tests)} TTS tests...\n")
    passed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            import traceback
            print(f"  ✗ {t.__name__}: {e}")
            traceback.print_exc()
    print(f"\n{passed}/{len(tests)} passed")
    sys.exit(0 if passed == len(tests) else 1)
