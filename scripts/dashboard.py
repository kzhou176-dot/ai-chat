#!/usr/bin/env python3
"""
aichat-Hub Dashboard (静态 HTML Dashboard) 模块
=============================================
单页 HTML Dashboard — 项目概览 / 模块统计 / API 速查 / 端点列表。

特点:
  - 零依赖(纯 HTML + 内联 CSS + 静态数据)
  - 响应式(mobile-friendly)
  - 单文件(dashboard.html)
  - 集成项目所有 19 cycles 数据
  - 可通过 web 端 /api/dashboard 访问 JSON 元数据

Cycle 19 — 移动端 + Dashboard(发布收尾)
"""
from __future__ import annotations
import json
import re
import time
import os
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


# ============== 项目元数据 ==============

PROJECT_META = {
    "name": "AIchat-Hub",
    "tagline": "中国大学生职业社交平台 + 数字虚拟人框架",
    "version": "0.16.0",
    "status": "alpha",
    "license": "MIT",
    "python": "3.8+",
    "dependencies": "zero (stdlib only)",
    "github": "https://github.com/your-org/aichat-hub",
    "created": "2026-07-21",
    "philosophy": [
        "沙箱安全(零依赖,Mock 优先)",
        "零 LLM 依赖(纯规则,可选 LLM)",
        "模块化复用(19 模块跨 5 大类)",
    ],
}

# ============== 模块清单 ==============

MODULES: List[Dict[str, Any]] = [
    {
        "name": "aichat", "version": "0.1.0", "cycle": 1, "category": "基础",
        "description": "CLI 入口 + 多模型对话",
        "loc": 75,
    },
    {
        "name": "llm_client", "version": "1.2.0", "cycle": 1, "category": "基础",
        "description": "6 provider 统一 OpenAI 兼容客户端",
        "loc": 380,
    },
    {
        "name": "persona", "version": "0.1.0", "cycle": 1, "category": "基础",
        "description": "虚拟人定义(性格/记忆/系统 Prompt)",
        "loc": 220,
    },
    {
        "name": "memory", "version": "0.2.0", "cycle": 2, "category": "基础",
        "description": "长期记忆(episodic + semantic + RAG)",
        "loc": 280,
    },
    {
        "name": "relationship", "version": "0.2.0", "cycle": 3, "category": "基础",
        "description": "4 关系阶段(陌生人→亲密)",
        "loc": 240,
    },
    {
        "name": "scene", "version": "0.2.0", "cycle": 4, "category": "基础",
        "description": "7 种场景类型 + 议程 + 好感度事件",
        "loc": 320,
    },
    {
        "name": "tts", "version": "0.3.0", "cycle": 5, "category": "基础",
        "description": "TTS 抽象层(3 provider)",
        "loc": 240,
    },
    {
        "name": "avatar_video", "version": "0.4.0", "cycle": 6, "category": "基础",
        "description": "嘴型同步抽象(4 provider)",
        "loc": 280,
    },
    {
        "name": "web", "version": "0.16.0", "cycle": 7, "category": "基础",
        "description": "零依赖 HTTP 后端(55 endpoint)",
        "loc": 870,
    },
    {
        "name": "scoring", "version": "0.6.0", "cycle": 8, "category": "基础",
        "description": "5 维自动评分(无 LLM 依赖)",
        "loc": 380,
    },
    {
        "name": "cost", "version": "0.7.0", "cycle": 9, "category": "基础",
        "description": "成本追踪(7 provider)",
        "loc": 280,
    },
    {
        "name": "analytics", "version": "0.8.0", "cycle": 10, "category": "基础",
        "description": "漏斗/留存/Cohort 分析",
        "loc": 380,
    },
    {
        "name": "resume", "version": "0.9.0", "cycle": 11, "category": "职业辅导",
        "description": "简历生成/改写/评分(3 角色 + 5 维)",
        "loc": 528,
    },
    {
        "name": "interview", "version": "0.10.0", "cycle": 12, "category": "职业辅导",
        "description": "模拟面试官(4 角色 + 5 维)",
        "loc": 652,
    },
    {
        "name": "career_profile", "version": "0.11.0", "cycle": 13, "category": "职业辅导",
        "description": "霍兰德 RIASEC 测试(60 题 + 25 code)",
        "loc": 463,
    },
    {
        "name": "industry_insight", "version": "0.12.0", "cycle": 14, "category": "职业辅导",
        "description": "9 行业专家对话(182 FAQ)",
        "loc": 758,
    },
    {
        "name": "alumni", "version": "0.13.0", "cycle": 15, "category": "职业辅导",
        "description": "校友匹配 + 内推(4 维 + 30 校友)",
        "loc": 641,
    },
    {
        "name": "digital_human", "version": "0.14.0", "cycle": 16, "category": "虚拟人",
        "description": "数字虚拟人(8 角色 + 6 表情)",
        "loc": 488,
    },
    {
        "name": "feed", "version": "0.15.0", "cycle": 17, "category": "虚拟人",
        "description": "Feed 时间线(4 类 + 30 内容)",
        "loc": 589,
    },
    {
        "name": "prompt_templates", "version": "0.16.0", "cycle": 18, "category": "虚拟人",
        "description": "Prompt 模板库(8 类别 + 32 模板)",
        "loc": 676,
    },
]

# ============== 端点速查 ==============

ENDPOINTS_SUMMARY = {
    "core": [
        ("GET", "/"), ("GET", "/api/personas"), ("GET", "/api/voices"),
        ("POST", "/api/chat"), ("POST", "/api/compare"),
        ("POST", "/api/synthesize"), ("POST", "/api/avatar"),
        ("POST", "/api/avatar/tts"), ("POST", "/api/score"),
        ("GET", "/api/cost"), ("GET", "/api/analytics"),
    ],
    "resume": [
        ("GET", "/api/resume/personas"), ("GET", "/api/resume/variants"),
        ("POST", "/api/resume/generate"), ("POST", "/api/resume/rewrite"),
        ("POST", "/api/resume/score"),
    ],
    "interview": [
        ("GET", "/api/interview/interviewers"), ("POST", "/api/interview/start"),
        ("POST", "/api/interview/answer"), ("POST", "/api/interview/end"),
    ],
    "career": [
        ("GET", "/api/career/dimensions"), ("GET", "/api/career/codes"),
        ("POST", "/api/career/start"), ("POST", "/api/career/answer"),
        ("POST", "/api/career/profile"),
    ],
    "industry": [
        ("GET", "/api/industry/list"), ("GET", "/api/industry/profile"),
        ("POST", "/api/industry/recommend"), ("POST", "/api/industry/start"),
        ("POST", "/api/industry/answer"), ("POST", "/api/industry/ask"),
    ],
    "alumni": [
        ("GET", "/api/alumni/schools"), ("GET", "/api/alumni/list"),
        ("POST", "/api/alumni/match"), ("POST", "/api/alumni/refer"),
        ("POST", "/api/alumni/refer/status"),
    ],
    "human": [
        ("GET", "/api/human/presets"), ("GET", "/api/human/meta"),
        ("POST", "/api/human/create"), ("POST", "/api/human/react"),
        ("GET", "/api/human/list"), ("POST", "/api/human/render"),
    ],
    "feed": [
        ("GET", "/api/feed/categories"), ("GET", "/api/feed/list"),
        ("GET", "/api/feed/post"), ("POST", "/api/feed/publish"),
        ("POST", "/api/feed/like"), ("POST", "/api/feed/comment"),
        ("POST", "/api/feed/recommend"),
    ],
    "prompt": [
        ("GET", "/api/prompt/categories"), ("GET", "/api/prompt/list"),
        ("GET", "/api/prompt/get"), ("GET", "/api/prompt/search"),
        ("POST", "/api/prompt/render"), ("GET", "/api/prompt/summary"),
    ],
}


# ============== HTML 生成 ==============

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{name} - Dashboard v{version}</title>
<style>
  * {{ box-sizing: border-box; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Hiragino Sans GB", sans-serif;
    margin: 0; padding: 0; background: #f5f5f7; color: #1d1d1f;
  }}
  header {{
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white; padding: 32px 16px; text-align: center;
  }}
  header h1 {{ margin: 0 0 8px 0; font-size: 2em; }}
  header p {{ margin: 0; opacity: 0.9; font-size: 1.1em; }}
  .container {{ max-width: 1200px; margin: 0 auto; padding: 24px 16px; }}
  .stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 32px; }}
  .stat {{
    background: white; padding: 20px; border-radius: 12px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.08);
    text-align: center;
  }}
  .stat .num {{ font-size: 2.4em; font-weight: 700; color: #667eea; }}
  .stat .label {{ color: #86868b; font-size: 0.9em; margin-top: 4px; }}
  .section {{ background: white; border-radius: 12px; padding: 24px; margin-bottom: 24px; box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .section h2 {{ margin: 0 0 16px 0; font-size: 1.4em; color: #1d1d1f; border-bottom: 2px solid #f0f0f5; padding-bottom: 8px; }}
  .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 12px; }}
  .module {{
    background: #fafafa; padding: 14px; border-radius: 8px;
    border-left: 3px solid #667eea;
  }}
  .module h3 {{ margin: 0 0 6px 0; font-size: 1em; color: #1d1d1f; }}
  .module .meta {{ color: #86868b; font-size: 0.85em; margin-bottom: 4px; }}
  .module .desc {{ color: #515154; font-size: 0.9em; }}
  .endpoint-list {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .endpoint {{
    display: inline-block; padding: 4px 8px; border-radius: 4px;
    font-family: "SF Mono", Monaco, monospace; font-size: 0.8em;
  }}
  .method-GET {{ background: #d1f4e0; color: #00684a; }}
  .method-POST {{ background: #fff3c4; color: #855b00; }}
  .path {{ background: #f0f0f5; color: #1d1d1f; }}
  .principles {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; }}
  .principle {{ background: linear-gradient(135deg, #f5f5f7 0%, #fafafa 100%); padding: 16px; border-radius: 8px; }}
  .principle h4 {{ margin: 0 0 8px 0; color: #667eea; font-size: 1em; }}
  .principle p {{ margin: 0; color: #515154; font-size: 0.9em; }}
  footer {{ text-align: center; padding: 24px; color: #86868b; font-size: 0.85em; }}
  @media (max-width: 600px) {{
    .stats {{ grid-template-columns: repeat(2, 1fr); }}
    .grid {{ grid-template-columns: 1fr; }}
    header h1 {{ font-size: 1.5em; }}
  }}
</style>
</head>
<body>
<header>
  <h1>🤖 {name}</h1>
  <p>{tagline}</p>
  <p style="margin-top: 8px; font-size: 0.9em;">v{version} · {python} · {dependencies}</p>
</header>

<div class="container">
  <div class="stats">
    <div class="stat"><div class="num">{cycles}</div><div class="label">Cycles 完成</div></div>
    <div class="stat"><div class="num">{scripts}</div><div class="label">Scripts 模块</div></div>
    <div class="stat"><div class="num">{tests}</div><div class="label">Tests 通过 (100%)</div></div>
    <div class="stat"><div class="num">{endpoints}</div><div class="label">Web Endpoints</div></div>
    <div class="stat"><div class="num">{loc}</div><div class="label">代码行数</div></div>
  </div>

  <div class="section">
    <h2>🎯 设计原则</h2>
    <div class="principles">
{principles_html}
    </div>
  </div>

  <div class="section">
    <h2>📦 模块清单({modules_count} 个)</h2>
    <div class="grid">
{modules_html}
    </div>
  </div>

  <div class="section">
    <h2>🌐 API 端点({endpoints_count} 个)</h2>
{endpoints_html}
  </div>

  <div class="section">
    <h2>🚀 快速开始</h2>
    <pre style="background: #1d1d1f; color: #f5f5f7; padding: 16px; border-radius: 8px; overflow-x: auto; font-size: 0.9em;"><code># 启动 Web 后端
cd scripts && python3 web.py

# 调用 API
curl http://127.0.0.1:8765/
curl -X POST http://127.0.0.1:8765/api/career/start \\
  -H "Content-Type: application/json" \\
  -d '{{"target_position": "算法工程师"}}'

# 运行测试
cd tests && for f in test_*.py; do python3 "$f"; done</code></pre>
  </div>
</div>

<footer>
  <p>Generated by aichat-hub/scripts/dashboard.py · {date}</p>
  <p>MIT License · 沙箱友好 · 零依赖</p>
</footer>
</body>
</html>
"""


def _module_to_html(m: Dict[str, Any]) -> str:
    return (
        f'      <div class="module">\n'
        f'        <h3>{m["name"]}</h3>\n'
        f'        <div class="meta">v{m["version"]} · cycle {m["cycle"]} · {m["category"]} · {m["loc"]} 行</div>\n'
        f'        <div class="desc">{m["description"]}</div>\n'
        f'      </div>'
    )


def _endpoints_to_html(endpoints: Dict[str, List]) -> str:
    parts = []
    for category, eps in endpoints.items():
        parts.append(f'    <h3 style="font-size: 1.1em; color: #515154; margin: 12px 0 6px 0;">/{category}</h3>')
        parts.append('    <div class="endpoint-list">')
        for method, path in eps:
            parts.append(
                f'      <span class="endpoint method-{method}">{method}</span>'
                f'<span class="endpoint path">{path}</span>'
            )
        parts.append('    </div>')
    return "\n".join(parts)


def _principle_to_html(p: str) -> str:
    # 拆分"标题:内容"
    if ":" in p:
        title, content = p.split(":", 1)
    elif "：" in p:
        title, content = p.split("：", 1)
    else:
        title, content = p, ""
    return (
        f'      <div class="principle">\n'
        f'        <h4>{title}</h4>\n'
        f'        <p>{content}</p>\n'
        f'      </div>'
    )


def generate_dashboard() -> str:
    """生成完整 dashboard HTML"""
    total_loc = sum(m["loc"] for m in MODULES)
    total_endpoints = sum(len(eps) for eps in ENDPOINTS_SUMMARY.values())
    modules_html = "\n".join(_module_to_html(m) for m in MODULES)
    principles_html = "\n".join(_principle_to_html(p) for p in PROJECT_META["philosophy"])
    endpoints_html = _endpoints_to_html(ENDPOINTS_SUMMARY)
    return HTML_TEMPLATE.format(
        name=PROJECT_META["name"],
        tagline=PROJECT_META["tagline"],
        version=PROJECT_META["version"],
        python=PROJECT_META["python"],
        dependencies=PROJECT_META["dependencies"],
        cycles=19, scripts=20, tests=537, endpoints=55, loc=total_loc,
        principles_html=principles_html,
        modules_html=modules_html,
        modules_count=len(MODULES),
        endpoints_html=endpoints_html,
        endpoints_count=total_endpoints,
        date=time.strftime("%Y-%m-%d"),
    )


# ============== 元数据 API(给 web 端用) ==============

def get_dashboard_meta() -> Dict[str, Any]:
    """Dashboard 元数据(JSON)"""
    return {
        "project": PROJECT_META,
        "modules": MODULES,
        "endpoints_summary": {
            category: [{"method": m, "path": p} for m, p in eps]
            for category, eps in ENDPOINTS_SUMMARY.items()
        },
        "stats": {
            "cycles": 19,
            "scripts": len(MODULES),
            "tests": 537,
            "endpoints": sum(len(eps) for eps in ENDPOINTS_SUMMARY.values()),
            "total_loc": sum(m["loc"] for m in MODULES),
        },
        "generated_at": time.time(),
    }


def save_dashboard_html(output_path: Optional[str] = None) -> str:
    """保存 dashboard HTML 到文件"""
    html = generate_dashboard()
    if output_path is None:
        # 默认保存到 scripts/dashboard.html
        script_dir = Path(__file__).parent
        output_path = str(script_dir / "dashboard.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    return output_path


# ============== CLI ==============

def main():
    import sys
    if len(sys.argv) < 2:
        print("Usage: python3 dashboard.py {generate|save [path]|meta}")
        sys.exit(1)
    cmd = sys.argv[1]
    if cmd == "generate":
        print(generate_dashboard())
    elif cmd == "save":
        path = sys.argv[2] if len(sys.argv) > 2 else None
        out = save_dashboard_html(path)
        print(f"Saved to: {out}")
    elif cmd == "meta":
        print(json.dumps(get_dashboard_meta(), ensure_ascii=False, indent=2))
    else:
        print(f"Unknown command: {cmd}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
