"""Streamlit view helpers for management screens."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from drive_intelligence_platform.core.config import AppSettings
from drive_intelligence_platform.db.session import create_db_engine, create_session_factory, initialize_database
from drive_intelligence_platform.services.catalog import CatalogService
from drive_intelligence_platform.services.classifier import ClassifierService
from drive_intelligence_platform.services.dashboard import DashboardService
from drive_intelligence_platform.services.downloads import DownloadsCleanupService
from drive_intelligence_platform.services.execution import ExecutionService
from drive_intelligence_platform.services.file_types import FileTypeService
from drive_intelligence_platform.services.largest import LargeFileService
from drive_intelligence_platform.services.photo_analysis import PhotoAnalyzer
from drive_intelligence_platform.services.rollback import RollbackService
from drive_intelligence_platform.services.scanner import DriveScanner
from drive_intelligence_platform.services.search import SmartSearchService
from drive_intelligence_platform.services.screenshots import ScreenshotService
from drive_intelligence_platform.services.video_analysis import VideoAnalyzer


def render_dashboard(settings: AppSettings) -> None:
    """Render dashboard summary metrics."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        snapshot = DashboardService(session).snapshot()
    cols = st.columns(4)
    cols[0].metric("Total Files", snapshot.total_files)
    cols[1].metric("Storage Bytes", snapshot.total_size_bytes)
    cols[2].metric("Duplicate Groups", snapshot.duplicate_groups)
    cols[3].metric("Recommendations", snapshot.recommendations)


def render_scan(settings: AppSettings) -> None:
    """Render scan controls and catalog persistence."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    scan_path = st.text_input("Scan path", value=str(Path.home()), key="scan_path")
    if st.button("Run scan", key="run_scan"):
        source = Path(scan_path).expanduser()
        if not source.exists():
            st.error(f"Scan path does not exist: {source}")
            return

        progress_box = st.empty()
        progress_bar = st.progress(0, text="Preparing scan...")

        def update_progress(processed: int, total: int, current_path: Path | None) -> None:
            if total <= 0:
                progress_bar.progress(0, text="No files found to scan yet...")
                progress_box.caption("Scanning candidate files...")
                return

            ratio = processed / total
            label = f"Scanning {processed}/{total} files"
            if current_path is not None:
                label = f"{label} - {current_path}"
            progress_bar.progress(ratio, text=label)
            progress_box.caption(label)

        scanner = DriveScanner(max_workers=settings.max_workers, batch_size=settings.batch_size)
        result = scanner.scan([source], progress_callback=update_progress)
        with session_factory() as session:
            catalog = CatalogService(session)
            classifier = ClassifierService(settings)
            catalog.upsert_scanned_files(result.files)
            for item in result.files[:50]:
                catalog.store_recommendation(classifier.classify(item))
            session.commit()

        progress_bar.progress(1.0, text=f"Finished scanning {len(result.files)} files")
        progress_box.caption(f"Indexed {len(result.files)} files from {source}")
        st.success(f"Scanned {len(result.files)} files totaling {result.total_bytes} bytes")
        st.info(f"Indexed source: {source}")


def render_search(settings: AppSettings) -> None:
    """Render smart search controls."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    query = st.text_input("Search files", key="search_query")
    if st.button("Search", key="search_button") and query:
        with session_factory() as session:
            results = SmartSearchService(session).search(query)
        st.dataframe([{ "path": record.path, "name": record.name, "size_bytes": record.size_bytes } for record in results])


def render_duplicates(settings: AppSettings) -> None:
    """Render a duplicate overview screen."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        candidates = LargeFileService(session).largest_files(limit=20)
    st.dataframe([{ "path": row.path, "size_bytes": row.size_bytes } for row in candidates])


def render_large_files(settings: AppSettings) -> None:
    """Render largest files and folders."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        service = LargeFileService(session)
        largest_files = service.largest_files(limit=20)
        largest_folders = service.largest_folders(limit=20)
    st.subheader("Largest Files")
    st.dataframe([{ "path": row.path, "size_bytes": row.size_bytes } for row in largest_files])
    st.subheader("Largest Folders")
    st.dataframe([{ "folder_path": row.folder_path, "size_bytes": row.size_bytes } for row in largest_folders])


def render_file_types(settings: AppSettings) -> None:
    """Render file type counts."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        counts = FileTypeService(session).by_extension()
    st.bar_chart(counts)


def render_screenshots(settings: AppSettings) -> None:
    """Render screenshot summary."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        summary = ScreenshotService(session).summary()
    st.metric("Screenshot Count", summary.count)
    st.metric("Screenshot Bytes", summary.total_size_bytes)


def render_downloads_cleanup(settings: AppSettings) -> None:
    """Render downloads cleanup recommendations."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        candidates = DownloadsCleanupService(session).recommendations()
    st.dataframe([{ "path": candidate.path, "reason": candidate.reason, "size_bytes": candidate.size_bytes } for candidate in candidates])


def render_analysis(settings: AppSettings) -> None:
    """Render a lightweight single-file analysis form."""

    file_path = st.text_input("Analyze path", key="analyze_path")
    if st.button("Analyze", key="analyze_button") and file_path:
        path = Path(file_path)
        suffix = path.suffix.lower()
        if suffix in {".jpg", ".jpeg", ".png", ".gif", ".heic", ".raw", ".tiff", ".cr2", ".cr3", ".nef", ".arw", ".dng"}:
            st.json(PhotoAnalyzer().analyze(path).__dict__)
        elif suffix in {".mp4", ".mov", ".mkv", ".avi", ".webm"}:
            st.json(VideoAnalyzer().analyze(path).__dict__)
        else:
            from drive_intelligence_platform.services.content_analysis import ContentAnalyzer

            st.json(ContentAnalyzer().analyze(path).__dict__)


def render_execution(settings: AppSettings) -> None:
    """Render an execution preview screen."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    source = st.text_input("Source file", key="execution_source")
    destination = st.text_input("Destination file", key="execution_destination")
    if st.button("Preview move", key="preview_move") and source and destination:
        with session_factory() as session:
            service = ExecutionService(session)
            plan = service.preview_move(Path(source), Path(destination), approved=False)
            manifest = service.persist_manifest(plan)
            session.commit()
        st.json({"operation_id": manifest.operation_id, "status": manifest.status, "source": manifest.source_path, "destination": manifest.destination_path})


def render_rollback(settings: AppSettings) -> None:
    """Render rollback operations."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    operation_id = st.text_input("Operation ID", key="rollback_operation_id")
    if st.button("Prepare rollback", key="prepare_rollback") and operation_id:
        with session_factory() as session:
            result = RollbackService(session).restore_operation(operation_id)
            session.commit()
        st.write([str(path) for path in result])