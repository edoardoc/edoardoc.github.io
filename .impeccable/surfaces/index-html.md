---
version: 1
slug: "index-html"
primary_target: "index.html"
related_targets: ["hub.css","newsletter.js"]
---

# Hub homepage

Scope: index.html, hub.css, newsletter.js. Mode: Persuade.
Audience: visitors discovering Eddy's independent software. Action: explore a product or subscribe for updates.

## Direction contract

THESIS: A small independent software label expressed as a simple printed correspondence sheet. Products and the maker's invitation carry the page.

OWN-WORLD: The existing navy mark, white paper, Karla lettering, generous margins, ordinary underlined links, and a single navy signup region. No gradients, shadows, cards, or decorative animation.

STORY: The visitor meets Eddy, sees a clear invitation to receive product news, and browses the two apps and Botify. Personal writing stays on Eddy's site.

FIRST VIEWPORT: A compact mark and wordmark at left, plain navigation at right. A large two-line introduction pairs with a short first-person note. Immediately below, a navy signup block places the invitation beside a labeled email field and subscription action. Mobile stacks these elements in reading order. Signature interaction: the Updates navigation brings focus to the form; no motion beyond native feedback, respecting the user's restrained brief.

FORM: Candidate 4, independent-maker correspondence sheet. seed:9657ab0a8f202f16. The brief pins navy/white, simplicity, and lo-fi restraint; alternatives adding theatrical interface metaphors conflict with those constraints. Other grounded forms considered: small catalog, release bulletin, workshop index, correspondence sheet, software directory, folded leaflet, maker colophon.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Open decisions

No newsletter account or endpoint supplied. Use an honest email-request fallback that opens the visitor's mail app, with explicit copy requiring them to send. Do not claim an automated subscription or unsubscribe mechanism until a verified hosted form is connected. Build directly in code for this session; no standing build-path preference is recorded without an answer.

Current navigation uses the hub's /about/ page. Do not link to the unfinished personal writing site. The signup note requires sending an email and explains how to unsubscribe; the form remains a manual email request until a verified newsletter endpoint is supplied.
