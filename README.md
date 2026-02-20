# track - Time Tracker CLI

A lightweight CLI time tracker inspired by Watson.

Repository: https://github.com/welly/track

## Install

Install locally from this repository:

```bash
python -m pip install .
```

After installation, the `track` command is available on your PATH.

For isolated user installs, you can also use `pipx`:

```bash
pipx install .
```

## Features

- Start/stop live timers per project.
- Check current active timer status and elapsed time.
- Add manual sessions by date range.
- Add sessions by duration (e.g. `30 minutes`, `2h`).
- Attach one or more tags (e.g. `ABC-123` JIRA ticket references).
- Store raw session data as JSON with stable short UUID session IDs.
- Generate project reports with optional project/tag filters.
- Export session data to JSON, CSV, or XML.

## Usage

Once installed:

```bash
track <command> [options]
```

You can still run directly with Python during development:

```bash
python track.py <command> [options]
```

### Start / Stop a timer

```bash
track start --project myproject --tag ABC-123
track start --project "My Project" --tag "ABC_123"   # normalized to my-project / abc-123
track status
track stop
```

### Add by explicit date range

```bash
track add \
  --from "2018-03-20 12:00:00" \
  --to "2018-03-20 13:00:00" \
  --project myproject \
  --tag ABC-123 \
  --note "Standup meeting"
```

### Add by duration (retroactive)

```bash
track add --time "30 minutes" --project myproject --tag ABC-123
track add --time "15 minutes" --project myproject --note "Standup meeting"
```

This logs a session ending now and starting 30 minutes earlier.

### Name normalization and typo safety

- Project and tag names are normalized to lowercase kebab-case (`my project` -> `my-project`, `ABC_123` -> `abc-123`).
- Allowed characters after normalization are letters, numbers, and hyphens.
- If a new project/tag looks very close to an existing one, `track` blocks it and suggests the closest match.
- Use `--force-new-project` and/or `--force-new-tag` with `start`/`add` to intentionally create a close-but-new name.

### Reports

```bash
track report
track report --project myproject
track report --project myproject --tag ABC-123
track report --from 2014-04-01 --to 2014-04-30
track report --exact
```

Reports include the overall start/end datetime of the displayed data set.
By default, durations are rounded to the nearest 15-minute interval (midpoint `:07:30` rounds up) and displayed as `HH:MM`.
Use `--exact` to show unrounded durations as `HH:MM:SS`.

### Sessions

```bash
track sessions
track sessions --project myproject
track sessions --tag ABC-123
```

The sessions list shows the session ID, project, tags, start/end datetime, duration (`HH:MM:SS`), and note.

### Export

```bash
track export --output exports/report.json            # defaults to json
track export --format csv --output exports/report.csv
track export --format xml --output exports/report.xml
```

To print export data directly to your terminal, omit `--output`:

```bash
track export --format json
```

You can combine export filters:

```bash
track export --format csv --output exports/myproject.csv --project myproject --tag ABC-123
```

All export formats include the session `id` for each row/entry and `session_time` represented as decimal hours (for example: `0.25`, `0.5`, `0.75`, `1.25`).
`session_time` is always rounded to the nearest 15-minute interval using a 7m30s midpoint.

### Delete sessions

```bash
# delete an entire project and all its sessions
track delete --project myproject

# delete all sessions containing a tag
track delete --tag ABC-123

# delete one session by ID (from `track sessions`)
track delete --session a1b2c3d4
```

### Rename projects/tags

```bash
# rename a project everywhere
track rename --project oldproject --to newproject

# rename a tag everywhere
track rename --tag ABC-123 --to ABC-124

# rename a tag in one specific session
track rename --tag ABC-123 --to ABC-124 --session a1b2c3d4
```

## Data storage

By default, data is stored in:

- `~/.track/data.json`

Override location with environment variable:

```bash
TRACK_DATA_FILE=/tmp/track-data.json track report
```
