import os
from typing import Dict, Generator, List

from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph
from pydantic import BaseModel

from config import settings

llm = OllamaLLM(
    model=settings.CODE_REVIEW_MODEL,
    temperature=settings.LLM_TEMPERATURE,
    num_predict=settings.REVIEW_MAX_TOKENS,
)

llm_short = OllamaLLM(
    model=settings.CODE_REVIEW_MODEL,
    temperature=settings.LLM_TEMPERATURE,
    num_predict=settings.GITHUB_MAX_TOKENS,
)

# ── Prompts ────────────────────────────────────────────────────────────────────

FULL_REVIEW_PROMPT = """You are a senior code reviewer. Analyze this {language} code strictly.

RULES:
- Only report issues that are DIRECTLY VISIBLE in the code below. No assumptions.
- Rank by severity: CRITICAL first, then SECURITY, then PERF, then QUALITY.
- Merge related issues into one bullet. No duplicates.
- Hard stop after 5 bullets. If fewer real issues exist, list only those.
- Each bullet: one line description + one line fix. No padding.

```{language}
{code}
```

## Code Review

**Priority Issues** (🔴 CRITICAL → 🟠 SECURITY → 🟡 PERF → 🟢 QUALITY):
"""

SHORT_REVIEW_PROMPT = """Review this {language} code for a GitHub PR. Be strict and concise.

RULES:
- Only report issues visible in the code. No guessing.
- Merge related issues. No duplicates. Max 5 bullets. Stop after 5.

```{language}
{code}
```

Issues (most critical first):
"""


# ── State ──────────────────────────────────────────────────────────────────────

class CodeReviewState(BaseModel):
    file_path: str = ""
    project_path: str = ""
    code: str = ""
    language: str = "python"
    short_review: bool = False
    ignore_files: List[str] = []
    file_extensions: List[str] = []
    files_found: List[str] = []
    report: Dict[str, str] = {}


# ── Workflow (used for non-streaming calls) ────────────────────────────────────

workflow = StateGraph(CodeReviewState)


@workflow.add_node
def find_files_found(state: CodeReviewState) -> CodeReviewState:
    files_found = []
    ignore_set = set(state.ignore_files)

    if state.file_path:
        if os.path.isfile(state.file_path):
            _, ext = os.path.splitext(state.file_path)
            if not state.file_extensions or ext in state.file_extensions:
                files_found.append(state.file_path)
    elif state.project_path:
        for root, dirs, files in os.walk(state.project_path):
            dirs[:] = [d for d in dirs if d not in ignore_set]
            for file in files:
                if file not in ignore_set and any(file.endswith(ext) for ext in state.file_extensions):
                    files_found.append(os.path.join(root, file))

    return state.model_copy(update={"files_found": files_found})


@workflow.add_node
def review_code(state: CodeReviewState) -> CodeReviewState:
    report = {}
    model = llm_short if state.short_review else llm
    prompt_template = SHORT_REVIEW_PROMPT if state.short_review else FULL_REVIEW_PROMPT

    if state.code:
        prompt = prompt_template.format(language=state.language, code=state.code)
        report["__inline__"] = model.invoke(prompt)
        return state.model_copy(update={"report": report})

    for file in state.files_found:
        try:
            with open(file, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            report[file] = f"Error reading file: {e}"
            continue
        _, ext = os.path.splitext(file)
        language = ext.lstrip(".") or "text"
        prompt = prompt_template.format(language=language, code=code)
        report[file] = model.invoke(prompt)

    return state.model_copy(update={"report": report})


workflow.set_entry_point("find_files_found")
workflow.add_edge("find_files_found", "review_code")
workflow.add_edge("review_code", END)

code_review_executor = workflow.compile()


# ── Streaming generators ───────────────────────────────────────────────────────

def stream_code_review(code: str, language: str = "python") -> Generator[str, None, None]:
    prompt = FULL_REVIEW_PROMPT.format(language=language, code=code)
    yield from llm.stream(prompt)


def stream_short_review(code: str, language: str = "python") -> Generator[str, None, None]:
    prompt = SHORT_REVIEW_PROMPT.format(language=language, code=code)
    yield from llm_short.stream(prompt)


# ── Non-streaming public API ───────────────────────────────────────────────────

def get_code_review_for_code(code: str, language: str = "python") -> dict:
    result = code_review_executor.invoke(CodeReviewState(code=code, language=language))
    return dict(result["report"])


def get_short_review_for_code(code: str, language: str = "python") -> dict:
    result = code_review_executor.invoke(
        CodeReviewState(code=code, language=language, short_review=True)
    )
    return dict(result["report"])


def get_code_review_for_file(file_path: str) -> dict:
    result = code_review_executor.invoke(CodeReviewState(file_path=file_path))
    return dict(result["report"])


def get_code_review_for_folder(project_path: str, ignore_files: list, file_extensions: list) -> dict:
    result = code_review_executor.invoke(
        CodeReviewState(
            project_path=project_path,
            ignore_files=ignore_files,
            file_extensions=file_extensions,
        )
    )
    return dict(result["report"])
