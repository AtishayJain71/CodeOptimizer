from langchain_ollama import OllamaLLM
from langgraph.constants import END
from langgraph.graph import StateGraph
from pydantic import BaseModel

from config import settings

llm = OllamaLLM(model=settings.TEST_GEN_MODEL)

TEST_PROMPT = """You are a senior QA engineer and test automation expert.

Analyze the following {language} code and generate a comprehensive test suite:

```{language}
{code}
```

Generate tests covering:

### 1. Unit Tests
- Test each function/method individually
- Test normal (happy-path) inputs
- Test boundary values (empty, zero, max, min)
- Test expected return types and values

### 2. Edge Cases
- Null/None/undefined inputs
- Empty strings, lists, dicts
- Very large or very small numbers
- Unexpected types

### 3. Error / Exception Tests
- Inputs that should raise exceptions
- Verify the correct exception type is raised
- Verify error messages where applicable

### 4. Integration Hints
- Note which functions depend on each other
- Suggest mock objects where external calls are needed

Format:
- Use the standard testing framework for {language} (e.g. pytest for Python, Jest for JS)
- Write actual runnable test code
- Add a one-line comment above each test explaining what it validates
- Group tests by class/function being tested

Output ONLY the test code. No explanations outside the code."""


class TestGenState(BaseModel):
    code: str
    language: str = "python"
    tests: str = ""


workflow = StateGraph(TestGenState)


@workflow.add_node
def generate_tests(state: TestGenState) -> TestGenState:
    prompt = TEST_PROMPT.format(language=state.language, code=state.code)
    tests = llm.invoke(prompt)
    return state.model_copy(update={"tests": tests})


workflow.set_entry_point("generate_tests")
workflow.add_edge("generate_tests", END)

test_gen_executor = workflow.compile()


def get_test_cases(code: str, language: str = "python") -> str:
    result = test_gen_executor.invoke(TestGenState(code=code, language=language))
    return result["tests"]
