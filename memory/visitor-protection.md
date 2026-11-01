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

**Active as of 2026-11-01:** after the user updated token permissions,
`python3 cloudflare/visitor_policy.py --apply` succeeded. API read-back verified
one enabled `500nits_browser_visits` rule with the exact checked-in action and
expression. Before/after state and live-check results are saved privately in
`.cloudflare-local/visitor-policy/20261101T181346.219622Z/`.

Live checks: the apex, www, Doodle Tag, and Task page requests from curl received
HTTP 403 with `cf-mitigated: challenge`. A spoofed Googlebot user-agent was also
challenged. Each published site's robots.txt and sitemap.xml returned HTTP 200,
as did a sampled asset per site (hub.css, feature_graphic.svg, icon.png). These
prove the edge rule is taking effect and the sampled exclusions work. The search
crawler exception is configured but was not tested from a genuinely verified
crawler IP. A full browser challenge solve was not tested because browser
automation was unavailable. Do not claim every real person can pass or every bot
will fail. No other firewall rules or Bot Fight Mode toggles were changed.

Before the attempt, a fresh baseline was saved in
`.cloudflare-local/snapshots/20261101T180345.936722Z/`. The export was partial
(exit 2): two individual ruleset reads returned HTTP 403. The WAF custom-rules
entrypoint read returned HTTP 404. Bot-management configuration read returned
HTTP 403, so its current toggle values are unknown. The policy tool separately
saves before/after WAF state privately under `.cloudflare-local/visitor-policy/`.

Next: check page access in a regular browser, then review real verified-crawler
requests and challenge events as they arrive. Verified-crawler access cannot be tested by spoofing
a Googlebot user-agent. To roll back, run `python3 cloudflare/visitor_policy.py
--disable`, which only disables the rule with ref `500nits_browser_visits`.
Update this note with the actual outcome. Do not replace other WAF rules.
