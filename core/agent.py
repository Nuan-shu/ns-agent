"""NsAgent 核心 — Agent Loop。不关心工具有哪些，只从注册表读取。"""

import json
import os
from pathlib import Path

from dotenv import load_dotenv  # pyright: ignore
from openai import OpenAI

from core.context import compress, count_messages_tokens
from core.errors import NsAgentError
from core.fallback import call_with_fallback
from core.logging import get_logger, new_trace_id, setup_logging
from core.prompt import build_prompt
from core.retry import call_with_retry
from memory import session as sess
from memory.task import init_db as init_task_db
from skills.registry import inject_skills, match_skills
from tools.registry import execute, get_tool_definitions

# 加载 .env（agent.py 在 core/ 下，.env 在项目根目录）
load_dotenv(Path(__file__).parent.parent / ".env")

# 初始化结构化日志
setup_logging(dev_mode=True)

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")


def _stream_response(messages, tools, log):
    """流式调用 LLM，逐 token 打印，累积 tool_calls。

    Returns:
        (content, tool_calls): content 为累积文本，tool_calls 为工具调用列表。
    """
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools,
        temperature=0.7,
        stream=True,
        stream_options={"include_usage": True},
    )

    collected = ""
    tool_calls = []
    current_idx = -1

    for chunk in response:
        delta = chunk.choices[0].delta if chunk.choices else None
        if not delta:
            continue

        # 文本：逐 token 打印
        if delta.content:
            collected += delta.content
            print(delta.content, end="", flush=True)

        # 工具调用：累积 delta
        if delta.tool_calls:
            for tc_delta in delta.tool_calls:
                idx = tc_delta.index
                if idx > current_idx:
                    tool_calls.append({
                        "id": tc_delta.id or "",
                        "type": "function",
                        "function": {"name": "", "arguments": ""},
                    })
                    current_idx = idx

                tc = tool_calls[idx]
                if tc_delta.id:
                    tc["id"] = tc_delta.id
                if tc_delta.function:
                    if tc_delta.function.name:
                        tc["function"]["name"] += tc_delta.function.name
                    if tc_delta.function.arguments:
                        tc["function"]["arguments"] += tc_delta.function.arguments

    return collected, tool_calls


def run(messages=None, session_id=None, log=None, stream=True):
    """启动 Agent Loop。messages 为初始消息列表。"""
    if log is None:
        log = get_logger()

    if messages is None:
        messages = [{"role": "system", "content": build_prompt()}]

    tools = get_tool_definitions()
    log.info("agent.tools_loaded", count=len(tools))

    while True:
        token_count = count_messages_tokens(messages)
        if token_count > 4000:
            messages, summary = compress(messages)
            if summary:
                new_count = count_messages_tokens(messages)
                log.info("agent.compressed", before=token_count, after=new_count)

        log.info("agent.llm_request", messages=len(messages))

        if stream:
            # ── 流式模式：逐 token 打印 ──
            content, tool_calls = _stream_response(
                messages, tools if tools else None, log
            )
            print()  # 换行

            if not tool_calls:
                log.info("agent.response", content_length=len(content))
                break

            # 有工具调用：流式已累积完整参数
            for tc in tool_calls:
                name = tc["function"]["name"]
                args = json.loads(tc["function"]["arguments"])
                log.info("agent.tool_start", tool=name, args=args)

                result = execute(name, args)
                log.info("agent.tool_result", tool=name,
                         result_preview=str(result)[:100])

                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [tc],
                })
                if session_id:
                    sess.save_message(session_id, messages[-1])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc["id"],
                    "content": str(result),
                })
                if session_id:
                    sess.save_message(session_id, messages[-1])
        else:
            # ── 非流式模式（子Agent 用） ──
            response = call_with_fallback(
                messages=messages,
                tools=tools if tools else None,
                temperature=0.7,
                logger=log,
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                log.info("agent.response", content_length=len(msg.content or ""))
                print(f"\n{msg.content}\n")
                break

            for tc in msg.tool_calls:
                name = tc.function.name
                args = json.loads(tc.function.arguments)
                log.info("agent.tool_start", tool=name, args=args)

                result = execute(name, args)
                log.info("agent.tool_result", tool=name,
                         result_preview=str(result)[:100])

                messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [{
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": name,
                            "arguments": tc.function.arguments,
                        },
                    }],
                })
                if session_id:
                    sess.save_message(session_id, messages[-1])
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": str(result),
                })
                if session_id:
                    sess.save_message(session_id, messages[-1])


def chat():
    """交互式 REPL。自动恢复 24h 内会话。"""
    trace_id = new_trace_id()
    log = get_logger(trace_id=trace_id, module="agent")

    sess.init_db()
    init_task_db()
    session_id = sess.get_last_session()

    if session_id:
        old_messages = sess.load_session(session_id)
        log.info("nsagent.start", version="0.4.0", session_id=session_id,
                 restored=True, messages=len(old_messages))
        print(f"NsAgent v0.4.0 — 恢复了上次会话（{len(old_messages)} 条消息）")
        print("输入 /new 开始新会话，/exit 退出\n")
        messages = old_messages
    else:
        messages = [{"role": "system", "content": build_prompt()}]
        session_id = sess.create_session()
        sess.save_message(session_id, messages[0])
        log.info("nsagent.start", version="0.4.0", session_id=session_id, restored=False)
        print("NsAgent v0.4.0 — 输入 /exit 退出\n")

    while True:
        user_input = input("你: ").strip()
        if not user_input:
            continue
        if user_input == "/exit":
            log.info("session.exit", session_id=session_id)
            print(f"会话 {session_id} 已保存，再见。")
            break
        if user_input == "/new":
            session_id = sess.create_session()
            messages = [{"role": "system", "content": build_prompt()}]
            sess.save_message(session_id, messages[0])
            log.info("session.created", session_id=session_id)
            print("新会话已开始。")
            continue

        snapshot = len(messages)
        messages.append({"role": "user", "content": user_input})
        sess.save_message(session_id, messages[-1])

        matched = match_skills(user_input)
        if matched:
            skill_names = [s["description"] for s in matched]
            log.info("skill.activated", skills=skill_names, count=len(matched))
            messages = inject_skills(messages, matched)

        try:
            run(messages=messages, session_id=session_id, log=log.bind(phase="run"))
        except NsAgentError as e:
            log.error("agent.error", code=e.code, message=e.message)
            print(f"NsAgent 错误 [{e.code}]: {e.message}")
            del messages[snapshot:]
        except Exception as e:
            log.error("agent.unexpected_error", type=type(e).__name__, message=str(e))
            print(f"未预期错误: {type(e).__name__}: {e}")
            del messages[snapshot:]
