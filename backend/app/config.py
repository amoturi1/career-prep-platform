"""Application settings, read from environment variables (or a .env file)."""
import os
from pathlib import Path


def _load_dotenv() -> None:
    """Load KEY=VALUE pairs from backend/.env without overriding real env vars."""
    env_path = Path(__file__).resolve().parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


class Settings:
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./careerprep.db")
    secret_key: str = os.getenv("SECRET_KEY", "dev-only-secret-change-me-in-the-env-file-please")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
    cors_origins: list[str] = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
    ]
    jwt_algorithm: str = "HS256"

    # AI: "auto" uses Claude when an API key is set, otherwise the built-in engine.
    ai_provider: str = os.getenv("AI_PROVIDER", "auto").lower()  # auto | local | claude
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "claude-haiku-5-5")
    ai_timeout_seconds: float = float(os.getenv("AI_TIMEOUT_SECONDS", "45"))

    # Resume uploads (requirements Section 7: file types and size limit)
    max_resume_bytes: int = int(os.getenv("MAX_RESUME_MB", "2")) * 1024 * 1024
    max_resume_chars: int = 30_000


settings = Settings()
