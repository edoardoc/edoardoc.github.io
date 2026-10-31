#!/usr/bin/env python3
"""Read-only Cloudflare configuration snapshots for 500nits.com (Python 3.10+)."""

import argparse
from datetime import datetime, timedelta, timezone
import json
from html import escape
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

ROOT = Path(__file__).resolve().parent.parent
LOCAL = ROOT / ".cloudflare-local"
API = "https://api.cloudflare.com/client/v4"
DOMAIN = "500nits.com"


class ExportError(Exception):
    pass


class NoRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class Cloudflare:
    def __init__(self, token):
        self.token = token
        self.opener = build_opener(NoRedirects())

    def get(self, path, params=None, raw=False):
        url = API + path + ("?" + urlencode(params) if params else "")
        request = Request(url, method="GET", headers={
            "Authorization": "Bearer " + self.token,
            "Accept": "text/plain" if raw else "application/json",
        })
        body = self.read_response(request)
        if raw:
            return body
        try:
            data = json.loads(body)
        except ValueError:
            raise ExportError("Invalid JSON response") from None
        if not isinstance(data, dict) or data.get("success") is not True:
            raise ExportError("Cloudflare reported an unsuccessful response")
        return data

    def read_response(self, request):
        try:
            with self.opener.open(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except HTTPError as error:
            # Do not log response bodies, request headers, or credentials.
            raise ExportError(f"HTTP {error.code}") from None
        except (URLError, TimeoutError, OSError):
            raise ExportError("Network request failed") from None

    def crawler_traffic(self, zone_id, end):
        """A fixed read-only GraphQL query; user agents are not verified identities."""
        end = end.replace(microsecond=0)
        start = end - timedelta(hours=24)
        agents = {
            "googlebot": "Googlebot", "bingbot": "bingbot", "gptbot": "GPTBot",
            "oai_search": "OAI-SearchBot", "chatgpt_user": "ChatGPT-User",
            "claudebot": "ClaudeBot", "perplexitybot": "PerplexityBot",
        }
        groups = []
        for alias, agent in agents.items():
            filters = (
                'datetime_geq: ' + json.dumps(start.isoformat()) + ', '
                'datetime_leq: ' + json.dumps(end.isoformat()) + ', '
                'requestSource: "eyeball", userAgent_like: ' + json.dumps('%' + agent + '%')
            )
            groups.append(alias + ': httpRequestsAdaptiveGroups(limit: 500, filter: {' +
                          filters + '}) { count dimensions { clientRequestHTTPHost edgeResponseStatus } }')
        query = ('query CrawlerTraffic { viewer { zones(filter: {zoneTag: ' +
                 json.dumps(zone_id) + '}) { ' + ' '.join(groups) + ' } } }')
        result = self.query_zone(query)
        return {
            "window_start": start.isoformat(), "window_end": end.isoformat(),
            "user_agent_filters": agents,
            "limitations": ["User-agent strings can be spoofed; these are not verified crawler identities.",
                            "Adaptive analytics may be sampled and depend on plan and retention limits.",
                            "Only the listed user-agent patterns are included; this is not all bot traffic.",
                            "At most 500 hostname/status groups per pattern; a full page may be truncated.",
                            "Crawler requests are not evidence of indexing, rankings, or search impressions."],
            "possibly_truncated": [key for key, rows in result.items() if len(rows) >= 500],
            "data": result,
        }

    def traffic_analytics(self, zone_id, end, referrers=False):
        end = end.replace(microsecond=0)
        start = end - timedelta(hours=24)
        filters = ('datetime_geq: ' + json.dumps(start.isoformat()) +
                   ', datetime_lt: ' + json.dumps(end.isoformat()) + ', requestSource: "eyeball"')
        dimensions = {"referrers": "clientRefererHost"} if referrers else {
            "totals": None, "hourly": "datetimeHour", "hostnames": "clientRequestHTTPHost",
            "status_codes": "edgeResponseStatus", "countries": "clientCountryName",
            "paths": "clientRequestHTTPHost clientRequestPath", "cache": "cacheStatus",
        }
        groups = []
        for alias, fields in dimensions.items():
            selection = 'count sum { edgeResponseBytes visits }'
            if fields:
                selection += ' dimensions { ' + fields + ' }'
            groups.append(alias + ': httpRequestsAdaptiveGroups(limit: 500, orderBy: [count_DESC], filter: {' +
                          filters + '}) { ' + selection + ' }')
        query = ('query TrafficAnalytics { viewer { zones(filter: {zoneTag: ' +
                 json.dumps(zone_id) + '}) { ' + ' '.join(groups) + ' } } }')
        result = self.query_zone(query)
        return {
            "window_start": start.isoformat(), "window_end_exclusive": end.isoformat(),
            "dataset": "httpRequestsAdaptiveGroups", "request_source": "eyeball",
            "limitations": ["Adaptive request metrics may be sampled; counts are estimates.",
                            "Request counts include automated clients and assets, not just human page views.",
                            "Only traffic passing through Cloudflare for this zone is included.",
                            "Each breakdown is capped at the top 500 groups; full pages may be truncated.",
                            "Referrers can be absent or spoofed and do not reveal search query rankings.",
                            "This is edge traffic analytics, not browser-beacon Web Analytics or Google Search Console."],
            "possibly_truncated": [key for key, rows in result.items() if len(rows) >= 500],
            "data": result,
        }

    def query_zone(self, query):
        # Only the fixed read queries above call this; no GraphQL mutations are used.
        request = Request(API + "/graphql", method="POST",
                          data=json.dumps({"query": query}).encode(), headers={
                              "Authorization": "Bearer " + self.token,
                              "Content-Type": "application/json",
                          })
        try:
            data = json.loads(self.read_response(request))
        except ValueError:
            raise ExportError("Invalid JSON response") from None
        if data.get("errors"):
            messages = [str(e.get("message", "GraphQL error")) for e in data["errors"]]
            raise ExportError("; ".join(messages).replace(self.token, "[redacted]")[:500])
        zones = ((data.get("data") or {}).get("viewer") or {}).get("zones")
        if not isinstance(zones, list) or len(zones) != 1:
            raise ExportError("Analytics did not return the requested zone")
        return zones[0]

    def listing(self, path, params=None, pagination="page"):
        query = dict(params or {})
        query["per_page"] = 50
        if pagination == "page":
            query["page"] = 1
        items, seen = [], set()
        for _ in range(10000):
            data = self.get(path, query)
            batch = data.get("result")
            if not isinstance(batch, list):
                raise ExportError("Expected a list response")
            items.extend(batch)
            info = data.get("result_info") or {}
            if pagination == "cursor":
                cursor = (info.get("cursors") or {}).get("after")
                if not cursor:
                    return items
                if cursor in seen:
                    raise ExportError("Pagination repeated a cursor")
                seen.add(cursor)
                query["cursor"] = cursor
            else:
                total_pages = info.get("total_pages")
                total_count = info.get("total_count")
                if total_pages is not None and query["page"] >= total_pages:
                    if total_count is not None and len(items) != total_count:
                        raise ExportError("Record count changed during export; retry")
                    return items
                if total_pages is None and len(batch) < query["per_page"]:
                    return items
                if not batch:
                    raise ExportError("Pagination ended before the reported last page")
                fingerprint = json.dumps(batch, sort_keys=True)
                if fingerprint in seen:
                    raise ExportError("Pagination repeated a page")
                seen.add(fingerprint)
                query["page"] += 1
        raise ExportError("Pagination limit exceeded")


def save(path, value, raw=False):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    text = value if raw else json.dumps(value, indent=2, sort_keys=True) + "\n"
    with path.open("x", encoding="utf-8") as output:
        output.write(text)
    path.chmod(0o600)


def analytics_report(destination, sections):
    lines = ["# 500nits Analytics snapshot", "",
             "These are Cloudflare edge traffic observations, not Google indexing or rankings.",
             "Counts may be sampled estimates and include automated clients and asset requests.", "",
             "| Section | Status |", "| --- | --- |"]
    for name, section in sections.items():
        if name.startswith("analytics/"):
            status = section["status"]
            if "error" in section:
                status += ": " + section["error"]
            lines.append("| " + name + " | " + escape(status).replace("|", "\\|").replace("\n", " ") + " |")
    traffic_file = destination / "analytics/traffic.json"
    if traffic_file.exists():
        traffic = json.loads(traffic_file.read_text())
        rows = traffic["data"]
        lines += ["", "## Traffic", "",
                  f"UTC window: {traffic['window_start']} to {traffic['window_end_exclusive']} (end excluded).", ""]
        totals = rows.get("totals", [])
        if totals:
            total = totals[0]
            lines += [f"- Requests: {total['count']:,}",
                      f"- Response bytes: {total['sum']['edgeResponseBytes']:,}",
                      f"- Cloudflare visits metric: {total['sum']['visits']:,}", ""]
        for title, key, dimension in [("Hostnames", "hostnames", "clientRequestHTTPHost"),
                                      ("Response codes", "status_codes", "edgeResponseStatus")]:
            lines += ["### " + title, "", "| Value | Requests |", "| --- | ---: |"]
            for row in rows.get(key, []):
                label = escape(str(row["dimensions"][dimension])).replace("|", "\\|").replace("\n", " ")
                lines.append(f"| {label} | {row['count']:,} |")
            lines.append("")
        if traffic["possibly_truncated"]:
            lines += ["Potentially truncated at 500 groups: " + ", ".join(traffic["possibly_truncated"]) + ".", ""]
        lines += ["## Interpretation", ""] + ["- " + note for note in traffic["limitations"]]
    crawlers_file = destination / "analytics/crawler-traffic.json"
    if crawlers_file.exists():
        crawlers = json.loads(crawlers_file.read_text())
        lines += ["", "## Crawler user-agent matches", "",
                  "These strings can be spoofed and do not prove crawler identity or indexing.", "",
                  "| User-agent pattern | Requests |", "| --- | ---: |"]
        for name, rows in crawlers["data"].items():
            lines.append(f"| {crawlers['user_agent_filters'][name]} | {sum(row['count'] for row in rows):,} |")
    lines += ["", "No Cloudflare configuration was changed. Full JSON reports and manifest.json record coverage.", ""]
    save(destination / "analytics/README.md", "\n".join(lines), raw=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-file", type=Path, default=LOCAL / "api-token")
    parser.add_argument("--seo", action="store_true",
                        help="Also read bot/robots settings, stored speed reports, and 24-hour crawler analytics")
    parser.add_argument("--analytics", action="store_true",
                        help="Also export 24-hour edge traffic, referrer, and crawler analytics")
    args = parser.parse_args()
    os.umask(0o077)
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        try:
            token = args.token_file.read_text().strip()
        except OSError:
            raise ExportError("Set CLOUDFLARE_API_TOKEN or save a token in .cloudflare-local/api-token") from None
    if not token or any(c.isspace() for c in token):
        raise ExportError("Token is empty or contains whitespace")
    api = Cloudflare(token)
    zones = api.listing("/zones", {"name": DOMAIN})
    zones = [zone for zone in zones if zone.get("name") == DOMAIN]
    if len(zones) != 1:
        raise ExportError("Expected exactly one accessible 500nits.com zone")
    zone = zones[0]
    base = "/zones/" + quote(zone["id"], safe="")
    started = datetime.now(timezone.utc)
    destination = LOCAL / "snapshots" / started.strftime("%Y%m%dT%H%M%S.%fZ")
    destination.mkdir(parents=True, mode=0o700)
    manifest = {
        "domain": DOMAIN,
        "started_at": started.isoformat(),
        "read_only": True,
        "source": API,
        "sections": {},
        "outside_scope": [
            "Account-level bulk redirects and redirect lists",
            "Account-level email destination verification and rules",
            "Worker source code, bindings, secrets, and custom domains",
            "Cloudflare Pages projects and hosting configuration",
            "Registrar, billing, certificates, and other account products",
            "Mailboxes or forwarding managed by external email providers",
            "Crawler Hints (dashboard setting; no supported public API identified)",
            "Google Search Console indexing, rankings, clicks, and impressions",
        ],
    }

    def capture(name, path, listing=False, pagination="page", raw=False, reader=None):
        section = {"endpoint": path}
        manifest["sections"][name] = section
        try:
            if reader:
                result = reader()
            elif listing:
                result = api.listing(path, pagination=pagination)
            else:
                data = api.get(path, raw=raw)
                result = data if raw else data["result"]
            filename = name + (".txt" if raw else ".json")
            save(destination / filename, result, raw=raw)
            section.update(status="exported", file=filename)
            if isinstance(result, list):
                section["count"] = len(result)
            print(f"Exported {name}")
            return result
        except (ExportError, KeyError) as error:
            section.update(status="unavailable", error=str(error))
            print(f"Unavailable: {name} ({error})", file=sys.stderr)
            return None

    capture("zone", base)
    capture("dns-records", base + "/dns_records", listing=True)
    capture("dns-zone", base + "/dns_records/export", raw=True)
    capture("dns-settings", base + "/dns_settings")
    capture("dnssec", base + "/dnssec")
    zone_settings = capture("zone-settings", base + "/settings")
    capture("page-rules", base + "/pagerules")
    rulesets = capture("rulesets", base + "/rulesets", listing=True, pagination="cursor")
    for ruleset in rulesets or []:
        identifier = quote(ruleset["id"], safe="")
        capture("rulesets/" + identifier, base + "/rulesets/" + identifier)
    capture("worker-routes", base + "/workers/routes")
    capture("email-settings", base + "/email/routing")
    capture("email-dns", base + "/email/routing/dns")
    capture("email-rules", base + "/email/routing/rules", listing=True)
    capture("email-catch-all", base + "/email/routing/rules/catch_all")
    if args.seo:
        capture("seo/bot-management", base + "/bot_management")
        capture("seo/speed-pages", base + "/speed_api/pages")
        important = {
            "always_use_https", "automatic_https_rewrites", "ssl", "min_tls_version",
            "security_level", "browser_check", "challenge_ttl", "cache_level",
            "browser_cache_ttl", "early_hints", "http2", "http3", "brotli",
            "rocket_loader", "minify", "always_online", "mobile_redirect",
        }
        summary = {
            "domain": DOMAIN,
            "zone_settings_available": zone_settings is not None,
            "zone_settings": {item["id"]: {"value": item.get("value"), "editable": item.get("editable")}
                              for item in zone_settings or [] if item["id"] in important},
            "sections": {name: section for name, section in manifest["sections"].items()
                         if name.startswith("seo/")},
            "notes": ["No SEO policy was changed and no new speed test was started.",
                      "Cloudflare settings affect crawling and delivery; they do not prove Google indexing.",
                      "Titles, canonicals, sitemaps, and origin robots directives remain in site source.",
                      "See cloudflare/SEO.md for API capabilities, permissions, and control boundaries."],
        }
        save(destination / "seo/summary.json", summary)
    if args.seo or args.analytics:
        capture("analytics/crawler-traffic", "/graphql",
                reader=lambda: api.crawler_traffic(zone["id"], started))
    if args.analytics:
        capture("analytics/traffic", "/graphql",
                reader=lambda: api.traffic_analytics(zone["id"], started))
        capture("analytics/referrers", "/graphql",
                reader=lambda: api.traffic_analytics(zone["id"], started, referrers=True))
    if args.seo or args.analytics:
        analytics_report(destination, manifest["sections"])
    manifest["finished_at"] = datetime.now(timezone.utc).isoformat()
    manifest["all_requested_sections_exported"] = all(
        section["status"] == "exported" for section in manifest["sections"].values()
    )
    save(destination / "manifest.json", manifest)
    print(f"Snapshot saved: {destination.relative_to(ROOT)}")
    print("See manifest.json for coverage, errors, and exclusions.")
    return 0 if manifest["all_requested_sections_exported"] else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except ExportError as error:
        print(f"Export failed: {error}", file=sys.stderr)
        sys.exit(1)
