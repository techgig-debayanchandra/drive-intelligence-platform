from __future__ import annotations

from pathlib import Path

from drive_intelligence_platform.schemas import ScannedFile
from drive_intelligence_platform.services.duplicates import DuplicateEngine


def test_duplicate_engine_groups_exact_duplicates() -> None:
    first = ScannedFile(path=Path("a.txt"), name="a.txt", extension=".txt", size_bytes=10, sha256="same")
    second = ScannedFile(path=Path("b.txt"), name="b.txt", extension=".txt", size_bytes=20, sha256="same")

    groups = DuplicateEngine().group([first, second])

    assert len(groups) == 1
    assert groups[0].duplicate_kind == "exact"
    assert groups[0].recoverable_bytes == 10