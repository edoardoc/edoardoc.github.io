"""Read-only Search Console operations for sc-domain:500nits.com."""

import argparse
from datetime import date, datetime, timedelta, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import time
from urllib.parse import quote, urlsplit
import xml.etree.ElementTree as ET
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / ".search-console-local"
CREDENTIALS = Path.home() / ".config/500nits/search-console"
PROPERTY = "sc-domain:500nits.com"
SCOPE = "https://www.googleapis.com/auth/webmasters.readonly"
BASE = "https://www.googleapis.com/webmasters/v3/sites/" + quote(PROPERTY, safe="")
INSPECT = "https://searchconsole.googleapis.com/v1/urlInspection/index:inspect"
LIMITATIONS = [
    "Indexing results describe Google's stored index, not a live URL test. A submitted sitemap is not proof of indexing.",
    "Inspection coverage is the explicit URL set, not every URL Google knows. Local sitemaps express intended URLs and may include undeployed changes.",
    "Search Analytics dates use America/Los_Angeles. Only final data is requested; recent days can be missing.",
    "Query rows omit anonymized searches and may not sum to totals. Google returns top rows and does not guarantee an exhaustive export.",
    "Host-filtered metrics use page aggregation; domain totals use property aggregation. They need not add up. Position is an average, not a fixed ranking.",
    "No sitemap submission, indexing request, DNS change, or automatic SEO edit is performed.",
]


class Error(Exception):
    pass


def save(path, content):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if not isinstance(content, bytes):
        content = content.encode()
    with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as f:
        tmp = Path(f.name)
        try:
            f.write(content); f.flush(); os.fsync(f.fileno())
        except BaseException:
            tmp.unlink(missing_ok=True)
            raise
    try:
        tmp.chmod(0o600); tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def credential_path(path):
    path = path.expanduser().resolve()
    if path == ROOT or ROOT in path.parents:
        raise Error("Store Google credentials outside this repository")
    return path


def host_valid(host):
    return bool(host and re.fullmatch(r"[a-z0-9.-]+", host) and
                (host == "500nits.com" or host.endswith(".500nits.com")))


def scoped_url(url):
    parsed = urlsplit(url)
    if (parsed.scheme not in ("http", "https") or not host_valid(parsed.hostname) or
            parsed.username or parsed.password or parsed.port or parsed.fragment):
        raise Error("URL must be an HTTP(S) URL on 500nits.com or its subdomains, without credentials, port, or fragment")
    return url


def inventory():
    config = json.loads((ROOT / ".agents/sites.json").read_text())
    urls, hosts, sitemaps, warnings = set(), set(), [], []
    for site in config["sites"]:
        base = scoped_url(site["baseUrl"])
        host = urlsplit(base).hostname
        hosts.add(host); urls.add(base)
        sitemaps.append(base.rstrip("/") + "/" + site["sitemap"])
        path = (ROOT / site["sourcePath"] / site["sitemap"]).resolve()
        if ROOT not in path.parents:
            raise Error("Local sitemap source is outside the repository")
        try:
            tree = ET.parse(path)
            if tree.getroot().tag.rsplit("}", 1)[-1] != "urlset":
                warnings.append(str(path.relative_to(ROOT)) + ": sitemap index is not expanded")
                continue
            for node in tree.findall(".//{*}url/{*}loc"):
                url = scoped_url((node.text or "").strip())
                if urlsplit(url).hostname != host:
                    raise Error("Sitemap contains a URL on a different site hostname")
                urls.add(url)
        except (OSError, ET.ParseError):
            warnings.append(str(path.relative_to(ROOT)) + ": could not read local sitemap")
    return {"urls": sorted(urls), "hosts": sorted(hosts), "expected_sitemaps": sorted(sitemaps), "warnings": warnings}


def authorize(client_path, token_path, no_browser=False):
    from google_auth_oauthlib.flow import InstalledAppFlow
    client_path, token_path = credential_path(client_path), credential_path(token_path)
    try:
        config = json.loads(client_path.read_text())
    except (OSError, ValueError):
        raise Error("Save the downloaded Desktop app OAuth JSON as " + str(client_path)) from None
    installed = config.get("installed", {})
    if (installed.get("auth_uri") != "https://accounts.google.com/o/oauth2/auth" or
            installed.get("token_uri") != "https://oauth2.googleapis.com/token"):
        raise Error("Expected Google's downloaded Desktop app OAuth client JSON")
    flow = InstalledAppFlow.from_client_config(config, scopes=[SCOPE], autogenerate_code_verifier=True)
    try:
        creds = flow.run_local_server(host="127.0.0.1", port=0, open_browser=not no_browser,
                                      timeout_seconds=300, prompt="consent", access_type="offline",
                                      success_message="500nits Search Console authorization received. You may close this tab.")
    except Exception:
        raise Error("Google sign-in did not complete. Run auth again; sign in and approve in your browser.") from None
    if not creds or not creds.refresh_token:
        raise Error("Google did not return offline access. Run auth again and grant read-only access.")
    save(token_path, creds.to_json())
    print("Read-only authorization saved outside the repository.")


class API:
    def __init__(self, token_path):
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import AuthorizedSession, Request
        token_path = credential_path(token_path)
        try:
            config = json.loads(token_path.read_text())
            if config.get("token_uri") != "https://oauth2.googleapis.com/token":
                raise Error("Credential token endpoint must be Google's OAuth endpoint")
            self.credentials = Credentials.from_authorized_user_info(config, scopes=[SCOPE])
        except (OSError, ValueError):
            raise Error("No valid Search Console authorization. Run the auth command first.") from None
        try:
            if not self.credentials.valid:
                self.credentials.refresh(Request())
        except Exception:
            raise Error("Google authorization expired or was revoked. Run auth again.") from None
        self.session = AuthorizedSession(self.credentials)

    def request(self, endpoint, body=None):
        allowed = endpoint in (BASE, BASE + "/sitemaps", BASE + "/searchAnalytics/query", INSPECT)
        if not allowed:
            raise Error("Unsupported API endpoint")
        post = endpoint in (BASE + "/searchAnalytics/query", INSPECT)
        if post != (body is not None):
            raise Error("Unsupported request method")
        for attempt in range(3):
            try:
                response = self.session.request("POST" if post else "GET", endpoint, json=body,
                                                timeout=40, allow_redirects=False)
            except Exception:
                raise Error("Google API connection or authorization failed; no result inferred") from None
            if response.status_code in (429, 500, 502, 503, 504) and attempt < 2:
                time.sleep(2 ** attempt)
                continue
            if response.status_code != 200:
                reason = ""
                try:
                    error = response.json().get("error", {})
                    codes = [d.get("reason", "") for d in error.get("details", [])]
                    if "SERVICE_DISABLED" in codes:
                        reason = ": enable the Google Search Console API in the OAuth client's project"
                    elif response.status_code == 403:
                        reason = ": verify API enablement, read-only scope, and access to sc-domain:500nits.com"
                    elif response.status_code == 401:
                        reason = ": run auth again"
                except (ValueError, AttributeError):
                    pass
                raise Error(f"Google API HTTP {response.status_code}" + reason)
            try:
                result = response.json()
                if not isinstance(result, dict) or "error" in result:
                    raise ValueError
                return result
            except ValueError:
                raise Error("Invalid Google API response") from None

    def analytics(self, start, end, dimensions=(), host=None, max_rows=100000):
        body = {"startDate": str(start), "endDate": str(end), "dimensions": list(dimensions),
                "type": "web", "dataState": "final", "aggregationType": "auto", "rowLimit": 25000}
        if host:
            if not host_valid(host):
                raise Error("Invalid hostname")
            body["dimensionFilterGroups"] = [{"groupType": "and", "filters": [
                {"dimension": "page", "operator": "includingRegex", "expression": r"^https?://" + re.escape(host) + "/"}]}]
        rows, metadata = [], []
        while len(rows) < max_rows:
            body["startRow"] = len(rows)
            body["rowLimit"] = min(25000, max_rows-len(rows))
            result = self.request(BASE + "/searchAnalytics/query", body)
            page = result.get("rows", [])
            if not isinstance(page, list):
                raise Error("Invalid Search Analytics rows")
            if any(not isinstance(r, dict) or len(r.get("keys", [])) != len(dimensions) or
                   not all(isinstance(r.get(k), (int, float)) for k in ("clicks", "impressions", "ctr", "position")) for r in page):
                raise Error("Incomplete Search Analytics metrics")
            rows.extend(page)
            metadata.append({k: v for k, v in result.items() if k != "rows"})
            if len(page) < body["rowLimit"]:
                return {"rows": rows, "metadata": metadata, "row_cap_reached": False, "dimensions": list(dimensions)}
        return {"rows": rows, "metadata": metadata, "row_cap_reached": True, "dimensions": list(dimensions)}

    def inspect(self, url):
        result = self.request(INSPECT, {"inspectionUrl": scoped_url(url), "siteUrl": PROPERTY, "languageCode": "en-US"})
        if not isinstance(result.get("inspectionResult", {}).get("indexStatusResult"), dict):
            raise Error("Google did not return an index status")
        return result


def diagnose(url, result):
    status = result["inspectionResult"]["indexStatusResult"]
    canonical = status.get("googleCanonical")
    verdict = status.get("verdict", "VERDICT_UNSPECIFIED")
    state = "indexed" if verdict == "PASS" and canonical == url else "not_confirmed"
    actions = []
    if canonical and canonical != url:
        state = "different_canonical"
        actions.append("Compare Google's canonical with the intended URL; review duplicates, redirects, canonical tags, and internal links before changing anything.")
    if status.get("robotsTxtState") == "DISALLOWED":
        actions.append("Check the live robots.txt rule. Permit crawling only if this page should be public and indexable.")
    if status.get("indexingState") in ("BLOCKED_BY_META_TAG", "BLOCKED_BY_HTTP_HEADER"):
        actions.append("Check the live robots meta tag or X-Robots-Tag. Remove noindex only if indexability is intended.")
    fetch = status.get("pageFetchState")
    if fetch and fetch not in ("SUCCESSFUL", "PAGE_FETCH_STATE_UNSPECIFIED"):
        actions.append("Verify the current HTTP response and redirect chain; Google's stored fetch result is " + fetch + ".")
    if verdict != "PASS" and not actions:
        actions.append("Review Google's coverage reason, live fetch, canonical, sitemap, internal links, and useful page content. Submission alone cannot guarantee indexing.")
    return {"state": state, "verdict": verdict, "coverage": status.get("coverageState", "Unknown"),
            "google_canonical": canonical, "user_canonical": status.get("userCanonical"),
            "last_crawl": status.get("lastCrawlTime"), "next_checks": actions}


def markdown(report):
    def cell(value):
        return str(value).replace("|", "\\|").replace("\n", " ")
    lines = ["# 500nits Search Console", "", "Property: `" + PROPERTY + "`.",
             "Observed: " + report["generated_at"] + ". Status: " + report["status"] + ".", ""]
    if "window" in report:
        lines += ["Performance window: " + report["window"]["start"] + " through " + report["window"]["end"] + " (inclusive, Pacific time).", "",
                  "| Host | Clicks | Impressions | CTR | Average position |", "| --- | ---: | ---: | ---: | ---: |"]
        for host, sections in report.get("hosts", {}).items():
            rows = sections.get("totals", {}).get("rows", [])
            if rows:
                r = rows[0]
                ctr = f"{r['ctr']:.1%}" if r["impressions"] else "—"
                position = f"{r['position']:.1f}" if r["impressions"] else "—"
                lines.append(f"| {cell(host)} | {r['clicks']:,.0f} | {r['impressions']:,.0f} | {ctr} | {position} |")
            else:
                lines.append(f"| {cell(host)} | No data | — | — | — |")
        lines += ["", "Page/query/country/device breakdowns and the previous equal-length period are in report.json.", ""]
    if "sitemaps" in report:
        lines += ["## Sitemap submissions", "", "| Sitemap | Pending | Errors | Last downloaded |", "| --- | --- | ---: | --- |"]
        for row in report["sitemaps"].get("sitemap", []):
            lines.append("| " + " | ".join(cell(row.get(k, "Unknown")) for k in ("path", "isPending", "errors", "lastDownloaded")) + " |")
        for url in report.get("missing_sitemap_submissions", []):
            lines.append("- Expected sitemap not returned by the submissions list: " + url)
        lines.append("")
    lines += ["## URL inspection", "", "| URL | Stored index state | Google coverage reason | Last crawl |", "| --- | --- | --- | --- |"]
    for url, info in report.get("inspections", {}).items():
        d = info.get("diagnosis", {})
        lines.append("| " + " | ".join(cell(v) for v in (url, d.get("state", "unavailable"), d.get("coverage", "No result"), d.get("last_crawl") or "Unknown")) + " |")
    lines += ["", "## Checks to investigate", ""]
    for url, info in report.get("inspections", {}).items():
        for action in info.get("diagnosis", {}).get("next_checks", []):
            lines.append("- " + cell(url) + ": " + action)
    for error in report.get("errors", []):
        lines.append("- Unavailable: " + cell(error))
    for warning in report.get("warnings", []):
        lines.append("- Coverage note: " + cell(warning))
    lines += ["", "## Interpretation", ""] + ["- " + item for item in LIMITATIONS] + [""]
    return "\n".join(lines)


def pdf_report(report, destination):
    from html import escape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle
    from io import BytesIO
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("SmallCell", parent=styles["BodyText"], fontSize=8, leading=11))
    story = [Paragraph("500nits Search Console", styles["Title"])]
    table_rows = []

    def flush_table():
        if not table_rows:
            return
        cols = len(table_rows[0])
        widths = [155] + [(A4[0]-84-155)/(cols-1)]*(cols-1)
        table = LongTable(table_rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf2f1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LINEBELOW", (0, 0), (-1, 0), .5, colors.HexColor("#176a68")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ("TOPPADDING", (0, 0), (-1, -1), 7),
        ]))
        story.extend([table, Spacer(1, 10)])
        table_rows.clear()

    for line in markdown(report).splitlines()[2:]:
        if line.startswith("| ---"):
            continue
        if line.startswith("| "):
            cells = re.split(r"(?<!\\)\|", line)[1:-1]
            table_rows.append([Paragraph(escape(c.strip().replace("\\|", "|")), styles["SmallCell"]) for c in cells])
            continue
        flush_table()
        if not line:
            continue
        style = styles["Heading2"] if line.startswith("## ") else styles["BodyText"]
        story.append(Paragraph(escape(line.removeprefix("## ")), style))
        story.append(Spacer(1, 5))
    flush_table()
    output = BytesIO()
    SimpleDocTemplate(output, pagesize=A4, leftMargin=42, rightMargin=42, topMargin=42, bottomMargin=42,
                      title="500nits Search Console", author="500nits").build(story)
    save(destination, output.getvalue())


def collect(api, args):
    known = inventory()
    report = {"property": PROPERTY, "generated_at": datetime.now(timezone.utc).isoformat(),
              "status": "ok", "errors": [], "warnings": known["warnings"], "limitations": LIMITATIONS,
              "inventory": known, "inspections": {}}

    def read(label, call):
        try:
            value = call()
            if isinstance(value, dict) and value.get("row_cap_reached"):
                report["warnings"].append(label + ": local row cap reached; export is truncated")
            return value
        except Error as error:
            report["errors"].append(label + ": " + str(error))
            return None

    report["property_access"] = api.request(BASE)
    if args.command == "export":
        today = datetime.now(ZoneInfo("America/Los_Angeles")).date()
        end = date.fromisoformat(args.end_date) if args.end_date else today-timedelta(days=3)
        start = date.fromisoformat(args.start_date) if args.start_date else end-timedelta(days=args.days-1)
        if start > end or end >= today:
            raise Error("Choose an ordered date window ending before today in Pacific time")
        period = (end-start).days+1
        report["window"] = {"start": str(start), "end": str(end), "timezone": "America/Los_Angeles", "dataState": "final"}
        report["previous_window"] = {"start": str(start-timedelta(days=period)), "end": str(start-timedelta(days=1))}
        report["domain_totals"] = read("domain totals", lambda: api.analytics(start, end))
        report["domain_daily"] = read("domain daily", lambda: api.analytics(start, end, ["date"]))
        report["sitemaps"] = read("sitemap submissions", lambda: api.request(BASE + "/sitemaps"))
        if report["sitemaps"] is not None:
            submitted = {s["path"] for s in report["sitemaps"].get("sitemap", [])}
            report["missing_sitemap_submissions"] = sorted(set(known["expected_sitemaps"])-submitted)
        else:
            del report["sitemaps"]
        report["hosts"] = {}
        for host in ([args.host] if args.host else known["hosts"]):
            sections = {}
            for name, dimensions in [("totals", []), ("daily", ["date"]), ("pages", ["page"]),
                                     ("queries", ["query"]), ("countries", ["country"]), ("devices", ["device"])]:
                result = read(host + " " + name, lambda: api.analytics(start, end, dimensions, host))
                if result is not None:
                    sections[name] = result
            result = read(host + " previous totals", lambda: api.analytics(start-timedelta(days=period), start-timedelta(days=1), host=host))
            if result is not None:
                sections["previous_totals"] = result
            report["hosts"][host] = sections
        urls = [] if args.skip_inspection else [u for u in known["urls"] if not args.host or urlsplit(u).hostname == args.host]
    else:
        urls = sorted(set(scoped_url(url) for url in args.urls))
    if len(urls) > args.inspection_limit:
        report["warnings"].append(f"Inspection capped at {args.inspection_limit} of {len(urls)} URLs; remaining URLs are uninspected")
    report["inspection_requested"] = len(urls)
    for url in urls[:args.inspection_limit]:
        result = read(url, lambda: api.inspect(url))
        report["inspections"][url] = {"result": result, "diagnosis": diagnose(url, result)} if result else {"status": "unavailable"}
        time.sleep(.12)
    if report["errors"] or report["warnings"]:
        report["status"] = "partial"
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-file", type=Path, default=CREDENTIALS / "token.json")
    commands = parser.add_subparsers(dest="command", required=True)
    auth = commands.add_parser("auth", help="One-time Google read-only consent in your browser")
    auth.add_argument("--client-file", type=Path, default=CREDENTIALS / "client.json")
    auth.add_argument("--no-browser", action="store_true")
    commands.add_parser("inventory", help="Show intended local URLs without credentials or network access")
    commands.add_parser("status", help="Verify access to the domain property")
    export = commands.add_parser("export", help="Save performance, sitemap, and index status reports")
    export.add_argument("--days", type=int, default=28)
    export.add_argument("--start-date")
    export.add_argument("--end-date")
    export.add_argument("--host")
    export.add_argument("--skip-inspection", action="store_true")
    inspect = commands.add_parser("inspect", help="Read Google's stored status for explicit URLs")
    inspect.add_argument("urls", nargs="+")
    for cmd in [export, inspect]:
        cmd.add_argument("--inspection-limit", type=int, default=200)
        cmd.add_argument("--pdf", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    if args.command == "auth":
        authorize(args.client_file, args.token_file, args.no_browser)
        return 0
    if args.command == "inventory":
        print(json.dumps(inventory(), indent=2)); return 0
    if args.command == "export":
        if not 1 <= args.days <= 500:
            parser.error("--days must be between 1 and 500; older dates may be outside Google's retention")
        if args.host and not host_valid(args.host):
            parser.error("--host must be 500nits.com or a subdomain")
    if args.command in ("export", "inspect") and not 1 <= args.inspection_limit <= 2000:
        parser.error("--inspection-limit must be between 1 and 2000")
    api = API(args.token_file)
    if args.command == "status":
        result = api.request(BASE)
        print(json.dumps({"property": result.get("siteUrl"), "permission": result.get("permissionLevel")}, indent=2))
        return 0
    report = collect(api, args)
    destination = LOCAL / "snapshots" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    save(destination / "report.json", json.dumps(report, indent=2, sort_keys=True)+"\n")
    save(destination / "README.md", markdown(report))
    if args.pdf:
        pdf_report(report, destination / "report.pdf")
    print(destination.resolve())
    return 0 if report["status"] == "ok" else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (Error, OSError, ValueError, ImportError) as error:
        print("Search Console failed: " + str(error), file=sys.stderr)
        sys.exit(1)
