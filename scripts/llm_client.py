#!/usr/bin/env python3
"""
aichat-hub LLM Client
=====================
统一 LLM 客户端,支持多个 provider(OpenAI 兼容协议)。

Cycle 1 目标:
  - OpenAI / DeepSeek / 智谱 / 阿里 DashScope(都是 OpenAI 兼容)
  - mock 模式(无 key 也能跑)

设计:Provider 抽象 + 简单 fallback
"""
from __future__ import annotations
import os
import time
import json
from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from pathlib import Path


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str

    def to_dict(self) -> Dict[str, str]:
        return {"role": self.role, "content": self.content}


@dataclass
class ChatResponse:
    content: str
    model: str
    usage: Dict[str, int]  # {"prompt_tokens": ..., "completion_tokens": ..., "total_tokens": ...}
    cost_usd: float
    latency_ms: int
    raw: Optional[Dict[str, Any]] = None


# 已知 provider 配置(2026-07)
PROVIDER_PRESETS = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "input_price_per_1m": 0.15,   # USD
        "output_price_per_1m": 0.60,
    },
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "input_price_per_1m": 0.14,
        "output_price_per_1m": 0.28,
    },
    "zhipu": {
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
        "input_price_per_1m": 0.0,   # flash 免费
        "output_price_per_1m": 0.0,
    },
    "dashscope": {
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "input_price_per_1m": 0.8,
        "output_price_per_1m": 2.0,
    },
    "moonshot": {
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "input_price_per_1m": 2.0,
        "output_price_per_1m": 2.0,
    },
    "mock": {
        "base_url": "mock://local",
        "default_model": "mock-model-v1",
        "input_price_per_1m": 0.0,
        "output_price_per_1m": 0.0,
    },
}


class LLMClient:
    """统一 LLM 客户端"""

    def __init__(self, provider: str = "mock", api_key: str = None,
                 model: str = None, base_url: str = None,
                 config_path: Path = None):
        self.provider = provider
        preset = PROVIDER_PRESETS.get(provider, PROVIDER_PRESETS["mock"])
        self.model = model or preset["default_model"]
        self.base_url = base_url or preset["base_url"]
        self.input_price = preset["input_price_per_1m"]
        self.output_price = preset["output_price_per_1m"]
        self.api_key = api_key or self._load_api_key(provider)
        self._session = None

    def _load_api_key(self, provider: str) -> Optional[str]:
        """从环境变量加载"""
        env_map = {
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "zhipu": "ZHIPU_API_KEY",
            "dashscope": "DASHSCOPE_API_KEY",
            "moonshot": "MOONSHOT_API_KEY",
        }
        env_var = env_map.get(provider)
        if env_var:
            return os.environ.get(env_var)
        return None

    def _estimate_tokens(self, text: str) -> int:
        """粗略 token 估算(中英混合, ~1 token / 1.5 字符)"""
        if not text:
            return 0
        return max(1, int(len(text) / 1.5))

    def _calc_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        return (
            prompt_tokens * self.input_price / 1_000_000
            + completion_tokens * self.output_price / 1_000_000
        )

    def chat(
        self,
        messages: List[Message],
        temperature: float = 0.7,
        max_tokens: int = 512,
        **kwargs,
    ) -> ChatResponse:
        """调用 LLM(单轮)"""
        if self.provider == "mock" or not self.api_key:
            return self._mock_chat(messages)
        return self._openai_compat_chat(messages, temperature, max_tokens, **kwargs)

    def _mock_chat(self, messages: List[Message]) -> ChatResponse:
        """无 key 时的 mock 回复(根据 system prompt + 用户输入生成)"""
        t0 = time.time()
        # 找最后一条 user
        last_user = next(
            (m for m in reversed(messages) if m.role == "user"),
            None,
        )
        user_text = last_user.content if last_user else "(空)"

        # 找 system
        system = next(
            (m.content for m in messages if m.role == "system"),
            "",
        )

        # 模拟"虚拟人"回复
        if "医生" in system or "李医生" in system:
            content = (
                f"[李医生 mock] 根据您说的「{user_text[:30]}」,建议先观察 1-2 天,"
                f"如有加重及时就医。(这是 mock 回复,实际使用请配置真实 API key)"
            )
        elif "小爱" in system or "温柔" in system:
            content = (
                f"[小爱 mock] 嗯嗯,你说的是「{user_text[:30]}」呀~ "
                f"听起来你今天心情不错呢 🌸(mock)"
            )
        elif "小智" in system or "geek" in system.lower():
            content = (
                f"[小智 mock] 哦?「{user_text[:30]}」?这题有意思,等我 5 min, "
                f"我先 mock 一下 😎(mock)"
            )
        else:
            content = f"[mock:{self.provider}:{self.model}] 你说的是: {user_text[:100]}"

        prompt_tokens = sum(self._estimate_tokens(m.content) for m in messages)
        completion_tokens = self._estimate_tokens(content)
        latency = int((time.time() - t0) * 1000) + 200  # 假装 200ms

        return ChatResponse(
            content=content,
            model=self.model,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            cost_usd=self._calc_cost(prompt_tokens, completion_tokens),
            latency_ms=latency,
        )

    def _openai_compat_chat(
        self, messages: List[Message], temperature: float, max_tokens: int,
        **kwargs,
    ) -> ChatResponse:
        """调用 OpenAI 兼容协议"""
        try:
            import urllib.request
            import urllib.error
        except ImportError:
            return self._mock_chat(messages)

        url = f"{self.base_url.rstrip('/')}/chat/completions"
        body = {
            "model": self.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }
        t0 = time.time()
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as e:
            # 网络失败时回退 mock
            print(f"[llm_client] network error: {e}, fallback to mock")
            return self._mock_chat(messages)

        latency = int((time.time() - t0) * 1000)
        choice = data.get("choices", [{}])[0]
        content = choice.get("message", {}).get("content", "")
        usage = data.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", self._estimate_tokens(
            " ".join(m.content for m in messages)
        ))
        completion_tokens = usage.get("completion_tokens", self._estimate_tokens(content))

        return ChatResponse(
            content=content,
            model=data.get("model", self.model),
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            cost_usd=self._calc_cost(prompt_tokens, completion_tokens),
            latency_ms=latency,
            raw=data,
        )

    def parallel_chat(
        self, providers: List[str], messages: List[Message], **kwargs
    ) -> Dict[str, ChatResponse]:
        """并行调用 N 个 provider,返回 {provider: response}"""
        results = {}
        for prov in providers:
            client = LLMClient(provider=prov)
            try:
                results[prov] = client.chat(messages, **kwargs)
            except Exception as e:
                results[prov] = ChatResponse(
                    content=f"[error: {e}]",
                    model=client.model,
                    usage={"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
                    cost_usd=0.0,
                    latency_ms=0,
                )
        return results


if __name__ == "__main__":
    # demo
    print("=== aichat-hub LLM Client Demo ===\n")
    for prov in ["mock", "openai", "deepseek", "zhipu", "dashscope", "moonshot"]:
        c = LLMClient(provider=prov)
        print(f"Provider: {prov}")
        print(f"  base_url:  {c.base_url}")
        print(f"  model:     {c.model}")
        print(f"  api_key:   {'<set>' if c.api_key else '<not set, will mock>'}")
        print()
