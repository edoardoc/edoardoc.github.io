# 500nits visitor protection session

Updated 2026-11-02. Scope authorized by Eddy: **reduce the broad visitor challenge
and update hosting documentation only**. Cache handling and internal-file blocking
are explicitly deferred. Do not purge, add path blocks, or change cache policy.

## Current policy

`cloudflare/visitor-policy.json` now limits Managed Challenge to page requests
whose user agents declare ahrefsbot, semrushbot, mj12bot, dotbot, gptbot, claudebot,
ccbot, or bytespider. Cloudflare-verified Search Engine Crawler bots are exempt.
Normal browsers, generic command-line clients, previews, and monitors no longer
match merely by visiting a page. This is a spoofable identifier filter, not a
human-only guarantee or a scored bot classifier. Do not claim unknown bots are
excluded. The legacy cf.threat_score is always zero; paid bot score is unavailable
for this Free custom policy. Other Cloudflare protections are not modified.

The original blanket challenge was deployed on 2026-11-01. The narrowed policy
was applied in place on 2026-11-02 using `python3 cloudflare/visitor_policy.py
--apply`, with exact action/expression/enabled read-back. The tool saves private
before/after snapshots under `.cloudflare-local/visitor-policy/`. Its single-rule
update preserves other rules. `--disable` disables only this rule.

## Hosting state

The full public hub is in `docs/`, committed/pushed by Eddy as `74858ca` and
verified deployed. GitHub Pages for edoardoc/edoardoc.github.io was disabled by
Eddy; its URL returns 404. Cloudflare Pages remains the hub host. Product-site
GitHub Pages deployments are separate and stay enabled. See `HOSTING.md`.

Removed files can still exist in old cached responses even though the current
unique deployment returns 404. This remains unresolved and intentionally deferred.
The historical ~940 visits were estimated arrivals, not 940 distinct humans.
See `cloudflare/VISITOR-PROTECTION.md` for the current policy and limitations.
