from typing import Generator, List

from langchain_ollama import OllamaLLM

from config import settings

llm = OllamaLLM(
    model=settings.CODE_REVIEW_MODEL,
    temperature=0.2,
)

CHAT_PROMPT = """You previously reviewed this {language} code:

```{language}
{code}
```

Previous review:
{review}

Conversation so far:
{history}

User question: {message}

Answer concisely and accurately. Base your answer on the code and review above.
Do not repeat the entire review. Be direct and specific."""


def _format_history(messages: List[dict]) -> str:
    if not messages:
        return "(none)"
    lines = []
    for m in messages[-settings.CHAT_HISTORY_TURNS:]:
        role = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{role}: {m['content']}")
    return "\n".join(lines)


def stream_chat(
    code: str,
    review: str,
    message: str,
    history: List[dict],
    language: str = "python",
) -> Generator[str, None, None]:
    prompt = CHAT_PROMPT.format(
        language=language,
        code=code,
        review=review,
        history=_format_history(history),
        message=message,
    )
    yield from llm.stream(prompt)
