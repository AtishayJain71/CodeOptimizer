from typing import Dict, Generator

from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph
from pydantic import BaseModel

from config import settings

llm = OllamaLLM(
    model=settings.BUG_FIX_MODEL,
    temperature=settings.LLM_TEMPERATURE,
)

# Single prompt that does analysis + fix + corrected code in one shot.
# One LLM call instead of four — ~4x faster.
BUG_FIX_PROMPT = """Fix the following bug.

Error message:
{error_message}

Code:
{code}

Write your answer using these three sections. Do not skip any section.

## Root Cause
Explain what is causing the error and why.

## Fix
List every change that is needed, one change per line.

## Fixed Code
Write the complete corrected code with all fixes applied. Do not use placeholders."""


class BugFixState(BaseModel):
    file_path: str = ""
    error_message: str
    code: str = ""
    report: Dict[str, str] = {}


workflow = StateGraph(BugFixState)


@workflow.add_node
def read_file(state: BugFixState) -> BugFixState:
    if state.file_path and not state.code:
        with open(state.file_path, "r", encoding="utf-8") as f:
            code = f.read()
        return state.model_copy(update={"code": code})
    return state


@workflow.add_node
def analyze_and_fix(state: BugFixState) -> BugFixState:
    """Single LLM call: root cause + fix explanation + corrected code."""
    prompt = BUG_FIX_PROMPT.format(
        error_message=state.error_message,
        code=state.code,
    )
    result = llm.invoke(prompt)
    return state.model_copy(update={"report": {"final_report": result}})


workflow.set_entry_point("read_file")
workflow.add_edge("read_file", "analyze_and_fix")
workflow.add_edge("analyze_and_fix", END)

bug_fix_executor = workflow.compile()


def stream_bug_fix(code: str, error_msg: str) -> Generator[str, None, None]:
    prompt = BUG_FIX_PROMPT.format(error_message=error_msg, code=code)
    yield from llm.stream(prompt)


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
