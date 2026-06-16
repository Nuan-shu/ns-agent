"""API 重试 — 指数退避，可重试错误自动重试。"""

import time

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    RateLimitError,
)

MAX_RETRIES = 3
BASE_DELAY = 1  # 秒：1 → 2 → 4


RETRYABLE = (APIConnectionError, APITimeoutError, RateLimitError, InternalServerError)


def call_with_retry(fn, *args, **kwargs):
    """调用函数，可重试错误自动重试（指数退避）。

    不可重试的错误（400/401）直接抛出，不浪费重试次数。
    """
    last_error = None
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except RETRYABLE as e:
            last_error = e
            if attempt < MAX_RETRIES:
                delay = BASE_DELAY * (2 ** (attempt - 1))
                print(f"  [重试 {attempt}/{MAX_RETRIES}] {type(e).__name__}，{delay}s 后重试...")
                time.sleep(delay)

    # 所有重试耗尽
    if last_error:
        raise last_error
    raise RuntimeError("retry: unreachable")  # 理论上不会到这里
