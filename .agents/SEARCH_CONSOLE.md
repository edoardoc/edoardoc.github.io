# 500nits Google Search Console playbook

Use this playbook when the user asks to verify ownership, submit or remove a sitemap, inspect indexing, request a recrawl, or review search performance.

## Property strategy

The default property is `sc-domain:500nits.com`.

A Search Console domain property includes the apex domain, every subdomain, every path, and supported protocol variants. It is therefore the long-lived property for `500nits.com`, `doodletag.500nits.com`, `task.500nits.com`, and future `*.500nits.com` sites. Domain-property verification is done with DNS.

Create an additional URL-prefix property such as `https://task.500nits.com/` only when separate reporting, narrower access, or a property-scoped integration justifies it. A separate property is not required for the domain property to cover that subdomain.

Do not commit DNS verification values, OAuth credentials, access tokens, cookies, or account exports to this repository.

## Direct Search Console workflow

Use the Codex in-app browser for `https://search.google.com/search-console/` when browser access is available. Work from the visible interface and current authenticated account; do not guess selectors or URLs. If sign-in, a password, an authentication code, a CAPTCHA, or account recovery is required, hand that step to the user.

For a new site or material URL change:

1. Read `.agents/SITES.md` and identify the canonical site and Git worktree.
2. Run the local SEO audit, deploy, and complete the live checks in `.agents/SEO.md`.
3. Open Search Console and select the `500nits.com` domain property. If it does not exist, prepare to add it and surface the DNS verification requirement to the user.
4. Open the Sitemaps report and submit the site's full sitemap URL, for example `https://task.500nits.com/sitemap.xml`.
5. Verify that Search Console accepted the exact sitemap URL. Later processing success is a separate state; report it only when the UI shows it.
6. Inspect the canonical homepage and any newly launched or materially corrected high-value pages.
7. Compare Google's selected canonical, indexing state, last crawl, robots state, referring sitemap, and fetch result with the repository's intended signals.
8. Use **Request indexing** only after the live page is correct. Reserve it for a small set of important URLs; repeated requests do not make crawling faster.

Follow the browser's action-time confirmation requirements for external changes. A user request to perform a specific submission supplies task intent, but it does not authorize handling passwords, authentication codes, or unrelated account changes.

## API boundary

The general Search Console API can:

- list and manage Search Console properties;
- list, inspect, submit, and delete sitemap submissions;
- query Search Analytics data;
- inspect Google's stored index status for a URL.

The URL Inspection API does not test the live URL and does not provide a general request-indexing method. Google's separate Indexing API is restricted to eligible `JobPosting` pages and livestream pages with `BroadcastEvent` in `VideoObject`; do not use it for ordinary 500nits pages. For an ordinary page-level recrawl request, use the Search Console URL Inspection UI.

If API automation is added later, use OAuth with the minimum required scope and a local credential store outside the repository. Keep write commands explicit about the property and full sitemap URL, and show the planned target before execution.

## Reporting states accurately

Use these terms precisely:

- **Live:** the deployed URL returns the intended page.
- **Discoverable:** linked and/or listed in a reachable sitemap.
- **Submitted:** Search Console accepted the sitemap or recrawl request.
- **Processed:** Search Console processed the submitted sitemap.
- **Crawled:** Google reports a crawl for the URL.
- **Indexed:** URL Inspection reports that the canonical URL is in Google's index.

Never collapse these into “indexed.” Indexing is not guaranteed by a sitemap submission or a recrawl request and may take days or weeks.

When reporting a Search Console action, include the property, exact sitemap or page URL, action, visible result, and date. Do not expose account identifiers or private performance data unless the user requests it.

## Official references

- Add and understand properties: https://support.google.com/webmasters/answer/34592
- Verify site ownership: https://support.google.com/webmasters/answer/9008080
- Search Console API reference: https://developers.google.com/webmaster-tools/v1/api_reference_index
- Submit a sitemap with the API: https://developers.google.com/webmaster-tools/v1/sitemaps/submit
- URL Inspection API: https://developers.google.com/webmaster-tools/v1/urlInspection.index/inspect
- Indexing API eligibility: https://developers.google.com/search/apis/indexing-api/v3/using-api
- Request a recrawl: https://developers.google.com/search/docs/crawling-indexing/ask-google-to-recrawl
