"""Heuristic and AI-assisted classification."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path

from drive_intelligence_platform.core.config import AppSettings
from drive_intelligence_platform.services.ai import RecommendationServiceProtocol, create_ai_recommendation_service
from drive_intelligence_platform.services.content_analysis import ContentAnalyzer
from drive_intelligence_platform.services.photo_analysis import PhotoAnalyzer
from drive_intelligence_platform.services.video_analysis import VideoAnalyzer
from drive_intelligence_platform.schemas import RecommendationPayload, ScannedFile


class ClassifierService:
    """Generate organization recommendations from metadata and learned patterns."""

    def __init__(self, settings: AppSettings, ai_service: RecommendationServiceProtocol | None = None) -> None:
        self.settings = settings
        self.ai_service = ai_service if ai_service is not None else create_ai_recommendation_service(settings)

    def classify(self, file_item: ScannedFile) -> RecommendationPayload:
        """Classify a scanned file into a category and suggested folder."""

        heuristic = self._heuristic_recommendation(file_item)
        if heuristic.confidence >= self.settings.similarity_threshold or self.ai_service is None:
            return heuristic

        ai_context = self._build_ai_context(file_item, heuristic)
        ai_recommendation = self.ai_service.recommend(file_item, ai_context)
        if ai_recommendation is not None and ai_recommendation.confidence >= heuristic.confidence:
            return ai_recommendation
        return heuristic

    def _heuristic_recommendation(self, file_item: ScannedFile) -> RecommendationPayload:
        """Generate the best non-AI recommendation."""

        extension = file_item.extension.lower()
        name = file_item.name.lower()
        folder = file_item.folder_path.as_posix()

        if extension == ".pdf" and any(token in name for token in ("python", "etl", "oracle", "tableau")):
            return self._recommend(file_item, "Learning", "Python", Path("Learning/Python"), 0.97, "Content and filename match learning materials.")
        if file_item.file_kind == "photo":
            return self._recommend(file_item, "Photography", "Exports", Path("Photography/Exports"), 0.91, "Image-like file detected from metadata and extension.")
        if file_item.file_kind == "video" and "drone" in name:
            return self._recommend(file_item, "Videography", "Travel", Path("Videography/Travel"), 0.95, "Drone keyword suggests videography travel content.")
        if "downloads" in folder.lower():
            return self._recommend(file_item, "Review", "Downloads", Path("Downloads/Review"), 0.65, "File is in Downloads and should be reviewed manually.")
        return self._recommend(file_item, "Unsorted", "General", Path("Archives/Unsorted"), 0.4, "No high-confidence classification available.")

    def _build_ai_context(self, file_item: ScannedFile, heuristic: RecommendationPayload) -> dict[str, object]:
        """Build the structured context sent to the AI classifier."""

        context: dict[str, object] = {
            "heuristic": {
                "category": heuristic.category,
                "subcategory": heuristic.subcategory,
                "suggested_folder": str(heuristic.suggested_folder),
                "confidence": heuristic.confidence,
                "reason": heuristic.reason,
            },
            "metadata": {
                "mime_type": file_item.mime_type,
                "size_bytes": file_item.size_bytes,
                "folder_path": str(file_item.folder_path),
                "file_kind": file_item.file_kind,
                "sha256": file_item.sha256,
                "md5": file_item.md5,
            },
        }

        if not file_item.path.exists():
            return context

        if file_item.file_kind == "document":
            context["analysis"] = self._analysis_to_dict(ContentAnalyzer().analyze(file_item.path))
        elif file_item.file_kind == "photo":
            context["analysis"] = self._analysis_to_dict(PhotoAnalyzer().analyze(file_item.path))
        elif file_item.file_kind == "video":
            context["analysis"] = self._analysis_to_dict(VideoAnalyzer().analyze(file_item.path))

        return context

    def _analysis_to_dict(self, result: object) -> dict[str, object]:
        if is_dataclass(result):
            return asdict(result)
        if hasattr(result, "model_dump"):
            return result.model_dump()  # type: ignore[no-any-return]
        if hasattr(result, "dict"):
            return result.dict()  # type: ignore[no-any-return]
        if hasattr(result, "__dict__"):
            return vars(result)
        return {"value": str(result)}

    def _recommend(
        self,
        file_item: ScannedFile,
        category: str,
        subcategory: str,
        suggested_folder: Path,
        confidence: float,
        reason: str,
    ) -> RecommendationPayload:
        return RecommendationPayload(
            source_path=file_item.path,
            category=category,
            subcategory=subcategory,
            suggested_folder=suggested_folder,
            reason=reason,
            confidence=confidence,
        )