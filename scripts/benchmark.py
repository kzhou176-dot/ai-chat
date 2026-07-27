"""
benchmark.py — v1.0.1 端点性能基准测试

功能:
- run_endpoint(method, path, payload) 单次请求 + 计时(直接调用 web.ROUTES 中的 handler)
- run_endpoint_n(method, path, payload, n) 多次统计 p50/p95/p99/min/max/mean/error
- benchmark_all(endpoints) 批量跑所有 endpoint
- generate_report(results) 生成 markdown 报告
- get_all_endpoints() 从 web.ROUTES 反射出 74 个 endpoint 列表
- MemoryProbe:简单内存占用采样
- 沙箱友好:不依赖 LLM,纯 stdlib

设计原则:
- 12KB 内,单文件,无 pip install
- 计时用 time.perf_counter_ns() (纳秒精度)
- 100% mock,无外部网络
- 结果可导出为 JSON + Markdown

数据:
- data/benchmark_report.json
- reports/benchmark_report.md
"""

from __future__ import annotations

import json
import os
import sys
import time
import statistics
from dataclasses import dataclass, field, asdict
from typing import Any, Callable, Dict, List, Optional, Tuple

# 路径
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
REPORT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "reports")
BENCHMARK_JSON = os.path.join(DATA_DIR, "benchmark_report.json")
BENCHMARK_MD = os.path.join(REPORT_DIR, "benchmark_report.md")

# ============== Mock Handler ==============

class MockHandler:
    """伪装 BaseHTTPRequestHandler,提供 json_body + query 属性"""
    def __init__(self, json_body: Optional[Dict[str, Any]] = None, query: Optional[Dict[str, str]] = None):
        self._body = json_body
        self._query = query or {}
    @property
    def json_body(self) -> Optional[Dict[str, Any]]:
        return self._body
    @property
    def query(self) -> Dict[str, str]:
        return self._query


# ============== 数据类 ==============

@dataclass
class BenchmarkResult:
    method: str
    path: str
    n: int
    errors: int = 0
    times_ns: List[int] = field(default_factory=list)
    p50_ms: float = 0.0
    p95_ms: float = 0.0
    p99_ms: float = 0.0
    mean_ms: float = 0.0
    min_ms: float = 0.0
    max_ms: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=dict)
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ============== 单次请求 ==============

def run_endpoint(method: str, path: str, payload: Optional[Dict[str, Any]] = None,
                 query: Optional[Dict[str, str]] = None) -> Tuple[int, float, int]:
    """
    直接调用 web.ROUTES 中注册的 handler,返回 (status, elapsed_ms, status_code)
    沙箱环境下不依赖网络
    """
    try:
        from web import ROUTES
    except ImportError:
        # 兼容:加 scripts/ 到 sys.path
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from web import ROUTES

    handler_obj = MockHandler(json_body=payload, query=query)
    start = time.perf_counter_ns()
    status = 0
    body: Dict[str, Any] = {}
    try:
        for r in ROUTES:
            if r["method"] == method and r["path"] == path:
                status, body = r["handler"](handler_obj)
                break
        else:
            status, body = 404, {"error": f"not found: {method} {path}"}
    except Exception as e:
        status, body = 500, {"error": f"internal: {e}"}
    elapsed_ms = (time.perf_counter_ns() - start) / 1_000_000.0
    return status, elapsed_ms, status


# ============== 多次统计 ==============

def run_endpoint_n(method: str, path: str, payload: Optional[Dict[str, Any]] = None,
                   n: int = 50, query: Optional[Dict[str, str]] = None) -> BenchmarkResult:
    """对单 endpoint 跑 N 次,统计 p50/p95/p99/min/max/mean"""
    res = BenchmarkResult(method=method, path=path, n=n)
    for _ in range(n):
        status, elapsed, _ = run_endpoint(method, path, payload, query)
        res.times_ns.append(int(elapsed * 1_000_000))  # 转回 ns
        res.status_codes[status] = res.status_codes.get(status, 0) + 1
        if status >= 500:
            res.errors += 1
    # 统计 (ms)
    times_ms = [t / 1_000_000 for t in res.times_ns]
    times_ms_sorted = sorted(times_ms)
    if times_ms_sorted:
        res.p50_ms = _percentile(times_ms_sorted, 50)
        res.p95_ms = _percentile(times_ms_sorted, 95)
        res.p99_ms = _percentile(times_ms_sorted, 99)
        res.mean_ms = statistics.mean(times_ms)
        res.min_ms = min(times_ms)
        res.max_ms = max(times_ms)
    return res


def _percentile(sorted_list: List[float], p: int) -> float:
    """计算百分位(线性插值)"""
    if not sorted_list:
        return 0.0
    k = (len(sorted_list) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(sorted_list) - 1)
    if f == c:
        return sorted_list[f]
    return sorted_list[f] + (sorted_list[c] - sorted_list[f]) * (k - f)


# ============== 批量 ==============

# 每个 endpoint 的"标准 payload" — 只 GET 无需 body,POST 给最小有效 payload
ENDPOINT_PAYLOADS: Dict[str, Dict[str, Any]] = {
    # 基础
    "POST /api/chat": {"persona": "xiaoai", "message": "hi"},
    "POST /api/compare": {"persona_a": "xiaoai", "persona_b": "dr_li", "message": "hi"},
    "POST /api/synthesize": {"text": "hello", "voice": "female-shaonv"},
    "POST /api/avatar": {"expression": "smile", "action": "wave"},
    "POST /api/avatar/tts": {"text": "hello", "voice": "female-shaonv"},
    "POST /api/score": {"response": "I am a junior developer with Python skills."},
    # Resume
    "POST /api/resume/generate": {"persona": "tech_resume", "info": {"name": "张三", "school": "清华"}},
    "POST /api/resume/rewrite": {"persona": "tech_resume", "content": "I developed apps.", "section": "experience"},
    "POST /api/resume/score": {"content": "I developed apps using Python."},
    # Interview
    "POST /api/interview/start": {"role": "tech_lead", "user_id": "u1"},
    "POST /api/interview/answer": {"session_id": "s1", "answer": "I used Python"},
    "POST /api/interview/end": {"session_id": "s1"},
    # Career
    "POST /api/career/start": {"user_id": "u1"},
    "POST /api/career/answer": {"session_id": "s1", "answers": ["A", "B", "C"]},
    "POST /api/career/profile": {"user_id": "u1", "answers": ["A", "B", "C"] * 20},
    # Industry
    "POST /api/industry/recommend": {"code": "RIA"},
    "POST /api/industry/start": {"industry": "tech", "user_id": "u1"},
    "POST /api/industry/answer": {"session_id": "s1", "question": "如何学习", "answer": "看官方文档"},
    "POST /api/industry/ask": {"industry": "tech", "question": "如何学习"},
    # Alumni
    "POST /api/alumni/match": {"school": "清华", "major": "CS"},
    "POST /api/alumni/refer": {"alumni_id": "a1", "user_id": "u1"},
    "POST /api/alumni/refer/status": {"refer_id": "r1"},
    # Human
    "POST /api/human/create": {"name": "测试人", "style": "2d_live"},
    "POST /api/human/react": {"human_id": "h1", "trigger": "smile"},
    "POST /api/human/render": {"human_id": "h1"},
    # Feed
    "POST /api/feed/publish": {"author": "u1", "content": "今天面试了", "category": "experience"},
    "POST /api/feed/like": {"post_id": "p1", "user_id": "u1"},
    "POST /api/feed/comment": {"post_id": "p1", "user_id": "u1", "text": "支持"},
    "POST /api/feed/recommend": {"user_id": "u1"},
    # Prompt
    "POST /api/prompt/render": {"template_id": "t1", "vars": {"name": "张三"}},
    # Papers
    "POST /api/papers/search": {"query": "LLM"},
    # Paper chat
    "POST /api/paper_chat/start": {"user_id": "u1"},
    "POST /api/paper_chat/ask": {"session_id": "s1", "question": "对比 RAG 和微调"},
    "POST /api/paper_chat/end": {"session_id": "s1"},
    # Release
    "POST /api/release/tag": {"tag": "v1.0.1-test"},
}


def get_all_endpoints() -> List[Tuple[str, str, Optional[Dict[str, Any]]]]:
    """
    反射 web.ROUTES 拿到全部 endpoint 列表,自动注入标准 payload
    """
    try:
        from web import ROUTES
    except ImportError:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from web import ROUTES
    out: List[Tuple[str, str, Optional[Dict[str, Any]]]] = []
    for r in ROUTES:
        method, path = r["method"], r["path"]
        key = f"{method} {path}"
        payload = ENDPOINT_PAYLOADS.get(key)
        out.append((method, path, payload))
    return out


def benchmark_all(endpoints: Optional[List[Tuple[str, str, Optional[Dict[str, Any]]]]] = None,
                  n: int = 30, skip_paths: Optional[List[str]] = None) -> List[BenchmarkResult]:
    """批量跑所有 endpoint,返回 BenchmarkResult 列表"""
    if endpoints is None:
        endpoints = get_all_endpoints()
    skip = set(skip_paths or [])
    results: List[BenchmarkResult] = []
    for method, path, payload in endpoints:
        if path in skip:
            continue
        try:
            res = run_endpoint_n(method, path, payload, n=n)
            results.append(res)
        except Exception as e:
            err_res = BenchmarkResult(method=method, path=path, n=0, errors=1, note=str(e))
            results.append(err_res)
    return results


# ============== 报告生成 ==============

def generate_report(results: List[BenchmarkResult]) -> str:
    """生成 markdown 报告"""
    lines: List[str] = []
    lines.append("# AICHAT-HUB 端点性能基准报告 (v1.0.1)")
    lines.append("")
    lines.append(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    total = len(results)
    total_err = sum(r.errors for r in results)
    lines.append(f"**总端点数**: {total}")
    lines.append(f"**总错误数**: {total_err}")
    lines.append(f"**每端点请求数**: {results[0].n if results else 0}")
    lines.append("")
    # 排序:p95 升序
    sorted_res = sorted([r for r in results if r.n > 0], key=lambda x: x.p95_ms)
    # Top 10 fastest
    lines.append("## 🏆 Top 10 最快 (按 p95 排序)")
    lines.append("")
    lines.append("| 排名 | Method | Path | p50 (ms) | p95 (ms) | p99 (ms) | mean (ms) |")
    lines.append("|---|---|---|---|---|---|---|")
    for i, r in enumerate(sorted_res[:10], 1):
        lines.append(f"| {i} | {r.method} | `{r.path}` | {r.p50_ms:.2f} | {r.p95_ms:.2f} | {r.p99_ms:.2f} | {r.mean_ms:.2f} |")
    lines.append("")
    # Top 10 slowest
    lines.append("## 🐌 Top 10 最慢 (按 p95 排序)")
    lines.append("")
    lines.append("| 排名 | Method | Path | p50 (ms) | p95 (ms) | p99 (ms) | mean (ms) |")
    lines.append("|---|---|---|---|---|---|---|")
    for i, r in enumerate(sorted_res[-10:], 1):
        lines.append(f"| {i} | {r.method} | `{r.path}` | {r.p50_ms:.2f} | {r.p95_ms:.2f} | {r.p99_ms:.2f} | {r.mean_ms:.2f} |")
    lines.append("")
    # 分类汇总
    lines.append("## 📊 分类汇总")
    lines.append("")
    lines.append("| 类别 | 端点数 | p50 均值 | p95 均值 | p99 均值 |")
    lines.append("|---|---|---|---|---|")
    categories = _categorize_endpoints(results)
    for cat, members in categories.items():
        valid = [m for m in members if m.n > 0]
        if not valid:
            continue
        p50 = statistics.mean([r.p50_ms for r in valid])
        p95 = statistics.mean([r.p95_ms for r in valid])
        p99 = statistics.mean([r.p99_ms for r in valid])
        lines.append(f"| {cat} | {len(valid)} | {p50:.2f} | {p95:.2f} | {p99:.2f} |")
    lines.append("")
    # 全量列表
    lines.append("## 📋 全量列表 (按 path 字母排序)")
    lines.append("")
    lines.append("| Method | Path | p50 (ms) | p95 (ms) | mean (ms) | errors |")
    lines.append("|---|---|---|---|---|---|")
    for r in sorted(results, key=lambda x: x.path):
        if r.n == 0:
            lines.append(f"| {r.method} | `{r.path}` | - | - | - | ERR |")
        else:
            lines.append(f"| {r.method} | `{r.path}` | {r.p50_ms:.2f} | {r.p95_ms:.2f} | {r.mean_ms:.2f} | {r.errors} |")
    lines.append("")
    lines.append("## ✅ 结论")
    lines.append("")
    if total_err == 0:
        lines.append("- ✅ 所有端点 0 错误 100% 成功")
    else:
        lines.append(f"- ⚠️ {total_err} 个端点有错误,需关注")
    avg_p95 = statistics.mean([r.p95_ms for r in results if r.n > 0]) if any(r.n > 0 for r in results) else 0
    lines.append(f"- 📊 全局平均 p95: **{avg_p95:.2f} ms**")
    lines.append(f"- 🎯 最快端点 p95: **{min(r.p95_ms for r in results if r.n > 0):.2f} ms**")
    lines.append(f"- 🐢 最慢端点 p95: **{max(r.p95_ms for r in results if r.n > 0):.2f} ms**")
    return "\n".join(lines)


def _categorize_endpoints(results: List[BenchmarkResult]) -> Dict[str, List[BenchmarkResult]]:
    """按 path 前缀分类"""
    cats: Dict[str, List[BenchmarkResult]] = {}
    for r in results:
        # 提取 /api/<category>/...
        parts = r.path.split("/")
        if len(parts) >= 3 and parts[1] == "api":
            cat = parts[2]
            label = f"api/{cat}"
        elif r.path == "/":
            label = "core"
        else:
            label = "other"
        cats.setdefault(label, []).append(r)
    return cats


# ============== 内存采样 ==============

@dataclass
class MemorySample:
    label: str
    rss_kb: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def sample_memory(label: str = "current") -> MemorySample:
    """读取当前进程 RSS (KB),仅 macOS/Linux"""
    sample = MemorySample(label=label)
    try:
        import resource
        usage = resource.getrusage(resource.RUSAGE_SELF)
        rss = float(usage.ru_maxrss)
        # macOS returns bytes, Linux returns KB
        if rss > 1_000_000:  # > 1M 视为 bytes(macOS)
            sample.rss_kb = rss / 1024.0
        else:  # 已经是 KB
            sample.rss_kb = rss
    except Exception:
        pass
    return sample


# ============== 持久化 ==============

def save_results(results: List[BenchmarkResult], memory: Optional[List[MemorySample]] = None,
                 path: str = BENCHMARK_JSON) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "version": "v1.0.1",
        "total_endpoints": len(results),
        "total_errors": sum(r.errors for r in results),
        "results": [r.to_dict() for r in results],
        "memory": [m.to_dict() for m in (memory or [])],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)


def save_report(results: List[BenchmarkResult], path: str = BENCHMARK_MD) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    content = generate_report(results)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def load_results(path: str = BENCHMARK_JSON) -> Optional[Dict[str, Any]]:
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# ============== CLI ==============

def main() -> int:
    """CLI 入口"""
    import argparse
    parser = argparse.ArgumentParser(description="aichat-hub 性能基准")
    sub = parser.add_subparsers(dest="cmd")

    p_run = sub.add_parser("run", help="跑全部端点")
    p_run.add_argument("--n", type=int, default=20, help="每端点请求数 (default 20)")
    p_run.add_argument("--skip", nargs="*", default=[], help="跳过指定 path")

    p_one = sub.add_parser("one", help="跑单端点")
    p_one.add_argument("method")
    p_one.add_argument("path")
    p_one.add_argument("--n", type=int, default=20)
    p_one.add_argument("--payload", type=str, default=None, help="JSON 字符串")

    p_list = sub.add_parser("list", help="列出所有端点")
    p_report = sub.add_parser("report", help="生成 markdown 报告(基于已有 JSON)")
    p_summary = sub.add_parser("summary", help="打印汇总(基于已有 JSON)")

    args = parser.parse_args()
    if args.cmd == "list":
        eps = get_all_endpoints()
        print(f"Total endpoints: {len(eps)}")
        for m, p, _ in eps:
            print(f"  {m:6s} {p}")
        return 0
    if args.cmd == "one":
        payload = None
        if args.payload:
            try:
                payload = json.loads(args.payload)
            except json.JSONDecodeError:
                print(f"ERROR: invalid JSON payload: {args.payload}", file=sys.stderr)
                return 1
        res = run_endpoint_n(args.method, args.path, payload, n=args.n)
        print(f"Method: {res.method} Path: {res.path}")
        print(f"  n={res.n} errors={res.errors}")
        print(f"  p50={res.p50_ms:.2f}ms p95={res.p95_ms:.2f}ms p99={res.p99_ms:.2f}ms")
        print(f"  min={res.min_ms:.2f}ms max={res.max_ms:.2f}ms mean={res.mean_ms:.2f}ms")
        return 0
    if args.cmd == "run":
        results = benchmark_all(n=args.n, skip_paths=args.skip)
        mem = [sample_memory("post-bench")]
        save_results(results, memory=mem)
        save_report(results)
        print(f"Benchmarked {len(results)} endpoints")
        valid = [r for r in results if r.n > 0]
        if valid:
            print(f"  p95 mean: {statistics.mean([r.p95_ms for r in valid]):.2f}ms")
            print(f"  errors: {sum(r.errors for r in results)}")
        print(f"  JSON: {BENCHMARK_JSON}")
        print(f"  MD:   {BENCHMARK_MD}")
        return 0
    if args.cmd == "report":
        data = load_results()
        if not data:
            print("No benchmark data. Run 'benchmark.py run' first.", file=sys.stderr)
            return 1
        results_objs = [BenchmarkResult(**r) for r in data["results"]]
        save_report(results_objs)
        print(f"Report saved: {BENCHMARK_MD}")
        return 0
    if args.cmd == "summary":
        data = load_results()
        if not data:
            print("No benchmark data. Run 'benchmark.py run' first.", file=sys.stderr)
            return 1
        print(f"Generated: {data['generated_at']}")
        print(f"Total: {data['total_endpoints']} endpoints, {data['total_errors']} errors")
        results_objs = [BenchmarkResult(**r) for r in data["results"]]
        valid = [r for r in results_objs if r.n > 0]
        if valid:
            print(f"p95 mean: {statistics.mean([r.p95_ms for r in valid]):.2f}ms")
            print(f"Fastest p95: {min(r.p95_ms for r in valid):.2f}ms ({min(valid, key=lambda x: x.p95_ms).path})")
            print(f"Slowest p95: {max(r.p95_ms for r in valid):.2f}ms ({max(valid, key=lambda x: x.p95_ms).path})")
        return 0
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
