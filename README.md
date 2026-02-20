# track - Python Time Tracker CLI

A lightweight CLI time tracker inspired by Watson.

## Features

- Start/stop live timers per project.
- Add manual sessions by date range.
- Add sessions by duration (e.g. `30 minutes`, `2h`).
- Attach one or more tags (e.g. `ABC-123` JIRA ticket references).
- Store raw session data as JSON.
- Generate project reports with optional project/tag filters.
- Export session data to JSON, CSV, or XML.

## Usage

All examples assume running with Python directly:

```bash
python track.py <command> [options]
```

### Start / Stop a timer

```bash
python track.py start --project myproject --tag ABC-123
python track.py stop
```

### Add by explicit date range

```bash
python track.py add \
  --from "2018-03-20 12:00:00" \
  --to "2018-03-20 13:00:00" \
  --project myproject \
  --tag ABC-123
```

### Add by duration (retroactive)

```bash
python track.py add --time "30 minutes" --project myproject --tag ABC-123
```

This logs a session ending now and starting 30 minutes earlier.

### Reports

```bash
python track.py report
python track.py report --project myproject
python track.py report --project myproject --tag ABC-123
```

### Export

```bash
python track.py export --format csv --output exports/report.csv
python track.py export --format json --output exports/report.json
python track.py export --format xml --output exports/report.xml
```

You can combine export filters:

```bash
python track.py export --format csv --output exports/myproject.csv --project myproject --tag ABC-123
```

## Data storage

By default, data is stored in:

- `~/.timetracker/data.json`

Override location with environment variable:

```bash
TRACK_DATA_FILE=/tmp/track-data.json python track.py report
```
