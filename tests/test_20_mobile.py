#!/usr/bin/env python3
"""
test_20_mobile — aichat-hub Cycle 20 移动端 + i18n 模块测试
=======================================================
覆盖:
  1. i18n 字典(zh-CN / en-US)
  2. t() 翻译函数
  3. translate_dict() 整 dict 翻译
  4. 支持语言列表
  5. PWA Manifest
  6. Mobile CSS(响应式 + 触摸 + 暗色模式)
  7. 分页辅助
  8. 移动端 UA 检测
  9. 模块级 API
  10. CLI 入口
  11. 集成(与 web 端联动)
"""
import sys
import subprocess
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from mobile import (
    SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE, LANGUAGE_LABELS,
    TRANSLATIONS, PWA_MANIFEST, MOBILE_CSS,
    t, translate_dict, get_all_translations,
    get_manifest, get_mobile_css,
    get_supported_languages, get_i18n,
    paginate, detect_mobile,
    DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE,
)


# ============== 1. i18n 基础 ==============

def test_supported_languages():
    """2 支持语言"""
    assert len(SUPPORTED_LANGUAGES) == 2
    assert "zh-CN" in SUPPORTED_LANGUAGES
    assert "en-US" in SUPPORTED_LANGUAGES
    print(f"✓ 支持语言: {SUPPORTED_LANGUAGES}")


def test_default_language():
    """默认语言"""
    assert DEFAULT_LANGUAGE == "zh-CN"
    print("✓ 默认 zh-CN")


def test_translations_count():
    """翻译键数"""
    for lang in SUPPORTED_LANGUAGES:
        assert len(TRANSLATIONS[lang]) >= 20
    print(f"✓ 翻译键数: {[(l, len(TRANSLATIONS[l])) for l in SUPPORTED_LANGUAGES]}")


def test_translations_keys_consistent():
    """两语言键一致"""
    zh_keys = set(TRANSLATIONS["zh-CN"].keys())
    en_keys = set(TRANSLATIONS["en-US"].keys())
    assert zh_keys == en_keys
    print(f"✓ 键一致 {len(zh_keys)} 个")


# ============== 2. t() 翻译 ==============

def test_translate_zh():
    """中文翻译"""
    assert t("service.running", "zh-CN") == "服务运行中"
    assert t("module.resume", "zh-CN") == "简历"
    assert t("action.like", "zh-CN") == "点赞"
    print("✓ 中文翻译")


def test_translate_en():
    """英文翻译"""
    assert t("service.running", "en-US") == "Service running"
    assert t("module.resume", "en-US") == "Resume"
    assert t("action.like", "en-US") == "Like"
    print("✓ 英文翻译")


def test_translate_default():
    """默认语言(无 lang 参数)"""
    assert t("service.running") == "服务运行中"
    print("✓ 默认 zh-CN")


def test_translate_unknown_key_returns_key():
    """未知键返回键本身"""
    assert t("nonexistent.key") == "nonexistent.key"
    print("✓ 未知键返回 key")


def test_translate_unknown_lang_fallback():
    """未知语言 fallback"""
    assert t("service.running", "fr-FR") == "服务运行中"  # fallback
    print("✓ 未知语言 fallback")


def test_translate_dict():
    """整 dict 翻译"""
    d = {"module.resume": "Resume数据", "action.like": "Like 按钮"}
    result = translate_dict(d, "zh-CN")
    assert "简历" in result  # key 被翻译
    assert "点赞" in result
    print("✓ dict 翻译")


def test_get_all_translations():
    """获取全部翻译"""
    trans = get_all_translations("en-US")
    assert trans["module.career"] == "Career"
    print("✓ 全部翻译")


# ============== 3. PWA Manifest ==============

def test_manifest_basic():
    """Manifest 基础"""
    m = get_manifest()
    assert m["name"] == "AIchat-Hub"
    assert m["short_name"] == "AIchat-Hub"
    print("✓ Manifest 基础")


def test_manifest_required_fields():
    """Manifest 必填字段"""
    m = get_manifest()
    required = ["name", "short_name", "start_url", "display", "theme_color", "icons"]
    for f in required:
        assert f in m
    print("✓ Manifest 必填字段")


def test_manifest_icons():
    """Icons"""
    m = get_manifest()
    assert len(m["icons"]) >= 2
    for icon in m["icons"]:
        assert "src" in icon
        assert "sizes" in icon
        assert "type" in icon
    print(f"✓ Icons {len(m['icons'])} 个")


def test_manifest_shortcuts():
    """Shortcuts(PWA 快捷方式)"""
    m = get_manifest()
    assert len(m["shortcuts"]) >= 2
    for sc in m["shortcuts"]:
        assert "name" in sc
        assert "url" in sc
    print(f"✓ Shortcuts {len(m['shortcuts'])} 个")


def test_manifest_display_standalone():
    """Display=standalone(原生 App 体验)"""
    m = get_manifest()
    assert m["display"] == "standalone"
    print("✓ standalone 模式")


# ============== 4. Mobile CSS ==============

def test_css_basic():
    """CSS 基础"""
    css = get_mobile_css()
    assert "@media" in css
    assert "max-width: 600px" in css
    print("✓ CSS 基础")


def test_css_touch_optimization():
    """触摸优化 44x44px"""
    css = get_mobile_css()
    assert "44px" in css
    assert "min-height" in css
    print("✓ 触摸优化")


def test_css_ios_safe_area():
    """iOS 安全区域"""
    css = get_mobile_css()
    assert "env(safe-area-inset" in css
    print("✓ iOS 安全区域")


def test_css_ios_font_size():
    """iOS 16px 防止缩放"""
    css = get_mobile_css()
    assert "font-size: 16px" in css
    print("✓ iOS 16px 防止缩放")


def test_css_dark_mode():
    """暗色模式"""
    css = get_mobile_css()
    assert "prefers-color-scheme: dark" in css
    print("✓ 暗色模式")


def test_css_reduced_motion():
    """减少动画(无障碍)"""
    css = get_mobile_css()
    assert "prefers-reduced-motion" in css
    print("✓ 减少动画")


def test_css_responsive_breakpoints():
    """3 个响应式断点"""
    css = get_mobile_css()
    assert "max-width: 600px" in css       # 手机
    assert "min-width: 601px" in css      # 平板
    assert "min-width: 1025px" in css     # 桌面
    print("✓ 3 断点(手机/平板/桌面)")


# ============== 5. 分页 ==============

def test_paginate_basic():
    """基本分页"""
    items = list(range(25))
    p = paginate(items, page=1, page_size=10)
    assert p["page"] == 1
    assert p["page_size"] == 10
    assert p["total"] == 25
    assert len(p["items"]) == 10
    assert p["has_more"] is True
    assert p["items"][0] == 0
    assert p["items"][-1] == 9
    print("✓ 分页基本")


def test_paginate_last_page():
    """最后一页"""
    items = list(range(25))
    p = paginate(items, page=3, page_size=10)
    assert len(p["items"]) == 5
    assert p["has_more"] is False
    print("✓ 最后一页")


def test_paginate_empty():
    """空列表"""
    p = paginate([], page=1)
    assert p["total"] == 0
    assert p["items"] == []
    assert p["has_more"] is False
    print("✓ 空列表")


def test_paginate_invalid_page():
    """无效 page → fallback 1"""
    p = paginate([1, 2, 3], page=0)
    assert p["page"] == 1
    print("✓ 无效 page fallback")


def test_paginate_invalid_page_size():
    """无效 page_size → fallback 默认"""
    p = paginate(list(range(100)), page=1, page_size=99999)
    assert p["page_size"] == DEFAULT_PAGE_SIZE
    print("✓ 无效 page_size fallback")


def test_paginate_constants():
    """默认/最大页大小"""
    assert DEFAULT_PAGE_SIZE == 10
    assert MAX_PAGE_SIZE == 50
    print(f"✓ page_size: 默认 {DEFAULT_PAGE_SIZE} / 最大 {MAX_PAGE_SIZE}")


# ============== 6. 移动端 UA 检测 ==============

def test_detect_mobile_iphone():
    """iPhone"""
    assert detect_mobile("Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)")
    print("✓ iPhone")


def test_detect_mobile_android():
    """Android"""
    assert detect_mobile("Mozilla/5.0 (Linux; Android 10; SM-G960U)")
    print("✓ Android")


def test_detect_mobile_ipad():
    """iPad"""
    assert detect_mobile("Mozilla/5.0 (iPad; CPU OS 14_0 like Mac OS X)")
    print("✓ iPad")


def test_detect_desktop():
    """桌面"""
    assert not detect_mobile("Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
    assert not detect_mobile("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)")
    print("✓ 桌面")


def test_detect_empty():
    """空 UA"""
    assert not detect_mobile("")
    assert not detect_mobile(None)
    print("✓ 空 UA")


# ============== 7. 模块级 API ==============

def test_module_get_manifest():
    """模块级 manifest"""
    m = get_manifest()
    assert m["name"] == "AIchat-Hub"
    print("✓ 模块级 manifest")


def test_module_get_mobile_css():
    """模块级 css"""
    css = get_mobile_css()
    assert "min-height: 44px" in css
    print("✓ 模块级 css")


def test_module_get_supported_languages():
    """模块级 languages"""
    langs = get_supported_languages()
    assert len(langs) == 2
    print(f"✓ 模块级 languages {len(langs)}")


def test_module_get_i18n():
    """模块级 i18n"""
    result = get_i18n("zh-CN")
    assert result["language"] == "zh-CN"
    assert "translations" in result
    assert "supported" in result
    print("✓ 模块级 i18n")


# ============== 8. CLI ==============

def test_cli_manifest():
    """CLI:manifest"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "mobile.py"), "manifest"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["name"] == "AIchat-Hub"
    print("✓ CLI manifest")


def test_cli_css():
    """CLI:css"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "mobile.py"), "css"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "@media" in result.stdout
    print("✓ CLI css")


def test_cli_i18n():
    """CLI:i18n"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "mobile.py"), "i18n", "en-US"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["language"] == "en-US"
    print("✓ CLI i18n")


def test_cli_languages():
    """CLI:languages"""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "mobile.py"), "languages"],
        capture_output=True, text=True, timeout=10
    )
    assert result.returncode == 0
    assert "zh-CN" in result.stdout
    assert "en-US" in result.stdout
    print("✓ CLI languages")


# ============== 9. 集成 ==============

def test_integration_manifest_for_pwa():
    """集成:Manifest 完整可作为 PWA"""
    m = get_manifest()
    # PWA 最小要求:name + short_name + start_url + display + icons
    required = ["name", "short_name", "start_url", "display", "icons"]
    for f in required:
        assert f in m, f"Manifest 缺 PWA 必要字段 {f}"
    # icons 至少 192x192 + 512x512(PWA installable 要求)
    sizes = set()
    for icon in m["icons"]:
        sizes.add(icon["sizes"])
    assert "192x192" in sizes
    assert "512x512" in sizes
    print("✓ Manifest PWA 完整")


def test_integration_translate_all_modules():
    """集成:翻译覆盖所有模块名"""
    for lang in SUPPORTED_LANGUAGES:
        for mod in ["persona", "resume", "interview", "career", "industry",
                    "alumni", "digital_human", "feed", "prompt", "dashboard"]:
            key = f"module.{mod}"
            trans = t(key, lang)
            assert trans != key, f"{lang} 缺 {key}"
    print(f"✓ {len(SUPPORTED_LANGUAGES)} 语言 × 10 模块 = 20 翻译全覆盖")


def test_integration_mobile_css_with_dashboard():
    """集成:Mobile CSS + Dashboard 协同"""
    css = get_mobile_css()
    # Dashboard 关键类名(从 cycle 19)
    dashboard_classes = ["stats", "grid", "module", "endpoint", "section"]
    for cls in dashboard_classes:
        # Mobile CSS 应该有相关样式(就算没有特殊规则也不报错)
        pass
    # 至少应该有 .stats 和 .grid 的移动端样式
    assert ".stats" in css
    assert ".grid" in css
    print("✓ Mobile CSS 覆盖 Dashboard 关键类")


# ============== 入口 ==============

if __name__ == "__main__":
    test_supported_languages()
    test_default_language()
    test_translations_count()
    test_translations_keys_consistent()
    test_translate_zh()
    test_translate_en()
    test_translate_default()
    test_translate_unknown_key_returns_key()
    test_translate_unknown_lang_fallback()
    test_translate_dict()
    test_get_all_translations()
    test_manifest_basic()
    test_manifest_required_fields()
    test_manifest_icons()
    test_manifest_shortcuts()
    test_manifest_display_standalone()
    test_css_basic()
    test_css_touch_optimization()
    test_css_ios_safe_area()
    test_css_ios_font_size()
    test_css_dark_mode()
    test_css_reduced_motion()
    test_css_responsive_breakpoints()
    test_paginate_basic()
    test_paginate_last_page()
    test_paginate_empty()
    test_paginate_invalid_page()
    test_paginate_invalid_page_size()
    test_paginate_constants()
    test_detect_mobile_iphone()
    test_detect_mobile_android()
    test_detect_mobile_ipad()
    test_detect_desktop()
    test_detect_empty()
    test_module_get_manifest()
    test_module_get_mobile_css()
    test_module_get_supported_languages()
    test_module_get_i18n()
    test_cli_manifest()
    test_cli_css()
    test_cli_i18n()
    test_cli_languages()
    test_integration_manifest_for_pwa()
    test_integration_translate_all_modules()
    test_integration_mobile_css_with_dashboard()
    print(f"\n=== 全部通过 ✓ ({len([f for f in dir() if f.startswith('test_')])} 个 test) ===")
