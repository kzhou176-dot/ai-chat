#!/usr/bin/env python3
"""
aichat-hub Web 后端(零依赖)
=============================
基于 stdlib http.server 的简易 REST API。

Endpoints:
  GET  /                       - 服务信息
  GET  /api/personas           - 列出所有虚拟人
  GET  /api/voices             - 列出所有 TTS 声音
  POST /api/chat               - 单 LLM 对话
  POST /api/compare            - 多 LLM 对比
  POST /api/synthesize         - TTS 合成(返回元数据)
  POST /api/avatar             - 嘴型同步(返回元数据)
  POST /api/avatar/tts         - TTS + Avatar 串联

特点:
  - 零外部依赖(用 stdlib http.server + json)
  - JSON 请求/响应
  - 错误返回统一格式 {"error": "..."}
  - 可用 python -m aichat_hub.web 启动
  - 测试可用 urllib.request 模拟 HTTP

Cycle 7 - 基础版
"""
from __future__ import annotations
import json
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlparse

# 让同目录模块可导入
sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))


# ============== 路由注册 ==============

ROUTES: List[Dict[str, Any]] = []


def route(method: str, path: str):
    """路由装饰器"""
    def decorator(func: Callable) -> Callable:
        ROUTES.append({"method": method, "path": path, "handler": func})
        return func
    return decorator


# ============== 健康检查 ==============

@route("GET", "/")
def index(_handler) -> Tuple[int, Dict[str, Any]]:
    return 200, {
        "service": "aichat-hub",
        "version": "1.0.0",
        "endpoints": [
            "GET  /api/personas",
            "GET  /api/voices",
            "POST /api/chat",
            "POST /api/compare",
            "POST /api/synthesize",
            "POST /api/avatar",
            "POST /api/avatar/tts",
            "POST /api/score",
            "GET  /api/cost",
            "GET  /api/analytics",
            "GET  /api/resume/personas",
            "GET  /api/resume/variants",
            "POST /api/resume/generate",
            "POST /api/resume/rewrite",
            "POST /api/resume/score",
            "GET  /api/interview/interviewers",
            "POST /api/interview/start",
            "POST /api/interview/answer",
            "POST /api/interview/end",
            "GET  /api/career/dimensions",
            "GET  /api/career/codes",
            "POST /api/career/start",
            "POST /api/career/answer",
            "POST /api/career/profile",
            "GET  /api/industry/list",
            "GET  /api/industry/profile",
            "POST /api/industry/recommend",
            "POST /api/industry/start",
            "POST /api/industry/answer",
            "POST /api/industry/ask",
            "GET  /api/alumni/schools",
            "GET  /api/alumni/list",
            "POST /api/alumni/match",
            "POST /api/alumni/refer",
            "POST /api/alumni/refer/status",
            "GET  /api/human/presets",
            "GET  /api/human/meta",
            "POST /api/human/create",
            "POST /api/human/react",
            "GET  /api/human/list",
            "POST /api/human/render",
            "GET  /api/feed/categories",
            "GET  /api/feed/list",
            "GET  /api/feed/post",
            "POST /api/feed/publish",
            "POST /api/feed/like",
            "POST /api/feed/comment",
            "POST /api/feed/recommend",
            "GET  /api/prompt/categories",
            "GET  /api/prompt/list",
            "GET  /api/prompt/get",
            "GET  /api/prompt/search",
            "POST /api/prompt/render",
            "GET  /api/prompt/summary",
            "GET  /api/dashboard/meta",
            "GET  /api/dashboard/html",
            "GET  /api/mobile/manifest",
            "GET  /api/mobile/css",
            "GET  /api/mobile/languages",
            "GET  /api/mobile/i18n",
            "GET  /api/papers/stats",
            "GET  /api/papers/keywords",
            "GET  /api/papers/list",
            "GET  /api/papers/get",
            "POST /api/papers/search",
            "GET  /api/papers/cite",
            "POST /api/paper_chat/start",
            "POST /api/paper_chat/ask",
            "POST /api/paper_chat/end",
            "GET  /api/release/readiness",
            "GET  /api/release/stats",
            "GET  /api/release/tags",
            "GET  /api/release/notes",
            "POST /api/release/tag",
        ],
        "personas": ["xiaoai", "dr_li", "xiaozhi"],
        "resume_personas": ["mentor", "hr", "senior"],
        "interviewers": ["tech", "behavioral", "hr", "pressure"],
        "career_dimensions": ["R", "I", "A", "S", "E", "C"],
        "industries": ["algorithm", "product", "operation", "design", "data",
                       "finance", "consulting", "fmcg", "realestate"],
        "digital_human_presets": ["xiaoai", "dr_li", "xiaozhi", "interview_tech", "interview_hr",
                                  "career_guide", "industry_algorithm", "senior_eng"],
        "feed_categories": ["alumni_post", "industry_post", "career_post", "recruit_post"],
        "prompt_categories": ["resume", "interview", "career", "industry", "alumni",
                              "digital_human", "feed", "general"],
        "providers": ["openai", "deepseek", "zhipu", "dashscope", "moonshot", "anthropic"],
    }


# ============== 虚拟人 ==============

@route("GET", "/api/personas")
def list_personas(_handler) -> Tuple[int, Dict[str, Any]]:
    from persona import PersonaStore
    store = PersonaStore()
    return 200, {
        "personas": store.list_all(),
    }


# ============== TTS 声音 ==============

@route("GET", "/api/voices")
def list_voices(handler) -> Tuple[int, Dict[str, Any]]:
    from tts import MockProvider
    lang_filter = handler.query.get("lang")
    mock = MockProvider()
    voices = mock.list_voices(lang_filter)
    return 200, {
        "voices": [
            {
                "id": v.id,
                "name": v.name,
                "language": v.language,
                "gender": v.gender,
                "age_range": v.age_range,
                "style": v.style,
            }
            for v in voices
        ]
    }


# ============== LLM 对话 ==============

@route("POST", "/api/chat")
def chat_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    prompt = body.get("prompt") or body.get("message")
    if not prompt:
        return 400, {"error": "missing 'prompt' field"}
    provider = body.get("provider", "openai")
    persona = body.get("persona")
    system = body.get("system")
    temperature = float(body.get("temperature", 0.7))

    # 集成 Persona(注入 system prompt)
    if persona and not system:
        from persona import PersonaStore
        pstore = PersonaStore()
        p = pstore.load(persona)
        if p:
            system = p.to_system_prompt()

    from llm_client import LLMClient, Message
    client = LLMClient(provider=provider)
    msgs = []
    if system:
        msgs.append(Message("system", system))
    msgs.append(Message("user", prompt))

    resp = client.chat(msgs, temperature=temperature)
    # ChatResponse 没有 error 字段(llm_client 沙盒 mock 永远成功)
    # 用 getattr 兜底
    error = getattr(resp, "error", None)
    has_error = error is not None and error != ""
    return 500 if has_error else 200, {
        "ok": not has_error,
        "provider": provider,
        "model": resp.model,
        "content": resp.content,
        "error": error,
        "latency_ms": resp.latency_ms,
        "total_tokens": resp.usage.get("total_tokens", 0),
        "cost_usd": resp.cost_usd,
    }


# ============== 多 LLM 对比 ==============

@route("POST", "/api/compare")
def compare_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    body = handler.json_body
    if not body:
        return 400, {"error": "empty body"}
    prompt = body.get("prompt") or body.get("message")
    if not prompt:
        return 400, {"error": "missing 'prompt' field"}
    providers = body.get("providers") or ["openai", "deepseek", "zhipu"]

    from llm_client import LLMClient, Message
    msgs = [Message("user", prompt)]
    results = []
    for prov in providers:
        client = LLMClient(provider=prov)
        resp = client.chat(msgs)
        error = getattr(resp, "error", None)
        has_error = error is not None and error != ""
        results.append({
            "provider": prov,
            "model": resp.model,
            "ok": not has_error,
            "content": resp.content if not has_error else None,
            "error": error,
            "latency_ms": resp.latency_ms,
            "total_tokens": resp.usage.get("total_tokens", 0),
            "cost_usd": resp.cost_usd,
        })
    return 200, {"prompt": prompt, "results": results}


# ============== TTS 合成 ==============

@route("POST", "/api/synthesize")
def synthesize_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    body = handler.json_body
    if not body:
        return 400, {"error": "empty body"}
    text = body.get("text")
    if not text:
        return 400, {"error": "missing 'text' field"}
    voice_id = body.get("voice_id", "female-young")
    provider = body.get("provider", "mock")
    speed = float(body.get("speed", 1.0))
    pitch = float(body.get("pitch", 0.0))

    from tts import get_provider, AudioFormat
    prov = get_provider(provider)
    fmt = AudioFormat(body.get("format", "mp3"))
    result = prov.synthesize(text, voice_id, fmt, speed=speed, pitch=pitch)
    return 200, {"result": result.to_dict()}


# ============== Avatar 视频 ==============

@route("POST", "/api/avatar")
def avatar_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    body = handler.json_body
    if not body:
        return 400, {"error": "empty body"}
    text = body.get("text")
    avatar_id = body.get("avatar_id", "default_avatar")
    if not text:
        return 400, {"error": "missing 'text' field"}
    voice_id = body.get("voice_id", "female-young")
    provider = body.get("provider", "mock")
    quality = body.get("quality", "standard")

    from avatar_video import get_provider, AvatarQuality
    prov = get_provider(provider)
    q = AvatarQuality(quality)
    result = prov.synthesize_video(
        text=text, voice_id=voice_id, avatar_id=avatar_id, quality=q
    )
    return 200, {"result": result.to_dict()}


# ============== TTS + Avatar 串联 ==============

@route("POST", "/api/avatar/tts")
def avatar_tts_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    body = handler.json_body
    if not body:
        return 400, {"error": "empty body"}
    text = body.get("text")
    persona = body.get("persona", "xiaoai")
    if not text:
        return 400, {"error": "missing 'text' field"}

    from tts import MockProvider, get_voice_for_persona
    from avatar_video import MockProvider as AvatarMock, get_avatar_for_persona

    # Step 1: TTS
    tts_mock = MockProvider()
    voice_id = get_voice_for_persona(persona)
    tts_result = tts_mock.synthesize(text, voice_id)

    # Step 2: Avatar(用 TTS 时长)
    avatar_mock = AvatarMock()
    avatar_id = get_avatar_for_persona(persona)
    avatar_result = avatar_mock.synthesize_video(
        text=text,
        voice_id=voice_id,
        avatar_id=avatar_id,
        audio_format=tts_result,
    )
    return 200, {
        "persona": persona,
        "text": text,
        "tts": tts_result.to_dict(),
        "avatar": avatar_result.to_dict(),
    }


# ============== 用户行为分析 ==============

@route("GET", "/api/analytics")
def analytics_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    from analytics import Analytics
    a = Analytics()
    return 200, {"report": a.report(), "events_count": len(a.events)}


# ============== 成本追踪 ==============

@route("GET", "/api/cost")
def cost_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    from cost import CostTracker
    budget = float(handler.query.get("budget", 0)) or None
    tracker = CostTracker(budget_usd=budget)
    return 200, {
        "report": tracker.report(),
        "entries_count": len(tracker.entries),
    }


# ============== 5 维评分 ==============

@route("POST", "/api/score")
def score_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    text = body.get("text", "")
    prompt = body.get("prompt", "")
    latency_ms = float(body.get("latency_ms", 0.0))

    from scoring import Scorer
    scorer = Scorer()
    result = scorer.score(text, prompt, latency_ms)
    return 200, {"result": result.to_dict()}


@route("GET", "/api/resume/personas")
def resume_personas_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出简历辅导的 3 个角色"""
    from resume import list_personas
    return 200, {"personas": list_personas()}


@route("GET", "/api/resume/variants")
def resume_variants_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出简历变体"""
    from resume import list_variants
    return 200, {"variants": list_variants()}


@route("POST", "/api/resume/generate")
def resume_generate_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """生成简历(3 变体之一)"""
    from resume import ResumeProfile, generate_resume
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    profile_d = body.get("profile", {})
    variant = body.get("variant", "technical")
    try:
        profile = ResumeProfile.from_dict(profile_d)
    except Exception as e:
        return 400, {"error": f"invalid profile: {e}"}
    text = generate_resume(profile, variant=variant)
    return 200, {"text": text, "variant": variant, "length": len(text)}


@route("POST", "/api/resume/rewrite")
def resume_rewrite_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """改写简历(3 角色之一)"""
    from resume import ResumeProfile, rewrite_resume
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    profile_d = body.get("profile", {})
    variant = body.get("variant", "technical")
    persona = body.get("persona", "mentor")
    try:
        profile = ResumeProfile.from_dict(profile_d)
    except Exception as e:
        return 400, {"error": f"invalid profile: {e}"}
    text, notes = rewrite_resume(profile, variant=variant, persona=persona)
    return 200, {"text": text, "notes": notes, "variant": variant, "persona": persona}


@route("POST", "/api/resume/score")
def resume_score_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """5 维评分"""
    from resume import ResumeProfile, score_resume
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    profile_d = body.get("profile", {})
    try:
        profile = ResumeProfile.from_dict(profile_d)
    except Exception as e:
        return 400, {"error": f"invalid profile: {e}"}
    result = score_resume(profile)
    return 200, {"result": result.to_dict()}


# ============== 模拟面试(Cycle 12) ==============

# 内存 session 存储(沙箱友好,重启即清)
_INTERVIEW_SESSIONS: Dict[str, Any] = {}


@route("GET", "/api/interview/interviewers")
def interview_interviewers_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出 4 个面试官"""
    from interview import list_interviewers
    return 200, {"interviewers": list_interviewers()}


@route("POST", "/api/interview/start")
def interview_start_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """开启模拟面试"""
    from interview import start_interview, get_interviewer
    body = handler.json_body
    if body is None:
        body = {}
    role = body.get("interviewer", "tech")
    target_position = body.get("target_position", "算法工程师")
    rounds = int(body.get("rounds", 3))
    session = start_interview(role, target_position=target_position, rounds=rounds)
    # 存 session
    import uuid
    sid = str(uuid.uuid4())[:8]
    _INTERVIEW_SESSIONS[sid] = session
    return 200, {
        "session_id": sid,
        "interviewer": get_interviewer(role),
        "target_position": target_position,
        "rounds": len(session.questions),
        "first_question": {
            "text": session.questions[0].text,
            "key_points": session.questions[0].key_points,
            "difficulty": session.questions[0].difficulty,
        },
    }


@route("POST", "/api/interview/answer")
def interview_answer_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """提交回答"""
    from interview import submit_answer
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    sid = body.get("session_id")
    answer = body.get("answer", "")
    if not sid or sid not in _INTERVIEW_SESSIONS:
        return 404, {"error": "session not found"}
    session = _INTERVIEW_SESSIONS[sid]
    try:
        result = submit_answer(session, answer)
    except ValueError as e:
        return 400, {"error": str(e)}
    next_q = None
    if not session.completed and session.round_idx < len(session.questions):
        nq = session.questions[session.round_idx]
        next_q = {
            "text": nq.text,
            "key_points": nq.key_points,
            "difficulty": nq.difficulty,
        }
    return 200, {
        "result": result.to_dict(),
        "next_question": next_q,
        "completed": session.completed,
        "round_idx": session.round_idx,
    }


@route("POST", "/api/interview/end")
def interview_end_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """结束面试 + 复盘报告"""
    from interview import end_interview
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    sid = body.get("session_id")
    if not sid or sid not in _INTERVIEW_SESSIONS:
        return 404, {"error": "session not found"}
    session = _INTERVIEW_SESSIONS[sid]
    report = end_interview(session)
    # 清理 session
    del _INTERVIEW_SESSIONS[sid]
    return 200, {"report": report}


# ============== 霍兰德职业测试(Cycle 13) ==============

# 内存 test session 存储
_CAREER_SESSIONS: Dict[str, Any] = {}


@route("GET", "/api/career/dimensions")
def career_dimensions_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出 6 维 RIASEC"""
    from career_profile import list_dimensions
    return 200, {"dimensions": list_dimensions()}


@route("GET", "/api/career/codes")
def career_codes_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出 Holland Code 映射"""
    from career_profile import HOLLAND_CODE_MAP
    return 200, {"codes": HOLLAND_CODE_MAP}


@route("POST", "/api/career/start")
def career_start_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """开启霍兰德测试"""
    from career_profile import start_career_test
    body = handler.json_body
    if body is None:
        body = {}
    target_position = body.get("target_position", "")
    question_count = int(body.get("question_count", 60))
    session = start_career_test(
        target_position=target_position,
        question_count=question_count,
    )
    import uuid
    sid = str(uuid.uuid4())[:8]
    _CAREER_SESSIONS[sid] = session
    first = session.questions[0] if session.questions else None
    return 200, {
        "session_id": sid,
        "target_position": target_position,
        "total_questions": len(session.questions),
        "first_question": first,
    }


@route("POST", "/api/career/answer")
def career_answer_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """提交一题答案"""
    from career_profile import submit_answer
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    sid = body.get("session_id")
    qid = body.get("qid", "")
    answer = body.get("answer", "")
    if not sid or sid not in _CAREER_SESSIONS:
        return 404, {"error": "session not found"}
    session = _CAREER_SESSIONS[sid]
    try:
        result = submit_answer(session, qid, answer)
    except ValueError as e:
        return 400, {"error": str(e)}
    return 200, result


@route("POST", "/api/career/profile")
def career_profile_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """生成职业画像"""
    from career_profile import compute_profile
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    sid = body.get("session_id")
    if not sid or sid not in _CAREER_SESSIONS:
        return 404, {"error": "session not found"}
    session = _CAREER_SESSIONS[sid]
    if not session.completed:
        return 400, {"error": f"test not completed, {session.round_idx}/{len(session.questions)}"}
    profile = compute_profile(session)
    # 清理 session
    del _CAREER_SESSIONS[sid]
    return 200, {"profile": profile.to_dict()}


# ============== 行业洞察(Cycle 14) ==============

_INDUSTRY_SESSIONS: Dict[str, Any] = {}


@route("GET", "/api/industry/list")
def industry_list_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出 9 大行业"""
    from industry_insight import list_industries
    return 200, {"industries": list_industries()}


@route("GET", "/api/industry/profile")
def industry_profile_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """获取单个行业画像"""
    from industry_insight import get_industry
    industry = handler.query.get("id", "algorithm")
    return 200, {"profile": get_industry(industry)}


@route("POST", "/api/industry/recommend")
def industry_recommend_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """基于 Holland Code 推荐行业"""
    from industry_insight import recommend_industries_for_holland
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    code = body.get("holland_code", "")
    recs = recommend_industries_for_holland(code)
    return 200, {"recommendations": recs, "holland_code": code}


@route("POST", "/api/industry/start")
def industry_start_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """开启行业洞察对话"""
    from industry_insight import start_industry_session
    body = handler.json_body
    if body is None:
        body = {}
    industry = body.get("industry", "algorithm")
    rounds = int(body.get("rounds", 3))
    user_holland_code = body.get("user_holland_code", "")
    session = start_industry_session(
        industry=industry, rounds=rounds,
        user_holland_code=user_holland_code,
    )
    import uuid
    sid = str(uuid.uuid4())[:8]
    _INDUSTRY_SESSIONS[sid] = session
    first = session.questions[0] if session.questions else None
    return 200, {
        "session_id": sid,
        "industry": industry,
        "user_holland_code": user_holland_code,
        "rounds": len(session.questions),
        "first_question": {"text": first.text, "key_points": first.key_points} if first else None,
    }


@route("POST", "/api/industry/answer")
def industry_answer_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """提交行业洞察对话回答"""
    from industry_insight import submit_answer
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    sid = body.get("session_id")
    answer = body.get("answer", "")
    if not sid or sid not in _INDUSTRY_SESSIONS:
        return 404, {"error": "session not found"}
    session = _INDUSTRY_SESSIONS[sid]
    try:
        result = submit_answer(session, answer)
    except ValueError as e:
        return 400, {"error": str(e)}
    next_q = None
    if not session.completed and session.round_idx < len(session.questions):
        nq = session.questions[session.round_idx]
        next_q = {"text": nq.text, "key_points": nq.key_points}
    return 200, {
        "result": result.to_dict(),
        "next_question": next_q,
        "completed": session.completed,
        "round_idx": session.round_idx,
    }


@route("POST", "/api/industry/ask")
def industry_ask_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """行业问答(基于规则,无 LLM)"""
    from industry_insight import answer_industry_question
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    industry = body.get("industry", "algorithm")
    question = body.get("question", "")
    result = answer_industry_question(industry, question)
    return 200, result


# ============== 校友匹配 + 内推(Cycle 15) ==============


@route("GET", "/api/alumni/schools")
def alumni_schools_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出支持邮箱验证的学校"""
    from alumni import list_supported_schools
    return 200, {"schools": list_supported_schools()}


@route("GET", "/api/alumni/list")
def alumni_list_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """列出校友(可按学校/行业筛选)"""
    from alumni import list_alumni
    school = handler.query.get("school", "")
    industry = handler.query.get("industry", "")
    items = list_alumni(school=school, industry=industry)
    return 200, {"alumni": items, "count": len(items)}


@route("POST", "/api/alumni/match")
def alumni_match_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """4 维匹配 Top N 校友"""
    from alumni import StudentProfile, find_matches, verify_school_email
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    s = StudentProfile(
        name=body.get("name", ""),
        school=body.get("school", ""),
        department=body.get("department", ""),
        major=body.get("major", ""),
        graduation_year=body.get("graduation_year", 2026),
        target_industry=body.get("target_industry", "互联网"),
        target_position=body.get("target_position", "算法工程师"),
        target_city=body.get("target_city", "北京"),
        email=body.get("email", ""),
    )
    top_n = int(body.get("top_n", 5))
    matches = find_matches(s, top_n=top_n)
    verified = s.is_verified() if s.email else False
    return 200, {
        "student_verified": verified,
        "matches": [m.to_dict() for m in matches],
        "count": len(matches),
    }


@route("POST", "/api/alumni/refer")
def alumni_refer_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """发起内推请求"""
    from alumni import request_refer
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    try:
        req = request_refer(
            student_name=body.get("student_name", ""),
            student_school=body.get("student_school", ""),
            student_major=body.get("student_major", ""),
            target_company=body.get("target_company", ""),
            target_position=body.get("target_position", ""),
            alumni_id=body.get("alumni_id", ""),
            message=body.get("message", ""),
        )
    except ValueError as e:
        return 400, {"error": str(e)}
    return 200, {"request": req.to_dict()}


@route("POST", "/api/alumni/refer/status")
def alumni_refer_status_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """查询/更新内推状态(简化版:返回合法状态列表)"""
    from alumni import REFER_STATUS
    req_id = handler.query.get("request_id", "")
    return 200, {
        "request_id": req_id,
        "valid_statuses": list(REFER_STATUS.keys()),
        "status_labels": REFER_STATUS,
    }


# ============== 数字虚拟人(Cycle 16) ==============


@route("GET", "/api/human/presets")
def human_presets_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出 8 个预设虚拟人"""
    from digital_human import list_presets
    return 200, {"presets": list_presets()}


@route("GET", "/api/human/meta")
def human_meta_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """枚举:表情/动作/状态/风格"""
    from digital_human import EXPRESSIONS, ACTIONS, STATES, STYLES
    return 200, {
        "expressions": EXPRESSIONS,
        "actions": ACTIONS,
        "states": STATES,
        "styles": STYLES,
    }


@route("POST", "/api/human/create")
def human_create_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """创建数字虚拟人"""
    from digital_human import create_digital_human, save_human, Appearance
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    preset = body.get("preset_id", "")
    name = body.get("name")
    # 自定义外观
    app_data = body.get("appearance")
    custom_app = None
    if app_data:
        custom_app = Appearance(**app_data)
    custom_p = body.get("personality")
    h = create_digital_human(
        preset_id=preset,
        name=name,
        custom_appearance=custom_app,
        custom_personality=custom_p,
    )
    save_human(h)
    return 200, {"human": h.to_dict()}


@route("POST", "/api/human/react")
def human_react_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """触发虚拟人反应"""
    from digital_human import get_human, detect_expression_from_text
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    hid = body.get("human_id", "")
    h = get_human(hid)
    if h is None:
        return 404, {"error": "human not found"}
    trigger = body.get("trigger", "")
    expression = body.get("expression", "")
    action = body.get("action", "")
    note = body.get("note", "")
    # 如果没指定 expression,自动检测
    if not expression and trigger:
        expression = detect_expression_from_text(trigger)
    try:
        log = h.react(trigger, expression=expression or "neutral", action=action, note=note)
    except ValueError as e:
        return 400, {"error": str(e)}
    return 200, {
        "reaction": {
            "trigger": log.trigger,
            "expression": log.expression,
            "action": log.action,
            "state": log.state,
        },
        "human": h.to_dict(),
    }


@route("GET", "/api/human/list")
def human_list_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出所有创建的虚拟人"""
    from digital_human import list_humans
    return 200, {"humans": list_humans()}


@route("POST", "/api/human/render")
def human_render_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """生成渲染元数据(沙箱友好)"""
    from digital_human import get_human, render_metadata
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    hid = body.get("human_id", "")
    h = get_human(hid)
    if h is None:
        return 404, {"error": "human not found"}
    return 200, {"metadata": render_metadata(h)}


# ============== Feed 时间线(Cycle 17) ==============


@route("GET", "/api/feed/categories")
def feed_categories_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出 4 类 Feed"""
    from feed import list_categories
    return 200, {"categories": list_categories()}


@route("GET", "/api/feed/list")
def feed_list_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """列出 Feed(可按 category/school/industry 筛选)"""
    from feed import list_feed
    category = handler.query.get("category", "") or None
    school = handler.query.get("school", "")
    industry = handler.query.get("industry", "")
    sort = handler.query.get("sort", "time")
    limit = int(handler.query.get("limit", "20"))
    items = list_feed(
        category=category, author_school=school,
        author_industry=industry, sort=sort, limit=limit,
    )
    return 200, {"items": items, "count": len(items)}


@route("GET", "/api/feed/post")
def feed_get_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """获取单条 Feed"""
    from feed import get_post
    pid = handler.query.get("id", "")
    post = get_post(pid)
    if post is None:
        return 404, {"error": "post not found"}
    return 200, {"post": post}


@route("POST", "/api/feed/publish")
def feed_publish_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """发布 Feed"""
    from feed import publish_post
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    post = publish_post(
        author_id=body.get("author_id", "anonymous"),
        author_name=body.get("author_name", "Anonymous"),
        author_role=body.get("author_role", "user"),
        author_avatar=body.get("author_avatar", "👤"),
        content=body.get("content", ""),
        category=body.get("category", "career_post"),
        tags=body.get("tags", []),
        author_school=body.get("author_school", ""),
        author_industry=body.get("author_industry", ""),
    )
    return 200, {"post": post}


@route("POST", "/api/feed/like")
def feed_like_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """点赞 / 取消"""
    from feed import like_post
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    pid = body.get("post_id", "")
    user_id = body.get("user_id", "")
    result = like_post(pid, user_id)
    if "error" in result:
        return 404, result
    return 200, result


@route("POST", "/api/feed/comment")
def feed_comment_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """评论"""
    from feed import add_comment
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    pid = body.get("post_id", "")
    result = add_comment(
        post_id=pid,
        user_id=body.get("user_id", ""),
        user_name=body.get("user_name", "Anonymous"),
        content=body.get("content", ""),
    )
    if "error" in result:
        return 404, result
    return 200, result


@route("POST", "/api/feed/recommend")
def feed_recommend_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """个性化推荐"""
    from feed import recommend_for_user
    body = handler.json_body
    if body is None:
        body = {}
    recs = recommend_for_user(
        holland_code=body.get("holland_code", ""),
        target_industry=body.get("target_industry", ""),
        user_school=body.get("user_school", ""),
        limit=body.get("limit", 10),
    )
    return 200, {"recommendations": recs, "count": len(recs)}


# ============== Prompt 模板库(Cycle 18) ==============


@route("GET", "/api/prompt/categories")
def prompt_categories_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出 8 类别"""
    from prompt_templates import list_categories
    return 200, {"categories": list_categories()}


@route("GET", "/api/prompt/list")
def prompt_list_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """列出模板(可按 category/role/tag 筛选)"""
    from prompt_templates import list_templates
    cat = handler.query.get("category", "") or None
    role = handler.query.get("role", "") or None
    tag = handler.query.get("tag", "") or None
    items = list_templates(category=cat, role=role, tag=tag)
    return 200, {"items": items, "count": len(items)}


@route("GET", "/api/prompt/get")
def prompt_get_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """获取单模板"""
    from prompt_templates import get_template
    tid = handler.query.get("id", "")
    t = get_template(tid)
    if t is None:
        return 404, {"error": "template not found"}
    return 200, {"template": t}


@route("GET", "/api/prompt/search")
def prompt_search_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """关键词搜索"""
    from prompt_templates import search_templates
    kw = handler.query.get("q", "")
    results = search_templates(kw)
    return 200, {"results": results, "count": len(results), "keyword": kw}


@route("POST", "/api/prompt/render")
def prompt_render_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """渲染模板(替换 {var} 占位符)"""
    from prompt_templates import render_template
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    tid = body.get("template_id", "")
    variables = body.get("variables", {})
    rendered = render_template(tid, variables)
    if rendered is None:
        return 404, {"error": "template not found"}
    return 200, {"rendered": rendered, "template_id": tid}


@route("GET", "/api/prompt/summary")
def prompt_summary_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """分类统计"""
    from prompt_templates import categories_summary, total_templates
    return 200, {
        "summary": categories_summary(),
        "total": total_templates(),
    }


# ============== Dashboard(Cycle 19) ==============


@route("GET", "/api/dashboard/meta")
def dashboard_meta_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """Dashboard 元数据"""
    from dashboard import get_dashboard_meta
    return 200, get_dashboard_meta()


# HTML 端点需要直接写 response(不走 JSON 流程)
# 标记此路径需要特殊处理
_DASHBOARD_HTML_ROUTES = {"/api/dashboard/html"}


# ============== Mobile / i18n(Cycle 20) ==============


@route("GET", "/api/mobile/manifest")
def mobile_manifest_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """PWA Manifest"""
    from mobile import get_manifest
    return 200, get_manifest()


@route("GET", "/api/mobile/css")
def mobile_css_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """Mobile CSS 元数据(因 CSS 直接返回文本,改走特殊处理)"""
    from mobile import get_mobile_css
    return 200, {"available": True, "size": len(get_mobile_css())}


@route("GET", "/api/mobile/languages")
def mobile_languages_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """支持语言列表"""
    from mobile import get_supported_languages
    return 200, {"languages": get_supported_languages()}


@route("GET", "/api/mobile/i18n")
def mobile_i18n_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """i18n 字典"""
    from mobile import get_i18n
    lang = handler.query.get("lang", "zh-CN")
    return 200, get_i18n(lang)


# ============== Papers 论文管理(Cycle 21) ==============


@route("GET", "/api/papers/stats")
def papers_stats_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """论文统计"""
    from papers import get_statistics
    return 200, get_statistics()


@route("GET", "/api/papers/keywords")
def papers_keywords_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """论文 keyword 列表"""
    from papers import list_keywords
    return 200, {"keywords": list_keywords()}


@route("GET", "/api/papers/list")
def papers_list_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """列出论文(可按 keyword/year 筛选)"""
    from papers import list_by_keyword, list_by_year, total_papers
    keyword = handler.query.get("keyword", "")
    year = handler.query.get("year", "")
    if keyword:
        items = list_by_keyword(keyword)
    elif year:
        try:
            items = list_by_year(int(year))
        except ValueError:
            items = []
    else:
        from papers import _get_paper_index
        items = [p.to_dict() for p in _get_paper_index()]
    return 200, {"items": items, "count": len(items), "total": total_papers()}


@route("GET", "/api/papers/get")
def papers_get_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """获取单篇论文"""
    from papers import get_paper
    arxiv_id = handler.query.get("id", "")
    paper = get_paper(arxiv_id)
    if paper is None:
        return 404, {"error": "paper not found"}
    return 200, {"paper": paper}


@route("POST", "/api/papers/search")
def papers_search_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """搜索论文"""
    from papers import search_by_title, search_by_author, search_by_abstract
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    field = body.get("field", "title")
    keyword = body.get("keyword", "")
    limit = body.get("limit", 10)
    if field == "title":
        results = search_by_title(keyword, limit=limit)
    elif field == "author":
        results = search_by_author(keyword, limit=limit)
    elif field == "abstract":
        results = search_by_abstract(keyword, limit=limit)
    else:
        return 400, {"error": f"unknown field: {field}"}
    return 200, {"results": results, "count": len(results)}


@route("GET", "/api/papers/cite")
def papers_cite_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """论文引用(4 风格)"""
    from papers import get_paper, format_citation
    arxiv_id = handler.query.get("id", "")
    style = handler.query.get("style", "apa")
    paper = get_paper(arxiv_id)
    if paper is None:
        return 404, {"error": "paper not found"}
    citation = format_citation(paper, style)
    return 200, {
        "arxiv_id": arxiv_id,
        "style": style,
        "citation": citation,
    }


# ============== 论文对话(Cycle 22) ==============


@route("POST", "/api/paper_chat/start")
def paper_chat_start_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """开启论文对话"""
    from paper_chat import start_chat, save_session
    body = handler.json_body
    if body is None:
        body = {}
    user_id = body.get("user_id", "anonymous")
    topic = body.get("topic", "")
    session = start_chat(user_id, topic=topic)
    save_session(session)
    return 200, {
        "session_id": session.id,
        "user_id": user_id,
        "topic": topic,
        "welcome": session.messages[0].content if session.messages else "",
    }


@route("POST", "/api/paper_chat/ask")
def paper_chat_ask_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """论文对话提问"""
    from paper_chat import get_session, ask
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    sid = body.get("session_id", "")
    question = body.get("question", "")
    session = get_session(sid)
    if session is None:
        return 404, {"error": "session not found"}
    try:
        response = ask(session, question)
    except ValueError as e:
        return 400, {"error": str(e)}
    return 200, {
        "response": response.to_dict(),
        "round_idx": session.round_idx,
    }


@route("POST", "/api/paper_chat/end")
def paper_chat_end_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """结束论文对话"""
    from paper_chat import get_session, end_chat
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    sid = body.get("session_id", "")
    session = get_session(sid)
    if session is None:
        return 404, {"error": "session not found"}
    summary = end_chat(session)
    return 200, {"summary": summary}


# ============== Release / v1.0 发布(Cycle 23) ==============


@route("GET", "/api/release/readiness")
def release_readiness_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """v1.0 发布就绪检查"""
    from release import check_readiness
    return 200, check_readiness()


@route("GET", "/api/release/stats")
def release_stats_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """项目统计"""
    from release import get_project_stats
    return 200, get_project_stats()


@route("GET", "/api/release/tags")
def release_tags_endpoint(_handler) -> Tuple[int, Dict[str, Any]]:
    """列出发布 tag"""
    from release import list_tags
    return 200, {"tags": list_tags(), "count": len(list_tags())}


@route("GET", "/api/release/notes")
def release_notes_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """生成 release notes"""
    from release import generate_release_notes
    version = handler.query.get("version", "v1.0.0")
    notes = generate_release_notes(version)
    return 200, {"version": version, "notes": notes}


@route("POST", "/api/release/tag")
def release_tag_endpoint(handler) -> Tuple[int, Dict[str, Any]]:
    """创建发布 tag(模拟 git tag)"""
    from release import create_tag
    body = handler.json_body
    if body is None:
        return 400, {"error": "empty body"}
    version = body.get("version", "")
    if not version:
        return 400, {"error": "version required"}
    tag = create_tag(
        version=version,
        title=body.get("title", ""),
        description=body.get("description", ""),
        changes=body.get("changes", []),
    )
    return 200, {"tag": tag}


# 标记 CSS 端点走 HTML 输出
_DASHBOARD_HTML_ROUTES.add("/api/mobile/css")


# ============== HTTP Handler ==============

class APIHandler(BaseHTTPRequestHandler):
    """API HTTP handler"""

    # 抑制默认 access log
    def log_message(self, format, *args):
        pass

    def _send(self, status: int, body: Dict[str, Any]):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        body_bytes = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_header("Content-Length", str(len(body_bytes)))
        self.end_headers()
        self.wfile.write(body_bytes)

    @property
    def query(self) -> Dict[str, str]:
        parsed = urlparse(self.path)
        out = {}
        if parsed.query:
            for kv in parsed.query.split("&"):
                if "=" in kv:
                    k, v = kv.split("=", 1)
                    out[k] = v
        return out

    @property
    def json_body(self) -> Optional[Dict[str, Any]]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length == 0:
                return None
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw)
        except (ValueError, json.JSONDecodeError):
            return None

    def _handle(self, method: str):
        parsed = urlparse(self.path)
        path = parsed.path
        # 特殊端点:不走 JSON
        if method == "GET" and path in _DASHBOARD_HTML_ROUTES:
            content_type = "text/css; charset=utf-8" if "css" in path else "text/html; charset=utf-8"
            content = ""
            if "css" in path:
                from mobile import get_mobile_css
                content = get_mobile_css()
            else:
                from dashboard import generate_dashboard
                content = generate_dashboard()
            body_bytes = content.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(body_bytes)))
            self.end_headers()
            self.wfile.write(body_bytes)
            return
        for r in ROUTES:
            if r["method"] == method and r["path"] == path:
                try:
                    status, body = r["handler"](self)
                    self._send(status, body)
                except Exception as e:
                    self._send(500, {"error": f"internal: {e}"})
                return
        self._send(404, {"error": f"not found: {method} {path}"})

    def do_GET(self):
        self._handle("GET")

    def do_POST(self):
        self._handle("POST")


# ============== 启动 ==============

def run_server(host: str = "127.0.0.1", port: int = 8765, debug: bool = False):
    """启动 HTTP server"""
    server = ThreadingHTTPServer((host, port), APIHandler)
    if debug:
        print(f"[aichat-hub] Listening on http://{host}:{port}")
        print(f"[aichat-hub] Endpoints: {len(ROUTES)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        if debug:
            print("\n[aichat-hub] Shutting down...")
        server.shutdown()


# ============== HTTP 客户端(供测试用) ==============

def http_get(url: str) -> Tuple[int, Dict[str, Any]]:
    """用 urllib 发 GET"""
    import urllib.request
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=10) as resp:
        body = json.loads(resp.read().decode("utf-8"))
        return resp.status, body


def http_post(url: str, payload: Dict[str, Any]) -> Tuple[int, Dict[str, Any]]:
    """用 urllib 发 POST"""
    import urllib.request
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            body = json.loads(resp.read().decode("utf-8"))
            return resp.status, body
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8"))
        return e.code, body


if __name__ == "__main__":
    run_server(debug=True)
