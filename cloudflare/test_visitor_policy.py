"""Verify that deploying and rolling back this policy preserve unrelated rules."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import visitor_policy as policy


class VisitorPolicyTests(unittest.TestCase):
    def test_add_uses_single_rule_endpoint_and_saves_existing_state(self):
        desired = json.loads(policy.POLICY.read_text())
        existing = {"id": "entry", "rules": [{"id": "other", "ref": "unrelated", "action": "block"}]}
        final = {"id": "entry", "rules": existing["rules"] + [{**desired, "id": "mine"}]}
        api = Mock()
        api.listing.return_value = [{"name": "500nits.com", "id": "zone"}]
        api.get.side_effect = [{"result": existing}, {"result": final}]
        with tempfile.TemporaryDirectory() as tmp, patch.object(policy, "LOCAL", Path(tmp)), patch.object(policy, "write") as write:
            policy.apply(api, desired)
            self.assertEqual(write.call_args.args[1:3], ("POST", "/zones/zone/rulesets/entry/rules"))
            self.assertEqual(write.call_args.args[3], desired)
            before = list(Path(tmp).rglob("before.json"))[0]
            self.assertEqual(json.loads(before.read_text())["entrypoint"], existing)

    def test_rollback_only_disables_owned_rule(self):
        desired = json.loads(policy.POLICY.read_text())
        existing = {"id": "entry", "rules": [{"id": "mine", **desired}, {"id": "other", "ref": "unrelated"}]}
        api = Mock()
        api.listing.return_value = [{"name": "500nits.com", "id": "zone"}]
        api.get.side_effect = [{"result": existing}, {"result": {"rules": [{"id": "mine", **desired, "enabled": False}]}}]
        with tempfile.TemporaryDirectory() as tmp, patch.object(policy, "LOCAL", Path(tmp)), patch.object(policy, "write") as write:
            policy.apply(api, desired, disable=True)
            self.assertEqual(write.call_args.args[1:], ("PATCH", "/zones/zone/rulesets/entry/rules/mine", {"enabled": False}))

    def test_permission_error_read_never_becomes_empty_ruleset(self):
        api = Mock()
        api.listing.return_value = [{"name": "500nits.com", "id": "zone"}]
        api.get.side_effect = policy.ExportError("HTTP 403")
        with patch.object(policy, "write") as write, self.assertRaises(policy.ExportError):
            policy.apply(api, json.loads(policy.POLICY.read_text()))
        write.assert_not_called()


if __name__ == "__main__":
    unittest.main()
