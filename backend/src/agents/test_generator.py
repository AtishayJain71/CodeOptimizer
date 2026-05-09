from typing import Generator

from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph
from pydantic import BaseModel

from config import settings

llm = OllamaLLM(
    model=settings.TEST_GEN_MODEL,
    temperature=settings.LLM_TEMPERATURE,
)

# Language → test framework mapping shown to the model
FRAMEWORK = {
    "python": "pytest",
    "javascript": "Jest",
    "typescript": "Jest",
    "java": "JUnit 5",
    "go": "Go testing package",
    "cpp": "Google Test",
    "ruby": "RSpec",
    "rust": "Rust built-in #[test]",
}

TEST_PROMPT = """Write {framework} tests for the following {language} code.

RULES:
- Output ONLY valid, runnable {framework} test code. No explanations outside code.
- Import or require the functions/classes being tested.
- Each test function name must describe what it tests.
- Cover: (1) normal inputs, (2) edge cases (empty, zero, None/null, boundary), (3) expected errors/exceptions.
- Keep each test short and focused on one thing.

Code to test:
```{language}
{code}
```

Start your response with the import statements. Output only code."""


class TestGenState(BaseModel):
    code: str
    language: str = "python"
    tests: str = ""


workflow = StateGraph(TestGenState)


@workflow.add_node
def generate_tests(state: TestGenState) -> TestGenState:
    framework = FRAMEWORK.get(state.language.lower(), state.language + " testing framework")
    prompt = TEST_PROMPT.format(
        framework=framework,
        language=state.language,
        code=state.code,
    )
    tests = llm.invoke(prompt)

    # Strip markdown fences if the model wrapped its output
    cleaned = tests.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first and last fence lines
        inner = [l for l in lines if not l.strip().startswith("```")]
        cleaned = "\n".join(inner).strip()

    return state.model_copy(update={"tests": cleaned})


workflow.set_entry_point("generate_tests")
workflow.add_edge("generate_tests", END)

test_gen_executor = workflow.compile()


def stream_tests(code: str, language: str = "python") -> Generator[str, None, None]:
    framework = FRAMEWORK.get(language.lower(), language + " testing framework")
    prompt = TEST_PROMPT.format(framework=framework, language=language, code=code)
    yield from llm.stream(prompt)


def get_test_cases(code: str, language: str = "python") -> str:
    result = test_gen_executor.invoke(TestGenState(code=code, language=language))
    return result["tests"]
