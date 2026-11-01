# 500nits Cloudflare session memory

Last verified: 2026-10-31. Domain: `500nits.com`. Hub: https://500nits.com/.

## Scope and decisions

Eddy wants this repository to be the control point for DNS, CNAMEs, redirects,
email routing, and analytics. The configuration and analytics exporters are read-only.
No DNS apply command exists. A separate explicit visitor-policy apply/disable
tool was added on 2026-11-01; see [its actual deployment status](visitor-protection.md).
Exports themselves do not change live settings.
Existing redirect source is `cloudflare/www-redirect.js`, with deployment config
in `wrangler.www-redirect.jsonc`. Hosting `_redirects` are a separate mechanism.
Do not infer that checked-in Worker source is identical to deployed source.

Implementation commits already pushed before this note:

- `6712a62`: read-only configuration exporter.
- `e6f77c5`: analytics and SEO-related exports.
- `63e6948`: daily bot-filtered PDF reports.

## Files and commands

Run from the repository root unless using absolute paths.

| Purpose | Command or file |
| --- | --- |
| Configuration snapshot | `python3 cloudflare/export.py` |
| Snapshot plus rolling 24-hour edge analytics | `python3 cloudflare/export.py --analytics` |
| Additional bot/robots and stored speed observations | `python3 cloudflare/export.py --analytics --seo` |
| Previous complete UTC day's browser visits | `.cloudflare-local/.venv/bin/python cloudflare/export.py --human-pdf` |
| Rerun a complete day | Append `--report-date YYYY-MM-DD` |
| Custom report destination | Append `--pdf-output /absolute/path/report.pdf` |
| Daily report implementation | `cloudflare/human_report.py` |
| Dependencies | `cloudflare/requirements-report.txt` (ReportLab) |
| Focused tests | `.cloudflare-local/.venv/bin/python -m unittest discover -s cloudflare -p 'test_*.py'` |
| Operating documentation | `cloudflare/README.md` and `cloudflare/SEO.md` |

The local virtualenv exists. An external script will call the daily report every
24 hours; no scheduler or delivery service was installed. Prefer after 01:00 UTC.
Exit 0 means usable report; exit 2 means unavailable/missing collection, with an
explanation PDF; other failures must not deliver a stale report. PDF and JSON
are replaced atomically per file and concurrent daily writers are locked.

## Access and private artifacts

The token is read from `CLOUDFLARE_API_TOKEN`, otherwise
`.cloudflare-local/api-token`. Never print its value. Snapshots are in
`.cloudflare-local/snapshots/<timestamp>/`; read each `manifest.json` for coverage
and failed endpoints. PDFs and companion JSON are in `.cloudflare-local/reports/`.
These are Git-ignored; generated files are mode 0600.

The Web Analytics discovery HTTP 403 was resolved after token access was updated.
Successful daily and full-history reads were verified. Required access includes
Zone Read, Account Settings Read, and Account Analytics Read on the owning account.
The account site-discovery endpoint is `/accounts/{account_id}/rum/site_info/list`.
Zone-only analytics permission does not grant account Web Analytics access.

Configuration snapshots cover DNS/BIND export, DNSSEC/settings, zone settings,
Page Rules, zone rulesets, Worker routes, and Email Routing configuration. They do
not constitute a full account backup: account bulk redirects, account email
destinations/rules, Worker source/secrets, Pages projects, registrar/billing, and
external mailboxes need separate workflows. Missing export sections are not empty
configuration. Exports are sequential observations rather than a transaction.

## Human visits: meaning and limitations

The PDF uses account-level `rumPageloadEventsAdaptiveGroups`, scoped to matching
site tags and exactly `500nits.com` or its subdomains, with `bot: 0` on every
displayed metric. `sum.visits` counts arrivals; `count` is filtered page views.
Neither is a count of unique people. The Free zone rejected edge
`botManagementDecision`; do not substitute raw requests or a user-agent denylist.

Cloudflare bot detection is imperfect. Blocked browser beacons can undercount.
No collection is an unavailable report, not evidence of zero humans. Daily mode
uses an undisplayed unfiltered collection check to distinguish these states.
Search Console indexing, search queries, and rankings are separate from this data.

## Full retained history

The account's settings node returned these actual dataset limits on 2026-10-31:

| Setting | Value |
| --- | --- |
| enabled | true |
| notOlderThan | 15,897,600 seconds = 184 days |
| maxDuration | 8,035,200 seconds = 93 days per query |
| maxPageSize | 10,000 groups |

Read `viewer.accounts.settings.rumPageloadEventsAdaptiveGroups` again on future
runs. The 30-day assumption did not apply to this browser dataset.
[Cloudflare documents six months and sampling](https://developers.cloudflare.com/web-analytics/faq/).

A private helper, `.cloudflare-local/report-all-history.py`, queries the settings,
includes matching historical site configurations even if disabled, fetches two
adjacent half-open windows, and merges complete dimensional groups. It refuses
saturated group limits rather than silently combining truncated top lists. It
leaves a 60-second margin at the moving oldest retention boundary. The first and
last calendar dates are partial. Raw query windows and merged data are retained
in the companion JSON. This is a local helper, not an `--all-history` CLI option.

Rerun the local fetch with:

```sh
.cloudflare-local/.venv/bin/python .cloudflare-local/report-all-history.py
```

The tracked renderer can rebuild the PDF from the saved JSON without refetching:

```sh
.cloudflare-local/.venv/bin/python cloudflare/render_history.py \
  .cloudflare-local/reports/500nits-human-visits-all-history-2026-10-31.json
```

The revised PDF has a numbered daily chart, monthly axis labels, an explained
peak, and chronological tables of each date's visits and views. Zero means no
qualifying measurement returned; it is not proof that nobody visited. The tables
use the same saved data as the chart. Large-window queries can use different
sampling from single-day queries, so their daily values can differ. Do not replace
individual historical rows with unrelated daily queries while retaining the old
total. The three-page report was visually checked after regeneration.

## Follow-up boundaries

Promote the private full-history fetcher into a tested public CLI if repeatable
history exports are needed on other machines. Preserve retention discovery,
half-open boundaries, domain scoping, bot filtering, and truncation checks.
For configuration changes, first refresh the snapshot and identify exact desired
values; distinguish DNS, Workers, rulesets, origin hosting, and external mail.
Do not treat repository push as Cloudflare configuration deployment.
