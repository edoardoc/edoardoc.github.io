# 500nits visitor protection session

Observed 2026-11-01. Eddy requested basic access protection allowing people and
search engines while reducing other crawlers. The motivating ~940 visits versus
~42,000 hits comparison mixes sampled arrivals with raw requests; neither gives a
verified count of unique humans or a defensible exact bot percentage.

Live DNS inspection confirmed the apex and www use Cloudflare Pages; Doodle Tag
and Task use GitHub Pages. All four hostnames are proxied. Eddy's intended
hostname had no current CNAME/A/AAAA record. `.htaccess` is ineffective on these
hosts, so the prepared implementation is a Cloudflare WAF managed-challenge rule.

Files: `cloudflare/visitor-policy.json`, `cloudflare/visitor_policy.py`, and
`cloudflare/VISITOR-PROTECTION.md`. The rule challenges directory, extensionless,
and `.html` page requests except Cloudflare-verified Search Engine Crawler bots.
It leaves assets, robots.txt, XML sitemaps, and Cloudflare infrastructure open.
It is not proof of human identity, a complete asset/API gate, or protection of
alternate origin hostnames. Normal browsers may be challenged; some can fail.
Edge request totals can still include rejected/challenged traffic.

**Deployment is blocked, not active:** `python3 cloudflare/visitor_policy.py
--apply` returned HTTP 403. The user was asked to add Zone → WAF → Edit scoped to
500nits.com to the existing token. No successful deployment was verified. Do not
report visitor protection as enabled merely because these files were committed.

Before the attempt, a fresh baseline was saved in
`.cloudflare-local/snapshots/20261101T180345.936722Z/`. The export was partial
(exit 2): two individual ruleset reads returned HTTP 403. The WAF custom-rules
entrypoint read returned HTTP 404. Bot-management configuration read returned
HTTP 403, so its current toggle values are unknown. The policy tool separately
saves before/after WAF state privately under `.cloudflare-local/visitor-policy/`.

Next: after the token update, apply the policy, read back the exact action,
expression, and enabled flag, then check browser page access and public discovery
files on each live hostname. Verified-crawler access cannot be tested by spoofing
a Googlebot user-agent. To roll back, run `python3 cloudflare/visitor_policy.py
--disable`, which only disables the rule with ref `500nits_browser_visits`.
Update this note with the actual outcome. Do not replace other WAF rules.
