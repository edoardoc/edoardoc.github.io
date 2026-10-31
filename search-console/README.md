# 500nits Search Console automation

Read-only reporting for `sc-domain:500nits.com`, covering the hub and all
subdomains. The current registered sites come from `.agents/sites.json`; local
sitemaps supply the URLs to inspect. See the [Search Console playbook](../.agents/SEARCH_CONSOLE.md)
and [session memory](../memory/README.md).

## One-time connection

Credentials must stay outside the repository, in
`~/.config/500nits/search-console/` by default. A Cloudflare token, Google Drive
connection, or browser login does not authorize the Search Console API.

1. In [Google Cloud Console](https://console.cloud.google.com/), select or create a project.
2. [Enable Google Search Console API](https://console.cloud.google.com/apis/library/searchconsole.googleapis.com) for that project.
3. In **Google Auth Platform → Branding**, configure the app name (`500nits search reports`) and your support/contact email.
4. In **Audience**, choose External for a personal Google account. While in Testing, add the Google account with access to the domain property as a test user.
5. In **Data Access**, add `https://www.googleapis.com/auth/webmasters.readonly`.
6. In **Clients**, create a **Desktop app** client and download its JSON as `~/.config/500nits/search-console/client.json`.
7. Install the isolated dependencies and authorize:

   ```sh
   python3 -m venv .search-console-local/.venv
   .search-console-local/.venv/bin/python -m pip install -r search-console/requirements.txt
   .search-console-local/.venv/bin/python search-console/gsc.py auth
   .search-console-local/.venv/bin/python search-console/gsc.py status
   ```

Sign in and grant read-only access in your browser. The local loopback callback
receives the authorization; do not paste codes or JSON credentials into chat.
`--no-browser` prints a sign-in link instead of opening the browser automatically.
Authorization waits up to five minutes. `token.json` stores the refresh credential
beside the client file with owner-only permissions. API reads refresh expired
access tokens automatically. No other Google credential store is modified.

An External app in Testing generally receives refresh tokens that expire in seven
days for this scope. Before unattended operation, review Google's publishing and
verification requirements and move the app to Production when appropriate for
your personal use. Do not claim unattended access is permanent: grants can be
revoked or expire. The script exits nonzero and asks for sign-in when that occurs.

If Google shows **403 access_denied during browser sign-in**, check Audience →
Test users in the same Cloud project and add the exact account selected in the
browser. Workspace account policies can also block consent. This is separate
from an API HTTP 403 after sign-in, which can mean the API is disabled or the
account lacks access to the property. [Google's sign-in error guidance](https://support.google.com/accounts/answer/16668185).

## Daily or on-demand export

From any working directory:

```sh
/Users/eddy/edoardoc.github.io/.search-console-local/.venv/bin/python \
  /Users/eddy/edoardoc.github.io/search-console/gsc.py export --pdf
```

The default exports 28 days of finalized web-search performance ending three days
ago in **America/Los_Angeles**, allowing for Google's usual reporting delay. It
also reads the previous equal-length period's totals per host, sitemap submission
status, and Google's stored indexing state for the local sitemap URL inventory.
The current inventory has four hostnames and twelve intended canonical URLs;
rerun `inventory` rather than hardcoding those counts.

Each run prints a new private snapshot directory containing `report.json`,
`README.md`, and optionally `report.pdf`. No scheduler or message delivery is
installed; call this from your existing daily script. Deliver results only after
checking the exit code:

| Exit | Meaning |
| --- | --- |
| 0 | Requested reads succeeded; read the interpretation notes |
| 2 | Partial snapshot, failed sections, missing local sources, or explicit truncation; review before delivery |
| 1 | Startup/authentication/runtime failure; do not deliver an old report |

Argument-parser errors also use exit 2 without creating a snapshot. Exports are
Git-ignored under `.search-console-local/`; files are mode 0600. Keep private
exports out of static hosting uploads and back them up separately. Snapshot names
are unique; simultaneous processes still share Google's quotas.

## Questions and focused commands

```sh
# List the intended URLs locally; no credentials required.
python3 search-console/gsc.py inventory

# Read one site's performance and inspect its intended URLs.
.search-console-local/.venv/bin/python search-console/gsc.py export \
  --host doodletag.500nits.com --days 28 --pdf

# An explicit inclusive date window, within Google's available retention.
.search-console-local/.venv/bin/python search-console/gsc.py export \
  --start-date 2026-09-01 --end-date 2026-09-30 --skip-inspection

# Ask Google about specific URLs, including an older URL outside current sitemaps.
.search-console-local/.venv/bin/python search-console/gsc.py inspect \
  https://500nits.com/ https://task.500nits.com/privacy/ --pdf
```

Ask the agent questions such as “Which Doodle Tag pages are not confirmed indexed?”,
“Did Task's search clicks improve over the previous period?”, “Which queries have
many impressions but few clicks?”, or “Does Google choose a different canonical
for this URL?” The agent should refresh the relevant export, name its observation
date/window, then explain evidence and proposed fixes. Query and page breakdowns
are separate; do not infer which query belongs to which page from those tables.

## Coverage and interpretation

- The domain property includes future subdomains. Add sites to the inventory for default monitoring, or pass an explicit `--host`/inspection URL. Unknown URLs and retired pages are not automatically enumerated from Google's index.
- URL Inspection describes Google's stored index, not the live site. The report only labels a URL `indexed` when the verdict is PASS and Google's selected canonical matches it; other states are explicit.
- Sitemaps being submitted, processed, or reachable do not establish indexing. Missing expected submissions are reported; nothing is submitted automatically.
- Performance contains clicks, impressions, CTR, average position, daily rows, pages, queries, countries, and devices. No impressions is not proof a URL is unindexed. Average position is not a guaranteed ranking.
- Domain metrics and host-filtered metrics can use different aggregation. Do not add host averages, average daily CTRs, or reconstruct totals from privacy-filtered query rows.
- Pagination follows `startRow` with up to 25,000 rows per request, stopping at a local 100,000-row cap with a warning. Google itself returns top rows, omits anonymized queries, and documents a 50,000-row daily limit per search type. Pagination does not prove completeness.
- Only finalized web-search data is requested. Empty dates are left absent, rather than fabricated as measurements. Use explicit dates to inspect longer available history; dates outside retention can return no rows.
- The default inspection cap is 200 URLs per run; `--inspection-limit` allows up to 2,000. Google's per-property quota is shared with other callers. Rate-limit/server errors get bounded retries; persistent errors stay visible.
- This is not an API copy of every dashboard panel. Full Page Indexing reports, live tests, request-indexing actions, manual actions, security issues, and links require other supported sources/UI workflows.
- Suggested checks are conditional: verify live HTTP/robots/canonical/content and intended page visibility before applying changes. Do not remove intentional noindex, promise rankings, or submit ordinary pages to Google's restricted Indexing API.

## Validation

```sh
.search-console-local/.venv/bin/python -m unittest discover -s search-console -p 'test_*.py'
```

Offline tests verify domain boundaries, canonical-based status, conditional
diagnostics, pagination, truncation reporting, partial failures, allowed read
endpoints, and private output. A successful `status` and real export are required
to establish that live account access works.

## Official references

- [OAuth authorization](https://developers.google.com/webmaster-tools/v1/how-tos/authorizing)
- [Desktop OAuth flow](https://developers.google.com/identity/protocols/oauth2/native-app)
- [Search Analytics query](https://developers.google.com/webmaster-tools/v1/searchanalytics/query)
- [Performance export and data limits](https://developers.google.com/webmaster-tools/v1/how-tos/all-your-data)
- [URL Inspection](https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect)
- [API usage quotas](https://developers.google.com/webmaster-tools/limits)
