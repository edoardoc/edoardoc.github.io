# 500nits visitor protection

The sites use Cloudflare Pages (hub) and GitHub Pages (product sites), with
Cloudflare proxying their public hostnames. Apache `.htaccess` is not an access
control mechanism on either static host. Use a Cloudflare WAF custom rule.

## Policy

[`visitor-policy.json`](visitor-policy.json) defines one managed-challenge rule.
It covers the apex, www, Doodle Tag, Task, and the intended Eddy hostname. It
matches directory paths, `.html` pages, and extensionless paths. It exempts
Cloudflare-verified bots classified as `Search Engine Crawler`, including Google
and Bing; a claimed user-agent alone does not exempt a request. Other automation,
including preview services and command-line tools, can encounter a challenge.

Static asset URLs, `robots.txt`, and XML sitemaps remain publicly fetchable. These
exclusions avoid putting an HTML challenge in front of scripts, images, and search
discovery files. `/cdn-cgi/` is excluded for Cloudflare's own infrastructure. This
is a basic page-access policy for the current static sites, not an API protection
policy or an asset access-control system. Review it when introducing new routes,
non-HTML page extensions, APIs, or hostnames.

Browsers generally pass Cloudflare's check automatically; some visitors see an
interaction. Some browsers can fail and sophisticated automation can pass. This
does not prove human identity or enforce human-only access. Alternate origin
hostnames such as `pages.dev` or `github.io` are outside this hostname policy.
Origin access restrictions would require a separate hosting assessment.

The reported ~940 historical visits were sampled estimates of arrivals, not
unique people. Raw request hits include assets, bots, and repeated requests.
Compare equal time windows and equivalent metrics. Blocked/challenged requests
can still be counted in Cloudflare edge traffic, so total hits need not converge
to the browser visit count after deploying this policy.

## Deployment and rollback

Requires **Zone / WAF / Edit** on `500nits.com` and existing zone read access.
Use the existing private API-token file or `CLOUDFLARE_API_TOKEN`.

```sh
# Print the exact policy without network requests.
python3 cloudflare/visitor_policy.py

# Apply only this rule, saving before/after state privately.
python3 cloudflare/visitor_policy.py --apply

# Roll back by disabling only this rule.
python3 cloudflare/visitor_policy.py --disable
```

The tool uses a single-rule create/update endpoint when a custom-rules entrypoint
already exists. It never replaces the full rules array. It saves current state
under `.cloudflare-local/visitor-policy/<timestamp>/`, and verifies the result by
reading it back. An HTTP 403 or failed verification is not a successful deployment.
Only an actual 404 is treated as an absent entrypoint. Repository push alone does
not deploy this Cloudflare rule.

After a successful deployment, check the affected sites in a browser, compare
Security Events for this rule, and ensure robots/sitemap/static assets still work.
Spoofing Googlebot in curl cannot test the verified-crawler exception. A full
browser test and observed real verified-crawler requests provide stronger evidence.
Roll back promptly if legitimate page access fails.

## References

- [Cloudflare managed challenges](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/)
- [Verified bot categories](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/)
- [Add one rule while preserving others](https://developers.cloudflare.com/ruleset-engine/rulesets-api/add-rule/)
