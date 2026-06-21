"""Learning engine for folder and naming patterns."""

from __future__ import annotations

from collections import Counter
from pathlib import Path


class LearningEngine:
    """Infer common folder destinations from existing approvals."""

    def learn_folder_pattern(self, file_path: Path, suggested_folder: Path) -> str:
        """Derive a stable pattern key for a file-to-folder mapping."""

        folder_tokens = tuple(part.lower() for part in suggested_folder.parts if part)
        extension = file_path.suffix.lower()
        return f"{extension}:{'/'.join(folder_tokens)}"

    def summarize_patterns(self, mappings: list[tuple[Path, Path]]) -> dict[str, int]:
        """Count observed mapping patterns."""

        counter: Counter[str] = Counter()
        for source_path, destination_path in mappings:
            counter[self.learn_folder_pattern(source_path, destination_path)] += 1
        return dict(counter)