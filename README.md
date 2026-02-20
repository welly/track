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
track stop
```

### Add by explicit date range

```bash
track add \
  --from "2018-03-20 12:00:00" \
  --to "2018-03-20 13:00:00" \
  --project myproject \
  --tag ABC-123
```

### Add by duration (retroactive)

```bash
track add --time "30 minutes" --project myproject --tag ABC-123
```

This logs a session ending now and starting 30 minutes earlier.

### Reports

```bash
track report
track report --project myproject
track report --project myproject --tag ABC-123
track report --from 2014-04-01 --to 2014-04-30
```

Reports include the overall start/end datetime of the displayed data set.

### Sessions

```bash
track sessions
track sessions --project myproject
track sessions --tag ABC-123
```

The sessions list shows the session ID, project, tags, start/end datetime, and duration (`HH:MM:SS`).

### Export

```bash
track export --format csv --output exports/report.csv
track export --format json --output exports/report.json
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

All export formats include the session `id` for each row/entry.

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
