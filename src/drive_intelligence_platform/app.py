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
from drive_intelligence_platform.ui.views import (
    render_analysis,
    render_dashboard,
    render_downloads_cleanup,
    render_duplicates,
    render_execution,
    render_file_types,
    render_large_files,
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
    st.title("Drive Intelligence Platform")
    st.caption("Read only by default. Every action requires approval.")

    tabs = st.tabs([
        "Dashboard",
        "Scan",
        "Analysis",
        "Duplicates",
        "Large Files",
        "File Types",
        "Screenshots",
        "Downloads Cleanup",
        "Search",
        "Execution",
        "Rollback",
    ])

    with tabs[0]:
        render_dashboard(settings)
    with tabs[1]:
        render_scan(settings)
    with tabs[2]:
        render_analysis(settings)
    with tabs[3]:
        render_duplicates(settings)
    with tabs[4]:
        render_large_files(settings)
    with tabs[5]:
        render_file_types(settings)
    with tabs[6]:
        render_screenshots(settings)
    with tabs[7]:
        render_downloads_cleanup(settings)
    with tabs[8]:
        render_search(settings)
    with tabs[9]:
        render_execution(settings)
    with tabs[10]:
        render_rollback(settings)


if __name__ == "__main__":
    main()