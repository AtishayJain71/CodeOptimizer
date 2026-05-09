from pathlib import Path
from pydantic_settings import BaseSettings

# backend/.env — one level above the src/ directory where uvicorn runs
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # Ollama model names — change to match what you have pulled locally.
    # Run `ollama list` to see available models.
    CODE_REVIEW_MODEL: str = "qwen2.5-coder:7b"
    BUG_FIX_MODEL: str = "qwen2.5-coder:7b"
    PLANNING_MODEL: str = "llama3.1:8b"
    TEST_GEN_MODEL: str = "qwen2.5-coder:7b"

    # GitHub comment token limit — kept short so comments fit in PR timeline.
    # All other agents have no num_predict cap; conciseness is enforced via prompt.
    GITHUB_MAX_TOKENS: int = 600

    # Chat history turns to keep in context.
    # qwen2.5-coder:7b has a 32k-token context window.
    # Budget: ~1500 tokens (code + review) + CHAT_HISTORY_TURNS * ~200 tokens each.
    # Can safely raise this; 20 turns well within the 32k window.
    CHAT_HISTORY_TURNS: int = 12

    LLM_TEMPERATURE: float = 0.1

    # Ollama base URL (default local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # CORS origins allowed to call the API
    ALLOWED_ORIGINS: list = ["*"]

    # GitHub webhook integration
    GITHUB_SECRET: str = ""
    GITHUB_TOKEN: str = ""

    class Config:
        env_file = str(_ENV_FILE)


settings = Settings()
