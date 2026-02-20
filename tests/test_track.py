from datetime import timedelta
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


if __name__ == "__main__":
    unittest.main()
