from __future__ import annotations

import re
from datetime import date, datetime, timedelta

from .constants import DATETIME_FORMAT
from .errors import TrackError


def parse_datetime(value: str) -> datetime:
    try:
        return datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise TrackError(
                f"Invalid datetime '{value}'. Use '{DATETIME_FORMAT}' or ISO-8601 format."
            ) from exc


def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise TrackError(f"Invalid date '{value}'. Use 'YYYY-MM-DD'.") from exc


def parse_duration(value: str) -> timedelta:
    normalized = value.strip().lower()
    short_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([mh])", normalized)
    if short_match:
        amount = float(short_match.group(1))
        unit = short_match.group(2)
        return timedelta(minutes=amount if unit == "m" else 0, hours=amount if unit == "h" else 0)

    word_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(minute|minutes|hour|hours)", normalized)
    if not word_match:
        raise TrackError("Invalid duration. Examples: '30 minutes', '1.5 hours', '45m', '2h'.")

    amount = float(word_match.group(1))
    unit = word_match.group(2)
    if unit.startswith("minute"):
        return timedelta(minutes=amount)
    return timedelta(hours=amount)


def fmt_duration(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
