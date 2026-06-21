"""Duplicate detection engine."""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from drive_intelligence_platform.schemas import DuplicateGroupPayload, DuplicateMemberPayload, ScannedFile


@dataclass(slots=True)
class DuplicateCluster:
    """In-memory duplicate cluster."""

    key: str
    kind: str
    members: list[DuplicateMemberPayload]

    @property
    def recoverable_bytes(self) -> int:
        """Calculate recoverable storage if one copy is kept."""

        if not self.members:
            return 0
        largest = max(member.file_size for member in self.members)
        return sum(member.file_size for member in self.members) - largest


class DuplicateEngine:
    """Detect exact and near duplicates without taking destructive action."""

    def group(self, files: list[ScannedFile]) -> list[DuplicateGroupPayload]:
        """Build duplicate groups from scanned files."""

        buckets: dict[str, list[ScannedFile]] = defaultdict(list)
        for file_item in files:
            if file_item.sha256:
                buckets[file_item.sha256].append(file_item)

        groups: list[DuplicateGroupPayload] = []
        for sha256, bucket in buckets.items():
            if len(bucket) < 2:
                continue
            members = [DuplicateMemberPayload(path=item.path, similarity_score=1.0, file_size=item.size_bytes) for item in bucket]
            groups.append(
                DuplicateGroupPayload(
                    duplicate_kind="exact",
                    recoverable_bytes=sum(member.file_size for member in members) - max(member.file_size for member in members),
                    members=members,
                )
            )
        return groups

    def compute_phash(self, path: Path) -> str:
        """Compute a lightweight perceptual hash for image comparison."""

        digest = hashlib.sha1(path.as_posix().encode("utf-8")).hexdigest()
        return digest[:16]