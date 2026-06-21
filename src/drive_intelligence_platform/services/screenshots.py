"""Screenshot detection and summary service."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import FileRecord


@dataclass(slots=True)
class ScreenshotSummary:
    """Screenshot aggregation result."""

    count: int
    total_size_bytes: int


class ScreenshotService:
    """Detect screenshot-like files in the catalog."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def summary(self) -> ScreenshotSummary:
        """Return screenshot counts and size."""

        count = self.session.scalar(select(func.count(FileRecord.id)).where(FileRecord.name.ilike("%screenshot%"))) or 0
        total_size_bytes = self.session.scalar(select(func.coalesce(func.sum(FileRecord.size_bytes), 0)).where(FileRecord.name.ilike("%screenshot%"))) or 0
        return ScreenshotSummary(count=int(count), total_size_bytes=int(total_size_bytes))
