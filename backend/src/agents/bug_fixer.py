from typing import Dict, Optional

from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph
from pydantic import BaseModel

from config import settings

llm = OllamaLLM(model=settings.BUG_FIX_MODEL)


class BugFixState(BaseModel):
    file_path: str = ""
    error_message: str
    code: str = ""
    error_analysis: str = ""
    fix_suggestion: str = ""
    fixed_code: str = ""
    validation_result: str = ""
    report: Dict[str, str] = {}


workflow = StateGraph(BugFixState)


@workflow.add_node
def read_file(state: BugFixState) -> BugFixState:
    if state.file_path:
        with open(state.file_path, "r", encoding="utf-8") as f:
            code = f.read()
        return state.model_copy(update={"code": code})
    return state


@workflow.add_node
def analyze_error(state: BugFixState) -> BugFixState:
    prompt = f"""You are an expert software debugger.

Error message:
{state.error_message}

Code:
```
{state.code}
```

Analyze the root cause of this error. Explain exactly:
1. What is going wrong and why
2. Which line(s) are responsible
3. Any edge cases that could trigger this

Be precise and technical."""

    analysis = llm.invoke(prompt)
    return state.model_copy(update={
        "error_analysis": analysis,
        "report": {**state.report, "error_analysis": analysis}
    })


@workflow.add_node
def suggest_fix(state: BugFixState) -> BugFixState:
    prompt = f"""You are an expert software engineer.

Error analysis:
{state.error_analysis}

Original code:
```
{state.code}
```

Based on the analysis, suggest a clear and complete fix. Explain:
1. What change is needed and why
2. Any side effects to watch for
3. Any related improvements worth making"""

    fix = llm.invoke(prompt)
    return state.model_copy(update={
        "fix_suggestion": fix,
        "report": {**state.report, "fix_suggestion": fix}
    })


@workflow.add_node
def apply_fix(state: BugFixState) -> BugFixState:
    """Ask the LLM to rewrite the code with the fix applied."""
    prompt = f"""You are an expert software engineer.

Original code:
```
{state.code}
```

Suggested fix:
{state.fix_suggestion}

Rewrite the COMPLETE code with the fix applied. Output ONLY the corrected code — no explanations, no markdown fences, no comments about what changed. The output must be directly executable."""

    fixed_code = llm.invoke(prompt)
    return state.model_copy(update={
        "fixed_code": fixed_code,
        "report": {**state.report, "fixed_code": fixed_code}
    })


@workflow.add_node
def validate_fix(state: BugFixState) -> BugFixState:
    prompt = f"""You are a code reviewer.

Original error: {state.error_message}

Fixed code:
```
{state.fixed_code}
```

Does this fixed code resolve the original error? Check for:
1. Does it address the root cause?
2. Are there any new syntax or logic errors introduced?
3. Are there remaining edge cases that could still fail?

Respond with: VALID (if the fix is correct) or ISSUES FOUND: <description> (if problems remain)."""

    validation = llm.invoke(prompt)
    return state.model_copy(update={
        "validation_result": validation,
        "report": {**state.report, "validation_result": validation}
    })


@workflow.add_node
def generate_report(state: BugFixState) -> BugFixState:
    final_report = f"""## Bug Fix Report

**Error:** {state.error_message}

---

### Root Cause Analysis
{state.error_analysis}

---

### Suggested Fix
{state.fix_suggestion}

---

### Fixed Code
```
{state.fixed_code}
```

---

### Validation
{state.validation_result}"""

    return state.model_copy(update={
        "report": {**state.report, "final_report": final_report}
    })


workflow.set_entry_point("read_file")
workflow.add_edge("read_file", "analyze_error")
workflow.add_edge("analyze_error", "suggest_fix")
workflow.add_edge("suggest_fix", "apply_fix")
workflow.add_edge("apply_fix", "validate_fix")
workflow.add_edge("validate_fix", "generate_report")
workflow.add_edge("generate_report", END)

bug_fix_executor = workflow.compile()


def get_bug_fixer_for_code(code: str, error_msg: str) -> dict:
    result = bug_fix_executor.invoke(
        BugFixState(code=code, error_message=error_msg)
    )
    return dict(result["report"])


def get_bug_fixer(file_path: str, error_msg: str) -> dict:
    result = bug_fix_executor.invoke(
        BugFixState(file_path=file_path, error_message=error_msg)
    )
    return dict(result["report"])
