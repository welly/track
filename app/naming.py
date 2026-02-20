from __future__ import annotations

import difflib
import re

from .errors import TrackError

NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9-]*$")


def normalize_name(value: str) -> str:
    normalized = value.strip().lower()
    normalized = re.sub(r"[\s_]+", "-", normalized)
    normalized = re.sub(r"-+", "-", normalized)
    return normalized


def validate_name(kind: str, value: str) -> None:
    if not value or not NAME_PATTERN.fullmatch(value):
        raise TrackError(
            f"Invalid {kind} '{value}'. Use lowercase letters, numbers, and hyphens only "
            "(for example: my-project, abc-123)."
        )


def suggest_close_match(candidate: str, known_values: set[str]) -> str | None:
    if not known_values:
        return None
    matches = difflib.get_close_matches(candidate, sorted(known_values), n=1, cutoff=0.84)
    return matches[0] if matches else None
