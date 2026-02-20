from __future__ import annotations

from .models import Session


def filter_sessions(sessions: list[Session], project: str | None, tag: str | None) -> list[Session]:
    filtered = sessions
    if project:
        filtered = [item for item in filtered if item.project == project]
    if tag:
        filtered = [item for item in filtered if tag in item.tags]
    return filtered
