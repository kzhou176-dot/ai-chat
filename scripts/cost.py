#!/usr/bin/env python3
"""
aichat-hub Cost (成本追踪) 模块
================================
追踪 LLM 调用的 token 与费用。

数据来源:
  - llm_client.PROVIDER_PRESETS 已有每个 provider 的 input/output 单价
  - LLMClient 调用的 ChatResponse.usage 和 cost_usd

功能:
  - 单次调用成本记录
  - 累计(总 token/总费用)
  - 按 provider / model 拆解
  - 持久化(JSON)
  - 预算告警(超过阈值)

Cycle 9 - 基础版
"""
from __future__ import annotations
import json
import time
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Dict, List, Optional, Any


# 默认单价(美元/百万 token)— 与 llm_client.PROVIDER_PRESETS 一致
# 来源:2026 年公开价格
DEFAULT_PRICING: Dict[str, Dict[str, float]] = {
    "openai": {"input": 0.15, "output": 0.60},       # gpt-4o-mini
    "deepseek": {"input": 0.14, "output": 0.28},     # deepseek-chat
    "zhipu": {"input": 0.0, "output": 0.0},          # glm-4-flash 免费
    "dashscope": {"input": 0.8, "output": 2.0},      # qwen-plus
    "moonshot": {"input": 2.0, "output": 2.0},       # moonshot-v1-8k
    "anthropic": {"input": 3.0, "output": 15.0},     # claude-3-5-sonnet
    "mock": {"input": 0.0, "output": 0.0},
}


@dataclass
class CostEntry:
    """单次调用成本记录"""
    ts: float
    provider: str
    model: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    cost_usd: float = 0.0
    latency_ms: int = 0
    label: str = ""  # 可选标签(如 persona 名字)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class CostTracker:
    """成本追踪器"""

    def __init__(
        self,
        root: Path = None,
        pricing: Dict[str, Dict[str, float]] = None,
        budget_usd: float = None,
    ):
        self.root = root or Path(
            "str(Path(__file__).parent.parent)/data/cost"
        )
        self.root.mkdir(parents=True, exist_ok=True)
        self.pricing = pricing or DEFAULT_PRICING
        self.budget_usd = budget_usd
        self.entries: List[CostEntry] = []
        self._load()

    def _path(self) -> Path:
        return self.root / "costs.json"

    def _load(self):
        path = self._path()
        if not path.exists():
            return
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.entries = [CostEntry(**e) for e in data.get("entries", [])]
        except (json.JSONDecodeError, TypeError) as e:
            print(f"[cost] load warning: {e}")

    def save(self):
        data = {
            "entries": [e.to_dict() for e in self.entries],
            "saved_at": time.time(),
        }
        self._path().write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    # ---------- 记录 ----------

    def record(
        self,
        provider: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int = 0,
        label: str = "",
    ) -> CostEntry:
        """记录一次调用成本"""
        total = prompt_tokens + completion_tokens
        cost = self._calc_cost(provider, prompt_tokens, completion_tokens)
        entry = CostEntry(
            ts=time.time(),
            provider=provider,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total,
            cost_usd=cost,
            latency_ms=latency_ms,
            label=label,
        )
        self.entries.append(entry)
        # 保留最近 1000 条
        if len(self.entries) > 1000:
            self.entries = self.entries[-1000:]
        return entry

    def _calc_cost(self, provider: str, prompt_tokens: int, completion_tokens: int) -> float:
        p = self.pricing.get(provider, {"input": 0, "output": 0})
        return (
            prompt_tokens * p.get("input", 0) / 1_000_000
            + completion_tokens * p.get("output", 0) / 1_000_000
        )

    # ---------- 统计 ----------

    def total(self) -> Dict[str, Any]:
        """累计统计"""
        return {
            "total_calls": len(self.entries),
            "total_tokens": sum(e.total_tokens for e in self.entries),
            "prompt_tokens": sum(e.prompt_tokens for e in self.entries),
            "completion_tokens": sum(e.completion_tokens for e in self.entries),
            "total_cost_usd": round(sum(e.cost_usd for e in self.entries), 6),
            "avg_latency_ms": (
                int(sum(e.latency_ms for e in self.entries) / len(self.entries))
                if self.entries else 0
            ),
        }

    def by_provider(self) -> Dict[str, Dict[str, Any]]:
        """按 provider 拆解"""
        out: Dict[str, Dict[str, Any]] = {}
        for e in self.entries:
            p = e.provider
            if p not in out:
                out[p] = {
                    "calls": 0,
                    "tokens": 0,
                    "cost_usd": 0.0,
                    "avg_latency_ms": 0,
                    "_latency_sum": 0,
                }
            out[p]["calls"] += 1
            out[p]["tokens"] += e.total_tokens
            out[p]["cost_usd"] += e.cost_usd
            out[p]["_latency_sum"] += e.latency_ms
        for p, v in out.items():
            v["cost_usd"] = round(v["cost_usd"], 6)
            v["avg_latency_ms"] = int(v["_latency_sum"] / v["calls"]) if v["calls"] else 0
            del v["_latency_sum"]
        return out

    def by_model(self) -> Dict[str, Dict[str, Any]]:
        """按 model 拆解"""
        out: Dict[str, Dict[str, Any]] = {}
        for e in self.entries:
            m = e.model
            if m not in out:
                out[m] = {"provider": e.provider, "calls": 0, "tokens": 0, "cost_usd": 0.0}
            out[m]["calls"] += 1
            out[m]["tokens"] += e.total_tokens
            out[m]["cost_usd"] += e.cost_usd
        for v in out.values():
            v["cost_usd"] = round(v["cost_usd"], 6)
        return out

    def by_label(self) -> Dict[str, Dict[str, Any]]:
        """按标签(如 persona)拆解"""
        out: Dict[str, Dict[str, Any]] = {}
        for e in self.entries:
            label = e.label or "(unlabeled)"
            if label not in out:
                out[label] = {"calls": 0, "tokens": 0, "cost_usd": 0.0}
            out[label]["calls"] += 1
            out[label]["tokens"] += e.total_tokens
            out[label]["cost_usd"] += e.cost_usd
        for v in out.values():
            v["cost_usd"] = round(v["cost_usd"], 6)
        return out

    def check_budget(self) -> Optional[str]:
        """检查预算,超过返回警告消息"""
        if self.budget_usd is None:
            return None
        total = sum(e.cost_usd for e in self.entries)
        if total > self.budget_usd:
            return (
                f"⚠️ 预算超支: ${total:.4f} / ${self.budget_usd:.2f} "
                f"({total / self.budget_usd * 100:.0f}%)"
            )
        elif total > self.budget_usd * 0.8:
            return (
                f"⚠️ 预算告警: ${total:.4f} / ${self.budget_usd:.2f} "
                f"({total / self.budget_usd * 100:.0f}%,80% 阈值)"
            )
        return None

    def report(self) -> Dict[str, Any]:
        """完整报告"""
        return {
            "total": self.total(),
            "by_provider": self.by_provider(),
            "by_model": self.by_model(),
            "by_label": self.by_label(),
            "budget_warning": self.check_budget(),
            "budget_usd": self.budget_usd,
        }

    def clear(self):
        """清空记录"""
        self.entries = []


# ============== /api/cost endpoint helper ==============

def cost_report_from_dict(payload: Dict[str, Any]) -> Dict[str, Any]:
    """从 dict 生成 cost report"""
    # 创建临时 tracker,加 entries
    tracker = CostTracker()
    for e in payload.get("entries", []):
        tracker.entries.append(CostEntry(
            ts=e.get("ts", time.time()),
            provider=e.get("provider", "unknown"),
            model=e.get("model", "unknown"),
            prompt_tokens=e.get("prompt_tokens", 0),
            completion_tokens=e.get("completion_tokens", 0),
            total_tokens=e.get("total_tokens", 0),
            cost_usd=e.get("cost_usd", 0.0),
            latency_ms=e.get("latency_ms", 0),
            label=e.get("label", ""),
        ))
    return tracker.report()


if __name__ == "__main__":
    # demo
    tracker = CostTracker(budget_usd=0.10)
    print("=== Cost Tracker Demo ===\n")

    # 模拟 5 次不同 provider/model 的调用
    samples = [
        ("openai", "gpt-4o-mini", 1000, 500, 800),
        ("deepseek", "deepseek-chat", 2000, 1000, 600),
        ("zhipu", "glm-4-flash", 500, 200, 300),
        ("openai", "gpt-4o-mini", 1500, 800, 900),
        ("anthropic", "claude-3-5-sonnet", 800, 400, 1200),
    ]
    for prov, model, pt, ct, lat in samples:
        e = tracker.record(prov, model, pt, ct, lat, label="xiaoai")
        print(f"  {prov}/{model}: {pt+ct} tokens, ${e.cost_usd:.6f}, {lat}ms")
    tracker.save()

    print("\n=== Total ===")
    print(json.dumps(tracker.total(), ensure_ascii=False, indent=2))
    print("\n=== By Provider ===")
    print(json.dumps(tracker.by_provider(), ensure_ascii=False, indent=2))
    print("\n=== By Label ===")
    print(json.dumps(tracker.by_label(), ensure_ascii=False, indent=2))
    print("\n=== Budget ===")
    print(tracker.check_budget() or "✓ 预算内")
