"""File type analysis and filtering service."""

from __future__ import annotations

from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import FileRecord


class FileTypeService:
    """Summarize files by extension, category, year, size, and folder."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def by_extension(self) -> dict[str, int]:
        """Count files by extension."""

        counter: Counter[str] = Counter()
        for extension, count in self.session.execute(select(FileRecord.extension, func.count()).group_by(FileRecord.extension)):
            counter[str(extension or "")] = int(count)
        return dict(counter)
