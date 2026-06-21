"""SQLAlchemy persistence models."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from drive_intelligence_platform.db.base import Base


class FileRecord(Base):
    """Catalog entry for a discovered file."""

    __tablename__ = "file_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    path: Mapped[str] = mapped_column(String(1024), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(512), index=True, nullable=False)
    extension: Mapped[str] = mapped_column(String(32), index=True, default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    accessed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sha256: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    md5: Mapped[str | None] = mapped_column(String(32), nullable=True)
    perceptual_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    folder_path: Mapped[str] = mapped_column(String(1024), index=True, default="")
    file_kind: Mapped[str] = mapped_column(String(32), index=True, default="other")
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)


class FolderPattern(Base):
    """Folder organization pattern learned from user behavior."""

    __tablename__ = "folder_patterns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    pattern_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False)
    folder_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    match_count: Mapped[int] = mapped_column(Integer, default=0)
    approval_count: Mapped[int] = mapped_column(Integer, default=0)
    rejection_count: Mapped[int] = mapped_column(Integer, default=0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)


class DuplicateGroup(Base):
    """Duplicate file grouping."""

    __tablename__ = "duplicate_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    duplicate_kind: Mapped[str] = mapped_column(String(32), nullable=False)
    recoverable_bytes: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    members: Mapped[list["DuplicateMember"]] = relationship(back_populates="group", cascade="all, delete-orphan")


class DuplicateMember(Base):
    """A member file within a duplicate group."""

    __tablename__ = "duplicate_members"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("duplicate_groups.id"), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    similarity_score: Mapped[float] = mapped_column(Float, default=1.0)
    file_size: Mapped[int] = mapped_column(Integer, default=0)
    kept: Mapped[bool] = mapped_column(Boolean, default=False)
    group: Mapped[DuplicateGroup] = relationship(back_populates="members")


class Recommendation(Base):
    """AI or rule-based organization recommendation."""

    __tablename__ = "recommendations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    suggested_folder: Mapped[str] = mapped_column(String(1024), nullable=False)
    category: Mapped[str] = mapped_column(String(128), nullable=False)
    subcategory: Mapped[str] = mapped_column(String(128), default="")
    reason: Mapped[str] = mapped_column(Text, default="")
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    approved: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AuditLogEntry(Base):
    """Append-only audit log entry."""

    __tablename__ = "audit_log_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_name: Mapped[str] = mapped_column(String(255), default="system")
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    result: Mapped[str] = mapped_column(String(255), default="pending")
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    details_json: Mapped[dict] = mapped_column(JSON, default=dict)


class OperationManifest(Base):
    """Rollback manifest for approved execution."""

    __tablename__ = "operation_manifests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    source_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    destination_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    before_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    after_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="planned")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class RuleDefinition(Base):
    """User-defined organization rule stored in YAML-backed form."""

    __tablename__ = "rule_definitions"

    __table_args__ = (UniqueConstraint("rule_name", name="uq_rule_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    rule_name: Mapped[str] = mapped_column(String(255), nullable=False)
    rule_json: Mapped[dict] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)