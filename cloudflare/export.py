#!/usr/bin/env python3
"""Read-only Cloudflare configuration snapshots for 500nits.com (Python 3.10+)."""

import argparse
from datetime import datetime, timezone
import json
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
        try:
            with self.opener.open(request, timeout=30) as response:
                body = response.read().decode("utf-8")
        except HTTPError as error:
            # Do not log response bodies, request headers, or credentials.
            raise ExportError(f"HTTP {error.code}") from None
        except (URLError, TimeoutError, OSError):
            raise ExportError("Network request failed") from None
        if raw:
            return body
        try:
            data = json.loads(body)
        except ValueError:
            raise ExportError("Invalid JSON response") from None
        if not isinstance(data, dict) or data.get("success") is not True:
            raise ExportError("Cloudflare reported an unsuccessful response")
        return data

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--token-file", type=Path, default=LOCAL / "api-token")
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
        ],
    }

    def capture(name, path, listing=False, pagination="page", raw=False):
        section = {"endpoint": path}
        manifest["sections"][name] = section
        try:
            if listing:
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
    capture("zone-settings", base + "/settings")
    capture("page-rules", base + "/pagerules", listing=True)
    rulesets = capture("rulesets", base + "/rulesets", listing=True, pagination="cursor")
    for ruleset in rulesets or []:
        identifier = quote(ruleset["id"], safe="")
        capture("rulesets/" + identifier, base + "/rulesets/" + identifier)
    capture("worker-routes", base + "/workers/routes")
    capture("email-settings", base + "/email/routing")
    capture("email-dns", base + "/email/routing/dns")
    capture("email-rules", base + "/email/routing/rules", listing=True)
    capture("email-catch-all", base + "/email/routing/rules/catch_all")
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
