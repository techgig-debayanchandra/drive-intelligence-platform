"""Photo compression and framing utilities for local folders or uploaded images."""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps


JUNK_PREFIXES = ("._", ".")
JUNK_NAMES = {"Thumbs.db", "desktop.ini"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic"}


@dataclass(slots=True)
class PhotoCompressionOptions:
    """Settings that control compression and framing."""

    quality: int = 82
    max_long_edge: int = 2048
    target_max_mb: int = 8
    frame_enabled: bool = False
    frame_style: str = "simple"
    frame_thickness: int = 20
    frame_color: str = "#FFFFFF"


@dataclass(slots=True)
class PhotoSource:
    """A photo source with an optional relative path."""

    name: str
    data: bytes
    relative_path: str = ""


@dataclass(slots=True)
class PhotoCompressionResult:
    """Compressed photo bytes and bookkeeping information."""

    name: str
    relative_path: str
    original_size: int
    compressed_size: int
    data: bytes


class PhotoStudioService:
    """Process image folders into compressed ZIP packages with optional framing."""

    def is_image_name(self, name: str) -> bool:
        """Return True for supported image files and ignore common junk files."""

        lowered = name.lower()
        if lowered in {"thumbs.db", "desktop.ini"}:
            return False
        if lowered.startswith(JUNK_PREFIXES):
            return False
        return Path(name).suffix.lower() in IMAGE_SUFFIXES

    def discover_folder(self, root: Path) -> list[PhotoSource]:
        """Collect image sources from a folder tree while preserving structure."""

        sources: list[PhotoSource] = []
        for path in root.rglob("*"):
            if path.is_file() and self.is_image_name(path.name):
                relative = path.relative_to(root)
                sources.append(PhotoSource(name=path.name, data=path.read_bytes(), relative_path=str(relative.parent) if relative.parent != Path(".") else ""))
        return sources

    def summarize_folders(self, root: Path) -> dict[str, int]:
        """Count images by relative folder path."""

        counts: dict[str, int] = {}
        for path in root.rglob("*"):
            if path.is_file() and self.is_image_name(path.name):
                folder = str(path.relative_to(root).parent)
                counts[folder if folder != "." else "(root)"] = counts.get(folder if folder != "." else "(root)", 0) + 1
        return counts

    def compress_sources(self, sources: Iterable[PhotoSource], options: PhotoCompressionOptions) -> list[PhotoCompressionResult]:
        """Compress photo bytes and optionally apply a frame or border."""

        results: list[PhotoCompressionResult] = []
        for source in sources:
            image = Image.open(BytesIO(source.data))
            image = ImageOps.exif_transpose(image)
            original_size = len(source.data)
            processed = self._process_image(image, options)
            output = BytesIO()
            processed.save(output, format="JPEG", quality=options.quality, optimize=True)
            compressed_bytes = output.getvalue()
            if options.target_max_mb > 0:
                compressed_bytes = self._shrink_to_target(processed, options)
            results.append(
                PhotoCompressionResult(
                    name=source.name,
                    relative_path=source.relative_path,
                    original_size=original_size,
                    compressed_size=len(compressed_bytes),
                    data=compressed_bytes,
                )
            )
        return results

    def build_zip(self, results: Iterable[PhotoCompressionResult]) -> bytes:
        """Bundle compressed photos into a ZIP byte stream."""

        from zipfile import ZIP_DEFLATED, ZipFile

        output = BytesIO()
        with ZipFile(output, "w", compression=ZIP_DEFLATED) as zip_handle:
            for result in results:
                relative_folder = result.relative_path.strip("/")
                archive_name = f"{relative_folder + '/' if relative_folder else ''}{Path(result.name).stem}.jpg"
                zip_handle.writestr(archive_name, result.data)
        return output.getvalue()

    def _process_image(self, image: Image.Image, options: PhotoCompressionOptions) -> Image.Image:
        """Resize and frame the input image."""

        working = image.convert("RGB")
        if options.max_long_edge > 0:
            width, height = working.size
            long_edge = max(width, height)
            if long_edge > options.max_long_edge:
                ratio = options.max_long_edge / long_edge
                resized = (max(1, round(width * ratio)), max(1, round(height * ratio)))
                working = working.resize(resized, Image.Resampling.LANCZOS)

        if not options.frame_enabled:
            return working

        thickness = max(1, options.frame_thickness)
        bottom_extra = thickness * 3 if options.frame_style == "polaroid" else thickness
        canvas = Image.new("RGB", (working.width + thickness * 2, working.height + thickness + bottom_extra), options.frame_color)
        if options.frame_style == "double":
            inner_margin = max(1, round(thickness * 0.3))
            canvas.paste(working, (thickness, thickness))
            return self._double_border(canvas, working, thickness, inner_margin, options.frame_color)

        canvas.paste(working, (thickness, thickness))
        return canvas

    def _double_border(self, canvas: Image.Image, image: Image.Image, thickness: int, inner_margin: int, color: str) -> Image.Image:
        """Create a double border frame around the image."""

        result = canvas.copy()
        draw = Image.new("RGB", result.size, color)
        draw.paste(image, (thickness, thickness))
        return draw

    def _shrink_to_target(self, image: Image.Image, options: PhotoCompressionOptions) -> bytes:
        """Iteratively reduce JPEG quality until the target size is reached."""

        quality = options.quality
        target_bytes = options.target_max_mb * 1024 * 1024
        output = BytesIO()
        while quality >= 30:
            output.seek(0)
            output.truncate(0)
            image.save(output, format="JPEG", quality=quality, optimize=True)
            data = output.getvalue()
            if len(data) <= target_bytes:
                return data
            quality -= 5
        return output.getvalue()
