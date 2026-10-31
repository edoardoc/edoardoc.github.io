# 500nits analytics and SEO controls

The Analytics dashboard contains observations of traffic. This repository can
export them, filter and compare saved results, and use them to inform changes.
It cannot edit historical traffic counts or treat those counts as search rankings.

## Available exports

Run `python3 cloudflare/export.py --analytics` from the repository root. It saves
the zone configuration and these reports under the timestamped, Git-ignored
`.cloudflare-local/snapshots/` directory:

| File | Information |
| --- | --- |
| `analytics/traffic.json` | Rolling 24-hour requests, bytes, visits metric, hourly activity, hostnames, response codes, countries, paths, and cache status |
| `analytics/referrers.json` | Referring hostnames when available to the token and plan |
| `analytics/crawler-traffic.json` | Selected search and AI crawler user-agent matches by hostname and response code |
| `analytics/README.md` | Summary and coverage for that snapshot |

These queries read `httpRequestsAdaptiveGroups` through the
[GraphQL Analytics API](https://developers.cloudflare.com/analytics/graphql-api/).
They use the same underlying API as Cloudflare traffic and crawler reports; they
do not promise to reproduce every dashboard panel or default filter.

Numbers can be sampled estimates. Requests include bots and assets. The reports
only cover traffic passing through Cloudflare, and each breakdown is capped at
500 groups with possible truncation recorded. User-agent matches can be spoofed
and are not verified identities. Referrers do not expose search queries or prove
organic-search conversions. Match the time window, timezone, metric, and filters
before comparing an export with the dashboard. Hourly rows are returned by request
count and must be sorted by timestamp before plotting them as a time series.

Cloudflare's browser-beacon Web Analytics/RUM and Google Search Console are separate
sources and are not queried by this exporter. Search Console is the relevant source
for Google's recorded indexing, impressions, clicks, and query performance; follow
`../.agents/SEARCH_CONSOLE.md` before accessing it.

## Configuration that can affect SEO

`--seo` adds Bot Management/managed robots configuration, stored Speed/Observatory
reports, and crawler analytics. It does not start tests or enable tracking.

| Feature | Read or observe | How changes are made |
| --- | --- | --- |
| HTTPS, TLS, cache, browser checks | Existing zone settings export | Zone Settings API with write permission, after choosing exact values |
| Bot policy and managed robots.txt | Bot Management API via `--seo` | Bot Management API with write permission; fields depend on plan |
| Redirects and crawler access rules | Page Rules, ruleset, and Worker-route exports | Relevant rules APIs or the existing Worker deployment |
| Speed/Observatory | Existing tested-page reports via `--seo` | Separate test/schedule APIs; no tests are started by exports |
| Crawler Hints | Dashboard; current status is not exported | Dashboard workflow; no supported public API was identified in the reviewed official docs |
| Titles, descriptions, canonicals, sitemap, origin robots.txt | Site source and deployed responses | Edit the appropriate site repository and follow the SEO release checklist |

No apply command is implemented. To change a policy, first capture its current
state and choose the exact desired values. Use the relevant API with suitable
write access, verify the saved response and served behavior, and capture the new
state. This request has not selected or applied any policy changes.

## Permissions

- Existing Zone Settings Read permits the stored Speed/Observatory page listing.
- Bot Management Read is required to inspect bot and managed robots settings;
  Bot Management Write is required to change them.
- Analytics requires access to the requested GraphQL dataset and zone. Cloudflare's
  [token guide](https://developers.cloudflare.com/analytics/graphql-api/getting-started/authentication/api-token-auth/)
  describes Account Analytics Read; token scope, dataset entitlements, and plan
  restrictions can still limit fields. Test existing access before expanding it.
- HTTP or GraphQL errors are recorded in `manifest.json`. Missing permissions,
  unavailable fields, and empty successful results are different states.

## Official references

- [HTTP traffic analytics](https://developers.cloudflare.com/analytics/graphql-api/tutorials/end-customer-analytics/)
- [AI Crawl Control analytics](https://developers.cloudflare.com/ai-crawl-control/reference/graphql-api/)
- [Read bot configuration](https://developers.cloudflare.com/api/resources/bot_management/methods/get/)
- [Update bot configuration](https://developers.cloudflare.com/api/resources/bot_management/methods/update/)
- [Stored Speed reports](https://developers.cloudflare.com/api/resources/speed/subresources/pages/methods/list/)
- [Crawler Hints](https://developers.cloudflare.com/cache/advanced-configuration/crawler-hints/)
