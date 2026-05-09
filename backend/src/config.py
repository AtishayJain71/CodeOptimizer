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

    # LLM generation limits — critical for speed.
    # num_predict caps how many tokens the model outputs (fewer = faster).
    # temperature 0.1 = more deterministic, better for code tasks.
    REVIEW_MAX_TOKENS: int = 1000      # code review output cap
    BUGFIX_MAX_TOKENS: int = 1200      # bug fix needs more room for rewritten code
    TESTGEN_MAX_TOKENS: int = 1500     # test code can be longer
    PLAN_MAX_TOKENS: int = 900         # planning output cap
    GITHUB_MAX_TOKENS: int = 600       # GitHub comments must be short

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
