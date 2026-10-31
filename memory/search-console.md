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

Connection status at this note: **Desktop OAuth client saved; browser consent
not completed**. The previous local Google authorization could not refresh. No
live Search Console export has yet succeeded. The user created the new client at
`~/.config/500nits/search-console/client.json`. Google returned `403 access_denied`
during consent; the user was directed to add the exact sign-in account under
Google Auth Platform → Audience → Test users. After that, rerun `auth`, have the
user complete browser consent, then run `status` and a real `export --pdf`.
Do not call the connection active based on offline tests. Review Testing-mode
seven-day refresh-token expiry before relying on unattended reporting.

Full Page Indexing dashboard counts are not exported by these methods. Inspect
known URLs individually; never call a submitted/live URL indexed by inference.
Unknown, excluded, different-canonical, and failed API results remain separate.
Search Analytics can omit query rows and aggregate differently by property/page;
do not derive reliable totals by summing query rows or average CTR/position values.
The API cannot request indexing of ordinary 500nits pages. Investigate current
live signals and intended page purpose before recommending fixes.
