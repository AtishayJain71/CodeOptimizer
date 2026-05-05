import os
from typing import Dict, List

from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph
from pydantic import BaseModel

from config import settings

llm = OllamaLLM(model=settings.CODE_REVIEW_MODEL)

REVIEW_PROMPT = """You are an expert code reviewer specializing in high-performance computing, security, and software architecture.
Analyze the following {language} code and provide a professional, structured review.

```{language}
{code}
```

Respond ONLY with a markdown-formatted review using this exact structure:

## Code Review

### 1. Errors & Bugs
- List syntax errors, logical mistakes, undefined behaviors, and edge cases.
- For each issue: describe it and provide a fix.

### 2. Performance & Optimization
- Identify inefficient algorithms, redundant operations, slow logic.
- Suggest optimized alternatives with reasoning.

### 3. Code Quality & Maintainability
- Evaluate structure, readability, modularity.
- Flag SOLID/DRY/KISS violations and suggest refactoring.

### 4. Security & Reliability
- Identify injection risks, unsafe input handling, concurrency issues.
- Recommend secure alternatives and better error handling.

### 5. Best Practices & Standards
- Assess naming, function decomposition, error handling.
- Recommend language-specific improvements.

Rules:
- Do NOT describe the file's purpose — focus only on the review.
- Do NOT make assumptions about missing parts — analyze only what is provided.
- Be specific and actionable."""


class CodeReviewState(BaseModel):
    file_path: str = ""
    project_path: str = ""
    code: str = ""
    language: str = "python"
    ignore_files: List[str] = []
    file_extensions: List[str] = []
    files_found: List[str] = []
    report: Dict[str, str] = {}


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

    # Direct code string (no file)
    if state.code:
        prompt = REVIEW_PROMPT.format(language=state.language, code=state.code)
        report["__inline__"] = llm.invoke(prompt)
        return state.model_copy(update={"report": report})

    # File(s)
    for file in state.files_found:
        try:
            with open(file, "r", encoding="utf-8") as f:
                code = f.read()
        except Exception as e:
            report[file] = f"Error reading file: {e}"
            continue

        _, ext = os.path.splitext(file)
        language = ext.lstrip(".") or "text"
        prompt = REVIEW_PROMPT.format(language=language, code=code)
        report[file] = llm.invoke(prompt)

    return state.model_copy(update={"report": report})


workflow.set_entry_point("find_files_found")
workflow.add_edge("find_files_found", "review_code")
workflow.add_edge("review_code", END)

code_review_executor = workflow.compile()


def get_code_review_for_code(code: str, language: str = "python") -> dict:
    result = code_review_executor.invoke(
        CodeReviewState(code=code, language=language)
    )
    return dict(result["report"])


def get_code_review_for_file(file_path: str) -> dict:
    result = code_review_executor.invoke(
        CodeReviewState(file_path=file_path)
    )
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
