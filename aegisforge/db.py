from __future__ import annotations

from pathlib import Path

from sqlalchemy import Engine, create_engine, inspect
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    pass


def make_engine(database_url: str) -> Engine:
    if database_url.startswith("sqlite:///"):
        Path(database_url.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    return create_engine(database_url, connect_args={"check_same_thread": False} if database_url.startswith("sqlite") else {})


def session_factory(database_url: str) -> sessionmaker[Session]:
    return sessionmaker(bind=make_engine(database_url), expire_on_commit=False)


def reset_legacy_alpha_schema(engine: Engine, base: type[DeclarativeBase]) -> None:
    inspector = inspect(engine)
    if "projects" not in inspector.get_table_names():
        return
    columns = {column["name"] for column in inspector.get_columns("projects")}
    if "name" in columns:
        return
    # 0.1.0-alpha used JSON blob tables; 0.2.0-alpha intentionally recreates them.
    base.metadata.drop_all(engine)
