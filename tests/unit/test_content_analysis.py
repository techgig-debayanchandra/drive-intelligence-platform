from __future__ import annotations

from pathlib import Path

from drive_intelligence_platform.services.content_analysis import ContentAnalyzer


def test_content_analyzer_extracts_keywords_and_topics(tmp_path: Path) -> None:
    source = tmp_path / "python-notes.md"
    source.write_text("Python ETL pipeline for Oracle reporting project DemoRepo", encoding="utf-8")

    result = ContentAnalyzer().analyze(source)

    assert "python" in result.keywords
    assert "etl" in result.topics
    assert "Oracle" in result.entities