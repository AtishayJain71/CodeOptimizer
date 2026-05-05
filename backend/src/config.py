from pathlib import Path
from pydantic_settings import BaseSettings

# backend/.env — one level above the src/ directory where uvicorn runs
_ENV_FILE = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    # Ollama model names — change these to match what you have pulled locally.
    # Run `ollama list` to see available models.
    CODE_REVIEW_MODEL: str = "deepseek-coder:1.3b"
    BUG_FIX_MODEL: str = "deepseek-coder:1.3b"
    PLANNING_MODEL: str = "llama3.2:1b"
    TEST_GEN_MODEL: str = "deepseek-coder:1.3b"

    # Ollama base URL (default local)
    OLLAMA_BASE_URL: str = "http://localhost:11434"

    # CORS origins allowed to call the API
    ALLOWED_ORIGINS: list = ["*"]

    # GitHub webhook integration
    # GITHUB_SECRET  — the secret string you set when creating the webhook on GitHub
    # GITHUB_TOKEN   — a Personal Access Token with repo + pull-requests read/write scope
    GITHUB_SECRET: str = ""
    GITHUB_TOKEN: str = ""

    class Config:
        env_file = str(_ENV_FILE)


settings = Settings()
