import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List

from config import settings
from agents.code_analysis import get_code_review_for_code, get_code_review_for_file, get_code_review_for_folder
from agents.bug_fixer import get_bug_fixer_for_code, get_bug_fixer
from agents.test_generator import get_test_cases
from agents.project_planner import get_project_plan

app = FastAPI(title="CodeOptimizer", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / Response models ──────────────────────────────────────────────────

class CodeReviewRequest(BaseModel):
    code: Optional[str] = None          # paste raw code
    file_path: Optional[str] = None     # OR provide a file path
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


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/review_code")
async def review_code(req: CodeReviewRequest) -> dict:
    code = _load_code(req.code, req.file_path)
    return {"review": get_code_review_for_code(code, req.language)}


@app.post("/review_folder")
async def review_folder(req: FolderReviewRequest) -> dict:
    if not os.path.isdir(req.folder_path):
        raise HTTPException(status_code=404, detail=f"Folder not found: {req.folder_path}")
    return {"review": get_code_review_for_folder(req.folder_path, req.ignore, req.extensions)}


@app.post("/fix_bug")
async def fix_bug(req: BugFixRequest) -> dict:
    code = _load_code(req.code, req.file_path)
    return {"report": get_bug_fixer_for_code(code, req.error_message)}


@app.post("/generate_tests")
async def generate_tests(req: TestGenRequest) -> dict:
    code = _load_code(req.code, req.file_path)
    return {"tests": get_test_cases(code, req.language)}


@app.post("/create_plan")
async def create_plan(req: PlanRequest) -> dict:
    return {"plan": get_project_plan(req.case_study)}


# ── Legacy GET endpoints (kept for backward compatibility) ─────────────────────

@app.get("/review_file")
async def review_file_legacy(file_path: str) -> dict:
    return {"review": get_code_review_for_file(file_path)}
