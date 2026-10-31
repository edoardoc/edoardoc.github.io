"""Run with the report virtualenv: python -m unittest discover -s cloudflare -p 'test_*.py'."""

from contextlib import redirect_stderr, redirect_stdout
from datetime import datetime, timezone
import fcntl
from io import StringIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from export import ExportError
import human_report as report


def data():
    return {"totals": [{"count": 12, "sum": {"visits": 7}}],
            "hourly": [{"count": 12, "sum": {"visits": 7}, "dimensions": {"datetimeHour": "2026-10-30T11:00:00Z"}}],
            "sites": [{"count": 12, "sum": {"visits": 7}, "dimensions": {"requestHost": "500nits.com"}}],
            "pages": [{"count": 12, "sum": {"visits": 7}, "dimensions": {"requestHost": "500nits.com", "requestPath": "/"}}],
            "countries": [{"count": 12, "sum": {"visits": 7}, "dimensions": {"countryName": "GR"}}],
            "collection": [{"count": 20}]}


class HumanReportTests(unittest.TestCase):
    def setUp(self):
        self.start, self.end = report.reporting_day("2026-10-30", datetime(2026, 10, 31, 12, tzinfo=timezone.utc))

    def test_calendar_windows_do_not_overlap(self):
        start, end = report.reporting_day(now=datetime(2026, 10, 31, 23, tzinfo=timezone.utc))
        self.assertEqual((start, end), (self.start, self.end))
        self.assertEqual((end-start).total_seconds(), 86400)
        for bad in ["2026-10-31", "2026-02-30", "20261030"]:
            with self.assertRaises(ExportError):
                report.reporting_day(bad, datetime(2026, 10, 31, tzinfo=timezone.utc))

    def test_every_report_metric_excludes_bots_and_scopes_the_domain(self):
        query = report.build_query("account", ["site"], self.start, self.end)
        self.assertTrue(query.startswith("query "))
        self.assertNotIn("mutation", query)
        self.assertNotIn("userAgent", query)
        for alias in ["totals", "hourly", "sites", "pages", "countries"]:
            filtered = query.split(alias + ": ", 1)[1].split("})", 1)[0]
            self.assertIn("bot: 0", filtered)
            self.assertIn('siteTag_in: ["site"]', filtered)
            self.assertIn('requestHost: "500nits.com"', filtered)
            self.assertIn('requestHost_like: "%.500nits.com"', filtered)
            self.assertIn("datetime_lt:", filtered)

    def test_similar_domains_are_not_accepted(self):
        self.assertFalse(report.belongs_to_domain("evil500nits.com"))
        self.assertFalse(report.belongs_to_domain("500nits.com.example.org"))
        self.assertTrue(report.belongs_to_domain("task.500nits.com"))
        with self.assertRaises(ExportError):
            report.site_tags([{"site_tag": "bad", "rules": [{"host": "evil500nits.com"}]}], "zone")

    def test_no_collection_is_not_reported_as_zero(self):
        api = Mock()
        api.listing.side_effect = [[{"name": "500nits.com", "id": "zone", "account": {"id": "account"}}],
                                   [{"site_tag": "site", "ruleset": {"zone_tag": "zone", "enabled": True}}]]
        empty = {key: [] for key in data()}
        with patch.object(report, "query_account", return_value=empty):
            self.assertEqual(report.collect(api, self.start, self.end)["status"], "no_data")

    def test_measured_day_with_no_non_bot_activity_can_be_zero(self):
        api = Mock()
        api.listing.side_effect = [[{"name": "500nits.com", "id": "zone", "account": {"id": "account"}}],
                                   [{"site_tag": "site", "ruleset": {"zone_tag": "zone"}}]]
        empty = {key: [] for key in data()}; empty["collection"] = [{"count": 20}]
        with patch.object(report, "query_account", return_value=empty):
            result = report.collect(api, self.start, self.end)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["data"]["totals"][0]["sum"]["visits"], 0)

    def test_graphql_partial_error_is_not_accepted(self):
        api = Mock(token="secret")
        api.read_response.return_value = json.dumps({"data": {"viewer": {"accounts": [data()]}},
                                                    "errors": [{"message": "secret account denied"}]})
        with self.assertRaises(ExportError) as error:
            report.query_account(api, "account", "query Fixed { viewer { __typename } }")
        self.assertNotIn("secret", str(error.exception))
        self.assertNotIn("account denied", str(error.exception))

    def test_retry_overwrites_stale_pdf_with_unavailable_and_nonzero_exit(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory)/"report.pdf"
            payload = data(); payload.pop("collection")
            with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
                with patch.object(report, "collect", return_value={"status": "ok", "data": payload}):
                    self.assertEqual(report.run(Mock(), "2026-10-30", pdf), 0)
                self.assertTrue(pdf.read_bytes().startswith(b"%PDF"))
                with patch.object(report, "collect", side_effect=ExportError("Access denied")):
                    self.assertEqual(report.run(Mock(), "2026-10-30", pdf), 2)
            saved = json.loads(pdf.with_suffix(".json").read_text())
            self.assertEqual(saved["status"], "unavailable")
            self.assertNotIn("data", saved)
            self.assertEqual(pdf.stat().st_mode & 0o777, 0o600)
            self.assertEqual(pdf.with_suffix(".json").stat().st_mode & 0o777, 0o600)

    def test_lock_prevents_concurrent_runs(self):
        with tempfile.TemporaryDirectory() as directory:
            pdf = Path(directory)/"report.pdf"
            with pdf.with_suffix(".lock").open("a") as lock:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                with self.assertRaises(ExportError), patch.object(report, "collect") as collect:
                    report.run(Mock(), "2026-10-30", pdf)
                collect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
