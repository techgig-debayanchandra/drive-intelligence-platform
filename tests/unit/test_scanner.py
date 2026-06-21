from __future__ import annotations

from pathlib import Path

from drive_intelligence_platform.services.scanner import DriveScanner


def test_scanner_classifies_code_file_as_code(tmp_path: Path) -> None:
    source = tmp_path / "example.py"
    source.write_text("print('hello')\n", encoding="utf-8")

    result = DriveScanner(max_workers=1).scan([tmp_path])

    assert len(result.files) == 1
    assert result.files[0].file_kind == "code"
    assert result.files[0].sha256 is not None