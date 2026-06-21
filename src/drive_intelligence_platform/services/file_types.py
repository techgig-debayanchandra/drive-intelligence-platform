"""File type analysis and filtering service."""

from __future__ import annotations

from collections import Counter
from pathlib import Path

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

    def extensions(self) -> list[str]:
        """Return distinct extensions currently present in the catalog."""

        rows = self.session.execute(select(FileRecord.extension).distinct().order_by(FileRecord.extension))
        return [str(row[0] or "") for row in rows]

    def files_for_extensions(self, extensions: list[str]) -> list[FileRecord]:
        """Return files matching a list of extensions."""

        cleaned = [ext.lower() for ext in extensions if ext]
        if not cleaned:
            return []
        statement = select(FileRecord).where(FileRecord.extension.in_(cleaned)).order_by(FileRecord.folder_path, FileRecord.name)
        return list(self.session.scalars(statement).all())

    def summary_for_extensions(self, extensions: list[str]) -> dict[str, int]:
        """Return count and size summary for selected extensions."""

        files = self.files_for_extensions(extensions)
        return {
            "count": len(files),
            "size_bytes": int(sum(file_item.size_bytes for file_item in files)),
        }
