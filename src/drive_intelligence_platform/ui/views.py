"""Streamlit view helpers for management screens."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from drive_intelligence_platform.core.config import AppSettings
from drive_intelligence_platform.db.session import create_session_factory, initialize_database
from drive_intelligence_platform.services.catalog import CatalogService
from drive_intelligence_platform.services.classifier import ClassifierService
from drive_intelligence_platform.services.drive_management import DriveManagementService, PhotoCompressionOptions, PhotoSource
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
from drive_intelligence_platform.services.photo_studio import PhotoStudioService
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


def render_control_center(settings: AppSettings) -> None:
    """Render the dedicated Drive Control Center dashboard."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        snapshot = DashboardService(session).snapshot()
        ext_counts = FileTypeService(session).by_extension()
        largest = LargeFileService(session).largest_files(limit=10)
        cleanup = DownloadsCleanupService(session).recommendations()[:10]

    st.subheader("Drive Control Center")
    cols = st.columns(4)
    cols[0].metric("Total Files", snapshot.total_files)
    cols[1].metric("Total Bytes", snapshot.total_size_bytes)
    cols[2].metric("Top Large Files", len(largest))
    cols[3].metric("Cleanup Candidates", len(cleanup))

    st.markdown("### File Type Distribution")
    st.bar_chart(ext_counts)

    left, right = st.columns(2)
    with left:
        st.markdown("### Largest Files")
        st.dataframe([
            {"path": str(item.path), "size_bytes": item.size_bytes}
            for item in largest
        ])
    with right:
        st.markdown("### Download Cleanup Candidates")
        st.dataframe([
            {"path": item.path, "size_bytes": item.size_bytes, "reason": item.reason}
            for item in cleanup
        ])


def render_organize_drive(settings: AppSettings) -> None:
    """Render drive structure planning and approved organization actions."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    st.subheader("Structure the Drive")
    source_root = Path(st.text_input("Source root", value=str(Path.home()), key="organize_source"))
    destination_root = Path(st.text_input("Destination root", value=str(Path.home() / "Drive-Organized"), key="organize_dest"))
    if st.button("Build organization plan", key="build_organization_plan"):
        if not source_root.exists():
            st.error(f"Source root does not exist: {source_root}")
        else:
            management = DriveManagementService(settings)
            plan = management.build_organization_plan(source_root, destination_root)
            st.session_state["organization_plan"] = plan
            st.success(f"Built {len(plan)} planned moves")

    plan = st.session_state.get("organization_plan", [])
    if plan:
        st.dataframe([
            {
                "source": str(item.source),
                "destination": str(item.destination),
                "category": item.recommendation.category,
                "subcategory": item.recommendation.subcategory,
                "confidence": item.recommendation.confidence,
            }
            for item in plan[:500]
        ])
        approved = st.checkbox("Approved execution mode", value=False, key="approved_execution_mode")
        if st.button("Execute approved moves", key="execute_organization_plan"):
            with session_factory() as session:
                management = DriveManagementService(settings, session=session)
                manifests = management.execute_organization_plan(plan, approved=approved)
            st.success(f"Executed {len(manifests)} moves{' (approved)' if approved else ' as preview only'}")


def render_backup_archive(settings: AppSettings) -> None:
    """Render backup and archive utilities."""

    st.subheader("Backup / Archive")
    management = DriveManagementService(settings)
    source_root = Path(st.text_input("Backup source", value=str(Path.home()), key="backup_source"))
    output_root = Path(st.text_input("Backup output", value=str(Path.home() / "Backups"), key="backup_output"))
    archive_name = st.text_input("Archive name", value="drive_backup", key="archive_name")
    method = st.selectbox("Method", ["zip", "tar.gz", "copy"], index=0, key="backup_method")
    if st.button("Create backup / archive", key="create_backup"):
        if not source_root.exists():
            st.error(f"Source root does not exist: {source_root}")
        else:
            artifact = management.backup_folder(source_root, output_root, archive_name, method=method)
            st.success(f"Created {artifact.method} at {artifact.path} ({artifact.size_bytes / 1024 / 1024:.1f} MB)")


def render_photo_studio(settings: AppSettings) -> None:
    """Render photo compression and framing utilities."""

    st.subheader("Photo Compressor & Framer")
    photo_service = PhotoStudioService()
    uploaded = st.file_uploader("Drop photos or a folder of photos", accept_multiple_files=True, type=["jpg", "jpeg", "png", "webp", "bmp", "tiff", "heic"])
    folder_path = st.text_input("Or pick a local folder", value=str(Path.home()), key="photo_folder")

    quality = st.slider("Quality", 50, 95, 82, 1, key="photo_quality")
    max_long_edge = st.selectbox("Max long edge", [1080, 2048, 3000, 0], index=1, key="photo_edge")
    target_mb = st.selectbox("Target max file size", [5, 8, 15, 0], index=1, key="photo_target")
    frame_enabled = st.toggle("Add frame to all photos", value=False, key="photo_frame")
    frame_style = st.selectbox("Frame style", ["simple", "double", "polaroid"], index=0, key="photo_frame_style")
    frame_thickness = st.slider("Thickness", 5, 120, 20, 1, key="photo_frame_thickness")
    frame_color = st.color_picker("Frame color", "#FFFFFF", key="photo_frame_color")

    sources: list[PhotoSource] = []
    if uploaded:
        for item in uploaded:
            if item.name and photo_service.is_image_name(item.name):
                sources.append(PhotoSource(name=item.name, data=item.getvalue(), relative_path=""))
    elif folder_path:
        root = Path(folder_path)
        if root.exists() and st.button("Load folder photos", key="load_folder_photos"):
            sources = photo_service.discover_folder(root)
            st.session_state["photo_sources"] = sources

    if "photo_sources" in st.session_state and not sources:
        sources = st.session_state["photo_sources"]

    if sources:
        folders = {}
        for source in sources:
            folders[source.relative_path or "(root)"] = folders.get(source.relative_path or "(root)", 0) + 1
        st.dataframe([{ "folder": k, "photos": v } for k, v in folders.items()])
        if st.button("Process photos", key="process_photos"):
            options = PhotoCompressionOptions(
                quality=quality,
                max_long_edge=max_long_edge,
                target_max_mb=target_mb,
                frame_enabled=frame_enabled,
                frame_style=frame_style,
                frame_thickness=frame_thickness,
                frame_color=frame_color,
            )
            results = photo_service.compress_sources(sources, options)
            zip_bytes = photo_service.build_zip(results)
            st.success(f"Processed {len(results)} photos")
            st.download_button("Download ZIP", data=zip_bytes, file_name="photos_compressed.zip", mime="application/zip")
            st.write({"original_mb": round(sum(r.original_size for r in results) / 1024 / 1024, 1), "compressed_mb": round(sum(r.compressed_size for r in results) / 1024 / 1024, 1)})


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
    """Render file type counts and multi-select delete workflow."""

    engine = initialize_database(settings)
    session_factory = create_session_factory(engine)
    with session_factory() as session:
        type_service = FileTypeService(session)
        counts = type_service.by_extension()
        extension_options = [ext for ext in type_service.extensions() if ext]
    st.bar_chart(counts)

    selected_extensions = st.multiselect(
        "Select one or more file types",
        options=extension_options,
        default=[ext for ext in extension_options if ext in {".tmp", ".log", ".bak", ".cache"}],
        key="file_type_multiselect",
    )

    approved = st.checkbox("Approved delete mode", value=False, key="file_type_delete_approved")
    if selected_extensions:
        with session_factory() as session:
            type_service = FileTypeService(session)
            matching = type_service.files_for_extensions(selected_extensions)
            summary = type_service.summary_for_extensions(selected_extensions)

        st.info(f"Selected {summary['count']} files totaling {summary['size_bytes'] / 1024 / 1024:.1f} MB")
        st.dataframe([
            {
                "path": file_item.path,
                "extension": file_item.extension,
                "size_bytes": file_item.size_bytes,
                "folder": file_item.folder_path,
            }
            for file_item in matching[:500]
        ])

        if st.button("Delete selected file types", key="delete_selected_types"):
            if not approved:
                st.warning("Enable approved delete mode to execute deletion.")
            else:
                trash_root = settings.data_root / "trash"
                with session_factory() as session:
                    executor = ExecutionService(session)
                    deleted = 0
                    for file_item in matching:
                        source = Path(file_item.path)
                        if source.exists():
                            executor.execute_delete(source, trash_root=trash_root, approved=True)
                            deleted += 1
                    session.commit()
                st.success(f"Moved {deleted} files to {trash_root}")


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

    approved = st.checkbox("Approved execution mode", value=False, key="exec_approved")
    if st.button("Execute move now", key="execute_move_now") and source and destination:
        with session_factory() as session:
            service = ExecutionService(session)
            manifest = service.execute_move(Path(source), Path(destination), approved=approved)
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