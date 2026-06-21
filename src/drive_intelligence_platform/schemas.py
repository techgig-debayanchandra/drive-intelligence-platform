"""Pydantic schemas for service contracts and UI payloads."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field


class ScannedFile(BaseModel):
    """Metadata extracted from a discovered file."""

    path: Path
    name: str
    extension: str
    size_bytes: int = 0
    created_at: datetime | None = None
    modified_at: datetime | None = None
    accessed_at: datetime | None = None
    mime_type: str | None = None
    sha256: str | None = None
    md5: str | None = None
    perceptual_hash: str | None = None
    folder_path: Path = Field(default_factory=Path)
    file_kind: str = "other"
    metadata: dict[str, object] = Field(default_factory=dict)


class RecommendationPayload(BaseModel):
    """Suggested organization action."""

    source_path: Path
    category: str
    subcategory: str = ""
    suggested_folder: Path
    reason: str
    confidence: float = Field(ge=0.0, le=1.0)


class DuplicateMemberPayload(BaseModel):
    """Member file in a duplicate group."""

    path: Path
    similarity_score: float = Field(ge=0.0, le=1.0)
    file_size: int = 0


class DuplicateGroupPayload(BaseModel):
    """A duplicate cluster and its recoverable space."""

    duplicate_kind: str
    recoverable_bytes: int
    members: list[DuplicateMemberPayload]


class ExecutionPlanItem(BaseModel):
    """A single approved file operation."""

    source: Path
    destination: Path
    operation: str
    approved: bool = False