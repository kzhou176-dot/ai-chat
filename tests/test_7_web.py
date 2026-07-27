"""
test_7_web — Web 后端 endpoint 测试
==================================
用 urllib 启动/调用/关闭 web server,验证:
  - GET / 返回服务信息
  - GET /api/personas 列出虚拟人
  - GET /api/voices 列出 TTS 声音(支持 lang 筛选)
  - POST /api/chat 单 LLM 对话(无 key 返回友好 error)
  - POST /api/compare 多 LLM 对比
  - POST /api/synthesize TTS 合成
  - POST /api/avatar 视频合成
  - POST /api/avatar/tts TTS+Avatar 串联
  - 404 未知路径
  - 400 错误请求
  - 集成 Persona → chat
"""
import sys
import json
import time
import socket
import threading
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from web import (
    APIHandler, ROUTES, run_server,
    http_get, http_post,
)


# 找到空闲端口
def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


# 全局 server 状态
_server_thread = None
_server = None
_base_url = None


def setup_server():
    """启动测试用 server(子线程)"""
    global _server_thread, _server, _base_url
    port = find_free_port()
    _base_url = f"http://127.0.0.1:{port}"
    _server = ThreadingHTTPServer = __import__(
        "http.server", fromlist=["ThreadingHTTPServer"]
    ).ThreadingHTTPServer
    from web import APIHandler
    _server = ThreadingHTTPServer(("127.0.0.1", port), APIHandler)
    _server_thread = threading.Thread(target=_server.serve_forever, daemon=True)
    _server_thread.start()
    # 等待启动
    time.sleep(0.3)


def teardown_server():
    """关闭测试 server"""
    global _server
    if _server:
        _server.shutdown()
        _server.server_close()


def test_server_starts():
    """server 能正常启动"""
    setup_server()
    assert _server_thread is not None
    assert _server_thread.is_alive()
    print(f"  ✓ server started on {_base_url}")


def test_index():
    """GET / 返回服务信息"""
    status, body = http_get(f"{_base_url}/")
    assert status == 200
    assert body["service"] == "aichat-hub"
    assert "endpoints" in body
    assert "personas" in body
    assert len(body["endpoints"]) >= 6
    print(f"  ✓ GET / → {body['service']} v{body['version']}")


def test_404():
    """未知路径返回 404"""
    try:
        status, body = http_get(f"{_base_url}/nonexistent")
    except HTTPError as e:
        status = e.code
        body = json.loads(e.read().decode("utf-8"))
    assert status == 404
    assert "not found" in body["error"]
    print("  ✓ 404 for unknown path")


def test_list_personas():
    """GET /api/personas 列出虚拟人"""
    status, body = http_get(f"{_base_url}/api/personas")
    assert status == 200
    assert "personas" in body
    # 至少有 3 个(如果之前 seed 过)
    assert isinstance(body["personas"], list)
    print(f"  ✓ /api/personas → {len(body['personas'])} personas")


def test_list_voices():
    """GET /api/voices 列出 TTS 声音"""
    status, body = http_get(f"{_base_url}/api/voices")
    assert status == 200
    assert "voices" in body
    assert len(body["voices"]) >= 5
    # 验证数据结构
    v = body["voices"][0]
    assert {"id", "name", "language", "gender"} <= set(v.keys())
    print(f"  ✓ /api/voices → {len(body['voices'])} voices")


def test_list_voices_with_lang_filter():
    """带 lang 筛选的 voices"""
    status, body = http_get(f"{_base_url}/api/voices?lang=zh")
    assert status == 200
    assert all(v["language"].startswith("zh") for v in body["voices"])
    print(f"  ✓ /api/voices?lang=zh → {len(body['voices'])} zh voices")


def test_chat_no_key():
    """POST /api/chat 无 key(沙盒走 mock 路径返 200,或真实环境返 500)"""
    try:
        status, body = http_post(f"{_base_url}/api/chat", {"prompt": "hello"})
    except HTTPError as e:
        status = e.code
        body = json.loads(e.read().decode("utf-8"))
    # 两种合法结果:
    # - 200 + mock fallback(沙盒无 key)
    # - 500 + "API key" error(真实环境)
    assert status in (200, 500)
    if status == 500:
        assert "error" in body
        assert "API key" in body.get("error", "") or "OPENAI_API_KEY" in body.get("error", "")
    else:
        # mock 路径,content 应有 mock 标识
        assert body.get("ok") is True
        assert "mock" in body.get("content", "").lower() or "mock" in body.get("model", "")
    print(f"  ✓ /api/chat no-key → {status} (sandbox mock 或 real key error)")


def test_chat_missing_prompt():
    """POST /api/chat 缺 prompt 返回 400"""
    try:
        status, body = http_post(f"{_base_url}/api/chat", {})
    except HTTPError as e:
        status = e.code
        body = json.loads(e.read().decode("utf-8"))
    assert status == 400
    assert "missing" in body.get("error", "")
    print("  ✓ /api/chat missing prompt → 400")


def test_chat_empty_body():
    """POST /api/chat 空 body 返回 400"""
    try:
        status, body = http_post(f"{_base_url}/api/chat", {})
    except HTTPError as e:
        status = e.code
        body = json.loads(e.read().decode("utf-8"))
    assert status == 400
    print("  ✓ /api/chat empty body → 400")


def test_compare_no_keys():
    """POST /api/compare 多 LLM 对比(无 key)"""
    # compare endpoint 即使个别 provider 失败也返回 200
    # 因为 results 数组包含每个 provider 的状态
    # 沙盒无 key,所有 provider 都失败但 endpoint 仍返 200
    try:
        status, body = http_post(
            f"{_base_url}/api/compare",
            {"prompt": "你好", "providers": ["openai", "deepseek"]},
        )
    except HTTPError as e:
        status = e.code
        body = json.loads(e.read().decode("utf-8"))
    # 200 or 500 都可(取决于实现)只要有 results
    if status == 200:
        assert "results" in body
        assert len(body["results"]) == 2
    else:
        assert status == 500
        assert "error" in body
    print(f"  ✓ /api/compare → status {status}, error-handled")


def test_compare_missing_prompt():
    """POST /api/compare 缺 prompt"""
    try:
        status, body = http_post(f"{_base_url}/api/compare", {})
    except HTTPError as e:
        status = e.code
        body = json.loads(e.read().decode("utf-8"))
    assert status == 400
    print("  ✓ /api/compare missing prompt → 400")


def test_synthesize():
    """POST /api/synthesize TTS 合成"""
    status, body = http_post(f"{_base_url}/api/synthesize", {
        "text": "你好世界",
        "voice_id": "female-young",
    })
    assert status == 200
    r = body["result"]
    assert r["text"] == "你好世界"
    assert r["voice_id"] == "female-young"
    assert r["provider"] == "mock"
    assert r["duration_estimate_s"] > 0
    print(f"  ✓ /api/synthesize → {r['duration_estimate_s']}s, {r['char_count']} chars")


def test_synthesize_missing_text():
    """POST /api/synthesize 缺 text"""
    try:
        status, body = http_post(f"{_base_url}/api/synthesize", {})
    except HTTPError as e:
        status = e.code
        body = json.loads(e.read().decode("utf-8"))
    assert status == 400
    print("  ✓ /api/synthesize missing text → 400")


def test_avatar():
    """POST /api/avatar 视频合成"""
    status, body = http_post(f"{_base_url}/api/avatar", {
        "text": "你好,我是小爱",
        "avatar_id": "xiaoai_avatar",
        "voice_id": "female-soft",
    })
    assert status == 200
    r = body["result"]
    assert r["text"] == "你好,我是小爱"
    assert r["avatar_id"] == "xiaoai_avatar"
    assert r["width"] == 640  # standard quality
    assert r["height"] == 480
    assert r["fps"] == 25
    print(f"  ✓ /api/avatar → {r['width']}x{r['height']}@{r['fps']}fps, {r['duration_s']}s")


def test_avatar_tts_pipeline():
    """POST /api/avatar/tts TTS+Avatar 串联"""
    status, body = http_post(f"{_base_url}/api/avatar/tts", {
        "text": "今天天气真不错",
        "persona": "xiaoai",
    })
    assert status == 200
    assert body["persona"] == "xiaoai"
    tts = body["tts"]
    avatar = body["avatar"]
    # 时长应该一致(TTS 驱动 Avatar)
    assert abs(tts["duration_estimate_s"] - avatar["duration_s"]) < 0.1
    print(f"  ✓ /api/avatar/tts → tts {tts['duration_estimate_s']}s = avatar {avatar['duration_s']}s")


def test_chat_with_persona():
    """POST /api/chat 集成 persona system prompt"""
    try:
        status, body = http_post(f"{_base_url}/api/chat", {
            "prompt": "你好",
            "persona": "xiaoai",
        })
    except HTTPError as e:
        status = e.code
        body = json.loads(e.read().decode("utf-8"))
    # 200(mock) 或 500(error) 都接受
    assert status in (200, 500)
    if status == 200:
        # mock 路径:persona 已注入 system prompt
        assert body.get("ok") is True
    else:
        assert "error" in body
    print(f"  ✓ /api/chat with persona → {status}")


def test_cors_header():
    """CORS header 存在"""
    import urllib.request
    req = urllib.request.Request(f"{_base_url}/")
    with urllib.request.urlopen(req) as resp:
        cors = resp.headers.get("Access-Control-Allow-Origin")
        assert cors == "*"
    print("  ✓ CORS header set")


def test_content_type_json():
    """响应 Content-Type 是 JSON"""
    status, body = http_get(f"{_base_url}/")
    import urllib.request
    req = urllib.request.Request(f"{_base_url}/")
    with urllib.request.urlopen(req) as resp:
        ct = resp.headers.get("Content-Type")
        assert "application/json" in ct
    print(f"  ✓ Content-Type: {ct}")


def test_routes_registered():
    """7 个路由都注册了"""
    methods_paths = {(r["method"], r["path"]) for r in ROUTES}
    assert ("GET", "/") in methods_paths
    assert ("GET", "/api/personas") in methods_paths
    assert ("GET", "/api/voices") in methods_paths
    assert ("POST", "/api/chat") in methods_paths
    assert ("POST", "/api/compare") in methods_paths
    assert ("POST", "/api/synthesize") in methods_paths
    assert ("POST", "/api/avatar") in methods_paths
    assert ("POST", "/api/avatar/tts") in methods_paths
    print(f"  ✓ {len(ROUTES)} routes registered")


def test_http_get_helper():
    """http_get 工具函数"""
    status, body = http_get(f"{_base_url}/")
    assert status == 200
    assert isinstance(body, dict)
    print("  ✓ http_get helper works")


def test_http_post_helper():
    """http_post 工具函数"""
    try:
        status, body = http_post(f"{_base_url}/api/chat", {"prompt": "hi"})
    except HTTPError as e:
        status = e.code
        body = json.loads(e.read().decode("utf-8"))
    # 沙盒 mock → 200,真实 key 错误 → 500
    assert status in (200, 500)
    assert isinstance(body, dict)
    print("  ✓ http_post helper works")


def teardown():
    teardown_server()


if __name__ == "__main__":
    try:
        # 先启动 server
        setup_server()
        print(f"Test server running on {_base_url}\n")

        tests = [
            test_server_starts,
            test_routes_registered,
            test_index,
            test_404,
            test_list_personas,
            test_list_voices,
            test_list_voices_with_lang_filter,
            test_chat_no_key,
            test_chat_missing_prompt,
            test_chat_empty_body,
            test_compare_no_keys,
            test_compare_missing_prompt,
            test_synthesize,
            test_synthesize_missing_text,
            test_avatar,
            test_avatar_tts_pipeline,
            test_chat_with_persona,
            test_cors_header,
            test_content_type_json,
            test_http_get_helper,
            test_http_post_helper,
        ]
        print(f"Running {len(tests)} web tests...\n")
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
    finally:
        teardown_server()
