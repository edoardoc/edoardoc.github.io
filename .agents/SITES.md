# 500nits site inventory and repository map

Read this file before editing, auditing, or deploying any 500nits website. The machine-readable companion is [`sites.json`](sites.json); update both files in the same change.

## Current sites

| Site | Canonical URL | Source path | Git ownership | Discovery files |
| --- | --- | --- | --- | --- |
| Studio hub | `https://500nits.com/` | repository root | root repository, `master` | `/robots.txt`, `/sitemap.xml` |
| Doodle Tag product site | `https://doodletag.500nits.com/` | `doodletag_500nits_com/` | separate repository and root submodule, `main` | `/CNAME`, `/robots.txt`, `/sitemap.xml` |
| Task for Spaces product site | `https://task.500nits.com/` | `task_500nits_com/` | separate ignored repository, `main` | `/CNAME`, `/robots.txt`, `/sitemap.xml` |

The hub page at `https://500nits.com/doodletag/` is a studio overview, not the source tree for `https://doodletag.500nits.com/`. Keep those two pages distinct and link the overview to the product site.

## Repository boundaries

Before editing, run status checks in the root and every target site repository. A clean root status says nothing about an ignored nested repository.

- Root work: check, commit, and push from the repository root.
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
