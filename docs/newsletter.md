# 500nits product updates

The homepage collects email signups directly into Nitrosend list 13128. It uses Nitrosend's public website key named 500nits and the documented POST /v1/public/contacts endpoint. The site stays static; no server or paid form service is required.

## Configuration

The local .env file is ignored by Git and has owner-only permissions. It contains NITROSEND_PUBLIC_KEY and NITROSEND_LIST_ID. Run `node scripts/configure-newsletter.mjs` after changing either value. The generator writes only those two public signup fields to newsletter-config.js; it rejects keys without the wpkey_live_ prefix.

newsletter-config.js is intentionally tracked and browser-visible because Nitrosend website keys are public. The .env file and any unrelated environment values are not published. Never use an account secret key in the browser configuration.

## Form behaviour

newsletter.js sends only the email address, destination list ID, homepage source URL, and company honeypot field. It omits browser credentials. The field remains labeled and uses native email validation. Submission disables the button and announces progress. The form shows success only after an HTTP success response containing ok: true. Errors preserve the email field for retry; network requests time out after 15 seconds. No visitor email address is logged or stored in the browser.

Nitrosend's hidden company honeypot is retained. The API ignores filled honeypots without creating contacts or triggering flows. Normal successful signups may enter any list-add automation already configured by the account owner. This integration does not create or activate campaigns or automations. Without JavaScript, the form offers an email contact link.

## Free-plan limits

Checked on 2026-11-02: Nitrosend's current pricing lists unlimited stored contacts and API access on Free, with 5,000 non-expiring starter emails and then 500 emails per month. No card is required. Collection does not require a paid feature. Sending, verification, enrichment, and optional services have separate allowances. The public website key cannot read the account's billing plan or balance, so published Free limits are not proof of the account's current billing state. No billing changes, paid features, verification purchases, or new delivery flows are part of this integration.

Sources: https://nitrosend.com/pricing and https://docs.nitrosend.com/guides/website-signup-forms.

## Verification

Validate the key and CORS with an empty payload, which cannot create a subscriber. A filled-honeypot request can exercise the real public endpoint without creating a contact or triggering a flow. Browser checks should intercept the API request and verify successful, rejected, rate-limited, malformed, offline, timeout, and duplicate-submit handling without adding test contacts.
