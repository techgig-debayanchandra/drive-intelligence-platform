"""Domain enumerations."""

from __future__ import annotations

from enum import Enum


class ExecutionMode(str, Enum):
    """System execution modes."""

    READ_ONLY = "read_only"
    RECOMMENDATION = "recommendation"
    APPROVED_EXECUTION = "approved_execution"


class FileKind(str, Enum):
    """High-level file kinds used by classifiers."""

    DOCUMENT = "document"
    PHOTO = "photo"
    VIDEO = "video"
    ARCHIVE = "archive"
    CODE = "code"
    OTHER = "other"


class DuplicateKind(str, Enum):
    """Duplicate classification categories."""

    EXACT = "exact"
    NEAR = "near"
    RESIZED = "resized"
    EDITED_VARIANT = "edited_variant"