"""Repository for file catalog records."""

from __future__ import annotations

from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import FileRecord
from drive_intelligence_platform.repositories.base import Repository


class FileRepository(Repository[FileRecord]):
    """Persist and query file records."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, FileRecord)