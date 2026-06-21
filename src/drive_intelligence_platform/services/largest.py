"""Large file and large folder summary service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import FileRecord


@dataclass(slots=True)
class LargestFileRow:
    """Largest file summary row."""

    path: str
    size_bytes: int


@dataclass(slots=True)
class LargestFolderRow:
    """Largest folder summary row."""

    folder_path: str
    size_bytes: int


class LargeFileService:
    """Identify large files and folders from the catalog."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def largest_files(self, limit: int = 25) -> list[LargestFileRow]:
        """Return the largest files in descending order."""

        rows = self.session.execute(
            select(FileRecord.path, FileRecord.size_bytes).order_by(FileRecord.size_bytes.desc()).limit(limit)
        )
        return [LargestFileRow(path=str(path), size_bytes=int(size_bytes or 0)) for path, size_bytes in rows]

    def largest_folders(self, limit: int = 25) -> list[LargestFolderRow]:
        """Return folder sizes aggregated from file catalog entries."""

        rows = self.session.execute(
            select(FileRecord.folder_path, func.sum(FileRecord.size_bytes)).group_by(FileRecord.folder_path).order_by(func.sum(FileRecord.size_bytes).desc()).limit(limit)
        )
        return [LargestFolderRow(folder_path=str(folder_path), size_bytes=int(size_bytes or 0)) for folder_path, size_bytes in rows]
