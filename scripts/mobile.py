#!/usr/bin/env python3
"""
aichat-Hub Mobile (移动端 PWA + i18n) 模块
=========================================
大学生移动端适配 + 国际化(i18n)基础。

三大核心:
  1. PWA manifest(JSON) — 让浏览器"添加到主屏幕"
  2. mobile.css(响应式 + 触摸优化 + iOS 安全区域)
  3. i18n 字典(中/英 20+ 关键字符串)

API 优化:
  - 列表分页(默认 limit=10)
  - payload 压缩
  - 移动端用户代理检测

沙箱安全:
  - 纯静态(manifest + CSS + dict)
  - 无 Service Worker(本地项目,沙箱友好)

Cycle 20 — 移动端 + 最终发布
"""
from __future__ import annotations
import json
import re
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


# ============== 支持语言 ==============

SUPPORTED_LANGUAGES = ["zh-CN", "en-US"]
DEFAULT_LANGUAGE = "zh-CN"

LANGUAGE_LABELS = {
    "zh-CN": "中文",
    "en-US": "English",
}


# ============== i18n 字典 ==============

TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "zh-CN": {
        # 通用
        "service.running": "服务运行中",
        "service.name": "AIchat-Hub",
        "error.bad_request": "请求错误",
        "error.not_found": "未找到",
        "error.internal": "内部错误",
        # 模块
        "module.persona": "虚拟人",
        "module.resume": "简历",
        "module.interview": "面试",
        "module.career": "职业规划",
        "module.industry": "行业",
        "module.alumni": "校友",
        "module.digital_human": "数字虚拟人",
        "module.feed": "Feed",
        "module.prompt": "Prompt 模板",
        "module.dashboard": "Dashboard",
        # 状态
        "status.completed": "已完成",
        "status.in_progress": "进行中",
        "status.failed": "失败",
        # 操作
        "action.create": "创建",
        "action.update": "更新",
        "action.delete": "删除",
        "action.publish": "发布",
        "action.like": "点赞",
        "action.comment": "评论",
        "action.share": "分享",
    },
    "en-US": {
        # General
        "service.running": "Service running",
        "service.name": "AIchat-Hub",
        "error.bad_request": "Bad request",
        "error.not_found": "Not found",
        "error.internal": "Internal error",
        # Modules
        "module.persona": "Persona",
        "module.resume": "Resume",
        "module.interview": "Interview",
        "module.career": "Career",
        "module.industry": "Industry",
        "module.alumni": "Alumni",
        "module.digital_human": "Digital Human",
        "module.feed": "Feed",
        "module.prompt": "Prompt Templates",
        "module.dashboard": "Dashboard",
        # Status
        "status.completed": "Completed",
        "status.in_progress": "In progress",
        "status.failed": "Failed",
        # Actions
        "action.create": "Create",
        "action.update": "Update",
        "action.delete": "Delete",
        "action.publish": "Publish",
        "action.like": "Like",
        "action.comment": "Comment",
        "action.share": "Share",
    },
}


# ============== i18n 函数 ==============

def t(key: str, lang: str = DEFAULT_LANGUAGE) -> str:
    """翻译查找(支持 fallback)"""
    if lang not in TRANSLATIONS:
        lang = DEFAULT_LANGUAGE
    translations = TRANSLATIONS.get(lang, TRANSLATIONS[DEFAULT_LANGUAGE])
    return translations.get(key, key)


def translate_dict(d: Dict[str, Any], lang: str) -> Dict[str, Any]:
    """翻译 dict 中的 key(简单替换:module.resume → 简历/Resume)"""
    result = {}
    for k, v in d.items():
        # 尝试翻译 key
        translated_key = t(k, lang) if "." in k else k
        result[translated_key] = v
    return result


def get_all_translations(lang: str = DEFAULT_LANGUAGE) -> Dict[str, str]:
    """获取某语言全部翻译"""
    return TRANSLATIONS.get(lang, {})


# ============== PWA Manifest ==============

PWA_MANIFEST: Dict[str, Any] = {
    "name": "AIchat-Hub",
    "short_name": "AIchat-Hub",
    "description": "中国大学生职业社交 + 数字虚拟人框架",
    "start_url": "/",
    "scope": "/",
    "display": "standalone",
    "orientation": "portrait",
    "background_color": "#f5f5f7",
    "theme_color": "#667eea",
    "lang": "zh-CN",
    "dir": "ltr",
    "categories": ["education", "productivity", "social"],
    "icons": [
        {
            "src": "/static/icon-192.png",
            "sizes": "192x192",
            "type": "image/png",
            "purpose": "any maskable",
        },
        {
            "src": "/static/icon-512.png",
            "sizes": "512x512",
            "type": "image/png",
            "purpose": "any maskable",
        },
    ],
    "shortcuts": [
        {
            "name": "简历",
            "short_name": "简历",
            "url": "/api/resume/personas",
            "icons": [{"src": "/static/icon-192.png", "sizes": "192x192"}],
        },
        {
            "name": "面试",
            "short_name": "面试",
            "url": "/api/interview/interviewers",
            "icons": [{"src": "/static/icon-192.png", "sizes": "192x192"}],
        },
        {
            "name": "Feed",
            "short_name": "Feed",
            "url": "/api/feed/list",
            "icons": [{"src": "/static/icon-192.png", "sizes": "192x192"}],
        },
    ],
}


# ============== Mobile CSS ==============

MOBILE_CSS = """/* AIchat-Hub Mobile-First CSS */
/* 触摸优化:按钮最小 44x44px */

* { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Hiragino Sans GB", sans-serif;
  margin: 0; padding: 0; background: #f5f5f7; color: #1d1d1f;
  /* iOS 安全区域 */
  padding-top: env(safe-area-inset-top);
  padding-bottom: env(safe-area-inset-bottom);
  padding-left: env(safe-area-inset-left);
  padding-right: env(safe-area-inset-right);
  -webkit-font-smoothing: antialiased;
  -webkit-text-size-adjust: 100%;
}

/* 触摸优化:按钮最小 44x44px */
button, .btn, [role="button"] {
  min-height: 44px;
  min-width: 44px;
  padding: 12px 20px;
  font-size: 16px;  /* iOS 防止缩放 */
  border: none;
  border-radius: 8px;
  background: #667eea;
  color: white;
  cursor: pointer;
  transition: opacity 0.2s;
}
button:active, .btn:active { opacity: 0.7; }

/* 输入框 iOS 16px 防止缩放 */
input, textarea, select {
  font-size: 16px;
  padding: 12px;
  border: 1px solid #d2d2d7;
  border-radius: 8px;
  width: 100%;
  -webkit-appearance: none;
  appearance: none;
}

/* 移动端:单列布局 */
@media (max-width: 600px) {
  .container { padding: 12px; }
  .stats { grid-template-columns: repeat(2, 1fr); gap: 8px; }
  .stat { padding: 12px; }
  .stat .num { font-size: 1.6em; }
  .grid { grid-template-columns: 1fr; }
  .endpoint-list { gap: 4px; }
  .endpoint { font-size: 0.7em; }
  h1 { font-size: 1.5em !important; }
  h2 { font-size: 1.2em !important; }
  header { padding: 16px 12px !important; }
}

/* 平板:2 列 */
@media (min-width: 601px) and (max-width: 1024px) {
  .grid { grid-template-columns: repeat(2, 1fr); }
  .stats { grid-template-columns: repeat(3, 1fr); }
}

/* 桌面:3+ 列 */
@media (min-width: 1025px) {
  .grid { grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); }
}

/* 横屏适配 */
@media (orientation: landscape) and (max-height: 500px) {
  header { padding: 12px 16px !important; }
  .container { padding: 12px 16px; }
}

/* 暗色模式 */
@media (prefers-color-scheme: dark) {
  body { background: #1c1c1e; color: #f5f5f7; }
  .stat, .section, .module { background: #2c2c2e; color: #f5f5f7; }
  .endpoint.path { background: #3a3a3c; color: #f5f5f7; }
}

/* 减少动画(无障碍) */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
"""


# ============== 移动端 API 优化 ==============

# 默认分页
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50


def paginate(items: List[Any], page: int = 1, page_size: int = DEFAULT_PAGE_SIZE) -> Dict[str, Any]:
    """分页辅助"""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > MAX_PAGE_SIZE:
        page_size = DEFAULT_PAGE_SIZE
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "items": items[start:end],
        "page": page,
        "page_size": page_size,
        "total": len(items),
        "has_more": end < len(items),
    }


def detect_mobile(user_agent: str) -> bool:
    """检测移动端 User-Agent"""
    if not user_agent:
        return False
    ua = user_agent.lower()
    mobile_keywords = ["mobile", "android", "iphone", "ipad", "ipod",
                       "blackberry", "windows phone", "webos", "opera mini"]
    return any(kw in ua for kw in mobile_keywords)


# ============== 核心 API ==============

def get_manifest() -> Dict[str, Any]:
    """PWA Manifest"""
    return PWA_MANIFEST


def get_mobile_css() -> str:
    """Mobile CSS"""
    return MOBILE_CSS


def get_supported_languages() -> List[Dict[str, str]]:
    """支持语言"""
    return [
        {"code": lang, "label": LANGUAGE_LABELS[lang]}
        for lang in SUPPORTED_LANGUAGES
    ]


def get_i18n(lang: str = DEFAULT_LANGUAGE) -> Dict[str, Any]:
    """i18n 字典 + 元数据"""
    if lang not in TRANSLATIONS:
        lang = DEFAULT_LANGUAGE
    return {
        "language": lang,
        "translations": TRANSLATIONS[lang],
        "supported": SUPPORTED_LANGUAGES,
        "total_keys": len(TRANSLATIONS[lang]),
    }


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 mobile.py {manifest|css|translations|i18n <lang>|languages}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "manifest":
        print(json.dumps(get_manifest(), ensure_ascii=False, indent=2))
    elif cmd == "css":
        print(get_mobile_css())
    elif cmd == "translations":
        # 默认 zh-CN
        lang = sys.argv[2] if len(sys.argv) > 2 else "zh-CN"
        print(json.dumps(get_i18n(lang), ensure_ascii=False, indent=2))
    elif cmd == "i18n":
        lang = sys.argv[2] if len(sys.argv) > 2 else "zh-CN"
        print(json.dumps(get_i18n(lang), ensure_ascii=False, indent=2))
    elif cmd == "languages":
        for l in get_supported_languages():
            print(f"  {l['code']}: {l['label']}")
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
