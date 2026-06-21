from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from drive_intelligence_platform.db.base import Base
from drive_intelligence_platform.core.config import AppSettings
from drive_intelligence_platform.services.catalog import CatalogService
from drive_intelligence_platform.services.classifier import ClassifierService
from drive_intelligence_platform.services.scanner import DriveScanner


def test_catalog_pipeline_stores_scan_results(tmp_path: Path) -> None:
    archive = tmp_path / "archive"
    archive.mkdir()
    source = archive / "python-guide.pdf"
    source.write_text("Python ETL Oracle report", encoding="utf-8")

    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)

    scanner = DriveScanner(max_workers=1)
    scan_result = scanner.scan([archive])

    with session_factory() as session:
        catalog = CatalogService(session)
        classifier = ClassifierService(AppSettings())
        catalog.upsert_scanned_files(scan_result.files)
        for item in scan_result.files:
            catalog.store_recommendation(classifier.classify(item))
        session.commit()

    with session_factory() as session:
        assert session.query(catalog.files.model).count() == 1
        assert session.query(catalog.recommendations.model).count() == 1