"""Smart search over catalogued files and recommendations."""

from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import FileRecord, Recommendation


class SmartSearchService:
    """Provide filename, content, metadata, and location search."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def search(self, query: str) -> list[FileRecord]:
        """Search the file catalog using basic fuzzy matching."""

        needle = f"%{query.lower()}%"
        statement = select(FileRecord).where(
            or_(
                FileRecord.path.ilike(needle),
                FileRecord.name.ilike(needle),
                FileRecord.extension.ilike(needle),
                FileRecord.folder_path.ilike(needle),
            )
        )
        return list(self.session.scalars(statement).all())

    def search_recommendations(self, query: str) -> list[Recommendation]:
        """Search recommendation records."""

        needle = f"%{query.lower()}%"
        statement = select(Recommendation).where(
            or_(
                Recommendation.source_path.ilike(needle),
                Recommendation.suggested_folder.ilike(needle),
                Recommendation.category.ilike(needle),
                Recommendation.reason.ilike(needle),
            )
        )
        return list(self.session.scalars(statement).all())