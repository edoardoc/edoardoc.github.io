# 500nits visitor protection

The Cloudflare WAF rule in `visitor-policy.json` is a **targeted crawler deterrent**.
The previous policy challenged every ordinary page visitor. On 2026-11-02 Eddy
requested reducing that friction; the rule was narrowed in place.

## Current policy

It covers the apex, www, Doodle Tag, Task, and the intended Eddy hostname. Only
requests for directory, extensionless, and `.html` page paths that identify with
one of these case-insensitive user-agent strings match:

- `ahrefsbot`, `semrushbot`, `mj12bot`, `dotbot`
- `gptbot`, `claudebot`, `ccbot`, `bytespider`

Matching requests receive **Managed Challenge**. Cloudflare-verified bots in the
`Search Engine Crawler` category are exempt. Generic browser, curl, preview, and
monitoring user agents do not match this rule merely because they request a page.
Assets, robots.txt, XML sitemaps, and `/cdn-cgi/` remain outside its page filter.
Other independent Cloudflare protections can still challenge traffic.

User-agent identifiers can be spoofed or changed. Unknown automation and bots
claiming to be browsers can pass. This is not a human-only guarantee or a verified
bot classifier. The Free plan does not expose the paid bot-score field for this
custom rule; the legacy `cf.threat_score` is always zero and must not be used as
an alternative classifier. No broad Bot Fight Mode toggle was enabled or changed.
Alternate origin URLs remain outside this hostname policy.

No cache purge, cache-rule edit, or internal-path block is part of this change.

## Apply and disable

Requires Zone / WAF / Edit on `500nits.com` plus zone read access. The token is
read from the private `.cloudflare-local/api-token` or `CLOUDFLARE_API_TOKEN`.

```sh
# Inspect the exact rule without network requests.
python3 cloudflare/visitor_policy.py

# Apply only this rule, saving before/after state and verifying read-back.
python3 cloudflare/visitor_policy.py --apply

# Disable only this rule if it causes problems.
python3 cloudflare/visitor_policy.py --disable
```

The tool updates the single rule with ref `500nits_browser_visits` and preserves
other rules. Private snapshots are in `.cloudflare-local/visitor-policy/`.
A successful API read-back verifies configuration; live requests verify behavior.
The original blanket policy is retained in earlier private snapshots, not as the
default rule to reapply. A repository push alone does not update this WAF rule.

The protection does not make hits equivalent to people. Requests include assets
and automation; Web Analytics visits are sampled arrivals, not unique humans.

## References

- [Managed challenges](https://developers.cloudflare.com/cloudflare-challenges/challenge-types/challenge-pages/)
- [Verified bot categories](https://developers.cloudflare.com/bots/concepts/bot/verified-bots/)
- [Threat score no longer classifies risk](https://developers.cloudflare.com/ruleset-engine/rules-language/fields/reference/cf.threat_score/)
