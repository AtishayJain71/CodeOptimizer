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
)

llm_short = OllamaLLM(
    model=settings.CODE_REVIEW_MODEL,
    temperature=settings.LLM_TEMPERATURE,
    num_predict=settings.GITHUB_MAX_TOKENS,  # GitHub PR comments must stay short
)

# ── Prompts ────────────────────────────────────────────────────────────────────

FULL_REVIEW_PROMPT = """You are a senior code reviewer. Review the {language} code below.

Rules (follow strictly):
- Only report issues that are LITERALLY VISIBLE in the code. No guessing, no assumptions.
- Each distinct issue must appear EXACTLY ONCE. Writing the same bullet twice is an error.
- If two issues share the same root cause, combine them into ONE bullet. No duplicates.
- Rank: 🔴 CRITICAL bugs first → 🟠 SECURITY → 🟡 PERFORMANCE → 🟢 CODE QUALITY last.
- Each bullet format: [emoji] **Label**: what is wrong. Fix: what to change.
- Maximum 8 bullets total. Each bullet must describe a DIFFERENT issue. Stop after all unique issues are listed.

```{language}
{code}
```

## Code Review

"""

SHORT_REVIEW_PROMPT = """Review this {language} code for a GitHub PR. Be strict and concise.

RULES:
- Only report issues visible in the code. No guessing.
- Merge related issues. No duplicates.
- Each bullet: one line problem + one line fix.

```{language}
{code}
```

Issues (most critical first):
"""


# ── Deduplication ─────────────────────────────────────────────────────────────

def _deduplicate_review(text: str) -> str:
    """Remove repeated lines from LLM output (local models tend to loop)."""
    seen = set()
    result = []
    for line in text.splitlines():
        key = " ".join(line.split())  # normalise whitespace before comparing
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        result.append(line)
    return "\n".join(result)


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
        report["__inline__"] = _deduplicate_review(model.invoke(prompt))
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
        report[file] = _deduplicate_review(model.invoke(prompt))

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
