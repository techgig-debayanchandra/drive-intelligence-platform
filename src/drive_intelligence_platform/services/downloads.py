"""Downloads cleanup recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import FileRecord


@dataclass(slots=True)
class CleanupCandidate:
    """A file that may be eligible for cleanup after review."""

    path: str
    reason: str
    size_bytes: int


class DownloadsCleanupService:
    """Detect installer, archive, and temporary files under Downloads."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def recommendations(self) -> list[CleanupCandidate]:
        """Return reviewable cleanup candidates from Downloads."""

        rows = self.session.execute(select(FileRecord).where(FileRecord.folder_path.ilike("%downloads%")))
        candidates: list[CleanupCandidate] = []
        for record in rows.scalars():
            lowered = record.name.lower()
            if record.extension in {".zip", ".exe", ".dmg", ".pkg", ".msi", ".tmp", ".log", ".bak"} or any(token in lowered for token in ("install", "setup", "temp")):
                candidates.append(CleanupCandidate(path=record.path, reason="Downloads cleanup candidate", size_bytes=record.size_bytes))
        return candidates
