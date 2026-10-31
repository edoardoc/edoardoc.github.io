# 500nits Search Console session memory

Updated 2026-10-31. Default property: `sc-domain:500nits.com`.

Eddy requested the same local automation approach as Cloudflare, to ask about
indexing across subdomains, troubleshoot problems, and improve SEO using evidence.
Use the [project playbook](../.agents/SEARCH_CONSOLE.md) and
[automation README](../search-console/README.md).

Implemented `search-console/gsc.py` commands: `auth`, `status`, `inventory`,
`export`, and `inspect`. Exports contain private JSON, Markdown, and optional PDF.
The default performance window is 28 finalized Pacific-time days ending three
days ago, plus previous-period per-host totals. URLs come from local sitemaps and
site inventory; these are intended URLs, not verified live deployment state.
Use explicit hostname/date/URL arguments for focused questions.

Credentials live outside Git at `~/.config/500nits/search-console/`. Only the
`webmasters.readonly` OAuth scope is requested. Output and the virtualenv are
Git-ignored in `.search-console-local/`. No scheduler, sitemap submission, recrawl
request, or SEO change was installed/applied by this reporting workflow.

Connection status at this note: **read-only OAuth authorization succeeded on
2026-10-31**. A real `status` request confirmed access to `sc-domain:500nits.com`
with the signed-in account's `siteOwner` permission. The script still requests
only read-only OAuth scope. Client and refresh credentials are saved privately
outside the repository; neither belongs in exports or version control.

The earlier `403 access_denied` occurred during browser consent, not a Search
Console data request. Setup guidance covered adding the exact sign-in account
under Google Auth Platform → Audience → Test users; a fresh consent flow then
succeeded. Do not reuse old localhost authorization links after their listener
exits. Review Testing-mode seven-day refresh-token expiry before relying on
unattended reporting; the project's publishing status has not been verified.

The first real `export --pdf` completed successfully (exit 0) on 2026-10-31.
Private artifacts: `.search-console-local/snapshots/20261031T195050.858277Z/`.
Read `report.json` for exact metrics, raw indexing evidence, and query coverage;
`README.md` and `report.pdf` summarize it. The run covered the four configured
hosts, twelve intended URLs, sitemap submissions, and finalized performance for
2026-10-01 through 2026-10-28 in Pacific time. Private findings are recorded in
`memory/local/2026-10-31.md`. Refresh before answering a later live-state question.
Hosts with no impressions show no CTR/average-position value in the summary;
Google's returned zero placeholders must not be described as a ranking of zero.

Full Page Indexing dashboard counts are not exported by these methods. Inspect
known URLs individually; never call a submitted/live URL indexed by inference.
Unknown, excluded, different-canonical, and failed API results remain separate.
Search Analytics can omit query rows and aggregate differently by property/page;
do not derive reliable totals by summing query rows or average CTR/position values.
The API cannot request indexing of ordinary 500nits pages. Investigate current
live signals and intended page purpose before recommending fixes.
