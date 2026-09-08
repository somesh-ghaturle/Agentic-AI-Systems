# Static checks on the path between a Function App and the private endpoint on AI Search.
#
# This file used to assert that no Function App was VNet-integrated, which was true and was
# the problem: supplying `knowledge_private_dns_zone_ids` in prod or staging creates the
# private endpoint and sets `public_network_access_enabled = false` in the same breath, so
# the public route closed and no handler had a private one. The delegated subnet in
# modules/networking and the `virtual_network_subnet_id` on each Function App are the other
# half, and what is guarded now is that the two stay together.
#
# The Y1 exception is real and is not a gap. The Consumption plan has no VNet integration at
# any price, so dev does not wire it and staging follows its own SKU rather than assuming
# EP1 — which is exactly why staging cannot rehearse the private path on the cheap plan.
#
#     python3 -m unittest discover -s infra/terraform-azure/tests

import os
import re
import unittest

from test_write_boundary import block_body, strip_comments_preserving_lines, tf_files

COUPLED = re.compile(
    r"public_network_access_enabled\s*=\s*var\.knowledge_private_dns_zone_ids\s*==\s*null"
)
INTEGRATION = re.compile(r"virtual_network_subnet_id\s*=")
DELEGATION = "Microsoft.Web/serverFarms"

# Every module here that declares a Function App.
HANDLER_MODULES = ("tools", "approval", "observability")


def read(path):
    with open(path, encoding="utf-8") as handle:
        return strip_comments_preserving_lines(handle.read())


def module_text(module):
    return "\n".join(
        read(p) for p in tf_files() if os.path.basename(os.path.dirname(p)) == module
    )


def root_text(env):
    return "\n".join(
        read(p) for p in tf_files()
        if os.path.dirname(p).endswith(os.path.join("envs", env))
    )


def coupled_roots():
    return sorted(
        os.path.basename(os.path.dirname(path))
        for path in tf_files()
        if COUPLED.search(read(path))
    )


class TestPrivateEndpointHasHandlersInside(unittest.TestCase):
    def test_the_coupled_roots_are_still_prod_and_staging(self):
        self.assertEqual(coupled_roots(), ["prod", "staging"])

    def test_every_coupled_root_integrates_every_handler_module(self):
        for env in coupled_roots():
            text = root_text(env)
            for module in HANDLER_MODULES:
                start = text.index(f'module "{module}" ')
                end = text.index("\n}\n", start)
                self.assertRegex(
                    text[start:end], INTEGRATION,
                    f"envs/{env} closes AI Search's public route the moment a DNS zone id "
                    f"is supplied, but leaves module.{module} outside the VNet. Pass "
                    "virtual_network_subnet_id, or stop coupling public access to the zone "
                    "variable.",
                )

    def test_the_integration_subnet_is_delegated(self):
        # Scoped to the resource body on purpose: the same string appears in the
        # `integration_subnet_prefix` description, and a description is a string rather than
        # a comment, so a whole-module search passes even with the delegation deleted. The
        # first version of this test did exactly that and survived its own mutation.
        text = module_text("networking")
        start = text.index('resource "azurerm_subnet" "integration"')
        body = block_body(text, text.index("{", start))
        self.assertIn(
            DELEGATION, body,
            "The integration subnet lost its Microsoft.Web/serverFarms delegation. VNet "
            "integration fails without it, and the error names the subnet rather than the "
            "delegation.",
        )

    def test_dev_stays_on_the_public_network(self):
        self.assertNotRegex(
            root_text("dev"), INTEGRATION,
            "envs/dev wired VNet integration. Dev runs Y1, which has no VNet integration at "
            "any price, so this cannot apply — and dev exists to be deployable in a flat "
            "network.",
        )


if __name__ == "__main__":
    unittest.main()
