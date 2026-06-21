from __future__ import annotations

from pathlib import Path

from drive_intelligence_platform.core.config import AppSettings
from drive_intelligence_platform.schemas import RecommendationPayload, ScannedFile
from drive_intelligence_platform.services.classifier import ClassifierService


class FakeAIService:
    def recommend(self, file_item: ScannedFile, context: dict[str, object]) -> RecommendationPayload | None:
        return RecommendationPayload(
            source_path=file_item.path,
            category="Learning",
            subcategory="Oracle",
            suggested_folder=Path("Learning/Oracle"),
            reason="AI classification based on metadata and content",
            confidence=0.99,
        )


def test_classifier_uses_ai_for_low_confidence_item() -> None:
    settings = AppSettings(similarity_threshold=0.92)
    file_item = ScannedFile(
        path=Path("Downloads/unknown-guide.pdf"),
        name="unknown-guide.pdf",
        extension=".pdf",
        folder_path=Path("Downloads"),
        file_kind="document",
    )

    recommendation = ClassifierService(settings, ai_service=FakeAIService()).classify(file_item)

    assert recommendation.category == "Learning"
    assert str(recommendation.suggested_folder) == "Learning/Oracle"
    assert recommendation.confidence == 0.99