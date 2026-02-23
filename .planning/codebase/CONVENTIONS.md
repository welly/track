# Coding Conventions

**Analysis Date:** 2026-02-23

## Naming Patterns

**Files:**
- Lowercase with underscores: `models.py`, `commands.py`, `storage.py`
- Module names are concise, single-word or two-word descriptors
- Test files use `test_` prefix: `test_track.py`

**Functions:**
- snake_case for all function definitions
- Descriptive function names following action verbs: `parse_duration()`, `normalize_name()`, `validate_name()`, `collect_known_names()`, `humanize_elapsed()`
- Command handlers prefixed with `cmd_`: `cmd_start()`, `cmd_stop()`, `cmd_add()`, `cmd_report()`, `cmd_export()`, `cmd_delete()`, `cmd_rename()`

**Variables:**
- snake_case: `raw_project`, `known_projects`, `normalized_tags`, `session_ids`, `total_seconds`, `payload`, `used_ids`
- Abbreviated forms acceptable: `tmp` for temporary directory, `fh` for file handle, `out` for output
- Descriptive names for loop variables: `for item in sessions:`, `for tag_name in item.tags:`

**Types:**
- PascalCase for classes: `Session`, `Storage`, `TrackError`
- Private module-level regex patterns use UPPERCASE: `SESSION_ID_PATTERN`, `NAME_PATTERN`, `DATETIME_FORMAT`

## Code Style

**Formatting:**
- No explicit formatter specified in configuration
- 4-space indentation (Python standard)
- Line length appears to target ~100-120 characters
- Blank lines between functions in modules

**Linting:**
- No .eslintrc, .pylintrc, or similar configuration detected
- Type hints present throughout: `from __future__ import annotations` used for forward compatibility
- Type annotations on function signatures: `def parse_datetime(value: str) -> datetime:`, `def collect_known_names(sessions: list[Session], active: dict[str, Any] | None) -> tuple[set[str], set[str]]:`
- Union types use pipe operator: `str | None`, `dict[str, Any] | None`
- Generic type hints: `list[str]`, `dict[str, timedelta]`, `set[str]`

## Import Organization

**Order:**
1. `from __future__ import annotations` (always first)
2. Standard library: `import argparse`, `import json`, `from datetime import datetime`, `from pathlib import Path`
3. Relative imports from same package: `from .models import Session`, `from .errors import TrackError`

**Path Aliases:**
- No path aliases detected; uses relative imports with dot notation

**Example from `commands.py` lines 1-25:**
```python
from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .constants import DATETIME_FORMAT
from .errors import TrackError
from .filters import filter_sessions
from .models import Session
from .naming import normalize_name, suggest_close_match, validate_name
from .parsing import (
    fmt_duration,
    fmt_duration_minutes,
    parse_date,
    parse_datetime,
    parse_duration,
    round_duration_to_nearest_interval,
)
from .storage import Storage, load_sessions, next_session_id, save_sessions
```

## Error Handling

**Patterns:**
- Custom exception class `TrackError` defined in `errors.py` for all user-facing errors
- Errors raised with descriptive messages: `raise TrackError(f"Project '{project}' is close to existing project '{suggestion}'. Use --force-new-project to create it anyway.")`
- Exception chaining with `from exc` for context: `raise TrackError(...) from exc` (see `parsing.py` lines 17-19, 26)
- Try/except blocks used for parsing/validation: `try: ... except ValueError as exc: raise TrackError(...)`
- Functions validate inputs early and raise TrackError before proceeding
- CLI entry point catches TrackError and exits with code 1 (`cli.py` lines 95-100)

**Example from `parsing.py`:**
```python
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
```

## Logging

**Framework:** No logging framework used (logging module not imported)

**Patterns:**
- All output via `print()` to stdout for user-facing messages
- Errors printed to stderr: `print(f"Error: {exc}", file=sys.stderr)` in `cli.py` line 98
- Informational messages printed to stdout: `print(f"Started timer for project '{args.project}'.")`

## Comments

**When to Comment:**
- Very minimal commenting; code is self-documenting through clear naming
- Comments not observed in production code modules
- Docstrings not used for functions

**JSDoc/TSDoc:**
- Not applicable to Python; no pydoc-style docstrings in use

## Function Design

**Size:** Functions are concise and focused:
- Utility functions: 10-30 lines (`parse_duration()`, `humanize_elapsed()`)
- Command handlers: 20-70 lines (`cmd_start()`, `cmd_report()`)
- Helper functions: 5-20 lines (`collect_known_names()`, `normalize_tag_inputs()`)

**Parameters:**
- Explicit positional parameters, some with defaults
- Keyword-only parameters use `*` separator: `normalize_project_input(raw_project: str, known_projects: set[str], *, force_new_project: bool)`
- Type annotations on all parameters

**Return Values:**
- Functions return tuples when multiple values needed: `def load_sessions(...) -> tuple[list[Session], bool]:`
- Functions return None implicitly when performing side effects (loading/saving storage)
- Union types for optional returns: `str | None`

## Module Design

**Exports:**
- Barrel file pattern in `app/__init__.py` defines `__all__` with exported public API:
```python
from .cli import main
from .parsing import parse_duration

__all__ = ["main", "parse_duration"]
```

**Barrel Files:**
- Main entry point `app/__init__.py` exports main() and parse_duration() for external use
- Submodules import directly without intermediate barrel files

**Module organization:**
- `models.py`: Data structures (Session dataclass)
- `cli.py`: Argument parsing and main entry point
- `commands.py`: Command implementations
- `parsing.py`: DateTime, duration parsing and formatting utilities
- `storage.py`: JSON file persistence and session ID generation
- `naming.py`: Name normalization and validation
- `filters.py`: Session filtering logic
- `errors.py`: Custom exception class
- `constants.py`: Regex patterns and datetime format constant

---

*Convention analysis: 2026-02-23*
