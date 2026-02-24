# External Integrations

**Analysis Date:** 2026-02-23

## APIs & External Services

**None detected** - Application is completely self-contained with zero external API dependencies.

## Data Storage

**Databases:**
- None detected - No database client or ORM used

**File Storage:**
- Local filesystem only
  - Default location: `~/.track/data.json`
  - Format: JSON
  - Structure: Single file containing `{"active": {...}, "sessions": [...]}`
  - Implementation: `app/storage.py:Storage` class
  - Data model: `Session` dataclass in `app/models.py` with fields: id, project, tags, note, start, end

**Caching:**
- None - Data is read from disk and held in memory for single command execution

## Authentication & Identity

**Auth Provider:**
- None detected - No authentication system
- Single-user CLI application with no access control

## Monitoring & Observability

**Error Tracking:**
- None detected - No error monitoring service

**Logs:**
- Console output only via `print()` statements
- Error output to `sys.stderr` for error messages
- Implementation: `app/cli.py:main()` catches `TrackError` exceptions and prints to stderr

## CI/CD & Deployment

**Hosting:**
- Not applicable - CLI application, runs locally on user's machine

**CI Pipeline:**
- Not detected - No CI configuration files found (no `.github/workflows/`, `.gitlab-ci.yml`, etc.)

## Environment Configuration

**Required env vars:**
- None - All functionality works without environment variables

**Optional env vars:**
- `TRACK_DATA_FILE` - Override default data file location
  - Implementation: `app/storage.py:resolve_store()`
  - Example: `TRACK_DATA_FILE=/tmp/track-data.json track report`

**Secrets location:**
- Not applicable - No API keys, credentials, or secrets required

## Webhooks & Callbacks

**Incoming:**
- None detected - CLI-only application

**Outgoing:**
- None detected - No external service notifications or callbacks

## Data Export & Integration Points

**Export Formats:**
- JSON format - Machine-readable export with session objects including rounded session_time in decimal hours
  - Command: `track export --format json [--output <file>]`
  - Implementation: `app/commands.py:cmd_export()` lines 330-337

- CSV format - Spreadsheet-compatible with columns: id, project, tags, note, start, end, session_time
  - Command: `track export --format csv [--output <file>]`
  - Implementation: `app/commands.py:cmd_export()` lines 338-355
  - Tags are semicolon-delimited in CSV format

- XML format - XML document with session elements
  - Command: `track export --format xml [--output <file>]`
  - Implementation: `app/commands.py:cmd_export()` lines 356-369
  - Root element: `<sessions>`, child elements: `<session>` with sub-elements for each field

**Import:**
- Not supported - No import functionality. Data can only be created via CLI commands.

## Data Portability

**Migration Path:**
- All data stored in single JSON file at `~/.track/data.json`
- Can be manually backed up, transferred, or imported to another installation
- JSON structure is simple and documented in `app/models.py:Session.to_dict()`

---

*Integration audit: 2026-02-23*
