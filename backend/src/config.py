from pathlib import Path
from pydantic_settings import BaseSettings

# backend/.env — one level above the src/ directory where uvicorn runs
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # Ollama model names — change to match what you have pulled locally.
    # Run `ollama list` to see available models.
    CODE_REVIEW_MODEL: str = "deepseek-coder:1.3b"
    BUG_FIX_MODEL: str = "deepseek-coder:1.3b"
    PLANNING_MODEL: str = "llama3.2:1b"
    TEST_GEN_MODEL: str = "deepseek-coder:1.3b"

    # GitHub comment token limit — kept short so comments fit in PR timeline.
    # All other agents have no num_predict cap; conciseness is enforced via prompt.
    GITHUB_MAX_TOKENS: int = 600

    # Chat history turns to keep in context.
    # deepseek-coder:1.3b has a 4096-token context window.
    # Budget: ~1500 tokens (code + review) + CHAT_HISTORY_TURNS * ~200 tokens each.
    # Keep CHAT_HISTORY_TURNS ≤ 12 to stay within the 4096-token window.
    CHAT_HISTORY_TURNS: int = 6

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
