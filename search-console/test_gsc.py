import argparse
from datetime import date
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import Mock, patch

import gsc


def metric(keys=()):
    return {"keys": list(keys), "clicks": 2, "impressions": 20, "ctr": .1, "position": 4.5}


def inspection(verdict="PASS", canonical="https://500nits.com/", **fields):
    return {"inspectionResult": {"indexStatusResult": {
        "verdict": verdict, "googleCanonical": canonical, "coverageState": "Example status", **fields}}}


class SearchConsoleTests(unittest.TestCase):
    def test_scope_rejects_similar_domains_and_credentials(self):
        for url in ["https://evil500nits.com/", "https://500nits.com.example.net/", "file:///tmp/x", "https://user@500nits.com/", "https://500nits.com:8443/"]:
            with self.assertRaises(gsc.Error):
                gsc.scoped_url(url)
        self.assertEqual(gsc.scoped_url("https://task.500nits.com/privacy/"), "https://task.500nits.com/privacy/")

    def test_indexed_requires_matching_google_canonical(self):
        url = "https://500nits.com/"
        self.assertEqual(gsc.diagnose(url, inspection())["state"], "indexed")
        self.assertEqual(gsc.diagnose(url, inspection(canonical="https://www.500nits.com/"))["state"], "different_canonical")
        self.assertEqual(gsc.diagnose(url, inspection(canonical=None))["state"], "not_confirmed")
        self.assertEqual(gsc.diagnose(url, inspection(verdict="NEUTRAL"))["state"], "not_confirmed")

    def test_noindex_and_fetch_findings_do_not_instruct_blind_removal(self):
        d = gsc.diagnose("https://500nits.com/", inspection(verdict="NEUTRAL", indexingState="BLOCKED_BY_META_TAG", pageFetchState="NOT_FOUND"))
        self.assertIn("only if indexability is intended", " ".join(d["next_checks"]))
        self.assertIn("NOT_FOUND", " ".join(d["next_checks"]))

    def test_pagination_and_exact_hostname_filter(self):
        api = gsc.API.__new__(gsc.API)
        calls = []
        def request(endpoint, body):
            calls.append(json.loads(json.dumps(body)))
            return {"rows": [metric(["query"])]*25000 if body["startRow"] == 0 else [metric(["last"])]}
        api.request = request
        result = api.analytics(date(2026, 9, 1), date(2026, 9, 28), ["query"], "task.500nits.com")
        self.assertEqual(len(result["rows"]), 25001)
        self.assertEqual([b["startRow"] for b in calls], [0, 25000])
        self.assertFalse(result["row_cap_reached"])
        pattern = calls[0]["dimensionFilterGroups"][0]["filters"][0]["expression"]
        self.assertIsNotNone(re.match(pattern, "https://task.500nits.com/"))
        self.assertIsNone(re.match(pattern, "https://task.500nits.com.evil.net/"))
        self.assertIsNone(re.match(pattern, "https://othertask.500nits.com/"))
        self.assertEqual(calls[0]["dataState"], "final")

    def test_saturation_is_explicit(self):
        api = gsc.API.__new__(gsc.API)
        api.request = Mock(return_value={"rows": [metric()]})
        self.assertTrue(api.analytics("2026-09-01", "2026-09-02", max_rows=1)["row_cap_reached"])

    def test_no_impressions_does_not_imply_position_zero(self):
        report = {"generated_at": "2026-10-31", "status": "ok", "window": {"start": "2026-10-01", "end": "2026-10-28"},
                  "hosts": {"500nits.com": {"totals": {"rows": [{"clicks": 0, "impressions": 0, "ctr": 0, "position": 0}]}}}}
        self.assertIn("| 500nits.com | 0 | 0 | — | — |", gsc.markdown(report))

    def test_partial_export_never_calls_an_unavailable_url_indexed(self):
        api = Mock()
        api.request.return_value = {"siteUrl": gsc.PROPERTY}
        api.inspect.side_effect = gsc.Error("Unavailable")
        args = argparse.Namespace(command="inspect", urls=["https://500nits.com/"], inspection_limit=200)
        known = {"urls": args.urls, "hosts": ["500nits.com"], "expected_sitemaps": [], "warnings": []}
        with patch.object(gsc, "inventory", return_value=known), patch.object(gsc.time, "sleep"):
            result = gsc.collect(api, args)
        self.assertEqual(result["status"], "partial")
        self.assertEqual(result["inspections"][args.urls[0]], {"status": "unavailable"})
        self.assertIn("unavailable", gsc.markdown(result))

    def test_endpoint_allowlist_excludes_remote_writes(self):
        api = gsc.API.__new__(gsc.API)
        api.session = Mock()
        with self.assertRaises(gsc.Error):
            api.request(gsc.BASE + "/sitemaps/sitemap.xml", {})
        with self.assertRaises(gsc.Error):
            api.request(gsc.BASE, {})
        api.session.request.assert_not_called()

    def test_credential_location_and_private_output(self):
        with self.assertRaises(gsc.Error):
            gsc.credential_path(gsc.ROOT / "token.json")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "report.json"
            gsc.save(path, '{"status":"ok"}')
            self.assertEqual(path.stat().st_mode & 0o777, 0o600)
            gsc.save(path, '{"status":"partial"}')
            self.assertEqual(json.loads(path.read_text())["status"], "partial")


if __name__ == "__main__":
    unittest.main()
