# 500nits site inventory and repository map

Read this file before editing, auditing, or deploying any 500nits website. The machine-readable companion is [`sites.json`](sites.json); update both files in the same change.

## Current sites

| Site | Canonical URL | Source path | Git ownership | Discovery files |
| --- | --- | --- | --- | --- |
| Product-label hub | `https://500nits.com/` | `docs/` (current noindex test) | root repository, `master` | `/robots.txt`, `/sitemap.xml` |
| Eddy's personal site | `https://eddy.500nits.com/` | `eddy_500nits_com/` | separate repository, `main` | `/CNAME`, `/robots.txt`, `/sitemap.xml` |
| Doodle Tag product site | `https://doodletag.500nits.com/` | `doodletag_500nits_com/` | separate repository and root submodule, `main` | `/CNAME`, `/robots.txt`, `/sitemap.xml` |
| Task for Spaces product site | `https://task.500nits.com/` | `task_500nits_com/` | separate ignored repository, `main` | `/CNAME`, `/robots.txt`, `/sitemap.xml` |

Doodle Tag's canonical product site is `https://doodletag.500nits.com/`, sourced from `doodletag_500nits_com/`. At Eddy's request, the former hub overview at `https://500nits.com/doodletag/` is retired. Redirect `/doodletag`, `/doodletag/`, and `/doodletag/index.html` permanently to the product site, link there directly, and omit the retired page from the hub sitemap. The hub's `retiredPages` entry in `sites.json` records this decision.

The hub's About page is `https://500nits.com/about/` (`aboutUrl` on the hub in `sites.json`). Eddy's latest request keeps this page on the hub and supersedes the earlier local deletion and proposed redirects to the personal site. Use `About` in navigation. Eddy's personal writing site is not ready to link from the hub.

## Hub publishing settings

Read [`HOSTING.md`](../HOSTING.md) before changing publishing directories.
As updated on 2026-11-02, both the Cloudflare Pages project
`edoardoc-github-io` (500nits.com) and GitHub Pages (`edoardoc.github.io`) publish
`master` → `docs/`. Cloudflare's root/build command remain empty; its output
is `docs`. These settings are independent and must be maintained separately.

Eddy explicitly requested the Cloudflare switch while file work remains in
progress. No files were moved: the former full website remains at the repository
root; `docs/` currently publishes the small noindex test, not the full hub.
The hub `sourcePath` is now `docs`, with `deploymentStage: test`. All HTML pages
must remain noindex during that stage. Root About/redirect/sitemap plans above
remain intended full-site requirements, not claims about the current test output.
Update the stage and complete the full SEO release checklist when `docs/` is ready.

## Repository boundaries

Before editing, run status checks in the root and every target site repository. A clean root status says nothing about an ignored nested repository.

- Root work: check, commit, and push from the repository root.
- Eddy personal-site work: check, commit, and push from `eddy_500nits_com/`. It is ignored by the root repository, so do not expect a root commit.
- Doodle Tag product-site work: check, commit, and push from `doodletag_500nits_com/`; then commit and push the changed submodule pointer from the root.
- Task product-site work: check, commit, and push from `task_500nits_com/`. It is ignored by the root repository, so do not expect a root commit.
- Never mix pre-existing changes from a nested repository into an SEO or deployment commit unless the user explicitly includes them.

## Adding a product site

Use a short lowercase DNS label and a canonical URL of `https://<project>.500nits.com/`.

1. Create or attach a dedicated static-site repository in `<project>_500nits_com/`.
2. Add a `CNAME` containing exactly `<project>.500nits.com` with a final newline.
3. Add a root `robots.txt` that permits the intended crawl policy and names the full sitemap URL.
4. Add a root `sitemap.xml` containing only absolute canonical HTTPS URLs on that hostname.
5. Add the site to this inventory and `.agents/sites.json`.
6. Add a useful, crawlable link from the hub. Add a short hub overview when it helps discovery, press, or support.
7. Extend the local multi-site launcher when local preview is useful.
8. Configure DNS and GitHub Pages, enable HTTPS, deploy, and run the live checks in `.agents/SEO.md`.
9. Submit the sitemap and inspect the homepage under the Search Console domain property by following `.agents/SEARCH_CONSOLE.md`.

## Discovering unregistered sites

Do not rely only on this inventory. Search for `CNAME` files and nested `.git` directories, compare the results with `.agents/sites.json`, and resolve any difference before a release. A CNAME proves the intended host; it does not prove that DNS, HTTPS, canonicalization, or Google indexing is healthy.
