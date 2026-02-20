#!/usr/bin/env python3
from __future__ import annotations

from app.cli import main
from app.parsing import parse_duration

__all__ = ["main", "parse_duration"]


if __name__ == "__main__":
    raise SystemExit(main())
