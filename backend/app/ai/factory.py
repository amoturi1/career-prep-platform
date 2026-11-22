"""Choose the AI engine from settings. Tests force the built-in engine (AI_PROVIDER=local)."""
from functools import lru_cache

from app.ai.local_engine import LocalEngine
from app.config import settings


@lru_cache
def get_engine():
    provider = settings.ai_provider
    use_claude = provider == "claude" or (provider == "auto" and settings.anthropic_api_key)
    if use_claude and settings.anthropic_api_key:
        from app.ai.claude_engine import ClaudeEngine

        return ClaudeEngine(settings.anthropic_api_key, settings.ai_model, settings.ai_timeout_seconds)
    return LocalEngine()
