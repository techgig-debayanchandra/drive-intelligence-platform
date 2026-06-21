"""Approval-gated execution planning and rollback support."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import OperationManifest
from drive_intelligence_platform.schemas import ExecutionPlanItem


@dataclass(slots=True)
class ExecutionPlan:
    """A preview of approved file operations."""

    operation_id: str
    items: list[ExecutionPlanItem]


class ExecutionService:
    """Generate and persist execution plans without taking action automatically."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def preview_move(self, source: Path, destination: Path, approved: bool = False) -> ExecutionPlan:
        """Prepare a single-file move preview."""

        plan_item = ExecutionPlanItem(source=source, destination=destination, operation="move", approved=approved)
        return ExecutionPlan(operation_id=str(uuid4()), items=[plan_item])

    def persist_manifest(self, plan: ExecutionPlan) -> OperationManifest:
        """Store a rollback manifest for an approved operation."""

        first_item = plan.items[0]
        manifest = OperationManifest(
            operation_id=plan.operation_id,
            source_path=str(first_item.source),
            destination_path=str(first_item.destination),
            before_path=str(first_item.source),
            after_path=str(first_item.destination),
            status="planned" if not first_item.approved else "approved",
        )
        self.session.add(manifest)
        self.session.flush()
        self.session.refresh(manifest)
        self.session.expunge(manifest)
        return manifest

    def mark_completed(self, operation_id: str) -> OperationManifest | None:
        """Mark a manifest as completed after a manually approved operation finishes."""

        manifest = self.session.query(OperationManifest).filter_by(operation_id=operation_id).one_or_none()
        if manifest is not None:
            manifest.status = "completed"
            self.session.flush()
            self.session.refresh(manifest)
            self.session.expunge(manifest)
        return manifest