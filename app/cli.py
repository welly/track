from __future__ import annotations

import argparse
import sys

from .commands import (
    cmd_add,
    cmd_delete,
    cmd_export,
    cmd_rename,
    cmd_report,
    cmd_sessions,
    cmd_start,
    cmd_stop,
)
from .errors import TrackError
from .storage import resolve_store


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="track", description="Simple time tracker CLI.")
    subparsers = parser.add_subparsers(dest="command", title="Available commands", metavar="")

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

    sessions = subparsers.add_parser("sessions", help="List sessions")
    sessions.add_argument("--project")
    sessions.add_argument("--tag")
    sessions.set_defaults(func=cmd_sessions)

    export = subparsers.add_parser("export", help="Export sessions")
    export.add_argument("--format", choices=["json", "csv", "xml"], required=True)
    export.add_argument("--output", help="Output file path; if omitted, write to stdout")
    export.add_argument("--project")
    export.add_argument("--tag")
    export.set_defaults(func=cmd_export)

    delete = subparsers.add_parser("delete", help="Delete sessions")
    delete.add_argument("--project", help="Delete all sessions for a project")
    delete.add_argument("--tag", help="Delete sessions containing a tag")
    delete.add_argument("--session", dest="session_id", help="Delete a single session by id")
    delete.set_defaults(func=cmd_delete)

    rename = subparsers.add_parser("rename", help="Rename a project or tag")
    rename.add_argument("--project", help="Old project name to rename")
    rename.add_argument("--tag", help="Old tag name to rename")
    rename.add_argument("--session", dest="session_id", help="Restrict tag rename to a specific session id")
    rename.add_argument("--to", required=True, help="New name")
    rename.set_defaults(func=cmd_rename)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not getattr(args, "command", None):
        parser.print_help()
        return 0

    store = resolve_store()

    try:
        args.func(args, store)
    except TrackError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0
