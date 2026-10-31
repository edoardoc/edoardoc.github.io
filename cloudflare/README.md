# 500nits domain configuration

This directory is the starting point for managing `500nits.com` from this repository.
The exporter reads the live Cloudflare API; it does not apply changes. A snapshot is
observed state, not a configuration file that is automatically deployed on push.

## Export current configuration

Use Python 3.10 or newer. No third-party packages are needed.

1. Create a Cloudflare API token scoped to `500nits.com` with read permissions for
   Zone, DNS, Zone Settings, Page Rules, Workers Routes, Email Routing Rules, and
   the rulesets used by the zone (including redirects).
2. Save only the token value to `.cloudflare-local/api-token` at the repository root,
   or supply it through the `CLOUDFLARE_API_TOKEN` environment variable. Do not put
   the token in a command argument, a tracked file, or chat.
3. Run from the repository root:

   ```sh
   python3 cloudflare/export.py
   ```

Each run creates a new `.cloudflare-local/snapshots/<UTC timestamp>/` directory.
Read its `manifest.json` first: it records each endpoint, export status, counts,
and coverage limitations. An unavailable section is not evidence that there is
no configuration. Exit status 2 means some sections could not be exported;
status 1 means startup or authentication failed.

The snapshot includes DNS records and a BIND zone export; DNS settings and DNSSEC;
zone settings such as TLS and HTTPS; Page Rules; zone rulesets and their details;
Worker routes; and Email Routing settings, DNS, rules, and the catch-all rule.
Paginated list endpoints are followed. Configuration requests use GET; optional
analytics use read-only GraphQL queries sent with POST. Exports are sequential
observations, not a transactionally consistent backup.

## Analytics and SEO-related information

### Daily PDF for your external scheduler

The lightweight PDF mode uses browser-based Cloudflare Web Analytics with
**Exclude Bots** enabled (`bot = 0`). It reports estimated human visits, filtered
page views, hourly visits, and the top sites, countries, and entry pages on one
page. It does not download DNS, email, rulesets, or the general edge traffic export.
Bot detection is imperfect; this cannot certify that every included visit is human.

One-time setup from this repository:

```sh
python3 -m venv .cloudflare-local/.venv
.cloudflare-local/.venv/bin/python -m pip install -r cloudflare/requirements-report.txt
```

The environment is already installed on this machine. Call this from any working
directory in your existing daily script:

```sh
/Users/eddy/edoardoc.github.io/.cloudflare-local/.venv/bin/python \
  /Users/eddy/edoardoc.github.io/cloudflare/export.py --human-pdf
```

The default window is the **previous complete UTC calendar day**, from midnight
inclusive to the next midnight exclusive. Schedule after 01:00 UTC to leave time
for analytics ingestion. The command prints the absolute PDF path to stdout;
diagnostics go to stderr. No scheduler is installed by this repository.

Outputs are `.cloudflare-local/reports/500nits-human-visits-YYYY-MM-DD.pdf` and a
matching JSON file. Both remain private and Git-ignored. Rerunning a date replaces
that date's files; each file is written through an atomic replacement, and an
output lock prevents concurrent writers. Treat the exit status as authoritative.

| Exit | Meaning |
| --- | --- |
| `0` | Filtered measurements were retrieved and PDF/JSON were written; safe for the caller to deliver |
| `2` | Data unavailable or no browser measurements; PDF/JSON explain the problem and contain no inferred human count |
| `1` | Startup, invalid report date, dependency, lock, or other runtime failure; do not deliver an existing file |

Argument-parser usage errors also exit `2` but do not produce a report. A caller
should deliver output only on exit `0`, for example:

```sh
if report_path="$(/Users/eddy/edoardoc.github.io/.cloudflare-local/.venv/bin/python \
  /Users/eddy/edoardoc.github.io/cloudflare/export.py --human-pdf)"; then
  printf '%s\n' "$report_path"
  # Pass this path to your existing delivery step.
else
  report_status=$?
  printf 'Daily visit report failed (exit %s).\n' "$report_status" >&2
  exit "$report_status"
fi
```

For a rerun/backfill within Cloudflare's retention window:

```sh
.cloudflare-local/.venv/bin/python cloudflare/export.py --human-pdf \
  --report-date 2026-10-30 \
  --pdf-output .cloudflare-local/reports/review-2026-10-30.pdf
```

Web Analytics must already be enabled and collecting browser measurements. The
token needs **Zone Read**, **Account Settings Read** (to identify the site's
configuration), and **Account Analytics Read**, scoped to the owning account.
Existing zone-only analytics access does not grant account Web Analytics access.
The command does not enable tracking, change Cloudflare settings, or upgrade plans.
It never substitutes raw edge requests or a user-agent denylist for human visits.

Run the focused checks with:

```sh
.cloudflare-local/.venv/bin/python -m unittest discover -s cloudflare -p 'test_*.py'
```

### General edge analytics

To save the past 24 hours of Analytics dashboard traffic alongside configuration:

```sh
python3 cloudflare/export.py --analytics
```

This adds traffic totals, hourly activity, hostnames, status codes, countries,
requested paths, cache status, referrers when available, and selected crawler
user-agent matches. Results live in the snapshot's `analytics/` directory with a
readable report. Each JSON file records its time window and limitations.

Use `--seo` to additionally read bot policies, managed robots settings, and stored
Speed/Observatory reports. Combine `--analytics --seo` for both. These flags never
change policies or start new speed tests. See [SEO.md](SEO.md) for permissions,
API capabilities, and the difference between traffic, crawl activity, and indexing.

Account-level bulk redirects, account-level email rules and destination verification,
Worker code and bindings, Pages projects, registrar settings, and other account
products require separate exports. External mailbox configuration is not available
through the Cloudflare zone API. These exclusions are also recorded in the manifest.

## Local data and version control

Full snapshots stay local and are ignored by Git: they may reveal origin addresses,
email forwarding destinations, verification records, or private rule values.
The API token is never copied into a snapshot. New export files are owner-readable
and owner-writable only. Keep backups of this local directory separately if needed.
Do not force-add it to Git or include it in a static hosting upload.

The tracked exporter and documentation provide the repeatable workflow. Before
adding a configuration change workflow, compare a fresh export with the baseline
and review the exact proposed changes. No DNS apply command exists yet.

## Existing redirect

`www-redirect.js` is the existing Worker source; `../wrangler.www-redirect.jsonc`
defines its deployment route. This source alone does not establish what is live.
`../_redirects` contains hosting redirects, which are separate from DNS records and
Cloudflare zone rules.

## API references

- [DNS records and exports](https://developers.cloudflare.com/api/resources/dns/)
- [Zone settings](https://developers.cloudflare.com/api/resources/zones/subresources/settings/methods/list/)
- [Rulesets](https://developers.cloudflare.com/ruleset-engine/rulesets-api/view/)
- [Email Routing](https://developers.cloudflare.com/api/resources/email_routing/)
- [Worker routes](https://developers.cloudflare.com/api/resources/workers/subresources/routes/)
- [API token permissions](https://developers.cloudflare.com/fundamentals/api/reference/permissions/)
