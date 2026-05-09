import json
import os
from typing import List, Optional

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import settings
from agents.code_analysis import (
    get_code_review_for_code, get_code_review_for_file,
    get_code_review_for_folder, stream_code_review,
)
from agents.bug_fixer import get_bug_fixer_for_code, get_bug_fixer, stream_bug_fix
from agents.test_generator import get_test_cases, stream_tests
from agents.project_planner import get_project_plan
from agents.chat_agent import stream_chat
from agents.github_agent import verify_signature, handle_push, handle_pull_request

app = FastAPI(title="CodeOptimizer", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request models ─────────────────────────────────────────────────────────────

class CodeReviewRequest(BaseModel):
    code: Optional[str] = None
    file_path: Optional[str] = None
    language: str = "python"


class FolderReviewRequest(BaseModel):
    folder_path: str
    ignore: List[str] = ["node_modules", ".git", "__pycache__", ".venv"]
    extensions: List[str] = [".py", ".js", ".ts", ".java", ".cpp", ".go"]


class BugFixRequest(BaseModel):
    code: Optional[str] = None
    file_path: Optional[str] = None
    error_message: str


class TestGenRequest(BaseModel):
    code: Optional[str] = None
    file_path: Optional[str] = None
    language: str = "python"


class PlanRequest(BaseModel):
    case_study: str


class ChatRequest(BaseModel):
    code: str
    review: str
    message: str
    history: List[dict] = []
    language: str = "python"


# ── Helper ─────────────────────────────────────────────────────────────────────

def _load_code(code: Optional[str], file_path: Optional[str]) -> str:
    if code:
        return code
    if file_path:
        if not os.path.isfile(file_path):
            raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    raise HTTPException(status_code=400, detail="Provide either 'code' or 'file_path'.")


def _sse_stream(generator):
    """Wrap a text generator into Server-Sent Events format."""
    for chunk in generator:
        yield f"data: {json.dumps({'token': chunk})}\n\n"
    yield "data: [DONE]\n\n"


def _streaming_response(generator) -> StreamingResponse:
    return StreamingResponse(
        _sse_stream(generator),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",       # disable nginx buffering
            "Access-Control-Allow-Origin": "*",
        },
    )


# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


# ── Code Review ────────────────────────────────────────────────────────────────

@app.post("/review_code/stream")
def review_code_stream(req: CodeReviewRequest):
    """Streaming code review — tokens arrive in real time."""
    code = _load_code(req.code, req.file_path)
    return _streaming_response(stream_code_review(code, req.language))


@app.post("/review_code")
def review_code(req: CodeReviewRequest) -> dict:
    code = _load_code(req.code, req.file_path)
    return {"review": get_code_review_for_code(code, req.language)}


@app.post("/review_folder")
def review_folder(req: FolderReviewRequest) -> dict:
    if not os.path.isdir(req.folder_path):
        raise HTTPException(status_code=404, detail=f"Folder not found: {req.folder_path}")
    return {"review": get_code_review_for_folder(req.folder_path, req.ignore, req.extensions)}


# ── Bug Fixer ──────────────────────────────────────────────────────────────────

@app.post("/fix_bug/stream")
def fix_bug_stream(req: BugFixRequest):
    """Streaming bug fix."""
    code = _load_code(req.code, req.file_path)
    return _streaming_response(stream_bug_fix(code, req.error_message))


@app.post("/fix_bug")
def fix_bug(req: BugFixRequest) -> dict:
    code = _load_code(req.code, req.file_path)
    return {"report": get_bug_fixer_for_code(code, req.error_message)}


# ── Test Generator ─────────────────────────────────────────────────────────────

@app.post("/generate_tests/stream")
def generate_tests_stream(req: TestGenRequest):
    """Streaming test generation."""
    code = _load_code(req.code, req.file_path)
    return _streaming_response(stream_tests(code, req.language))


@app.post("/generate_tests")
def generate_tests(req: TestGenRequest) -> dict:
    code = _load_code(req.code, req.file_path)
    return {"tests": get_test_cases(code, req.language)}


# ── Project Planner ────────────────────────────────────────────────────────────

@app.post("/create_plan")
def create_plan(req: PlanRequest) -> dict:
    return {"plan": get_project_plan(req.case_study)}


# ── Chat (conversational follow-up) ───────────────────────────────────────────

@app.post("/chat/stream")
def chat_stream(req: ChatRequest):
    """Streaming follow-up conversation about a previous review."""
    return _streaming_response(
        stream_chat(req.code, req.review, req.message, req.history, req.language)
    )


# ── GitHub Webhook ─────────────────────────────────────────────────────────────

@app.post("/webhook/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    payload_bytes = await request.body()
    event = request.headers.get("X-GitHub-Event", "")
    signature = request.headers.get("X-Hub-Signature-256", "")

    if settings.GITHUB_SECRET:
        if not verify_signature(payload_bytes, signature, settings.GITHUB_SECRET):
            raise HTTPException(status_code=401, detail="Invalid webhook signature.")

    if not settings.GITHUB_TOKEN:
        raise HTTPException(status_code=500, detail="GITHUB_TOKEN is not configured.")

    payload = json.loads(payload_bytes)

    if event == "push":
        if payload.get("ref", "").startswith("refs/heads/"):
            background_tasks.add_task(handle_push, payload, settings.GITHUB_TOKEN)

    elif event == "pull_request":
        if payload.get("action", "") in ("opened", "synchronize", "reopened"):
            background_tasks.add_task(handle_pull_request, payload, settings.GITHUB_TOKEN)

    return {"status": "received", "event": event}


# ── Legacy ─────────────────────────────────────────────────────────────────────

@app.get("/review_file")
def review_file_legacy(file_path: str) -> dict:
    return {"review": get_code_review_for_file(file_path)}
