"""多模型 Fallback 链 — 按优先级尝试多个模型，任一可用即返回。

配置方式：在 .env 中设置 FALLBACK_MODELS（JSON 格式）：
  FALLBACK_MODELS='[{"model":"deepseek-chat","base_url":"...","api_key":"..."}, ...]'

未配置时默认只用 DeepSeek。
"""

import json
import os

from dotenv import load_dotenv  # pyright: ignore
from openai import OpenAI
from pathlib import Path

from core.retry import RETRYABLE

# 加载 .env
load_dotenv(Path(__file__).parent.parent / ".env")

DEFAULT_CHAIN = [
    {
        "model": "deepseek-chat",
        "base_url": "https://api.deepseek.com",
        "api_key": os.getenv("DEEPSEEK_API_KEY", ""),
    }
]


def _load_chain() -> list[dict]:
    """从环境变量加载模型链。"""
    raw = os.getenv("FALLBACK_MODELS", "")
    if raw:
        try:
            chain = json.loads(raw)
            if chain:
                return chain
        except json.JSONDecodeError:
            pass
    return DEFAULT_CHAIN


def call_with_fallback(messages, tools, temperature=0.7, logger=None):
    """按优先级尝试模型链，第一个成功的结果直接返回。

    所有模型都失败时抛出最后一个错误。
    """
    chain = _load_chain()
    last_error = None

    for i, cfg in enumerate(chain):
        model = cfg["model"]
        try:
            client = OpenAI(
                api_key=cfg.get("api_key") or os.getenv("DEEPSEEK_API_KEY"),
                base_url=cfg["base_url"],
            )
            if logger:
                logger.info("fallback.try", model=model, index=i, total=len(chain))

            return client.chat.completions.create(
                model=model,
                messages=messages,
                tools=tools,
                temperature=temperature,
            )

        except RETRYABLE as e:
            last_error = e
            if logger:
                logger.warning(
                    "fallback.switch",
                    from_model=model,
                    error=type(e).__name__,
                    remaining=len(chain) - i - 1,
                )
            continue
        except Exception as e:
            # 不可重试的错误（如 401）不 fallback
            raise

    # 所有模型均失败
    if last_error:
        raise last_error
    raise RuntimeError("fallback: no models configured")
