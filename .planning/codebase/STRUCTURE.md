# Codebase Structure

*Mapped: 2026-02-23*

## Directory Layout

```
track/
├── track.py                    # Root entry point → delegates to app/cli.py:main()
├── app/                        # Core application package (10 modules)
│   ├── __init__.py
│   ├── cli.py                  # Argument parser and command dispatcher
│   ├── commands.py             # 8 command handlers
│   ├── models.py               # Session dataclass with serialization
│   ├── storage.py              # JSON file I/O and session ID generation
│   ├── parsing.py              # Input parsing and output formatting utilities
│   ├── naming.py               # Name normalization and typo detection
│   ├── filters.py              # Session filtering by project/tag
│   ├── errors.py               # TrackError exception class
│   └── constants.py            # Format strings and validation regex
├── tests/
│   └── test_track.py           # Single test file covering full application
└── .planning/
    └── codebase/               # Codebase analysis documents
```

## Key File Purposes

| File | Purpose |
|------|---------|
| `track.py` | Entry point — calls `app/cli.py:main()` |
| `app/cli.py` | Argument parser and command dispatcher |
| `app/commands.py` | 8 command handlers: start, stop, add, report, sessions, export, delete, rename |
| `app/models.py` | `Session` dataclass with serialization |
| `app/storage.py` | JSON file I/O and session ID generation |
| `app/parsing.py` | Input parsing and output formatting utilities |
| `app/naming.py` | Name normalization and typo detection |
| `app/filters.py` | Session filtering by project/tag |
| `app/errors.py` | `TrackError` exception class |
| `app/constants.py` | Format strings and validation regex |

## Naming Conventions

- **Functions:** `snake_case` (e.g., `cmd_start`, `parse_datetime`)
- **Classes:** `PascalCase` (e.g., `Session`, `Storage`)
- **Constants:** `UPPER_CASE` (e.g., `DATETIME_FORMAT`, `SESSION_ID_PATTERN`)

## Where to Add New Code

- **New commands:** Add handler to `app/commands.py`, parser entry to `app/cli.py`
- **New utilities:** Add to appropriate module (`parsing.py`, `naming.py`, etc.)
- **Tests:** Add to `tests/test_track.py`

## Data Storage

- Location: `~/.track/data.json`
- Overridable via `TRACK_DATA_FILE` environment variable
