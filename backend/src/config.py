from pydantic_settings import BaseSettings


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

    class Config:
        env_file = ".env"


settings = Settings()
