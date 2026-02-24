# Concerns & Technical Debt

*Mapped: 2026-02-23*

## Summary

Small, focused CLI tool with clean architecture. Main concerns are around data safety (no file locking, no backup) and missing test coverage for edge cases. No blocking issues — all concerns are manageable.

---

## Data Safety

### No File Locking (Medium)
**File:** `app/storage.py:24-26`

`Storage.save()` does a direct open+write with no locking. Concurrent invocations (e.g. two terminal tabs running `track` simultaneously) could corrupt `data.json` via a race condition.

```python
def save(self, payload: dict[str, Any]) -> None:
    with self.path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)
```

**Impact:** Data loss if two commands run at the same time. Low probability for single-user CLI, but possible.
**Remediation:** Use `filelock` or write to a temp file and atomically rename.

---

### No Backup / Recovery (Low)
**File:** `app/storage.py`

A failed write (crash mid-save, disk full) leaves `data.json` empty or truncated with no recovery path. No `.bak` file is written before overwriting.

**Impact:** Potential total data loss on write failure.
**Remediation:** Write to `data.json.tmp`, then `os.replace()` for atomic swap.

---

### Unhandled JSON Decode Errors (Medium)
**File:** `app/storage.py:21-22`

`storage.load()` calls `json.load()` with no exception handling. A corrupted or manually edited `data.json` raises an unhandled `json.JSONDecodeError`.

```python
with self.path.open("r", encoding="utf-8") as fh:
    return json.load(fh)
```

**Impact:** Cryptic traceback instead of a useful error message.
**Remediation:** Catch `json.JSONDecodeError` and raise a `TrackError` with a clear recovery message.

---

## Performance

### Full Load on Every Command (Low)
**Files:** `app/commands.py` — all command handlers

Every command (including read-only ones like `status`, `sessions`) loads the entire `data.json` into memory and deserializes all sessions.

**Impact:** Negligible for personal use. Would degrade with very large session counts (10k+).
**Remediation:** Not needed unless data grows significantly. Note for future if needed.

---

## Testing Gaps

### No Concurrent Access Tests (Low)
No tests exercise simultaneous writes — the race condition in `Storage.save()` is untested.

### No Corrupted Data Tests (Low)
`storage.load()` is not tested with malformed JSON, missing fields, or partial writes.

### `start`/`stop` Timer Flow Not Tested (Low)
`cmd_start` and `cmd_stop` are not directly exercised in `tests/test_track.py`. All timer-based tests use `cmd_add` with explicit timestamps.

### No Timezone Edge Case Tests (Low)
All tests use naive `datetime` objects. Behavior around DST transitions or systems with non-UTC local time is untested.

---

## Code Quality

### `normalize_name` Called Redundantly in `cmd_delete` (Low)
**File:** `app/commands.py:383-404`

`normalize_name()` is called both when constructing the filter and again inside the loop comparison, which is redundant but harmless.

### `bool(args.project) == bool(args.tag)` Guard in `cmd_rename` (Low)
**File:** `app/commands.py:420`

```python
if bool(args.project) == bool(args.tag):
    raise TrackError("Provide exactly one of --project or --tag.")
```

This is a non-obvious way to check XOR. Works correctly but could confuse future contributors.

---

## Security

### No CSV/XML Injection Protection (Low)
**File:** `app/commands.py:338-369`

Project names and tags are written directly into CSV and XML exports without escaping. Python's `csv.DictWriter` handles CSV quoting correctly, and `xml.etree.ElementTree` escapes XML by default — so this is lower risk than it appears, but worth noting.

### File Permissions Not Set (Low)
`data.json` inherits the default umask. On shared systems, the file could be readable by other users. Not a concern for typical single-user development machines.

---

## Out of Scope / Won't Fix

| Issue | Reason |
|-------|--------|
| No pagination for `sessions` output | Personal tool, session counts stay manageable |
| No undo/rollback | Adds significant complexity; low demand for personal CLI |
| No multi-user support | Explicitly single-user tool |
