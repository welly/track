# Architecture

**Analysis Date:** 2026-02-23

## Pattern Overview

**Overall:** Modular CLI application with a command-driven dispatcher pattern

**Key Characteristics:**
- Single entry point (`track.py`) delegates to a CLI parser
- Command dispatcher that routes to domain-specific command handlers
- Data persistence via JSON file storage
- Name normalization and validation layer for robustness
- Functional modules with clear separation of concerns

## Layers

**CLI/Dispatcher Layer:**
- Purpose: Parse command-line arguments and route to appropriate command handler
- Location: `app/cli.py`
- Contains: Argument parser definition, main entry point, error handling
- Depends on: Storage layer, command handlers, error types
- Used by: Entry point `track.py`

**Command Handlers Layer:**
- Purpose: Implement domain logic for each user-facing command (start, stop, add, report, export, delete, rename)
- Location: `app/commands.py`
- Contains: `cmd_start()`, `cmd_stop()`, `cmd_add()`, `cmd_report()`, `cmd_sessions()`, `cmd_export()`, `cmd_delete()`, `cmd_rename()`
- Depends on: Models, storage, parsing, filtering, naming, formatting utilities
- Used by: CLI dispatcher

**Data Models Layer:**
- Purpose: Define core domain entities and serialization
- Location: `app/models.py`
- Contains: `Session` dataclass with ID, project, tags, note, start/end datetimes, and duration property
- Depends on: Python datetime module
- Used by: Storage layer, command handlers, filtering

**Storage Layer:**
- Purpose: Persist and load session data as JSON, manage active timer state
- Location: `app/storage.py`
- Contains: `Storage` class for file I/O, `load_sessions()` for deserialization with ID validation/repair, `save_sessions()` for persistence, session ID generation
- Depends on: Models, constants (ID validation pattern)
- Used by: All command handlers, CLI main()

**Utility Layers:**

**Parsing & Formatting (`app/parsing.py`):**
- Parse user input: datetime strings (with multiple formats), durations ("30m", "2 hours"), dates
- Format output: duration display as HH:MM:SS or HH:MM, duration rounding to nearest 15-minute interval
- Used by: Command handlers for input validation and output display

**Naming & Validation (`app/naming.py`):**
- Normalize names: convert to lowercase, replace spaces/underscores with hyphens, collapse multiple hyphens
- Validate names: enforce pattern `[a-z0-9][a-z0-9-]*`
- Suggest close matches: detect typos using difflib with 0.84 cutoff
- Used by: Command handlers for project/tag normalization and safety checks

**Filtering (`app/filters.py`):**
- Filter sessions by project and/or tag with normalized name matching
- Used by: Report, sessions, export commands

**Error Handling (`app/errors.py`):**
- Custom exception type `TrackError` for domain-level errors
- Used by: All layers for user-facing error communication

**Configuration (`app/constants.py`):**
- `DATETIME_FORMAT`: "YYYY-MM-DD HH:MM:SS" for display
- `SESSION_ID_PATTERN`: regex validating 8-character lowercase hex IDs

## Data Flow

**Start Timer Flow:**
1. User invokes: `track start --project myproject --tag abc-123`
2. CLI parser creates `Namespace` with args
3. `cmd_start()` handler:
   - Loads current state from storage (active timer check, existing sessions)
   - Validates project name (normalization + typo detection)
   - Validates tags (normalization only, no typo check)
   - Creates active timer entry in payload
   - Saves payload to storage
4. User sees confirmation message

**Stop Timer Flow:**
1. User invokes: `track stop`
2. `cmd_stop()` handler:
   - Loads state from storage
   - Retrieves active timer
   - Creates completed `Session` object with generated ID
   - Appends session to sessions list
   - Clears active timer from payload
   - Saves to storage
3. User sees completion message with session ID and duration

**Report Generation Flow:**
1. User invokes: `track report --project myproject --from 2026-01-01 --to 2026-02-28`
2. `cmd_report()` handler:
   - Loads sessions from storage
   - Applies project/tag filter using normalized name matching
   - Applies date range filter (defaults to current week if no --all flag)
   - Aggregates durations by project and tag (with optional rounding to 15-minute intervals)
   - Formats output as human-readable text table
   - Optionally includes per-session details if --notes flag present

**State Management:**

Storage payload structure:
```json
{
  "active": {
    "project": "my-project",
    "tags": ["tag1", "tag2"],
    "note": "Optional note",
    "start": "2026-02-23T10:00:00"
  },
  "sessions": [
    {
      "id": "a1b2c3d4",
      "project": "my-project",
      "tags": ["tag1"],
      "note": "Completed work",
      "start": "2026-02-23T09:00:00",
      "end": "2026-02-23T10:00:00"
    }
  ]
}
```

- `active`: null or dict representing running timer
- `sessions`: array of completed Session objects
- Default location: `~/.track/data.json` (overridable via `TRACK_DATA_FILE` env var)

## Key Abstractions

**Session:**
- Purpose: Represents a time tracking entry with temporal and metadata context
- Examples: `app/models.py` (definition), used throughout `app/commands.py`
- Pattern: Immutable dataclass with ISO datetime fields and computed duration property

**Storage:**
- Purpose: Abstract file I/O and provide consistent load/save interface
- Examples: `app/storage.py`
- Pattern: Simple class-based abstraction; load() returns dict, save() takes dict

**Name Normalization:**
- Purpose: Ensure consistent matching and user-friendly handling of project/tag names
- Examples: `app/naming.py` functions
- Pattern: Pure functions for normalize_name(), validate_name(), suggest_close_match()

**TrackError:**
- Purpose: Signal domain-level failures to user
- Examples: Invalid datetime format, project already exists, no active timer
- Pattern: Custom exception type caught and printed to stderr by CLI main()

## Entry Points

**`track.py` (Script Entry):**
- Location: `/track.py` (root-level wrapper)
- Triggers: User invokes `track` command or `python track.py`
- Responsibilities: Imports and calls `main()` from `app/cli.py`

**`app/cli.py:main()`:**
- Location: `app/cli.py` (entry point function)
- Triggers: Called from `track.py` or imported/tested
- Responsibilities:
  - Builds argument parser via `build_parser()`
  - Parses command-line arguments
  - Initializes storage via `resolve_store()`
  - Dispatches to command handler (via args.func)
  - Catches `TrackError` and prints to stderr with exit code 1
  - Returns exit code (0 for success, 1 for error)

## Error Handling

**Strategy:** Layer-by-layer validation with early exit on error

**Patterns:**

1. **Input Validation (Commands):** Name normalization checks, datetime parsing, duration parsing
2. **Business Logic Validation (Commands):** Duplicate timer check, time ordering validation, typo detection
3. **Data Integrity (Storage):** Session ID repair/regeneration on load
4. **CLI Error Reporting:** `TrackError` caught and printed to stderr with non-zero exit code

Example error flow:
```
User input → Parsing (parse_datetime raises TrackError) → CLI catches → prints to stderr → exit(1)
```

## Cross-Cutting Concerns

**Logging:** Console output via print() statements; no structured logging library

**Validation:**
- Names: Normalization + regex pattern + typo detection (projects only)
- Datetimes: Multiple format support (format string, ISO-8601)
- Durations: Natural language parsing (30m, 2 hours, etc.)

**Authentication:** Not applicable - single-user CLI with local storage

**Data Persistence:** JSON file with automatic parent directory creation; atomicity via full file rewrite

---

*Architecture analysis: 2026-02-23*
