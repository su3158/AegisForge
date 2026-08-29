from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Settings:
    data_dir: Path
    database_url: str
    host: str = "127.0.0.1"
    port: int = 8765
    offline: bool = False
    admin_password: str | None = None
    secret_key: str | None = None

    @classmethod
    def load(
        cls, config_file: str | Path | None = None, overrides: dict[str, Any] | None = None
    ) -> Settings:
        return load_settings(Path(config_file) if config_file else None, overrides)


def os_config_dir() -> Path:
    # App-wide secrets such as Hugging Face tokens are not project data.
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        return base / "AegisForge"
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / "aegisforge"


def load_settings(config_file: Path | None = None, overrides: dict[str, Any] | None = None) -> Settings:
    defaults: dict[str, Any] = {"data_dir": ".aegisforge", "host": "127.0.0.1", "port": 8765}
    file_values: dict[str, Any] = {}
    if config_file and config_file.exists():
        file_values = yaml.safe_load(config_file.read_text(encoding="utf-8")) or {}
    env_values = {
        "data_dir": os.environ.get("AEGISFORGE_DATA_DIR"),
        "database_url": os.environ.get("AEGISFORGE_DATABASE_URL"),
        "host": os.environ.get("AEGISFORGE_HOST"),
        "port": os.environ.get("AEGISFORGE_PORT"),
        "admin_password": os.environ.get("AEGISFORGE_ADMIN_PASSWORD"),
        "secret_key": os.environ.get("AEGISFORGE_SECRET_KEY"),
    }
    # Precedence is deliberate: command line overrides environment, then config files.
    values = (
        defaults
        | file_values
        | {k: v for k, v in env_values.items() if v not in (None, "")}
        | (overrides or {})
    )
    data_dir = Path(values["data_dir"]).expanduser()
    database_url = values.get("database_url") or f"sqlite:///{data_dir / 'aegisforge.db'}"
    return Settings(
        data_dir=data_dir,
        database_url=str(database_url),
        host=str(values.get("host", "127.0.0.1")),
        port=int(values.get("port", 8765)),
        offline=bool(values.get("offline", False)),
        admin_password=values.get("admin_password"),
        secret_key=values.get("secret_key"),
    )
