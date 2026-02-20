from datetime import timedelta
from io import StringIO
from contextlib import redirect_stdout
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

    def test_parse_duration_minutes(self):
        self.assertEqual(track.parse_duration("30 minutes"), timedelta(minutes=30))

    def test_parse_duration_hours_short(self):
        self.assertEqual(track.parse_duration("1.5h"), timedelta(hours=1.5))

    def test_add_and_report(self):
        rc = track.main([
            "add",
            "--from",
            "2018-03-20 12:00:00",
            "--to",
            "2018-03-20 13:00:00",
            "--project",
            "myproject",
            "--tag",
            "ABC-123",
        ])
        self.assertEqual(rc, 0)

        rc = track.main(["report", "--project", "myproject", "--tag", "ABC-123"])
        self.assertEqual(rc, 0)

    def test_report_breaks_down_tags_and_project_total(self):
        self.assertEqual(
            track.main([
                "add",
                "--from",
                "2018-03-20 12:00:00",
                "--to",
                "2018-03-20 13:00:00",
                "--project",
                "myproject",
                "--tag",
                "ABC-123",
            ]),
            0,
        )
        self.assertEqual(
            track.main([
                "add",
                "--from",
                "2018-03-20 13:00:00",
                "--to",
                "2018-03-20 13:30:00",
                "--project",
                "myproject",
                "--tag",
                "ABC-456",
            ]),
            0,
        )

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["report", "--project", "myproject"]), 0)

        report_output = stdout.getvalue()
        self.assertIn("- ABC-123", report_output)
        self.assertIn("- ABC-456", report_output)
        self.assertIn("Project total:", report_output)
        self.assertIn("01:30:00", report_output)

    def test_export_to_stdout_when_output_omitted_json(self):
        self.assertEqual(
            track.main([
                "add",
                "--from",
                "2018-03-20 12:00:00",
                "--to",
                "2018-03-20 13:00:00",
                "--project",
                "myproject",
                "--tag",
                "ABC-123",
            ]),
            0,
        )

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["export", "--format", "json"]), 0)

        export_output = stdout.getvalue()
        self.assertIn('"project": "myproject"', export_output)
        self.assertIn('"tags": [', export_output)

    def test_export_to_stdout_when_output_omitted_csv(self):
        self.assertEqual(
            track.main([
                "add",
                "--from",
                "2018-03-20 12:00:00",
                "--to",
                "2018-03-20 13:00:00",
                "--project",
                "myproject",
                "--tag",
                "ABC-123",
            ]),
            0,
        )

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["export", "--format", "csv"]), 0)

        export_output = stdout.getvalue()
        self.assertIn("project,tags,start,end,duration_seconds", export_output)
        self.assertIn("myproject,ABC-123", export_output)

    def test_report_shows_start_and_end_date_range(self):
        self.assertEqual(
            track.main([
                "add",
                "--from",
                "2018-03-20 12:00:00",
                "--to",
                "2018-03-20 13:00:00",
                "--project",
                "myproject",
                "--tag",
                "ABC-123",
            ]),
            0,
        )

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(track.main(["report"]), 0)

        report_output = stdout.getvalue()
        self.assertIn("Date range: 2018-03-20 12:00:00 -> 2018-03-20 13:00:00", report_output)

    def test_report_can_filter_by_date_range(self):
        self.assertEqual(
            track.main([
                "add",
                "--from",
                "2014-04-05 09:00:00",
                "--to",
                "2014-04-05 10:00:00",
                "--project",
                "alpha",
                "--tag",
                "A-1",
            ]),
            0,
        )
        self.assertEqual(
            track.main([
                "add",
                "--from",
                "2014-05-05 09:00:00",
                "--to",
                "2014-05-05 10:00:00",
                "--project",
                "beta",
                "--tag",
                "B-1",
            ]),
            0,
        )

        stdout = StringIO()
        with redirect_stdout(stdout):
            self.assertEqual(
                track.main(["report", "--from", "2014-04-01", "--to", "2014-04-30"]),
                0,
            )

        report_output = stdout.getvalue()
        self.assertIn("alpha", report_output)
        self.assertNotIn("beta", report_output)


if __name__ == "__main__":
    unittest.main()
