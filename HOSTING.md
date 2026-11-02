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

## Local migration awaiting review

The full public hub has been moved into `docs/` in the working tree, replacing
the temporary test homepage. It includes the homepage, About, Botify, shared
styles/scripts, newsletter configuration, images, fonts, PDFs, discovery files,
and Cloudflare redirects. Public URLs are unchanged.

Internal material stays outside `docs/`: agent instructions, memory, tooling,
credentials, setup notes, and drafts. Newsletter instructions moved from
`docs/newsletter.md` to `memory/newsletter.md`; the generator now writes
`docs/newsletter-config.js`. The standalone product-site repositories remain
where they were. `.nojekyll` keeps GitHub Pages serving the static files directly.
A noindex `404.html` prevents Cloudflare's default homepage fallback for missing
paths in the next deployment. Legacy Doodle Tag privacy URLs now redirect to
the product site's privacy page instead of an absent local file.

**Eddy requested local review only. Nothing in this migration is committed,
pushed, or deployed. Do not apply the automatic deployment rule until review is
complete.** The public hosts may still serve the earlier test deployment.

For a quick local preview from the repository root:

```sh
python3 -m http.server 8085 --bind 127.0.0.1 --directory docs
```

Open http://localhost:8085/ and check `/about/` and `/botify-agent/`.
This simple server verifies static pages and files; Cloudflare `_redirects`
are deployed rules and are not executed by Python's server. The existing
`scripts/serve-500nits.sh` also uses `docs/` for its hub preview.

A file such as `docs/about/index.html` appears at `https://500nits.com/about/`
once deployed; `docs` is not part of the URL. Only the selected publishing folder
will be included in new deployments. Files inside `docs/` are public, including
any notes accidentally added later. Old deployment preview URLs and stale caches
can still retain older content; cache troubleshooting is deferred at Eddy's request.

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
