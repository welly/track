from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any


@dataclass
class Session:
    id: str
    project: str
    tags: list[str]
    note: str | None
    start: datetime
    end: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "project": self.project,
            "tags": self.tags,
            "note": self.note,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Session":
        return cls(
            id=str(payload["id"]),
            project=payload["project"],
            tags=list(payload.get("tags", [])),
            note=payload.get("note"),
            start=datetime.fromisoformat(payload["start"]),
            end=datetime.fromisoformat(payload["end"]),
        )

    @property
    def duration(self) -> timedelta:
        return self.end - self.start
