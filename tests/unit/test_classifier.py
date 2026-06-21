from __future__ import annotations

from pathlib import Path

from drive_intelligence_platform.core.config import AppSettings
from drive_intelligence_platform.schemas import ScannedFile
from drive_intelligence_platform.services.classifier import ClassifierService


def test_classifier_suggests_learning_folder_for_python_pdf() -> None:
    file_item = ScannedFile(
        path=Path("Downloads/Oracle_ETL_Guide.pdf"),
        name="Oracle_ETL_Guide.pdf",
        extension=".pdf",
        folder_path=Path("Downloads"),
        file_kind="document",
    )

    recommendation = ClassifierService(AppSettings()).classify(file_item)

    assert recommendation.category == "Learning"
    assert str(recommendation.suggested_folder) == "Learning/Python"
    assert recommendation.confidence >= 0.9