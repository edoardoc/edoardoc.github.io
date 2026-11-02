# How 500nits is published

Verified on 2026-11-02. **GitHub stores the code; Cloudflare Pages hosts the hub.**

```text
GitHub: edoardoc/edoardoc.github.io, master, docs/
    → Cloudflare Pages: edoardoc-github-io
    → https://500nits.com/
```

| Address | Current role |
| --- | --- |
| https://500nits.com/ | Canonical public hub, hosted on Cloudflare Pages |
| https://www.500nits.com/ | Redirects to the apex using the existing Worker |
| https://edoardoc-github-io.pages.dev/ | Cloudflare project alias; also serves the site |
| https://edoardoc.github.io/ | GitHub Pages disabled by Eddy; public URL verified HTTP 404 |

The separate GitHub Pages publication was redundant. Disabling it does not stop
Cloudflare's Git integration: pushes to `master` still trigger Cloudflare builds.
Do not re-enable GitHub Pages for this hub repository. GitHub's API can retain
old source/deployment metadata after unpublishing; the old `master` → `/docs`
metadata is not evidence that the public GitHub site is currently online.

## Confirmed Cloudflare configuration

| Setting | Value |
| --- | --- |
| Project | `edoardoc-github-io` |
| Connected repository | `edoardoc/edoardoc.github.io` |
| Production branch | `master` |
| Build command | Empty |
| Root directory | Empty (repository root) |
| Build output directory | `docs` |
| Custom domains | `500nits.com`, `www.500nits.com` |

DNS sends apex and www to `edoardoc-github-io.pages.dev`, with proxying enabled.
Cloudflare publishes `docs/` independently of GitHub Pages settings.

## Public files and verification

The full hub migration was committed and pushed by Eddy as `74858ca` and verified
successfully deployed on Cloudflare. It is no longer a local-only/test migration.
The homepage, About, Botify, assets, newsletter scripts/configuration, robots.txt,
sitemap.xml, redirects, and 404 page live in `docs/`. Their public URLs are unchanged.

Internal material stays outside `docs/`: agent instructions, memory, tooling,
credentials, setup notes, and drafts. Newsletter instructions are in
`memory/newsletter.md`; its generator writes `docs/newsletter-config.js`.
The sitemap audit runs the full production checks again.

The new deployment serves the public pages successfully, returns 404 for absent
internal files, and applies the Doodle Tag redirects. Its `404.html` prevents the
old default homepage fallback. Only files intentionally placed in `docs/` belong
in future deployments. The `.nojekyll` file is harmless and can stay.

## Visitor challenges

The former all-visitors gate was narrowed on 2026-11-02. Normal page requests
are no longer selected by that custom rule. Only page requests declaring one of
the documented bulk/AI crawler identifiers are selected, with verified search
crawlers exempt. This is a limited deterrent, not human identification.
See [visitor protection](cloudflare/VISITOR-PROTECTION.md).

## Cache issue: intentionally deferred

Some exact old internal-file URLs still return retained content from an earlier
root deployment, although the current deployment and fresh URLs return 404.
This is distinct from whether the latest commit deployed. Cloudflare documents
that old assets may remain cached for up to one week:
[Serving Pages](https://developers.cloudflare.com/pages/configuration/serving-pages/#asset-retention).

Eddy explicitly requested waiting on the cache. Do not purge caches, change cache
rules, add internal-path blocking, or remove old deployments as part of the current
visitor-policy/documentation task. The old retained URLs have not been declared
fixed. Private evidence is in `.cloudflare-local/deployment-audit/`.

## Local preview

```sh
python3 -m http.server 8085 --bind 127.0.0.1 --directory docs
```

Open http://localhost:8085/ and check `/about/` and `/botify-agent/`.
This simple server serves files; it does not execute Cloudflare `_redirects`.
`scripts/serve-500nits.sh` also uses `docs/` for the hub preview.

## Other sites

Doodle Tag and Task use separate repositories and GitHub Pages deployments.
Their publishing settings are unchanged. Do not disable their Pages sites when
maintaining this hub. See [the site inventory](.agents/SITES.md).
