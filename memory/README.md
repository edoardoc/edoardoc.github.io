# 500nits working memory

Start here when resuming domain, analytics, or search work. These are dated
observations and operating decisions, not proof of current remote configuration.
Check the relevant API again before making a new claim about live state.

- [Cloudflare setup and reporting](cloudflare.md): exporter, daily PDF, full-history export, permissions, and interpretation.
- [Visitor protection](visitor-protection.md): managed-challenge policy and whether it has actually been activated.
- [Search Console setup](search-console.md): automation, connection status, and next steps; also follow the [project playbook](../.agents/SEARCH_CONSOLE.md).
- [Private session record](local/2026-10-31.md): local report results and snapshot references; available only on this machine.

Keep durable workflow notes in tracked Markdown. Keep account exports, exact
private traffic results, and troubleshooting details in `local/`, which is
Git-ignored. Credentials belong in their dedicated private credential locations,
never in memory notes. Back up private data separately; a fresh clone does not
restore it. Do not publish `memory/local/` or `.cloudflare-local/` with site assets.

Update the relevant note after material changes. Record the date, what was
verified, the command and artifact paths, limitations, and unfinished work.
Keep `AGENTS.md` as a short routing layer rather than copying these notes into it.
