from contextlib import redirect_stdout
from datetime import datetime, timedelta
from io import StringIO
import json
import os
import re
import tempfile
import unittest

import track


class TrackTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.data_file = os.path.join(self.tmp.name, "data.json")
        os.environ["TRACK_DATA_FILE"] = self.data_file

    def tearDown(self) -> None:
        self.tmp.cleanup()
        os.environ.pop("TRACK_DATA_FILE", None)

    def _add(self, start: str, end: str, project: str, tag: str | None = None) -> None:
        cmd = ["add", "--from", start, "--to", end, "--project", project]
        if tag:
            cmd += ["--tag", tag]
        self.assertEqual(track.main(cmd), 0)

    def _session_ids(self) -> list[str]:
        with open(self.data_file, "r", encoding="utf-8") as fh:
            payload = json.load(fh)
        return [entry["id"] for entry in payload.get("sessions", [])]

    def test_parse_duration_minutes(self):
        self.assertEqual(track.parse_duration("30 minutes"), timedelta(minutes=30))

    def test_parse_duration_hours_short(self):
        self.assertEqual(track.parse_duration("1.5h"), timedelta(hours=1.5))

    def test_status_no_active_timer(self):
        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["status"]), 0)
        self.assertIn("No active timer.", stdout.getvalue())

    def test_status_active_timer(self):
        start = datetime.now() - timedelta(minutes=5, seconds=12)
        payload = {"active": {"project": "myproject", "tags": ["ABC-123"], "start": start.isoformat()}, "sessions": []}
        with open(self.data_file, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["status"]), 0)

        out = stdout.getvalue()
        self.assertRegex(
            out,
            r"Project myproject \(ABC-123\) started \d+ minutes ago "
            r"\(\d{4}-\d{2}-\d{2} at \d{2}:\d{2}:\d{2}\)\n",
        )

    def test_status_active_timer_untagged(self):
        start = datetime.now() - timedelta(minutes=2)
        payload = {"active": {"project": "myproject", "tags": [], "start": start.isoformat()}, "sessions": []}
        with open(self.data_file, "w", encoding="utf-8") as fh:
            json.dump(payload, fh)

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["status"]), 0)
        self.assertIn("Project myproject (untagged)", stdout.getvalue())

    def test_no_command_prints_help(self):
        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main([]), 0)
        out = stdout.getvalue()
        self.assertIn("usage: track", out)
        self.assertIn("start", out)
        self.assertIn("status", out)
        self.assertIn("sessions", out)

    def test_report_breakdown_and_date_range(self):
        self._add("2018-03-20 12:00:00", "2018-03-20 13:00:00", "myproject", "ABC-123")
        self._add("2018-03-20 13:00:00", "2018-03-20 13:30:00", "myproject", "ABC-456")
        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["report", "--project", "myproject"]), 0)

        out = stdout.getvalue()
        self.assertIn("Date range: 2018-03-20 12:00:00 -> 2018-03-20 13:30:00", out)
        self.assertIn("- ABC-123", out)
        self.assertIn("- ABC-456", out)
        self.assertIn("Project total:", out)
        self.assertIn("01:30", out)

    def test_report_date_filter(self):
        self._add("2014-04-05 09:00:00", "2014-04-05 10:00:00", "alpha", "A-1")
        self._add("2014-05-05 09:00:00", "2014-05-05 10:00:00", "beta", "B-1")

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["report", "--from", "2014-04-01", "--to", "2014-04-30"]), 0)

        out = stdout.getvalue()
        self.assertIn("alpha", out)
        self.assertNotIn("beta", out)

    def test_export_stdout_json_and_csv(self):
        self._add("2018-03-20 12:00:00", "2018-03-20 13:00:00", "myproject", "ABC-123")

        stdout_json_default = StringIO()
        with redirect_stdout(stdout_json_default):
            self.assertEqual(track.main(["export"]), 0)
        self.assertIn('"session_time": 1.0', stdout_json_default.getvalue())

        stdout_json = StringIO()
        with redirect_stdout(stdout_json):
            self.assertEqual(track.main(["export", "--format", "json"]), 0)
        data = json.loads(stdout_json.getvalue())
        self.assertEqual(len(data), 1)
        self.assertRegex(data[0]["id"], r"^[0-9a-f]{8}$")
        self.assertEqual(data[0]["session_time"], 1.0)

        stdout_csv = StringIO()
        with redirect_stdout(stdout_csv):
            self.assertEqual(track.main(["export", "--format", "csv"]), 0)
        self.assertIn("id,project,tags,note,start,end,session_time", stdout_csv.getvalue())

        stdout_xml = StringIO()
        with redirect_stdout(stdout_xml):
            self.assertEqual(track.main(["export", "--format", "xml"]), 0)
        self.assertRegex(stdout_xml.getvalue(), r"<id>[0-9a-f]{8}</id>")
        self.assertRegex(stdout_xml.getvalue(), r"<session_time>\d+(?:\.\d+)?</session_time>")

    def test_add_note_saved_in_sessions_and_export(self):
        self.assertEqual(
            track.main(["add", "--project", "myproject", "--time", "15 minutes", "--note", "Standup meeting"]),
            0,
        )

        sessions_out = StringIO()
        with redirect_stdout(sessions_out):
            self.assertEqual(track.main(["sessions", "--project", "myproject"]), 0)
        self.assertIn("Standup meeting", sessions_out.getvalue())

        export_out = StringIO()
        with redirect_stdout(export_out):
            self.assertEqual(track.main(["export"]), 0)
        exported = json.loads(export_out.getvalue())
        self.assertEqual(exported[0]["note"], "Standup meeting")

    def test_report_rounding_nearest_and_exact(self):
        self._add("2018-03-20 12:00:00", "2018-03-20 13:34:19", "myproject", "ABC-123")

        stdout_rounded = StringIO()
        with redirect_stdout(stdout_rounded):
            self.assertEqual(track.main(["report", "--project", "myproject"]), 0)
        self.assertIn("01:30", stdout_rounded.getvalue())

        stdout_exact = StringIO()
        with redirect_stdout(stdout_exact):
            self.assertEqual(track.main(["report", "--project", "myproject", "--exact"]), 0)
        self.assertIn("01:34:19", stdout_exact.getvalue())

    def test_export_rounding_nearest(self):
        self._add("2018-03-20 12:00:00", "2018-03-20 13:48:00", "myproject", "ABC-123")

        stdout_json = StringIO()
        with redirect_stdout(stdout_json):
            self.assertEqual(track.main(["export", "--format", "json"]), 0)
        data = json.loads(stdout_json.getvalue())
        self.assertEqual(data[0]["session_time"], 1.75)

    def test_delete_project(self):
        self._add("2018-03-20 12:00:00", "2018-03-20 13:00:00", "proj-a", "A")
        self._add("2018-03-20 13:00:00", "2018-03-20 14:00:00", "proj-b", "B")
        self.assertEqual(track.main(["delete", "--project", "proj-a"]), 0)

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["report"]), 0)
        self.assertNotIn("proj-a", stdout.getvalue())
        self.assertIn("proj-b", stdout.getvalue())

    def test_delete_by_tag_and_session_id(self):
        self._add("2018-03-20 12:00:00", "2018-03-20 13:00:00", "p", "T1")
        self._add("2018-03-20 13:00:00", "2018-03-20 14:00:00", "p", "T2")
        session_ids = self._session_ids()
        self.assertEqual(track.main(["delete", "--tag", "T1"]), 0)
        self.assertEqual(track.main(["delete", "--session", session_ids[1]]), 0)

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["report"]), 0)
        self.assertIn("No sessions found.", stdout.getvalue())

    def test_rename_project_and_tag(self):
        self._add("2018-03-20 12:00:00", "2018-03-20 13:00:00", "old-project", "OLD-TAG")
        self._add("2018-03-20 13:00:00", "2018-03-20 14:00:00", "old-project", "OLD-TAG")
        session_ids = self._session_ids()

        self.assertEqual(track.main(["rename", "--project", "old-project", "--to", "new-project"]), 0)
        self.assertEqual(track.main(["rename", "--tag", "OLD-TAG", "--to", "NEW-TAG", "--session", session_ids[0]]), 0)

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["report", "--project", "new-project"]), 0)
        out = stdout.getvalue()
        self.assertIn("NEW-TAG", out)
        self.assertIn("OLD-TAG", out)

    def test_sessions_list_and_filters(self):
        self._add("2018-03-20 12:00:00", "2018-03-20 13:00:00", "alpha", "A-1")
        self._add("2018-03-20 13:00:00", "2018-03-20 14:30:00", "beta", "B-1")

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["sessions"]), 0)
        out = stdout.getvalue()
        self.assertIn("Sessions", out)
        self.assertIn("alpha", out)
        self.assertIn("beta", out)
        self.assertIn("01:30:00", out)
        for sid in self._session_ids():
            self.assertRegex(sid, r"^[0-9a-f]{8}$")
            self.assertIn(sid, out)

        stdout_project = StringIO()
        with redirect_stdout(stdout_project):
            self.assertEqual(track.main(["sessions", "--project", "alpha"]), 0)
        self.assertIn("alpha", stdout_project.getvalue())
        self.assertNotIn("beta", stdout_project.getvalue())

        stdout_tag = StringIO()
        with redirect_stdout(stdout_tag):
            self.assertEqual(track.main(["sessions", "--tag", "B-1"]), 0)
        self.assertIn("beta", stdout_tag.getvalue())
        self.assertNotIn("alpha", stdout_tag.getvalue())


if __name__ == "__main__":
    unittest.main()
