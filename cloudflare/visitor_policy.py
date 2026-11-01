"""Manage only the 500nits browser-visits WAF rule; preserve other rules."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from urllib.request import Request

from export import API, DOMAIN, LOCAL, Cloudflare, ExportError, save

POLICY = Path(__file__).with_name("visitor-policy.json")
REF = "500nits_browser_visits"
PHASE = "http_request_firewall_custom"


def write(api, method, path, payload):
    request = Request(API + path, method=method, data=json.dumps(payload).encode(),
                      headers={"Authorization": "Bearer " + api.token, "Content-Type": "application/json"})
    response = json.loads(api.read_response(request))
    if response.get("success") is not True:
        raise ExportError("Cloudflare did not accept the visitor policy")
    return response["result"]


def apply(api, policy, disable=False):
    zones = [z for z in api.listing("/zones", {"name": DOMAIN}) if z.get("name") == DOMAIN]
    if len(zones) != 1:
        raise ExportError("Expected exactly one 500nits.com zone")
    base = "/zones/" + zones[0]["id"] + "/rulesets"
    endpoint = base + "/phases/" + PHASE + "/entrypoint"
    try:
        existing = api.get(endpoint)["result"]
    except ExportError as error:
        if str(error) != "HTTP 404":
            raise
        existing = None
    matches = [r for r in (existing or {}).get("rules", []) if r.get("ref") == REF]
    if len(matches) > 1:
        raise ExportError("Duplicate visitor policy references; inspect before changing")
    if disable and not matches:
        print("Visitor policy is absent; nothing to disable.")
        return
    backup = LOCAL / "visitor-policy" / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    backup.mkdir(parents=True, mode=0o700)
    save(backup / "before.json", {"entrypoint": existing})
    if disable:
        target = base + "/" + existing["id"] + "/rules/" + matches[0]["id"]
        write(api, "PATCH", target, {"enabled": False})
    elif not existing:
        write(api, "POST", base, {"name": "500nits visitor protection", "kind": "zone", "phase": PHASE, "rules": [policy]})
    elif matches:
        target = base + "/" + existing["id"] + "/rules/" + matches[0]["id"]
        write(api, "PATCH", target, policy)
    else:
        write(api, "POST", base + "/" + existing["id"] + "/rules", policy)
    live = api.get(endpoint)["result"]
    save(backup / "after.json", {"entrypoint": live})
    result = [r for r in live.get("rules", []) if r.get("ref") == REF]
    if len(result) != 1 or result[0].get("enabled", True) != (not disable):
        raise ExportError("Policy write was attempted but read-back verification failed; inspect private backup")
    if not disable and any(result[0].get(k) != policy[k] for k in ["action", "expression"]):
        raise ExportError("Policy read-back does not match the requested rule")
    print("Visitor policy " + ("disabled" if disable else "enabled") + "; verified by API read-back.")
    print("Private backup: " + str(backup))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_mutually_exclusive_group()
    commands.add_argument("--apply", action="store_true", help="Deploy the checked-in rule")
    commands.add_argument("--disable", action="store_true", help="Disable only this rule for rollback")
    args = parser.parse_args()
    policy = json.loads(POLICY.read_text())
    if policy.get("ref") != REF or policy.get("action") != "managed_challenge" or policy.get("enabled") is not True:
        raise ExportError("Expected the enabled 500nits managed-challenge policy")
    if not (args.apply or args.disable):
        print(json.dumps(policy, indent=2)); return
    os.umask(0o077)
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip() or (LOCAL / "api-token").read_text().strip()
    try:
        apply(Cloudflare(token), policy, args.disable)
    except ExportError as error:
        if str(error) == "HTTP 403":
            raise ExportError("Cloudflare denied the visitor-policy request (HTTP 403). Add Zone / WAF / Edit for 500nits.com to the API token, then retry. No successful deployment has been verified.") from None
        raise


if __name__ == "__main__":
    try:
        main()
    except (ExportError, OSError, ValueError) as error:
        print("Visitor policy failed: " + str(error), file=sys.stderr)
        sys.exit(1)
