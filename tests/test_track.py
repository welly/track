from contextlib import redirect_stdout
from datetime import timedelta
from io import StringIO
import os
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

    def test_parse_duration_minutes(self):
        self.assertEqual(track.parse_duration("30 minutes"), timedelta(minutes=30))

    def test_parse_duration_hours_short(self):
        self.assertEqual(track.parse_duration("1.5h"), timedelta(hours=1.5))

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
        self.assertIn("01:30:00", out)

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

        stdout_json = StringIO()
        with redirect_stdout(stdout_json):
            self.assertEqual(track.main(["export", "--format", "json"]), 0)
        self.assertIn('"id": 1', stdout_json.getvalue())

        stdout_csv = StringIO()
        with redirect_stdout(stdout_csv):
            self.assertEqual(track.main(["export", "--format", "csv"]), 0)
        self.assertIn("id,project,tags,start,end,duration_seconds", stdout_csv.getvalue())

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
        self.assertEqual(track.main(["delete", "--tag", "T1"]), 0)
        self.assertEqual(track.main(["delete", "--session", "2"]), 0)

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["report"]), 0)
        self.assertIn("No sessions found.", stdout.getvalue())

    def test_rename_project_and_tag(self):
        self._add("2018-03-20 12:00:00", "2018-03-20 13:00:00", "old-project", "OLD-TAG")
        self._add("2018-03-20 13:00:00", "2018-03-20 14:00:00", "old-project", "OLD-TAG")

        self.assertEqual(track.main(["rename", "--project", "old-project", "--to", "new-project"]), 0)
        self.assertEqual(track.main(["rename", "--tag", "OLD-TAG", "--to", "NEW-TAG", "--session", "1"]), 0)

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["report", "--project", "new-project"]), 0)
        out = stdout.getvalue()
        self.assertIn("NEW-TAG", out)
        self.assertIn("OLD-TAG", out)


if __name__ == "__main__":
    unittest.main()
