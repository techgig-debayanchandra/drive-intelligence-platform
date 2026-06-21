"""Audit logging service."""

from __future__ import annotations

from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import AuditLogEntry


class AuditService:
    """Persist audit entries for all user-visible actions."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def record(self, action: str, result: str, details: dict[str, object] | None = None, user_name: str = "system") -> AuditLogEntry:
        """Create a new audit log entry."""

        entry = AuditLogEntry(user_name=user_name, action=action, result=result, details_json=details or {})
        self.session.add(entry)
        self.session.flush()
        return entry