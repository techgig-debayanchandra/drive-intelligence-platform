"""Video metadata extraction and classification."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class VideoAnalysisResult:
    """Structured video metadata output."""

    duration_seconds: float | None
    codec: str | None
    resolution: tuple[int, int] | None
    metadata: dict[str, object]
    classification: str


class VideoAnalyzer:
    """Extract lightweight video metadata and infer categories."""

    def analyze(self, path: Path) -> VideoAnalysisResult:
        """Analyze a video file."""

        metadata = self._extract_metadata(path)
        classification = self._classify(path)
        return VideoAnalysisResult(
            duration_seconds=metadata.get("duration_seconds"),
            codec=metadata.get("codec"),
            resolution=metadata.get("resolution"),
            metadata=metadata,
            classification=classification,
        )

    def _extract_metadata(self, path: Path) -> dict[str, object]:
        """Extract video metadata when OpenCV is available."""

        metadata: dict[str, object] = {}
        try:
            import cv2

            capture = cv2.VideoCapture(str(path))
            if capture.isOpened():
                frame_count = capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
                fps = capture.get(cv2.CAP_PROP_FPS) or 0.0
                width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
                height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
                codec_value = int(capture.get(cv2.CAP_PROP_FOURCC) or 0)
                codec = "".join(chr((codec_value >> (8 * index)) & 0xFF) for index in range(4)).strip("\x00 ")
                duration = frame_count / fps if fps else None
                metadata = {
                    "duration_seconds": duration,
                    "codec": codec or None,
                    "resolution": (width, height) if width and height else None,
                }
            capture.release()
        except Exception:
            metadata = {}
        return metadata

    def _classify(self, path: Path) -> str:
        """Classify a video using filename hints."""

        name = path.name.lower()
        if "screen" in name or "record" in name:
            return "screen recording"
        if "drone" in name:
            return "drone"
        if "youtube" in name:
            return "youtube content"
        if "vlog" in name:
            return "vlog"
        if "travel" in name:
            return "travel"
        return "family"