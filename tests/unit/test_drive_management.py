from __future__ import annotations

from pathlib import Path

from drive_intelligence_platform.core.config import AppSettings
from drive_intelligence_platform.schemas import RecommendationPayload, ScannedFile
from drive_intelligence_platform.services.drive_management import DriveManagementService
from drive_intelligence_platform.services.scanner import ScanResult


class _FakeScanner:
    def __init__(self, files: list[ScannedFile]) -> None:
        self._files = files

    def scan(self, roots: list[Path], progress_callback=None) -> ScanResult:  # noqa: ARG002
        return ScanResult(files=self._files, total_bytes=sum(item.size_bytes for item in self._files))


class _FakeClassifier:
    def classify(self, file_item: ScannedFile) -> RecommendationPayload:
        if file_item.file_kind == "photo":
            folder = Path("Photography/Exports")
        elif file_item.extension == ".pdf":
            folder = Path("Learning/Python")
        else:
            folder = Path("Archives/Unsorted")
        return RecommendationPayload(
            source_path=file_item.path,
            category="Mixed",
            subcategory="Test",
            suggested_folder=folder,
            reason="Synthetic recommendation",
            confidence=0.62,
        )


class _FakeFolderAIService:
    def recommend_folder_group(self, files, context):  # noqa: ANN001, ANN201
        return {
            "preserve_folder": False,
            "suggested_folder": "Projects/Acme",
            "reason": "Folder looks like an Acme project bundle",
            "confidence": 0.97,
            "category": "Project",
            "subcategory": "Acme",
        }


class _FakeClassifierWithFolderAI:
    def __init__(self) -> None:
        self.ai_service = _FakeFolderAIService()

    def classify(self, file_item: ScannedFile) -> RecommendationPayload:
        return RecommendationPayload(
            source_path=file_item.path,
            category="General",
            subcategory="",
            suggested_folder=Path("General"),
            reason="Base classifier",
            confidence=0.95,
        )


def test_build_plan_preserves_mixed_folder_context(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir(parents=True)
    mixed_folder = source_root / "Important_Project_Set"
    mixed_folder.mkdir(parents=True)

    files = [
        ScannedFile(
            path=mixed_folder / "cover.jpg",
            name="cover.jpg",
            extension=".jpg",
            size_bytes=120,
            folder_path=mixed_folder,
            file_kind="photo",
        ),
        ScannedFile(
            path=mixed_folder / "notes.pdf",
            name="notes.pdf",
            extension=".pdf",
            size_bytes=320,
            folder_path=mixed_folder,
            file_kind="document",
        ),
        ScannedFile(
            path=mixed_folder / "data.xlsx",
            name="data.xlsx",
            extension=".xlsx",
            size_bytes=520,
            folder_path=mixed_folder,
            file_kind="document",
        ),
    ]

    service = DriveManagementService(AppSettings())
    service.scanner = _FakeScanner(files)
    service.classifier = _FakeClassifier()

    destination_root = tmp_path / "organized"
    plan = service.build_organization_plan(source_root, destination_root)

    assert len(plan) == 3
    for entry in plan:
        assert str(entry.destination).startswith(str(destination_root / "Important_Project_Set"))
        assert "Preserved folder context" in entry.recommendation.reason
        assert entry.recommendation.confidence >= 0.85


def test_low_confidence_moves_are_preserved_for_safety(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir(parents=True)
    folder = source_root / "GeneralDocs"
    folder.mkdir(parents=True)

    files = [
        ScannedFile(
            path=folder / "item1.pdf",
            name="item1.pdf",
            extension=".pdf",
            size_bytes=120,
            folder_path=folder,
            file_kind="document",
        ),
        ScannedFile(
            path=folder / "item2.pdf",
            name="item2.pdf",
            extension=".pdf",
            size_bytes=320,
            folder_path=folder,
            file_kind="document",
        ),
    ]

    service = DriveManagementService(AppSettings())
    service.scanner = _FakeScanner(files)
    service.classifier = _FakeClassifier()

    destination_root = tmp_path / "organized"
    plan = service.build_organization_plan(
        source_root,
        destination_root,
        conservative_mode=False,
        min_move_confidence=0.9,
    )

    assert len(plan) == 2
    for entry in plan:
        assert str(entry.destination).startswith(str(destination_root / "GeneralDocs"))
        assert "Preserved" in entry.recommendation.reason


def test_folder_level_ai_batches_and_overrides_target(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source_root.mkdir(parents=True)
    folder = source_root / "acme_bundle"
    folder.mkdir(parents=True)

    files = [
        ScannedFile(
            path=folder / "spec.docx",
            name="spec.docx",
            extension=".docx",
            size_bytes=110,
            folder_path=folder,
            file_kind="document",
        ),
        ScannedFile(
            path=folder / "budget.xlsx",
            name="budget.xlsx",
            extension=".xlsx",
            size_bytes=240,
            folder_path=folder,
            file_kind="document",
        ),
    ]

    service = DriveManagementService(AppSettings())
    service.scanner = _FakeScanner(files)
    service.classifier = _FakeClassifierWithFolderAI()

    destination_root = tmp_path / "organized"
    plan = service.build_organization_plan(
        source_root,
        destination_root,
        conservative_mode=False,
        min_move_confidence=0.9,
    )

    assert len(plan) == 2
    for entry in plan:
        assert str(entry.destination).startswith(str(destination_root / "Projects/Acme"))
        assert "Folder AI plan" in entry.recommendation.reason
