"""Photo metadata extraction and classification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class PhotoAnalysisResult:
    """Structured photo metadata output."""

    exif: dict[str, object]
    classification: str
    is_raw: bool
    is_edited_variant: bool
    is_export: bool


class PhotoAnalyzer:
    """Read image metadata and infer usage patterns."""

    raw_extensions = {".raw", ".cr2", ".cr3", ".nef", ".arw", ".dng", ".orf", ".rw2"}
    export_extensions = {".jpg", ".jpeg", ".png", ".webp"}

    def analyze(self, path: Path) -> PhotoAnalysisResult:
        """Analyze an image file."""

        exif = self._extract_exif(path)
        classification = self._classify(path, exif)
        return PhotoAnalysisResult(
            exif=exif,
            classification=classification,
            is_raw=path.suffix.lower() in self.raw_extensions,
            is_edited_variant=self._looks_edited(path),
            is_export=path.suffix.lower() in self.export_extensions,
        )

    def _extract_exif(self, path: Path) -> dict[str, object]:
        """Extract EXIF metadata when supported."""

        metadata: dict[str, object] = {}
        try:
            from PIL import Image

            image = Image.open(path)
            exif_data = image.getexif()
            for key, value in exif_data.items():
                metadata[str(key)] = value
        except Exception:
            metadata = {}
        return metadata

    def _classify(self, path: Path, exif: dict[str, object]) -> str:
        """Classify a photo based on metadata and filename hints."""

        name = path.name.lower()
        if "screenshot" in name:
            return "screenshot"
        if any(token in name for token in ("scan", "document", "receipt")):
            return "document scan"
        if any(token in name for token in ("portrait", "headshot")):
            return "portrait"
        if any(token in name for token in ("drone", "aerial")):
            return "drone"
        if exif.get("Model") or exif.get("0x0110"):
            return "camera photo"
        return "landscape"

    def _looks_edited(self, path: Path) -> bool:
        """Detect edited filenames by common suffixes."""

        lowered = path.stem.lower()
        return any(token in lowered for token in ("edit", "edited", "retouch", "final", "copy"))