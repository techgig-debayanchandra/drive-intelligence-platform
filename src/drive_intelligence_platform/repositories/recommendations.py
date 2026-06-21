"""Repository for organization recommendations."""

from __future__ import annotations

from sqlalchemy.orm import Session

from drive_intelligence_platform.models.entities import Recommendation
from drive_intelligence_platform.repositories.base import Repository


class RecommendationRepository(Repository[Recommendation]):
    """Persist and query recommendations."""

    def __init__(self, session: Session) -> None:
        super().__init__(session, Recommendation)