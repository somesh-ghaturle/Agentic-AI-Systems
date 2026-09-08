# Static check on what turning on the knowledge private endpoint does to the handlers.
#
# In prod and staging, supplying `knowledge_private_dns_zone_ids` creates a private endpoint
# for AI Search and sets `public_network_access_enabled = false` in the same breath. No
# Function App in this tree is VNet-integrated, so the public route closes and no handler has
# a private one: retrieval fails at the network layer while every role assignment still reads
# as correct.
#
# The AWS tree has the same gap with the strict setting hardcoded in prod, guarded by
# infra/terraform-aws/tests/test_knowledge_reachability.py. Here it is worse in one respect —
# the trigger is an operator supplying a DNS zone id, which reads like a hardening step, so
# the failure arrives on the deploy that was meant to tighten things.
#
# What this guards is the pair staying honest: add VNet integration and the module note is
# wrong; drop the note and the trigger goes back to looking safe.
#
#     python3 -m unittest discover -s infra/terraform-azure/tests

import os
import re
import unittest

from test_write_boundary import TREE, strip_comments_preserving_lines, tf_files

# The lead of the caveat in the private endpoint block.
CAVEAT = "WHAT IT REMOVES IS NOT REPLACED"

VNET_INTEGRATION = re.compile(r"virtual_network_subnet_id\s*=")
COUPLED = re.compile(
    r"public_network_access_enabled\s*=\s*var\.knowledge_private_dns_zone_ids\s*==\s*null"
)

KNOWLEDGE = os.path.join(TREE, "modules", "knowledge", "main.tf")


def read(path):
    """The tree's own helper lives in the write-boundary module and takes no path."""
    with open(path, encoding="utf-8") as handle:
        return strip_comments_preserving_lines(handle.read())


class TestPrivateEndpointLeavesHandlersOutside(unittest.TestCase):
    def test_no_function_app_is_vnet_integrated(self):
        integrated = [
            os.path.relpath(path, TREE)
            for path in tf_files()
            if VNET_INTEGRATION.search(read(path))
        ]
        self.assertEqual(
            integrated,
            [],
            f"VNet integration appeared in {integrated}. That closes the gap this file "
            "guards, and it falsifies the note in modules/knowledge/main.tf, "
            "infra/CHOOSING-A-TREE.md section 4, and .checkov.yaml (CKV_AZURE_221). Update "
            "those, then this test.",
        )

    def test_roots_that_close_the_public_route_keep_the_caveat(self):
        coupled = sorted(
            os.path.relpath(os.path.dirname(path), TREE)
            for path in tf_files()
            if COUPLED.search(read(path))
        )
        self.assertEqual(coupled, ["envs/prod", "envs/staging"])

        with open(KNOWLEDGE, encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn(
            CAVEAT,
            source,
            f"{', '.join(coupled)} close the public route to AI Search the moment a DNS zone "
            "id is supplied, while no handler is inside the VNet. modules/knowledge/main.tf "
            "has to say so.",
        )


if __name__ == "__main__":
    unittest.main()
