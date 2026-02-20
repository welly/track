from __future__ import annotations

import argparse
import csv
import io
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET

from .constants import DATETIME_FORMAT
from .errors import TrackError
from .filters import filter_sessions
from .models import Session
from .naming import normalize_name, suggest_close_match, validate_name
from .parsing import (
    fmt_duration,
    fmt_duration_minutes,
    parse_date,
    parse_datetime,
    parse_duration,
    round_duration_to_nearest_interval,
)
from .storage import Storage, load_sessions, next_session_id, save_sessions


def humanize_elapsed(delta: timedelta) -> str:
    total_seconds = max(0, int(delta.total_seconds()))
    if total_seconds < 60:
        return "less than a minute"

    total_minutes = total_seconds // 60
    if total_minutes == 1:
        return "a minute"
    if total_minutes < 60:
        return f"{total_minutes} minutes"

    total_hours = total_minutes // 60
    if total_hours == 1:
        return "an hour"
    if total_hours < 24:
        return f"{total_hours} hours"

    total_days = total_hours // 24
    if total_days == 1:
        return "a day"
    return f"{total_days} days"


def collect_known_names(sessions: list[Session], active: dict[str, Any] | None) -> tuple[set[str], set[str]]:
    known_projects: set[str] = set()
    known_tags: set[str] = set()

    for item in sessions:
        known_projects.add(normalize_name(item.project))
        for tag_name in item.tags:
            known_tags.add(normalize_name(tag_name))

    if isinstance(active, dict):
        project_value = active.get("project")
        if isinstance(project_value, str):
            known_projects.add(normalize_name(project_value))
        for tag_value in active.get("tags", []):
            if isinstance(tag_value, str):
                known_tags.add(normalize_name(tag_value))

    return {p for p in known_projects if p}, {t for t in known_tags if t}


def normalize_project_input(
    raw_project: str,
    known_projects: set[str],
    *,
    force_new_project: bool,
) -> str:
    project = normalize_name(raw_project)
    validate_name("project", project)
    if project not in known_projects:
        suggestion = suggest_close_match(project, known_projects)
        if suggestion and suggestion != project and not force_new_project:
            raise TrackError(
                f"Project '{project}' is close to existing project '{suggestion}'. "
                "Use --force-new-project to create it anyway."
            )
    return project


def normalize_tag_inputs(
    raw_tags: list[str],
    known_tags: set[str],
    *,
    force_new_tag: bool,
) -> list[str]:
    normalized_tags: list[str] = []
    for raw_tag in raw_tags:
        tag = normalize_name(raw_tag)
        validate_name("tag", tag)
        if tag not in known_tags:
            suggestion = suggest_close_match(tag, known_tags)
            if suggestion and suggestion != tag and not force_new_tag:
                raise TrackError(
                    f"Tag '{tag}' is close to existing tag '{suggestion}'. "
                    "Use --force-new-tag to create it anyway."
                )
        normalized_tags.append(tag)
    return normalized_tags


def cmd_start(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    if payload.get("active"):
        raise TrackError("A timer is already running. Stop it before starting a new one.")

    sessions, changed = load_sessions(payload)
    if changed:
        save_sessions(payload, sessions)

    known_projects, known_tags = collect_known_names(sessions, payload.get("active"))
    project = normalize_project_input(args.project, known_projects, force_new_project=args.force_new_project)
    tags = normalize_tag_inputs(args.tag or [], known_tags, force_new_tag=args.force_new_tag)

    payload["active"] = {
        "project": project,
        "tags": tags,
        "note": args.note,
        "start": datetime.now().isoformat(),
    }
    store.save(payload)
    print(f"Started timer for project '{args.project}'.")


def cmd_status(_: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    active = payload.get("active")
    if not active:
        print("No active timer.")
        return

    start_raw = active.get("start")
    if not isinstance(start_raw, str):
        raise TrackError("Active timer is missing a valid start time.")

    start = datetime.fromisoformat(start_raw)
    elapsed = datetime.now() - start
    if elapsed < timedelta():
        elapsed = timedelta()

    tags = active.get("tags")
    tag_text = ", ".join(tags) if isinstance(tags, list) and tags else "untagged"
    start_text = start.strftime("%Y-%m-%d at %H:%M:%S")
    print(
        f"Project {active.get('project', '(unknown)')} ({tag_text}) "
        f"started {humanize_elapsed(elapsed)} ago ({start_text})"
    )


def cmd_stop(_: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    active = payload.get("active")
    if not active:
        raise TrackError("No active timer to stop.")

    sessions, changed = load_sessions(payload)
    if changed:
        save_sessions(payload, sessions)

    session = Session(
        id=next_session_id(sessions),
        project=active["project"],
        tags=active.get("tags", []),
        note=active.get("note"),
        start=datetime.fromisoformat(active["start"]),
        end=datetime.now(),
    )
    if session.end <= session.start:
        raise TrackError("Stop time must be after start time.")

    sessions.append(session)
    save_sessions(payload, sessions)
    payload["active"] = None
    store.save(payload)
    minutes = session.duration.total_seconds() / 60
    print(f"Stopped timer for project '{session.project}' (session #{session.id}, {minutes:.2f} minutes).")


def cmd_add(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    sessions, changed = load_sessions(payload)
    if changed:
        save_sessions(payload, sessions)

    known_projects, known_tags = collect_known_names(sessions, payload.get("active"))
    project = normalize_project_input(args.project, known_projects, force_new_project=args.force_new_project)
    tags = normalize_tag_inputs(args.tag or [], known_tags, force_new_tag=args.force_new_tag)

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

    sessions.append(
        Session(
            id=next_session_id(sessions),
            project=project,
            tags=tags,
            note=args.note,
            start=start,
            end=end,
        )
    )
    save_sessions(payload, sessions)
    store.save(payload)
    created = sessions[-1]
    print(
        f"Added session #{created.id} for project '{project}' from {start.strftime(DATETIME_FORMAT)} "
        f"to {end.strftime(DATETIME_FORMAT)}."
    )


def cmd_report(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    sessions, changed = load_sessions(payload)
    if changed:
        save_sessions(payload, sessions)
        store.save(payload)

    sessions = filter_sessions(sessions, args.project, args.tag)

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
        duration = item.duration if args.exact else round_duration_to_nearest_interval(item.duration, interval_minutes=15)
        project_data = by_project.setdefault(item.project, {"__project_total__": timedelta()})
        project_data["__project_total__"] = project_data["__project_total__"] + duration

        tags = item.tags or ["(untagged)"]
        for tag_name in tags:
            project_data[tag_name] = project_data.get(tag_name, timedelta()) + duration

    earliest = min(item.start for item in sessions)
    latest = max(item.end for item in sessions)

    print("Project report")
    print(f"Date range: {earliest.strftime(DATETIME_FORMAT)} -> {latest.strftime(DATETIME_FORMAT)}")
    print("=" * 40)
    for project, project_data in sorted(by_project.items()):
        print(project)
        for tag_name, total in sorted((k, v) for k, v in project_data.items() if k != "__project_total__"):
            display = fmt_duration(total) if args.exact else fmt_duration_minutes(total)
            print(f"  - {tag_name:16} {display}")
        project_total_display = fmt_duration(project_data["__project_total__"]) if args.exact else fmt_duration_minutes(project_data["__project_total__"])
        print(f"  {'Project total:':18} {project_total_display}")
        print("-" * 40)

    grand_total = sum(
        (item.duration if args.exact else round_duration_to_nearest_interval(item.duration, interval_minutes=15) for item in sessions),
        timedelta(),
    )
    grand_total_display = fmt_duration(grand_total) if args.exact else fmt_duration_minutes(grand_total)
    print(f"{'GRAND TOTAL':20} {grand_total_display}")


def cmd_sessions(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    sessions, changed = load_sessions(payload)
    if changed:
        save_sessions(payload, sessions)
        store.save(payload)

    sessions = filter_sessions(sessions, args.project, args.tag)
    if not sessions:
        print("No sessions found.")
        return

    print("Sessions")
    print("=" * 80)
    for item in sorted(sessions, key=lambda s: (s.start, s.id)):
        tags = ", ".join(item.tags) if item.tags else "(untagged)"
        note = item.note or ""
        print(
            f"{item.id}  {item.project:16} {tags:20} "
            f"{item.start.strftime(DATETIME_FORMAT)} -> {item.end.strftime(DATETIME_FORMAT)} "
            f"{fmt_duration(item.duration)} {note}"
        )


def cmd_export(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    sessions, changed = load_sessions(payload)
    if changed:
        save_sessions(payload, sessions)
        store.save(payload)

    sessions = filter_sessions(sessions, args.project, args.tag)

    rendered: str
    if args.format == "json":
        data = []
        for item in sessions:
            rounded_duration = round_duration_to_nearest_interval(item.duration, interval_minutes=15)
            payload = item.to_dict()
            payload["session_time"] = round((rounded_duration.total_seconds() / 3600), 2)
            data.append(payload)
        rendered = json.dumps(data, indent=2)
    elif args.format == "csv":
        csv_buffer = io.StringIO()
        writer = csv.DictWriter(csv_buffer, fieldnames=["id", "project", "tags", "note", "start", "end", "session_time"])
        writer.writeheader()
        for item in sessions:
            rounded_duration = round_duration_to_nearest_interval(item.duration, interval_minutes=15)
            writer.writerow(
                {
                    "id": item.id,
                    "project": item.project,
                    "tags": ";".join(item.tags),
                    "note": item.note or "",
                    "start": item.start.isoformat(),
                    "end": item.end.isoformat(),
                    "session_time": round((rounded_duration.total_seconds() / 3600), 2),
                }
            )
        rendered = csv_buffer.getvalue()
    else:
        root = ET.Element("sessions")
        for item in sessions:
            rounded_duration = round_duration_to_nearest_interval(item.duration, interval_minutes=15)
            node = ET.SubElement(root, "session")
            ET.SubElement(node, "id").text = item.id
            ET.SubElement(node, "project").text = item.project
            ET.SubElement(node, "tags").text = ",".join(item.tags)
            ET.SubElement(node, "note").text = item.note or ""
            ET.SubElement(node, "start").text = item.start.isoformat()
            ET.SubElement(node, "end").text = item.end.isoformat()
            ET.SubElement(node, "session_time").text = str(round((rounded_duration.total_seconds() / 3600), 2))

        rendered = ET.tostring(root, encoding="unicode", xml_declaration=True)

    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(rendered, encoding="utf-8")
        print(f"Exported {len(sessions)} sessions to {output} ({args.format}).")
    else:
        print(rendered)


def cmd_delete(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    sessions, _ = load_sessions(payload)
    project_filter = normalize_name(args.project) if args.project else None
    tag_filter = normalize_name(args.tag) if args.tag else None

    if args.session_id is not None:
        remaining = [s for s in sessions if s.id != args.session_id]
        removed = len(sessions) - len(remaining)
        if removed == 0:
            raise TrackError(f"Session id {args.session_id} not found.")
    elif tag_filter:
        remaining = [
            s
            for s in sessions
            if not (
                any(normalize_name(session_tag) == tag_filter for session_tag in s.tags)
                and (project_filter is None or normalize_name(s.project) == project_filter)
            )
        ]
        removed = len(sessions) - len(remaining)
        if removed == 0:
            raise TrackError("No sessions matched the requested tag/project filter.")
    elif project_filter:
        remaining = [s for s in sessions if normalize_name(s.project) != project_filter]
        removed = len(sessions) - len(remaining)
        if removed == 0:
            raise TrackError(f"Project '{project_filter}' not found.")
    else:
        raise TrackError("Provide --project, --tag, or --session.")

    save_sessions(payload, remaining)
    store.save(payload)
    print(f"Deleted {removed} session(s).")


def cmd_rename(args: argparse.Namespace, store: Storage) -> None:
    payload = store.load()
    sessions, _ = load_sessions(payload)

    if bool(args.project) == bool(args.tag):
        raise TrackError("Provide exactly one of --project or --tag.")

    changed = 0
    if args.project:
        from_project = normalize_name(args.project)
        to_project = normalize_name(args.to)
        validate_name("project", to_project)
        for item in sessions:
            if normalize_name(item.project) == from_project:
                item.project = to_project
                changed += 1
        if changed == 0:
            raise TrackError(f"Project '{from_project}' not found.")
    else:
        from_tag = normalize_name(args.tag)
        to_tag = normalize_name(args.to)
        validate_name("tag", to_tag)
        if args.session_id is not None:
            target = next((s for s in sessions if s.id == args.session_id), None)
            if not target:
                raise TrackError(f"Session id {args.session_id} not found.")
            if not any(normalize_name(t) == from_tag for t in target.tags):
                raise TrackError(f"Tag '{from_tag}' not found in session id {args.session_id}.")
            target.tags = [to_tag if normalize_name(t) == from_tag else t for t in target.tags]
            changed = 1
        else:
            for item in sessions:
                if any(normalize_name(t) == from_tag for t in item.tags):
                    item.tags = [to_tag if normalize_name(t) == from_tag else t for t in item.tags]
                    changed += 1
            if changed == 0:
                raise TrackError(f"Tag '{from_tag}' not found.")

    save_sessions(payload, sessions)
    store.save(payload)
    print(f"Updated {changed} session(s).")
