#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class TrackError(Exception):
    pass


@dataclass
class Session:
    project: str
    tags: list[str]
    start: datetime
    end: datetime

    def to_dict(self) -> dict[str, Any]:
        return {
            "project": self.project,
            "tags": self.tags,
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Session":
        return cls(
            project=payload["project"],
            tags=list(payload.get("tags", [])),
            start=datetime.fromisoformat(payload["start"]),
            end=datetime.fromisoformat(payload["end"]),
        )

    @property
    def duration(self) -> timedelta:
        return self.end - self.start


class Storage:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"active": None, "sessions": []}
        with self.path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def save(self, payload: dict[str, Any]) -> None:
        with self.path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)


def parse_datetime(value: str) -> datetime:
    try:
        return datetime.strptime(value, DATETIME_FORMAT)
    except ValueError:
        try:
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise TrackError(
                f"Invalid datetime '{value}'. Use '{DATETIME_FORMAT}' or ISO-8601 format."
            ) from exc




def parse_date(value: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise TrackError(f"Invalid date '{value}'. Use 'YYYY-MM-DD'.") from exc

def parse_duration(value: str) -> timedelta:
    normalized = value.strip().lower()
    short_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*([mh])", normalized)
    if short_match:
        amount = float(short_match.group(1))
        unit = short_match.group(2)
        return timedelta(minutes=amount if unit == "m" else 0, hours=amount if unit == "h" else 0)

    word_match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(minute|minutes|hour|hours)", normalized)
    if not word_match:
        raise TrackError(
            "Invalid duration. Examples: '30 minutes', '1.5 hours', '45m', '2h'."
        )

    amount = float(word_match.group(1))
    unit = word_match.group(2)
    if unit.startswith("minute"):
        return timedelta(minutes=amount)
    return timedelta(hours=amount)


def resolve_store() -> Storage:
    env_path = os.getenv("TRACK_DATA_FILE")
    if env_path:
        return Storage(Path(env_path).expanduser())
    return Storage(Path.home() / ".track" / "data.json")


def get_sessions(payload: dict[str, Any]) -> list[Session]:
    return [Session.from_dict(item) for item in payload.get("sessions", [])]


def save_sessions(payload: dict[str, Any], sessions: list[Session]) -> None:
    payload["sessions"] = [item.to_dict() for item in sessions]


def cmd_start(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    if payload.get("active"):
        raise TrackError("A timer is already running. Stop it before starting a new one.")

    payload["active"] = {
        "project": args.project,
        "tags": args.tag or [],
        "start": datetime.now().isoformat(),
    }
    store.save(payload)
    print(f"Started timer for project '{args.project}'.")


def cmd_stop(_: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    active = payload.get("active")
    if not active:
        raise TrackError("No active timer to stop.")

    session = Session(
        project=active["project"],
        tags=active.get("tags", []),
        start=datetime.fromisoformat(active["start"]),
        end=datetime.now(),
    )
    if session.end <= session.start:
        raise TrackError("Stop time must be after start time.")

    sessions = get_sessions(payload)
    sessions.append(session)
    save_sessions(payload, sessions)
    payload["active"] = None
    store.save(payload)
    minutes = session.duration.total_seconds() / 60
    print(f"Stopped timer for project '{session.project}' ({minutes:.2f} minutes).")


def cmd_add(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()

    if args.time:
        delta = parse_duration(args.time)
        end = datetime.now()
        start = end - delta
    else:
        if not args.from_time or not args.to:
            raise TrackError("Provide both --from and --to when not using --time.")
        start = parse_datetime(args.from_time)
        end = parse_datetime(args.to)

    if end <= start:
        raise TrackError("End time must be after start time.")

    session = Session(project=args.project, tags=args.tag or [], start=start, end=end)
    sessions = get_sessions(payload)
    sessions.append(session)
    save_sessions(payload, sessions)
    store.save(payload)
    print(
        f"Added session for project '{args.project}' from {start.strftime(DATETIME_FORMAT)} "
        f"to {end.strftime(DATETIME_FORMAT)}."
    )


def filter_sessions(sessions: list[Session], project: str | None, tag: str | None) -> list[Session]:
    filtered = sessions
    if project:
        filtered = [item for item in filtered if item.project == project]
    if tag:
        filtered = [item for item in filtered if tag in item.tags]
    return filtered


def fmt_duration(delta: timedelta) -> str:
    total_seconds = int(delta.total_seconds())
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def cmd_report(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    sessions = filter_sessions(get_sessions(payload), args.project, args.tag)

    start_date = parse_date(args.from_date) if args.from_date else None
    end_date = parse_date(args.to_date) if args.to_date else None
    if start_date and end_date and start_date > end_date:
        raise TrackError("--from date must be on or before --to date.")

    if start_date:
        sessions = [item for item in sessions if item.start.date() >= start_date]
    if end_date:
        sessions = [item for item in sessions if item.start.date() <= end_date]

    if not sessions:
        print("No sessions found.")
        return

    by_project: dict[str, dict[str, timedelta]] = {}
    for item in sessions:
        project_data = by_project.setdefault(item.project, {"__project_total__": timedelta()})
        project_data["__project_total__"] = project_data["__project_total__"] + item.duration

        tags = item.tags or ["(untagged)"]
        for tag_name in tags:
            project_data[tag_name] = project_data.get(tag_name, timedelta()) + item.duration

    earliest = min(item.start for item in sessions)
    latest = max(item.end for item in sessions)

    print("Project report")
    print(f"Date range: {earliest.strftime(DATETIME_FORMAT)} -> {latest.strftime(DATETIME_FORMAT)}")
    print("=" * 40)
    for project, project_data in sorted(by_project.items()):
        print(f"{project}")
        for tag_name, total in sorted((k, v) for k, v in project_data.items() if k != "__project_total__"):
            print(f"  - {tag_name:16} {fmt_duration(total)}")
        print(f"  {'Project total:':18} {fmt_duration(project_data['__project_total__'])}")
        print("-" * 40)

    grand_total = sum((item.duration for item in sessions), timedelta())
    print(f"{'GRAND TOTAL':20} {fmt_duration(grand_total)}")


def cmd_export(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    sessions = filter_sessions(get_sessions(payload), args.project, args.tag)

    rendered: str
    if args.format == "json":
        data = [item.to_dict() for item in sessions]
        rendered = json.dumps(data, indent=2)
    elif args.format == "csv":
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=["project", "tags", "start", "end", "duration_seconds"])
        writer.writeheader()
        for item in sessions:
            writer.writerow(
                {
                    "project": item.project,
                    "tags": ";".join(item.tags),
                    "start": item.start.isoformat(),
                    "end": item.end.isoformat(),
                    "duration_seconds": int(item.duration.total_seconds()),
                }
            )
        rendered = csv_buffer.getvalue()
    else:
        root = ET.Element("sessions")
        for item in sessions:
            node = ET.SubElement(root, "session")
            ET.SubElement(node, "project").text = item.project
            ET.SubElement(node, "tags").text = ",".join(item.tags)
            ET.SubElement(node, "start").text = item.start.isoformat()
            ET.SubElement(node, "end").text = item.end.isoformat()
            ET.SubElement(node, "duration_seconds").text = str(int(item.duration.total_seconds()))

        rendered = ET.tostring(root, encoding="unicode", xml_declaration=True)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"Exported {len(sessions)} sessions to {output} ({args.format}).")
    else:
        print(rendered)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="track", description="Simple time tracker CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    start = subparsers.add_parser("start", help="Start a timer")
    start.add_argument("--project", required=True)
    start.add_argument("--tag", action="append", help="Tag for the entry; may be repeated")
    start.set_defaults(func=cmd_start)

    stop = subparsers.add_parser("stop", help="Stop the active timer")
    stop.set_defaults(func=cmd_stop)

    add = subparsers.add_parser("add", help="Add an entry by datetime range or duration")
    add.add_argument("--project", required=True)
    add.add_argument("--tag", action="append", help="Tag for the entry; may be repeated")
    add.add_argument("--from", dest="from_time", help="Start datetime")
    add.add_argument("--to", help="End datetime")
    add.add_argument("--time", help="Duration (for example: '30 minutes' or '2h')")
    add.set_defaults(func=cmd_add)

    report = subparsers.add_parser("report", help="Show time report")
    report.add_argument("--project")
    report.add_argument("--tag")
    report.add_argument("--from", dest="from_date", help="Filter report by start date (YYYY-MM-DD)")
    report.add_argument("--to", dest="to_date", help="Filter report by end date (YYYY-MM-DD)")
    report.set_defaults(func=cmd_report)

    export = subparsers.add_parser("export", help="Export sessions")
    export.add_argument("--format", choices=["json", "csv", "xml"], required=True)
    export.add_argument("--output", help="Output file path; if omitted, write to stdout")
    export.add_argument("--project")
    export.add_argument("--tag")
    export.set_defaults(func=cmd_export)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    store = resolve_store()

    try:
        args.func(args, store)
    except TrackError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
