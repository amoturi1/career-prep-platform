"""AI layer (NFR-10): everything AI-related lives here, behind one interface.

    from app.ai import get_engine
    engine = get_engine()
    engine.analyze_match(...)

Two engines are available:
  * LocalEngine  - built-in, rule-based, works offline, deterministic (used by tests).
  * ClaudeEngine - calls the Anthropic Claude API when ANTHROPIC_API_KEY is set,
                   and falls back to LocalEngine if the API call fails (NFR-07).
"""
from app.ai.base import CareerAI
from app.ai.factory import get_engine

__all__ = ["CareerAI", "get_engine"]
