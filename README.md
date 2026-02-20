# track - Python Time Tracker CLI

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
- Store raw session data as JSON.
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
```

### Export

```bash
track export --format csv --output exports/report.csv
track export --format json --output exports/report.json
track export --format xml --output exports/report.xml
```

You can combine export filters:

```bash
track export --format csv --output exports/myproject.csv --project myproject --tag ABC-123
```

## Data storage

By default, data is stored in:

- `~/.track/data.json`

Override location with environment variable:

```bash
TRACK_DATA_FILE=/tmp/track-data.json track report
```
