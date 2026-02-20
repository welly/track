from __future__ import annotations

import json
import os
import uuid
from pathlib import Path
from typing import Any

from .constants import SESSION_ID_PATTERN
from .models import Session


class Storage:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"active": None, "sessions": []}
        with self.path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def save(self, payload: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)


def resolve_store() -> Storage:
    env_path = os.getenv("TRACK_DATA_FILE")
    if env_path:
        return Storage(Path(env_path).expanduser())
    return Storage(Path.home() / ".track" / "data.json")


def load_sessions(payload: dict[str, Any]) -> tuple[list[Session], bool]:
    raw_sessions = payload.get("sessions", [])
    used_ids: set[str] = set()
    changed = False

    sessions: list[Session] = []
    for item in raw_sessions:
        sid = item.get("id")
        sid_text = sid if isinstance(sid, str) else ""
        if not SESSION_ID_PATTERN.fullmatch(sid_text) or sid_text in used_ids:
            sid_text = create_session_id(used_ids)
            item["id"] = sid_text
            changed = True
        used_ids.add(sid_text)
        sessions.append(Session.from_dict(item))

    return sessions, changed


def save_sessions(payload: dict[str, Any], sessions: list[Session]) -> None:
    payload["sessions"] = [item.to_dict() for item in sessions]


def create_session_id(used_ids: set[str]) -> str:
    while True:
        candidate = uuid.uuid4().hex[:8]
        if candidate not in used_ids:
            return candidate


def next_session_id(sessions: list[Session]) -> str:
    return create_session_id({item.id for item in sessions})
