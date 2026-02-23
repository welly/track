# Technology Stack

**Analysis Date:** 2026-02-23

## Languages

**Primary:**
- Python 3.10+ - Entire application codebase

**Secondary:**
- None detected

## Runtime

**Environment:**
- Python 3.10.19 (specified in `.python-version`)

**Package Manager:**
- pip - Standard Python package manager
- Lockfile: Not detected (no requirements.txt or Poetry/Pipenv lock files)

## Frameworks

**Core:**
- None external frameworks used; all built-in Python standard library

**Standard Library Components:**
- argparse - CLI argument parsing (`app/cli.py`)
- json - Data serialization for session storage (`app/storage.py`)
- dataclasses - Data model definitions (`app/models.py`)
- datetime - Temporal operations throughout (`app/parsing.py`, `app/commands.py`)
- csv - CSV export format (`app/commands.py`)
- xml.etree.ElementTree - XML export format (`app/commands.py`)
- pathlib - Cross-platform file path handling (`app/storage.py`)
- difflib - Fuzzy string matching for typo suggestions (`app/naming.py`)
- re - Regular expression pattern matching (`app/constants.py`, `app/naming.py`, `app/parsing.py`)
- uuid - Session ID generation (`app/storage.py`)
- io - String buffer operations for CSV export (`app/commands.py`)
- tempfile - Test fixture support (`tests/test_track.py`)
- unittest - Testing framework (`tests/test_track.py`)

**Testing:**
- unittest - Python standard library test framework
- tempfile - Temporary directory creation for test isolation

**Build/Dev:**
- setuptools - Package building and distribution (`pyproject.toml`)
- wheel - Python binary package format

## Key Dependencies

**Critical:**
- None - Zero external dependencies. Application uses only Python standard library.

**Infrastructure:**
- None detected - Pure Python implementation with no external service clients

## Configuration

**Environment:**
- `TRACK_DATA_FILE` - Optional environment variable to override default data storage location
  - Defaults to `~/.track/data.json` when not set
  - Can be set to absolute path: `TRACK_DATA_FILE=/tmp/track-data.json track report`
  - Implementation: `app/storage.py:resolve_store()`

**Build:**
- `pyproject.toml` - Project configuration following PEP 517/518 standards
  - Build system: setuptools + wheel
  - Project metadata: name, version, description, authors, license
  - Entry point: `track = "track:main"` (CLI command)
  - Py-modules: `track` (module)
  - Packages: `app` (package)

## Platform Requirements

**Development:**
- Python 3.10+ (enforced in `pyproject.toml`: `requires-python = ">=3.10"`)
- pip for package installation
- Cross-platform compatible (uses pathlib for file paths)

**Production:**
- Python 3.10+ runtime
- Writable filesystem at `~/.track/` directory (for default data storage)
- Or custom writable path via `TRACK_DATA_FILE` environment variable

**Installation Methods:**
- Direct pip: `python -m pip install .`
- Isolated install via pipx: `pipx install .`

---

*Stack analysis: 2026-02-23*
