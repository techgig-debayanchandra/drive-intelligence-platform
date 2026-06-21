"""Rollback orchestration for approved operations."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import OperationManifest


class RollbackService:
    """Restore original paths from manifests."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def restore_single_file(self, operation_id: str) -> Path | None:
        """Return the original file path for a single rollback action."""

        manifest = self.session.query(OperationManifest).filter_by(operation_id=operation_id).one_or_none()
        if manifest is None:
            return None
        manifest.status = "rollback_ready"
        self.session.flush()
        return Path(manifest.before_path)

    def restore_operation(self, operation_id: str) -> list[Path]:
        """Return rollback targets for an entire operation."""

        manifest = self.session.query(OperationManifest).filter_by(operation_id=operation_id).one_or_none()
        if manifest is None:
            return []
        manifest.status = "rollback_ready"
        self.session.flush()
        return [Path(manifest.before_path)]