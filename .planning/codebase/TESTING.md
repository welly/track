# Testing

*Mapped: 2026-02-23*

## Framework

- **Framework:** `unittest` (Python standard library)
- **Test runner:** `python -m unittest` or direct execution (`python tests/test_track.py`)
- **Test file:** `tests/test_track.py` (single file, ~377 lines)

## Test Structure

Single test class `TrackTests(unittest.TestCase)` containing all test methods.

### setUp / tearDown

```python
def setUp(self) -> None:
    self.tmp = tempfile.TemporaryDirectory()
    self.data_file = os.path.join(self.tmp.name, "data.json")
    os.environ["TRACK_DATA_FILE"] = self.data_file

def tearDown(self) -> None:
    self.tmp.cleanup()
    os.environ.pop("TRACK_DATA_FILE", None)
```

- Each test gets an isolated temporary directory for data
- `TRACK_DATA_FILE` env var redirects storage away from real `~/.track/data.json`
- Temp directory is cleaned up after every test — no cross-test contamination

## Filesystem Isolation

Tests use `tempfile.TemporaryDirectory()` to isolate all file I/O. The `TRACK_DATA_FILE` environment variable is the injection point — all storage operations respect this override, making it the key seam for test isolation.

## Helper Methods

```python
def _add(self, start, end, project, tag=None, note=None) -> None:
    # Calls track.main(["add", ...]) and asserts exit code 0

def _session_ids(self) -> list[str]:
    # Reads data.json directly and returns session IDs
```

## stdout/stderr Capture Pattern

```python
stdout = StringIO()
with redirect_stdout(stdout):
    code = track.main(["command", "--flag"])
self.assertEqual(code, 0)
self.assertIn("expected text", stdout.getvalue())
```

Used throughout — tests drive the CLI via `track.main()` and capture output for assertions.

## Test Coverage

### Commands tested
| Command | Tests |
|---------|-------|
| `add` | Name normalization, invalid names, typo detection (`--force-new-project`), note saving |
| `status` | No active timer, active timer with/without tags |
| `report` | Breakdown, date range, date filter, default week range, `--all` flag, `--exact` rounding, `--notes` flag |
| `export` | JSON (default + explicit), CSV, XML formats; rounding |
| `sessions` | List all, filter by project, filter by tag |
| `delete` | By project, by tag, by session ID |
| `rename` | Project rename, tag rename (scoped to session) |
| (no command) | Prints help |

### Utilities tested
- `track.parse_duration("30 minutes")` → `timedelta(minutes=30)`
- `track.parse_duration("1.5h")` → `timedelta(hours=1.5)`

## Assertion Style

- `assertEqual(track.main([...]), 0)` — exit code check
- `assertIn("text", output)` / `assertNotIn("text", output)` — output content
- `assertRegex(output, pattern)` — structured output patterns (e.g. session IDs, timestamps)
- Direct JSON reads for structural assertions (e.g. verifying stored field values)

## Running Tests

```bash
python -m unittest tests/test_track.py
# or
python tests/test_track.py
```

## Gaps / Notes

- No dedicated unit tests for individual module functions (parsing, naming, filters) beyond what's exercised through CLI integration
- No mocking of `datetime.now()` — tests that depend on current date use relative offsets
- `start`/`stop` timer workflow not directly tested (only `add` for completed sessions)
- No test for export to file (only stdout tested)
