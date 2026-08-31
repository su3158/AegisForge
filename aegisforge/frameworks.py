from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class FrameworkControl:
    id: str
    title: str
    level: int
    status: str = "NOT_TESTED"


def load_asvs_l2_controls() -> list[FrameworkControl]:
    data_path = Path(__file__).resolve().parent.parent / "frameworks" / "asvs" / "5.0.0" / "controls.json"
    data = json.loads(data_path.read_text(encoding="utf-8"))
    controls: list[dict[str, Any]] = data["controls"]
    return [FrameworkControl(item["id"], item["title"], int(item["level"])) for item in controls]
