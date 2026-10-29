# 500nits domain configuration

This directory is the starting point for managing `500nits.com` from this repository.
The exporter reads the live Cloudflare API; it does not apply changes. A snapshot is
observed state, not a configuration file that is automatically deployed on push.

## Export current configuration

Use Python 3.10 or newer. No third-party packages are needed.

1. Create a Cloudflare API token scoped to `500nits.com` with read permissions for
   Zone, DNS, Zone Settings, Page Rules, Workers Routes, Email Routing Rules, and
   the rulesets used by the zone (including redirects).
2. Save only the token value to `.cloudflare-local/api-token` at the repository root,
   or supply it through the `CLOUDFLARE_API_TOKEN` environment variable. Do not put
   the token in a command argument, a tracked file, or chat.
3. Run from the repository root:

   ```sh
   python3 cloudflare/export.py
   ```

Each run creates a new `.cloudflare-local/snapshots/<UTC timestamp>/` directory.
Read its `manifest.json` first: it records each endpoint, export status, counts,
and coverage limitations. An unavailable section is not evidence that there is
no configuration. Exit status 2 means some sections could not be exported;
status 1 means startup or authentication failed.

The snapshot includes DNS records and a BIND zone export; DNS settings and DNSSEC;
zone settings such as TLS and HTTPS; Page Rules; zone rulesets and their details;
Worker routes; and Email Routing settings, DNS, rules, and the catch-all rule.
List endpoints are paginated. API requests use GET only. Exports are sequential
observations, not a transactionally consistent backup.

Account-level bulk redirects, account-level email rules and destination verification,
Worker code and bindings, Pages projects, registrar settings, and other account
products require separate exports. External mailbox configuration is not available
through the Cloudflare zone API. These exclusions are also recorded in the manifest.

## Local data and version control

Full snapshots stay local and are ignored by Git: they may reveal origin addresses,
email forwarding destinations, verification records, or private rule values.
The API token is never copied into a snapshot. New export files are owner-readable
and owner-writable only. Keep backups of this local directory separately if needed.
Do not force-add it to Git or include it in a static hosting upload.

The tracked exporter and documentation provide the repeatable workflow. Before
adding a configuration change workflow, compare a fresh export with the baseline
and review the exact proposed changes. No DNS apply command exists yet.

## Existing redirect

`www-redirect.js` is the existing Worker source; `../wrangler.www-redirect.jsonc`
defines its deployment route. This source alone does not establish what is live.
`../_redirects` contains hosting redirects, which are separate from DNS records and
Cloudflare zone rules.

## API references

- [DNS records and exports](https://developers.cloudflare.com/api/resources/dns/)
- [Zone settings](https://developers.cloudflare.com/api/resources/zones/subresources/settings/methods/list/)
- [Rulesets](https://developers.cloudflare.com/ruleset-engine/rulesets-api/view/)
- [Email Routing](https://developers.cloudflare.com/api/resources/email_routing/)
- [Worker routes](https://developers.cloudflare.com/api/resources/workers/subresources/routes/)
- [API token permissions](https://developers.cloudflare.com/fundamentals/api/reference/permissions/)
