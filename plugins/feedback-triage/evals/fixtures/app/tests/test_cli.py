import io
import unittest
from datetime import datetime, timezone

from tasklite import cli
from tasklite.dates import parse_due


class CliTest(unittest.TestCase):
    def test_add_and_list(self):
        tasks = []
        cli.add(tasks, "write report")
        cli.add(tasks, "ship it")
        self.assertEqual(cli.list_lines(tasks), ["[ ] 1: write report", "[ ] 2: ship it"])

    def test_done_hides_task(self):
        tasks = []
        cli.add(tasks, "a")
        cli.mark_done(tasks, 1)
        self.assertEqual(cli.list_lines(tasks), [])

    def test_export_header(self):
        out = io.StringIO()
        cli.export_csv([], out)
        self.assertTrue(out.getvalue().startswith("id,title,done,due"))

    def test_parse_due_date(self):
        self.assertEqual(parse_due("2026-03-01"), "2026-03-01")
        now = datetime(2026, 3, 1, 12, tzinfo=timezone.utc)
        self.assertEqual(parse_due("tomorrow", now), "2026-03-02")


if __name__ == "__main__":
    unittest.main()
