"""Typer command-line interface for the platform."""

from __future__ import annotations

from pathlib import Path

import typer
from loguru import logger

from drive_intelligence_platform.core.config import get_settings
from drive_intelligence_platform.core.logging import configure_logging
from drive_intelligence_platform.db.session import create_db_engine, create_session_factory, initialize_database
from drive_intelligence_platform.services.catalog import CatalogService
from drive_intelligence_platform.services.classifier import ClassifierService
from drive_intelligence_platform.services.content_analysis import ContentAnalyzer
from drive_intelligence_platform.services.photo_analysis import PhotoAnalyzer
from drive_intelligence_platform.services.video_analysis import VideoAnalyzer
from drive_intelligence_platform.services.scanner import DriveScanner

app = typer.Typer(add_completion=False, help="Drive Intelligence Platform command line interface")


@app.command()
def init_db() -> None:
    """Create or migrate the SQLite schema."""

    settings = get_settings()
    configure_logging(settings.log_level, settings.data_root / "logs")
    engine = initialize_database(settings)
    logger.info("database_initialized")


@app.command()
def scan(path: Path) -> None:
    """Scan a drive or directory tree."""

    settings = get_settings()
    configure_logging(settings.log_level, settings.data_root / "logs")
    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    scanner = DriveScanner(max_workers=settings.max_workers, batch_size=settings.batch_size)
    result = scanner.scan([path])
    with session_factory() as session:
        catalog = CatalogService(session)
        classifier = ClassifierService(settings)
        catalog.upsert_scanned_files(result.files)
        for item in result.files[:50]:
            catalog.store_recommendation(classifier.classify(item))
        session.commit()
    typer.echo(f"Scanned {len(result.files)} files totaling {result.total_bytes} bytes and stored them in SQLite")


@app.command()
def analyze(path: Path) -> None:
    """Analyze a single file using the appropriate analyzer."""

    settings = get_settings()
    configure_logging(settings.log_level, settings.data_root / "logs")
    suffix = path.suffix.lower()
    if suffix in {".jpg", ".jpeg", ".png", ".gif", ".heic", ".raw", ".tiff", ".cr2", ".cr3", ".nef", ".arw", ".dng"}:
        typer.echo(str(PhotoAnalyzer().analyze(path)))
    elif suffix in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
        typer.echo(str(VideoAnalyzer().analyze(path)))
    else:
        typer.echo(str(ContentAnalyzer().analyze(path)))


@app.command()
def ui() -> None:
    """Launch the Streamlit dashboard."""

    typer.echo("Run the Streamlit app with: streamlit run src/drive_intelligence_platform/app.py")


if __name__ == "__main__":
    app()