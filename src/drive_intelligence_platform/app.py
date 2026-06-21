"""Streamlit user interface for the platform."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

PROJECT_SRC = Path(__file__).resolve().parents[1]
if str(PROJECT_SRC) not in sys.path:
    sys.path.insert(0, str(PROJECT_SRC))

from drive_intelligence_platform.core.config import get_settings
from drive_intelligence_platform.db.base import Base
from drive_intelligence_platform.db.session import create_db_engine
try:
    from drive_intelligence_platform.ui.views import apply_bootstrap_ui
except ImportError:
    def apply_bootstrap_ui() -> None:
        return

from drive_intelligence_platform.ui.views import (
    render_analysis,
    render_backup_archive,
    render_control_center,
    render_dashboard,
    render_downloads_cleanup,
    render_duplicates,
    render_execution,
    render_file_types,
    render_organize_drive,
    render_large_files,
    render_photo_studio,
    render_rollback,
    render_scan,
    render_search,
    render_screenshots,
)


def main() -> None:
    """Render the main dashboard."""

    settings = get_settings()
    engine = create_db_engine(settings)
    Base.metadata.create_all(engine)
    st.set_page_config(page_title=settings.app_name, layout="wide")
    apply_bootstrap_ui()
    st.title("Drive Intelligence Platform")
    st.caption("Read only by default. Every action requires approval.")

    tabs = st.tabs([
        "Dashboard",
        "Drive Control Center",
        "Scan",
        "Organize Drive",
        "Backup / Archive",
        "Analysis",
        "Duplicates",
        "Large Files",
        "File Types",
        "Screenshots",
        "Downloads Cleanup",
        "Search",
        "Photo Studio",
        "Execution",
        "Rollback",
    ])

    with tabs[0]:
        render_dashboard(settings)
    with tabs[1]:
        render_control_center(settings)
    with tabs[2]:
        render_scan(settings)
    with tabs[3]:
        render_organize_drive(settings)
    with tabs[4]:
        render_backup_archive(settings)
    with tabs[5]:
        render_analysis(settings)
    with tabs[6]:
        render_duplicates(settings)
    with tabs[7]:
        render_large_files(settings)
    with tabs[8]:
        render_file_types(settings)
    with tabs[9]:
        render_screenshots(settings)
    with tabs[10]:
        render_downloads_cleanup(settings)
    with tabs[11]:
        render_search(settings)
    with tabs[12]:
        render_photo_studio(settings)
    with tabs[13]:
        render_execution(settings)
    with tabs[14]:
        render_rollback(settings)


if __name__ == "__main__":
    main()