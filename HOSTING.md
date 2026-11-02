# How 500nits is published

Checked on 2026-11-02. **Two separate hosting services deploy this repository.**
They use the same GitHub commits, but have independent publishing settings.

| Address | Hosting service | Files currently served |
| --- | --- | --- |
| https://edoardoc.github.io/ | GitHub Pages | `master`, `/docs` |
| https://500nits.com/ | Cloudflare Pages project `edoardoc-github-io` | Repository-root website |
| https://edoardoc-github-io.pages.dev/ | The same Cloudflare Pages project | The same repository-root website |

Changing GitHub Pages to `/docs` changes only the first row. Cloudflare Pages
does its own deployment; it does not copy the finished `edoardoc.github.io` site.
Recent GitHub commits have separate successful GitHub Pages and Cloudflare Pages
deployment checks.

## Why the addresses show different pages

GitHub's API confirms `master` → `/docs`, with no custom domain attached to that
GitHub Pages site. The public GitHub homepage exactly matches `docs/index.html`,
which is currently a small test page.

Cloudflare DNS sends `500nits.com` and `www.500nits.com` to
`edoardoc-github-io.pages.dev`, with proxying enabled. The `pages.dev` homepage
exactly matches the repository-root `index.html`.

Both `https://500nits.com/AGENTS.md` and
`https://edoardoc-github-io.pages.dev/AGENTS.md` return the repository-root
`AGENTS.md`. Root-level development files are therefore still in the Cloudflare
deployment. The Cloudflare visitor challenge is not a deployment-file exclusion.

Cloudflare's project API confirms these settings:

| Setting | Current value |
| --- | --- |
| Connected repository | `edoardoc/edoardoc.github.io` |
| Production branch | `master` |
| Build command | Empty (no build command) |
| Root directory | Empty (repository root) |
| Build output directory | Empty (publishes from the root) |
| Custom domains | `500nits.com`, `www.500nits.com` |

The mismatch is therefore GitHub's `/docs` setting versus Cloudflare's root
publishing settings. Changing one service does not update the other.

## Keep the current work in place

Eddy explicitly asked not to move files while work is in progress. This
investigation changes documentation only. No website files were relocated and
neither service's publishing settings were changed.

`docs/` currently contains a test homepage and a newsletter setup note. It is
not yet a complete replacement for the root website. Pointing Cloudflare there
now would replace the production hub with the test and omit its other files.

## When the website folder is ready

1. Finish assembling the intended public website in the chosen folder, including
   all pages, assets, `robots.txt`, `sitemap.xml`, and Cloudflare `_redirects`.
   Keep agent instructions, memory, setup notes, and tooling outside that folder.
2. For a shared `docs/` setup, keep GitHub Pages on `master` → `/docs`.
3. In Cloudflare's `edoardoc-github-io` Pages project, set the build output to
   `docs` relative to the repository root. Check the existing root/build settings
   first; a configured project root can change how output paths are resolved.
4. Redeploy Cloudflare Pages and verify the custom domain **and** the `pages.dev`
   address. Public pages/assets must work and internal files must no longer be
   served. A bot challenge alone does not establish that a file was removed.
5. Update `.agents/SITES.md`, `.agents/sites.json`, local preview, and audit paths
   together when the actual source directory changes.

Publishing-folder names do not appear in website URLs: `docs/about/index.html`
would still be `https://500nits.com/about/` when `docs` is the published root.

## Other sites

Doodle Tag and Task have their own repositories and GitHub Pages deployments.
They are not published from this repository's `docs/` folder. See
[the site inventory](.agents/SITES.md) for repository boundaries. The separate
`500nits-www-redirect` Worker source/configuration is in `cloudflare/` and
`wrangler.www-redirect.jsonc`; it does not choose the Pages output directory.

References: [GitHub publishing sources](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site),
[Cloudflare build/output directories](https://developers.cloudflare.com/pages/configuration/build-configuration/).
