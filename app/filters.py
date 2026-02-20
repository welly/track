from __future__ import annotations

from .models import Session
from .naming import normalize_name


def filter_sessions(sessions: list[Session], project: str | None, tag: str | None) -> list[Session]:
    normalized_project = normalize_name(project) if project else None
    normalized_tag = normalize_name(tag) if tag else None

    filtered = sessions
    if normalized_project:
        filtered = [item for item in filtered if normalize_name(item.project) == normalized_project]
    if normalized_tag:
        filtered = [
            item for item in filtered if any(normalize_name(item_tag) == normalized_tag for item_tag in item.tags)
        ]
    return filtered
