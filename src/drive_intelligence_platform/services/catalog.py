"""Cataloging service that persists scan outputs and recommendations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import FileRecord, Recommendation
from drive_intelligence_platform.repositories.files import FileRepository
from drive_intelligence_platform.repositories.recommendations import RecommendationRepository
from drive_intelligence_platform.schemas import RecommendationPayload, ScannedFile


class CatalogService:
    """Persist scanned file metadata and recommendations."""

    def __init__(self, session: Session) -> None:
        self.session = session
        self.files = FileRepository(session)
        self.recommendations = RecommendationRepository(session)

    def upsert_scanned_files(self, items: list[ScannedFile]) -> list[FileRecord]:
        """Store or update discovered files."""

        records: list[FileRecord] = []
        for item in items:
            existing = self.session.query(FileRecord).filter_by(path=str(item.path)).one_or_none()
            payload = {
                "path": str(item.path),
                "name": item.name,
                "extension": item.extension,
                "size_bytes": item.size_bytes,
                "created_at": item.created_at,
                "modified_at": item.modified_at,
                "accessed_at": item.accessed_at,
                "mime_type": item.mime_type,
                "sha256": item.sha256,
                "md5": item.md5,
                "perceptual_hash": item.perceptual_hash,
                "folder_path": str(item.folder_path),
                "file_kind": item.file_kind,
                "metadata_json": item.metadata,
            }
            if existing is None:
                record = FileRecord(**payload)
                self.files.add(record)
                records.append(record)
            else:
                for key, value in payload.items():
                    setattr(existing, key, value)
                records.append(existing)
        return records

    def store_recommendation(self, payload: RecommendationPayload, approved: bool | None = None) -> Recommendation:
        """Persist a classification recommendation."""

        record = Recommendation(
            source_path=str(payload.source_path),
            suggested_folder=str(payload.suggested_folder),
            category=payload.category,
            subcategory=payload.subcategory,
            reason=payload.reason,
            confidence=payload.confidence,
            approved=approved,
        )
        self.recommendations.add(record)
        return record