"""ns-agent FastAPI wrapper — 在线 Demo 接口

调用 main_demo.py --query（精简版，不含 akshare），超时 120s。
"""
import subprocess
import sys
import os

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel

app = FastAPI(title="NsAgent API", version="0.4.0")


class Question(BaseModel):
    question: str


@app.post("/ask")
def ask(q: Question):
    try:
        result = subprocess.run(
            [sys.executable, "main_demo.py", "--query", q.question],
            capture_output=True,
            text=True,
            cwd="/root/ns-agent",
            timeout=120,
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        output = result.stdout.strip() or result.stderr.strip()
        return {"answer": output, "exit_code": result.returncode}
    except subprocess.TimeoutExpired:
        return JSONResponse(
            status_code=504,
            content={"error": "请求超时（>120s），ECS 配置较低请重试", "question": q.question},
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)[:200]})


@app.get("/")
def health():
    return {"status": "ok", "service": "NsAgent v0.4.0"}
