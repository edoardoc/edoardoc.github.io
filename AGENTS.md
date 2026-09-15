# 500nits agent guidance

## Identity and scope

- Always write `500nits` in lowercase in UI copy, metadata, documentation, reports, and commit messages.
- Treat this repository as the control point for the 500nits web presence: the studio hub at `https://500nits.com/`, app overviews on the hub, and product sites at `https://<project>.500nits.com/`.
- Keep the web stack static, lightweight, accessible, and easy for one developer to maintain.

## Required reading and routing

- Before changing any site, domain, sitemap, or deployment, read [`.agents/SITES.md`](.agents/SITES.md). It defines the site inventory, repository boundaries, and release ownership.
- Before creating or changing public pages, metadata, redirects, robots directives, or sitemaps, read [`.agents/SEO.md`](.agents/SEO.md) and follow its release checklist.
- Before inspecting or changing Google Search Console, read [`.agents/SEARCH_CONSOLE.md`](.agents/SEARCH_CONSOLE.md). Use the verified domain property strategy described there.
- Treat these linked playbooks as required project instructions. If a playbook and an explicit user request conflict, follow the user request and call out the conflict.

## Repository safety

- The root, `doodletag_500nits_com/`, and `task_500nits_com/` are separate Git worktrees. Check `git status` in every affected worktree before editing and before committing.
- Preserve unrelated user changes. Stage only the files changed for the current task.
- Do not assume an ignored nested repository will appear in the root repository's status.
- Keep `uploads/` ignored. Copy a publishable asset into the correct tracked site before referencing it.

## Web presence requirements

- Maintain the hub as a concise explanation of the studio and a crawlable link to every live product site.
- Give each launched app a focused product site on its canonical `*.500nits.com` hostname, with useful product, store, support, privacy, and press information as applicable.
- Give a hub app overview and its product site distinct purposes and copy. If two pages become substantially duplicate, choose one canonical destination and align redirects, canonical tags, internal links, and sitemaps.
- Cross-link the hub and product sites with ordinary HTML links. Do not rely on JavaScript for primary copy, navigation, metadata, or store links.
- Every public HTML page must be intentionally indexable or explicitly `noindex`; do not leave accidental crawlable utility, staging, or generated pages.

## SEO release requirements

- Keep each site's canonical origin, `CNAME`, canonical tags, internal links, `robots.txt`, and sitemap URLs consistent.
- Include only canonical, indexable, successful URLs in sitemaps. Use absolute HTTPS URLs and one site hostname per sitemap.
- Give each indexable page a unique, descriptive title, meta description, self-referencing canonical, crawlable main heading, and useful visible copy.
- Add accurate social metadata to shareable pages and accurate JSON-LD only when it matches visible content. Never invent ratings, prices, availability, reviews, or release facts.
- Run `node scripts/audit-seo.mjs` from the root before deploying a site change. Resolve errors; review warnings and either fix them or explain why they are intentional.
- After deploying, verify the affected canonical URLs, robots file, and sitemap over HTTPS. A local check alone is not a release check.

## Google Search Console

- Use `sc-domain:500nits.com` as the default Search Console property because it covers the apex domain and all present and future subdomains. Add URL-prefix properties only when separate reporting or delegated access is useful.
- Search Console submission and indexing are different states. Never report a URL as indexed merely because it is live, present in a sitemap, submitted, or queued for recrawl.
- Submit each site's own sitemap after its first deployment and after material URL-set changes. Inspect important canonical URLs after launch or a significant SEO correction.
- The general-purpose Search Console API can submit sitemaps and inspect Google's stored index status, but it cannot request indexing for ordinary 500nits pages. Use the Search Console URL Inspection UI for that action.
- Never commit Google OAuth credentials, access tokens, verification secrets, cookies, or exported Search Console data containing private account information.

## Deployment process

- Redeploy automatically after any change: commit with a clear, lowercase-`500nits`-compliant message and immediately push the affected repository.
- For a nested site, commit and push inside that site's Git worktree. If the root tracks it as a submodule, then commit and push the updated gitlink in the root repository as a separate step.
- Verify the pushed commit and affected live URL. Allow for hosting propagation, then compare the live metadata and discovery files with the checked-in versions.
- In the final handoff, list every affected live URL and always include the full hub link: https://500nits.com/
