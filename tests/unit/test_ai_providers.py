from __future__ import annotations

from drive_intelligence_platform.core.config import AppSettings
from drive_intelligence_platform.services.ai import OllamaRecommendationService, create_ai_recommendation_service


def test_ai_factory_returns_none_when_disabled() -> None:
    settings = AppSettings(ai_provider="disabled")
    service = create_ai_recommendation_service(settings)
    assert service is None


def test_ai_factory_returns_ollama_provider() -> None:
    settings = AppSettings(ai_provider="ollama", ollama_base_url="http://localhost:11434", ollama_model="qwen2.5:14b")
    service = create_ai_recommendation_service(settings)
    assert isinstance(service, OllamaRecommendationService)
    assert service.api_url == "http://localhost:11434/api/generate"
