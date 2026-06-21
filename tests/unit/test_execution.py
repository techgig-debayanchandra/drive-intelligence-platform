from __future__ import annotations

from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from drive_intelligence_platform.db.base import Base
from drive_intelligence_platform.services.execution import ExecutionService


def test_execution_service_persists_manifest() -> None:
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, future=True)

    with session_factory() as session:
        service = ExecutionService(session)
        plan = service.preview_move(Path("source.txt"), Path("archive/source.txt"), approved=True)
        manifest = service.persist_manifest(plan)
        session.commit()

    assert manifest.operation_id == plan.operation_id
    assert manifest.status == "approved"