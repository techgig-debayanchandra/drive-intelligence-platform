"""Dashboard metrics and summary generation."""

from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import DuplicateGroup, FileRecord, Recommendation


@dataclass(slots=True)
class DashboardSnapshot:
    """Snapshot of key platform metrics."""

    total_files: int
    total_size_bytes: int
    duplicate_groups: int
    recommendations: int


class DashboardService:
    """Collect dashboard metrics for the UI."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def snapshot(self) -> DashboardSnapshot:
        """Return a compact metrics snapshot."""

        total_files = self.session.scalar(select(func.count(FileRecord.id))) or 0
        total_size_bytes = self.session.scalar(select(func.coalesce(func.sum(FileRecord.size_bytes), 0))) or 0
        duplicate_groups = self.session.scalar(select(func.count(DuplicateGroup.id))) or 0
        recommendations = self.session.scalar(select(func.count(Recommendation.id))) or 0
        return DashboardSnapshot(
            total_files=int(total_files),
            total_size_bytes=int(total_size_bytes),
            duplicate_groups=int(duplicate_groups),
            recommendations=int(recommendations),
        )