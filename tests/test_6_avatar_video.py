"""
test_6_avatar_video — 嘴型同步抽象层测试
=======================================
测试:
  - 4 provider 注册(mocks/wav2lip/sadtalker/musetalk)
  - MockProvider.list_avatars() 4 个形象
  - synthesize_video 返回 VideoResult
  - 4 档质量(DRAFT/STANDARD/HD/ULTRA)
  - 4 种视频格式
  - VRAM 门槛差异
  - 集成 TTS(cycle 5)→ AvatarVideo
  - 集成 Persona
  - 沙盒不返回实际视频字节
"""
import sys
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from avatar_video import (
    AvatarProvider, MockProvider, Wav2LipProvider, SadTalkerProvider, MuseTalkProvider,
    VideoResult, VideoFormat, AvatarQuality,
    get_provider, list_providers, get_avatar_for_persona, PERSONA_AVATAR_MAP,
)


def test_mock_provider_avatars():
    """Mock provider 4 个虚拟形象"""
    mock = MockProvider()
    avatars = mock.list_avatars()
    assert len(avatars) >= 4
    ids = {a["id"] for a in avatars}
    assert "xiaoai_avatar" in ids
    assert "drli_avatar" in ids
    assert "xiaozhi_avatar" in ids
    print(f"  ✓ mock avatars: {len(avatars)}")


def test_synthesize_video_returns_metadata():
    """synthesize_video 返回 VideoResult"""
    mock = MockProvider()
    r = mock.synthesize_video("你好", "female-soft", "xiaoai_avatar")
    assert isinstance(r, VideoResult)
    assert r.text == "你好"
    assert r.voice_id == "female-soft"
    assert r.avatar_id == "xiaoai_avatar"
    assert r.provider == "mock"
    assert r.duration_s > 0
    assert r.width > 0 and r.height > 0
    assert r.fps > 0
    assert r.total_frames > 0
    print(f"  ✓ synthesize: {r.duration_s}s, {r.width}x{r.height}@{r.fps}fps, {r.total_frames} frames")


def test_no_actual_video_bytes():
    """沙盒安全:不返回实际视频字节"""
    mock = MockProvider()
    r = mock.synthesize_video("hi", "v", "xiaoai_avatar")
    # VideoResult 不应有 raw 字段
    assert not hasattr(r, "video_bytes")
    assert not hasattr(r, "raw_data")
    assert r.video_path is None
    print("  ✓ no actual video bytes (sandbox safe)")


def test_quality_levels():
    """4 档质量对应不同分辨率/帧率"""
    mock = MockProvider()
    qs = [AvatarQuality.DRAFT, AvatarQuality.STANDARD, AvatarQuality.HD, AvatarQuality.ULTRA]
    sizes = []
    for q in qs:
        r = mock.synthesize_video("test", "v", "a", quality=q)
        sizes.append((r.width, r.height, r.fps))
    # 验证从低到高
    assert sizes[0][0] < sizes[1][0] < sizes[2][0] < sizes[3][0]
    assert sizes[0][1] < sizes[1][1] < sizes[2][1] < sizes[3][1]
    print(f"  ✓ quality: DRAFT={sizes[0]}, STD={sizes[1]}, HD={sizes[2]}, ULTRA={sizes[3]}")


def test_video_formats():
    """4 种视频格式"""
    mock = MockProvider()
    for fmt in [VideoFormat.MP4, VideoFormat.AVI, VideoFormat.WEBM, VideoFormat.MOV]:
        r = mock.synthesize_video("hi", "v", "a", video_format=fmt)
        assert r.format == fmt
    print(f"  ✓ formats: {[f.value for f in VideoFormat]}")


def test_cost_estimate_zero_for_mock():
    """mock provider 成本为 0"""
    mock = MockProvider()
    r = mock.synthesize_video("anything", "v", "a")
    assert r.cost_estimate == 0.0
    print("  ✓ mock cost = 0")


def test_cost_for_non_zero_provider():
    """非零成本 provider"""
    mock = MockProvider(cost_per_second=0.5)  # ¥0.5/秒
    r = mock.synthesize_video("a" * 50, "v", "a")  # 50 字符, ~20 秒
    assert r.cost_estimate > 0
    print(f"  ✓ cost: ¥{r.cost_estimate:.2f} for ~{r.duration_s}s")


def test_cache_key_consistency():
    """相同输入产生相同 cache_key"""
    mock = MockProvider()
    r1 = mock.synthesize_video("hi", "v", "a", quality=AvatarQuality.HD)
    r2 = mock.synthesize_video("hi", "v", "a", quality=AvatarQuality.HD)
    assert r1.cache_key == r2.cache_key
    r3 = mock.synthesize_video("hi", "v", "a", quality=AvatarQuality.STANDARD)
    assert r1.cache_key != r3.cache_key
    print("  ✓ cache_key consistent for same input")


def test_get_provider_mock():
    """get_provider('mock') → MockProvider"""
    p = get_provider("mock")
    assert isinstance(p, MockProvider)
    print("  ✓ get_provider('mock')")


def test_get_provider_unknown_fallback():
    """未知 provider fallback 到 mock"""
    p = get_provider("nonexistent")
    assert isinstance(p, MockProvider)
    print("  ✓ unknown provider → mock fallback")


def test_list_providers():
    """列出所有 provider + VRAM 门槛"""
    providers = list_providers()
    assert len(providers) >= 4
    ids = {p["id"] for p in providers}
    assert "mock" in ids
    assert "wav2lip" in ids
    assert "sadtalker" in ids
    assert "musetalk" in ids
    # VRAM 门槛递增
    vram = {p["id"]: p["min_vram_gb"] for p in providers}
    assert vram["mock"] == 0
    assert vram["wav2lip"] < vram["sadtalker"]
    print(f"  ✓ providers: {vram}")


def test_provider_vram_requirements():
    """各 provider VRAM 门槛符合预期"""
    wav2lip = Wav2LipProvider()
    sadtalker = SadTalkerProvider()
    musetalk = MuseTalkProvider()
    assert wav2lip.min_vram_gb == 4
    assert sadtalker.min_vram_gb == 8
    assert musetalk.min_vram_gb == 8
    print(f"  ✓ VRAM: wav2lip={wav2lip.min_vram_gb}GB, sadtalker={sadtalker.min_vram_gb}GB, musetalk={musetalk.min_vram_gb}GB")


def test_real_providers_fallback_in_sandbox():
    """真实 provider 在沙盒(无对应包)下 fallback mock"""
    for cls in [Wav2LipProvider, SadTalkerProvider, MuseTalkProvider]:
        p = cls()
        if not p._available:
            r = p.synthesize_video("test", "v", "a")
            assert r.provider == "mock", f"{cls.__name__} should fallback to mock"
            print(f"  ✓ {cls.__name__} not installed → mock fallback")
        else:
            r = p.synthesize_video("test", "v", "a")
            assert r.provider == cls.name
            print(f"  ✓ {cls.__name__} available → {cls.name} provider")


def test_persona_avatar_mapping():
    """3 个内置虚拟人有 avatar 映射"""
    assert "xiaoai" in PERSONA_AVATAR_MAP
    assert "dr_li" in PERSONA_AVATAR_MAP
    assert "xiaozhi" in PERSONA_AVATAR_MAP
    print(f"  ✓ persona avatar map: {PERSONA_AVATAR_MAP}")


def test_get_avatar_for_persona():
    """get_avatar_for_persona 正确返回"""
    assert get_avatar_for_persona("xiaoai") == "xiaoai_avatar"
    assert get_avatar_for_persona("dr_li") == "drli_avatar"
    assert get_avatar_for_persona("xiaozhi") == "xiaozhi_avatar"
    assert get_avatar_for_persona("nonexistent") == "default_avatar"
    print("  ✓ get_avatar_for_persona")


def test_video_result_to_dict():
    """VideoResult 可序列化"""
    mock = MockProvider()
    r = mock.synthesize_video("hi", "v", "a")
    d = r.to_dict()
    assert d["text"] == "hi"
    assert d["format"] == "mp4"
    assert d["quality"] == "standard"
    json_str = json.dumps(d)
    parsed = json.loads(json_str)
    assert parsed["provider"] == "mock"
    print(f"  ✓ VideoResult to_dict ({len(d)} keys)")


def test_integration_tts_to_avatar():
    """TTS → Avatar Video 串联"""
    sys.path.insert(0, str(SCRIPTS))
    from tts import MockProvider as TTSMock, get_voice_for_persona

    tts = TTSMock()
    avatar = MockProvider()

    text = "今天天气真不错,适合出去走走"
    persona = "xiaoai"

    # TTS
    tts_result = tts.synthesize(text, get_voice_for_persona(persona))
    assert tts_result.provider == "mock"

    # Avatar Video(传入 tts_result 作为 audio_format)
    video_result = avatar.synthesize_video(
        text=text,
        voice_id=tts_result.voice_id,
        avatar_id=get_avatar_for_persona(persona),
        audio_format=tts_result,  # 串联
    )
    # 时长应该和 tts 一致
    assert abs(video_result.duration_s - tts_result.duration_estimate_s) < 0.1, \
        f"durations differ: {video_result.duration_s} vs {tts_result.duration_estimate_s}"
    print(f"  ✓ TTS→Avatar: text '{text[:10]}...' = {video_result.duration_s}s video")


def test_integration_persona_to_avatar():
    """完整: Persona → TTS → Avatar"""
    sys.path.insert(0, str(SCRIPTS))
    from persona import PersonaStore, BUILTIN_PERSONAS
    from tts import MockProvider as TTSMock, get_voice_for_persona

    pstore = PersonaStore(root=ROOT / "data" / "test_av_personas")
    pstore.root.mkdir(parents=True, exist_ok=True)
    tts = TTSMock()
    avatar = MockProvider()

    for pname in ["xiaoai", "dr_li", "xiaozhi"]:
        pconf = dict(BUILTIN_PERSONAS[pname])
        pconf.pop("name", None)
        persona = pstore.create_default(pname, **pconf)

        # TTS
        tts_r = tts.synthesize(f"你好,我是{persona.name}", get_voice_for_persona(pname))
        # Avatar
        video_r = avatar.synthesize_video(
            f"你好,我是{persona.name}",
            tts_r.voice_id,
            get_avatar_for_persona(pname),
            audio_format=tts_r,
        )
        assert video_r.avatar_id == get_avatar_for_persona(pname)
        print(f"    [{pname}] tts={tts_r.voice_id} → avatar={video_r.avatar_id}, {video_r.duration_s}s")

    print("  ✓ full integration: Persona → TTS → Avatar")


def test_empty_text():
    """空文本不抛"""
    mock = MockProvider()
    r = mock.synthesize_video("", "v", "a")
    assert r.duration_s == 0.0
    assert r.total_frames == 0
    print("  ✓ empty text handled")


def test_long_text_estimate():
    """长文本时长估算合理"""
    mock = MockProvider()
    text = "你好" * 100  # 200 字符
    r = mock.synthesize_video(text, "v", "a")
    # 200 字符 / 2.5 字/秒 = 80 秒
    assert 75 < r.duration_s < 85
    print(f"  ✓ long text: {len(text)} chars → {r.duration_s}s")


def test_provider_base_class():
    """AvatarProvider 是 ABC"""
    from abc import ABC
    assert issubclass(AvatarProvider, ABC)
    print("  ✓ AvatarProvider is ABC")


if __name__ == "__main__":
    tests = [
        test_mock_provider_avatars,
        test_synthesize_video_returns_metadata,
        test_no_actual_video_bytes,
        test_quality_levels,
        test_video_formats,
        test_cost_estimate_zero_for_mock,
        test_cost_for_non_zero_provider,
        test_cache_key_consistency,
        test_get_provider_mock,
        test_get_provider_unknown_fallback,
        test_list_providers,
        test_provider_vram_requirements,
        test_real_providers_fallback_in_sandbox,
        test_persona_avatar_mapping,
        test_get_avatar_for_persona,
        test_video_result_to_dict,
        test_integration_tts_to_avatar,
        test_integration_persona_to_avatar,
        test_empty_text,
        test_long_text_estimate,
        test_provider_base_class,
    ]
    print(f"Running {len(tests)} avatar video tests...\n")
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
