# 500nits SEO and web presence playbook

Use this playbook for every public-page, metadata, URL, redirect, sitemap, robots, or launch change. It is designed for small static sites and favors durable search signals over SEO add-ons.

## Page intent

Classify every public HTML page before editing it.

- **Indexable:** useful as a standalone search result. Include it in the site's sitemap and give it complete metadata.
- **Utility:** needed by users or an app but not useful as a search result. Add `noindex` and omit it from the sitemap.
- **Retired or duplicate:** permanently redirect it to the closest useful canonical page when possible. If it must remain accessible, align its canonical signal deliberately.

Do not use `robots.txt` to solve duplicate content or canonicalization. A blocked page can still be indexed without its content being crawled.

## Indexable page contract

Each indexable page must have:

- a successful HTTPS response on its canonical hostname;
- valid HTML with a language declaration and a mobile viewport;
- a unique, concise `<title>` that describes the page;
- a unique meta description grounded in visible page content;
- one self-referencing absolute HTTPS canonical link;
- an indexable robots directive and no conflicting `X-Robots-Tag`;
- one clear primary heading and substantive visible text;
- crawlable HTML links for primary navigation and related 500nits properties;
- useful alternative text for informative images and empty alternative text for decorative images.

The title, visible heading, Open Graph title, structured data name, and anchor text do not need to be identical, but they must describe the same page without keyword stuffing.

## Canonical and duplicate-content rules

- Pick one canonical origin and trailing-slash convention for each URL.
- Make redirects, canonical tags, internal links, sitemap entries, social URLs, and structured data agree.
- Use permanent server-side redirects for retired duplicate URLs when hosting supports them.
- Keep the hub's app overview distinct from the canonical product site. The overview should explain the studio relationship and send readers to the product site; the product site should own detailed product, store, support, and privacy intent.
- Do not list redirected, noncanonical, `noindex`, error, or cross-host URLs in a site's sitemap.

## Discovery files

Each site root must contain:

- `robots.txt` with the intended crawl policy and an absolute `Sitemap:` line;
- `sitemap.xml` with UTF-8 XML and fully qualified canonical URLs;
- `CNAME` for GitHub Pages product sites, containing the exact hostname.

Keep one hostname per sitemap unless there is a deliberate, verified cross-site sitemap design. Sitemaps are discovery hints and canonical signals, not indexing guarantees.

## Social and structured data

- Add `og:type`, `og:title`, `og:description`, `og:url`, and an absolute `og:image` to shareable pages. Add a suitable Twitter/X card declaration.
- Prefer a purpose-made social image near 1200 by 630 pixels and provide accurate dimensions and alt text when practical.
- Use JSON-LD only for entities visible on the page. `Organization`, `WebSite`, `Article`, and `SoftwareApplication` are useful when the page supports them.
- Validate structured data before deployment. Never fabricate prices, ratings, reviews, platform support, versions, release dates, or availability.

## Content and site relationships

- Write for the person searching for the product or problem. Explain what the app does, supported platforms, its current availability, and the next useful action.
- Keep store, support, privacy, and press links current and crawlable.
- Link every live product site from the hub and link back to the hub from each product site where it fits naturally.
- Keep privacy and support pages specific enough to answer their search intent; avoid thin placeholders.
- Use descriptive internal anchor text. Avoid repeated generic links such as “click here.”

## Required verification

Before deployment:

1. Run `node scripts/audit-seo.mjs` from the root.
2. Review the diff for accidental canonical-host, brand-case, robots, and sitemap changes.
3. Check each affected Git worktree so unrelated changes remain unstaged.

After deployment, verify every affected site:

1. The canonical page returns a successful HTTPS response.
2. `robots.txt` and `sitemap.xml` return successful responses with suitable content types.
3. The live title, description, canonical, robots directive, and primary heading match the intended source.
4. Every submitted sitemap URL resolves without a redirect or error and declares itself canonical.
5. The hub and product-site links work in both directions where required.
6. Follow `.agents/SEARCH_CONSOLE.md` for sitemap submission and index inspection.

## Official references

- Google SEO Starter Guide: https://developers.google.com/search/docs/fundamentals/seo-starter-guide
- Canonical URL guidance: https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
- Sitemap guidance: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
- Software app structured data: https://developers.google.com/search/docs/appearance/structured-data/software-app
- Requesting a recrawl: https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl
