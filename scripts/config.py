"""
aichat-hub config
=================
简单的 API key 管理。从环境变量 / 配置文件 / .env 加载。
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Dict, Optional

ROOT = Path(__file__).resolve().parent.parent
CONFIG_FILE = ROOT / ".env"


# 预定义的模型适配器配置
MODELS: Dict[str, Dict] = {
    "openai": {
        "name": "OpenAI",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o-mini",
        "env_key": "OPENAI_API_KEY",
    },
    "deepseek": {
        "name": "DeepSeek",
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
        "env_key": "DEEPSEEK_API_KEY",
    },
    "zhipu": {
        "name": "智谱 GLM",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4-flash",
        "env_key": "ZHIPU_API_KEY",
    },
    "dashscope": {
        "name": "阿里通义",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-turbo",
        "env_key": "DASHSCOPE_API_KEY",
    },
    "moonshot": {
        "name": "Moonshot Kimi",
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "moonshot-v1-8k",
        "env_key": "MOONSHOT_API_KEY",
    },
    "anthropic": {
        "name": "Anthropic Claude",
        "base_url": "https://api.anthropic.com/v1",
        "default_model": "claude-3-5-sonnet-20241022",
        "env_key": "ANTHROPIC_API_KEY",
    },
}


def load_env_file(path: Path = CONFIG_FILE) -> Dict[str, str]:
    """简单的 .env 解析 (KEY=VALUE)"""
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def get_api_key(provider: str) -> Optional[str]:
    """获取某个 provider 的 API key(优先环境变量,其次 .env)"""
    if provider not in MODELS:
        return None
    env_key = MODELS[provider]["env_key"]
    val = os.environ.get(env_key)
    if val:
        return val
    env = load_env_file()
    return env.get(env_key)


def list_providers() -> list:
    """列出所有 provider 及其 key 是否就绪"""
    return [
        {
            "id": pid,
            "name": cfg["name"],
            "model": cfg["default_model"],
            "key_ready": bool(get_api_key(pid)),
        }
        for pid, cfg in MODELS.items()
    ]


if __name__ == "__main__":
    # 自测
    print("aichat-hub config — providers:")
    for p in list_providers():
        status = "✅" if p["key_ready"] else "❌"
        print(f"  {status} {p['id']:12s} {p['name']:20s} default: {p['model']}")
