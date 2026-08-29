from __future__ import annotations

from typing import Any

from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

from . import __version__
from .config import Settings, load_settings
from .db import Base, session_factory
from .models import Evidence, Finding, Project, Report, Scan, Target


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or load_settings()
    factory = session_factory(settings.database_url)
    Base.metadata.create_all(factory.kw["bind"])
    app = FastAPI(title="AegisForge", version=__version__)

    def get_db() -> Any:
        with factory() as session:
            yield session

    @app.get("/api/v1/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.get("/api/v1/settings")
    def read_settings() -> dict[str, str | bool]:
        # Never echo DSNs; Postgres URLs commonly include credentials.
        backend = "postgres" if settings.database_url.startswith("postgresql") else "sqlite"
        return {"database": backend, "offline": settings.offline}

    @app.get("/api/v1/console")
    def console() -> dict[str, list[Any]]:
        # The frontend falls back to demo data; this endpoint establishes the live API shape.
        return {
            "projects": [],
            "targets": [],
            "scans": [],
            "findings": [],
            "evidence": [],
            "chains": [],
            "coverage": [],
        }

    for path, model in {
        "projects": Project,
        "targets": Target,
        "scans": Scan,
        "findings": Finding,
        "evidence": Evidence,
        "reports": Report,
    }.items():
        _crud(app, path, model, get_db)

    return app


def _crud(app: FastAPI, path: str, model: type[Any], get_db: Any) -> None:
    db_dependency = Depends(get_db)

    @app.get(f"/api/v1/{path}", name=f"list_{path}")
    def list_rows(db: Session = db_dependency) -> list[dict[str, Any]]:
        return [
            {"id": row.id, "created_at": row.created_at.isoformat(), "data": row.data}
            for row in db.query(model).all()
        ]

    @app.post(f"/api/v1/{path}", name=f"create_{path}")
    def create_row(data: dict[str, Any], db: Session = db_dependency) -> dict[str, Any]:
        row = model(data=data)
        db.add(row)
        db.commit()
        return {"id": row.id, "created_at": row.created_at.isoformat(), "data": row.data}
