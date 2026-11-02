# How 500nits is published

Updated 2026-11-02. **Two independent hosting services deploy the same repository
and `master` branch. Both now publish only `docs/`.**

| Address | Hosting service | Published folder |
| --- | --- | --- |
| https://edoardoc.github.io/ | GitHub Pages | `master` → `/docs` |
| https://500nits.com/ | Cloudflare Pages project `edoardoc-github-io` | `docs` |
| https://edoardoc-github-io.pages.dev/ | The same Cloudflare Pages project | `docs` |

Cloudflare builds from GitHub commits; it does not copy the finished GitHub Pages
website. Changing one service's settings does not update the other.

## Confirmed Cloudflare settings

| Setting | Value |
| --- | --- |
| Repository | `edoardoc/edoardoc.github.io` |
| Production branch | `master` |
| Build command | Empty |
| Root directory | Empty (repository root) |
| Build output directory | `docs` |
| Custom domains | `500nits.com`, `www.500nits.com` |

DNS sends the apex and www to `edoardoc-github-io.pages.dev` with proxying enabled.
GitHub Pages has no custom domain attached. Both services redeploy from pushes.

## Current test and work in progress

At Eddy's explicit request, Cloudflare was switched from root output to `docs`
without moving website files. The former full website remains at the repository
root for ongoing work; it is no longer the Cloudflare publishing output.

`docs/index.html` is currently the small **noindex test page**. The full homepage,
About page, assets, robots.txt, sitemap.xml, and root `_redirects` remain outside
the output until intentionally added to `docs/`. This is not yet an SEO-ready
production release. The site inventory records `deploymentStage: test`; the audit
requires every HTML test page to remain noindex. Remove that stage and complete
the normal SEO checks when publishing the full site.

`docs/newsletter.md` is also published because it is inside `docs/`. Keep future
internal notes outside this folder. Root `AGENTS.md`, `memory/`, and tooling are
excluded from new production output. Without a custom 404 page, Cloudflare may
return its index-page fallback for missing paths: HTTP 200 alone does not prove
an excluded file exists; check the returned content. Old deployment-specific
preview URLs may retain earlier output; this switch updates current production.

The local hub preview now serves `docs/`. A future `docs/about/index.html` will
appear at `https://500nits.com/about/`; `docs` does not become part of the URL.

## History and rollback

GitHub was already on `/docs` while Cloudflare published the root. Cloudflare's
output setting was changed to `docs` by API and read back successfully; a push
triggers the new build. Private before/after project records are in
`.cloudflare-local/deployment-audit/docs-switch-20261102/`.

To restore root output, set Cloudflare's build output directory to empty and
trigger a fresh deployment. This would publish root-level internal files again;
prefer finishing the public folder.

## Other sites

Doodle Tag and Task use their own repositories and GitHub Pages deployments.
Their output settings are unchanged. See [the site inventory](.agents/SITES.md).
The separate www redirect Worker does not select the Pages output directory.

## Deployment verification and stale cache

The Cloudflare production deployment of commit `360cc46` succeeded with output
`docs`. Its unique deployment hostname and fresh requests match `docs/index.html`,
as does GitHub Pages. The custom-domain homepage still applies the existing
visitor challenge to command-line requests.

Immediately after the switch, the exact `/AGENTS.md` URLs on the custom domain
and project alias still returned cached root content. Cache-busted requests and
the unique new deployment returned the test page instead. The new artifact
excludes that file, but stale cache is a separate issue. A zone cache purge was
attempted and denied with HTTP 401; Cache Purge permission or a dashboard purge
is required to complete that cleanup. Do not call the old URLs inaccessible
until the exact URLs have been checked again. Cloudflare documents asset retention
and stale-cache cleanup in [Serving Pages](https://developers.cloudflare.com/pages/configuration/serving-pages/).

References: [GitHub publishing sources](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site),
[Cloudflare output directories](https://developers.cloudflare.com/pages/configuration/build-configuration/).
