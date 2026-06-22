"""Drive scanning service."""

from __future__ import annotations

import concurrent.futures as futures
import hashlib
import mimetypes
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

from loguru import logger

from drive_intelligence_platform.schemas import ScannedFile


@dataclass(slots=True)
class ScanResult:
    """Container for scan output."""

    files: list[ScannedFile]
    total_bytes: int


class DriveScanner:
    """Traverse mounted drives in read-only mode and capture file metadata."""

    def __init__(self, max_workers: int = 8, batch_size: int = 1000) -> None:
        self.max_workers = max_workers
        self.batch_size = batch_size

    def scan(
        self,
        roots: Iterable[Path],
        progress_callback: Callable[[int, int, Path | None], None] | None = None,
        compute_hashes: bool = True,
    ) -> ScanResult:
        """Scan directories and compute hashes for discovered files."""

        discovered: list[Path] = []
        for root in roots:
            if root.exists():
                discovered.extend(self._walk(root))

        total_candidates = len(discovered)
        if progress_callback is not None:
            progress_callback(0, total_candidates, None)

        total_bytes = 0
        files: list[ScannedFile] = []
        with futures.ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            future_map = {pool.submit(self._inspect_file, path, compute_hashes): path for path in discovered}
            completed = 0
            for future in futures.as_completed(future_map):
                item = future.result()
                if item is not None:
                    files.append(item)
                    total_bytes += item.size_bytes
                completed += 1
                if progress_callback is not None:
                    progress_callback(completed, total_candidates, future_map[future])
        logger.info("scan_completed", files=len(files), total_bytes=total_bytes)
        return ScanResult(files=files, total_bytes=total_bytes)

    def _walk(self, root: Path) -> list[Path]:
        """Collect files beneath a root path."""

        result: list[Path] = []
        skip_dirs = {
            ".git",
            ".svn",
            ".hg",
            ".Trash",
            ".Trashes",
            ".Spotlight-V100",
            ".fseventsd",
            "$RECYCLE.BIN",
            "System Volume Information",
            "node_modules",
            "__pycache__",
        }
        for current_root, dirnames, filenames in os.walk(root):
            dirnames[:] = [
                name
                for name in dirnames
                if name not in skip_dirs and not name.startswith(".")
            ]
            for filename in filenames:
                if filename in {".DS_Store", "Thumbs.db"}:
                    continue
                if filename.startswith("._"):
                    continue
                result.append(Path(current_root) / filename)
        return result

    def _inspect_file(self, path: Path, compute_hashes: bool = True) -> ScannedFile | None:
        """Inspect a single file and compute lightweight metadata."""

        try:
            stat_result = path.stat()
            mime_type, _ = mimetypes.guess_type(path.name)
            sha256: str | None = None
            md5: str | None = None
            if compute_hashes:
                sha256, md5 = self._hash_pair(path)
            return ScannedFile(
                path=path,
                name=path.name,
                extension=path.suffix.lower(),
                size_bytes=stat_result.st_size,
                created_at=None,
                modified_at=None,
                accessed_at=None,
                mime_type=mime_type,
                sha256=sha256,
                md5=md5,
                folder_path=path.parent,
                file_kind=self._classify_extension(path.suffix.lower()),
                metadata={},
            )
        except OSError as exc:
            logger.warning("failed_to_inspect_file", path=str(path), error=str(exc))
            return None

    def _hash_pair(self, path: Path) -> tuple[str, str]:
        """Compute SHA256 and MD5 in one file read pass."""

        sha256 = hashlib.sha256()
        md5 = hashlib.md5()
        with path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                sha256.update(chunk)
                md5.update(chunk)
        return sha256.hexdigest(), md5.hexdigest()

    def _hash(self, path: Path, hasher: "hashlib._Hash") -> str:
        """Hash a file in chunks."""

        with path.open("rb") as file_handle:
            for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _classify_extension(self, extension: str) -> str:
        """Map common extensions to coarse file kinds."""

        if extension in {".py", ".java", ".js", ".ts", ".tsx", ".cs", ".kt"}:
            return "code"
        if extension in {".jpg", ".jpeg", ".png", ".gif", ".heic", ".raw", ".tiff"}:
            return "photo"
        if extension in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
            return "video"
        if extension in {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt", ".md", ".json", ".xml", ".py", ".java", ".js"}:
            return "document"
        if extension in {".zip", ".tar", ".gz", ".7z", ".rar"}:
            return "archive"
        return "other"