# Static checks on the path between a handler and the VPC-only knowledge collection.
#
# This file used to assert the opposite of what it asserts now, and the change is the point.
# Prod and staging lock the collection to its VPC endpoint; for a long time no Lambda in the
# tree had a `vpc_config`, so the retrieve tool had no route to the endpoint it was
# authorized against and the strict setting was declared rather than exercised. That gap is
# closed — `modules/networking` supplies the endpoints and the security groups, and the
# three Lambda-bearing modules attach to the subnets.
#
# What is guarded now is that the two halves stay together. Either half alone is worse than
# neither: a VPC-only collection with unattached handlers is the old silent failure, and
# attached handlers with no endpoints is the same failure with a bigger bill, because
# there is deliberately no NAT gateway to fall back to.
#
#     python3 -m unittest discover -s infra/terraform-aws/tests

import os
import re
import unittest

from test_write_boundary import block_body, read, tf_files

STRICT = re.compile(r"allow_public_access\s*=\s*false")
VPC_CONFIG = re.compile(r'dynamic\s+"vpc_config"')
VPC_ACCESS_POLICY = "AWSLambdaVPCAccessExecutionRole"

# Every module in this tree that declares a Lambda. Each one has to be able to join the VPC,
# or an environment that attaches the others still has a handler outside it.
HANDLER_MODULES = ("tools", "approval", "observability")

# What the handlers call, from `boto3.client(...)` in infra/terraform-aws/src/. DynamoDB is
# absent because it is a gateway endpoint, asserted separately; opensearchserverless is
# absent because its endpoint lives with the collection in modules/knowledge.
EXPECTED_INTERFACE_SERVICES = {"bedrock-runtime", "logs", "lambda", "states"}


def module_files(module):
    return [p for p in tf_files("modules") if os.path.basename(os.path.dirname(p)) == module]


def module_text(module):
    return "\n".join(read(p) for p in module_files(module))


def root_text(env):
    return "\n".join(read(p) for p in tf_files(os.path.join("envs", env)))


def strict_roots():
    return sorted(
        os.path.basename(os.path.dirname(path))
        for path in tf_files("envs")
        if STRICT.search(read(path))
    )


class TestStrictRootsAttachTheirHandlers(unittest.TestCase):
    def test_the_strict_roots_are_still_prod_and_staging(self):
        self.assertEqual(strict_roots(), ["prod", "staging"])

    def test_every_strict_root_puts_every_handler_module_on_the_vpc(self):
        for env in strict_roots():
            text = root_text(env)
            for module in HANDLER_MODULES:
                body = block_body(text, text.index("{", text.index(f'module "{module}" ')))
                self.assertIn(
                    "subnet_ids", body,
                    f"envs/{env} locks the knowledge collection to its VPC endpoint but does "
                    f"not put module.{module} on the VPC. That is the failure this tree "
                    "documented for a year: the gate is correct and the caller cannot reach "
                    "it. Pass subnet_ids and the handler security group, or stop setting "
                    "allow_public_access = false.",
                )
                self.assertIn("security_group_ids", body, f"envs/{env}: module.{module}")

    def test_every_strict_root_declares_the_networking_module(self):
        for env in strict_roots():
            self.assertIn('module "networking"', root_text(env), f"envs/{env}")


class TestAttachmentCarriesWhatAttachmentNeeds(unittest.TestCase):
    def test_every_handler_module_can_join_a_vpc(self):
        for module in HANDLER_MODULES:
            self.assertRegex(
                module_text(module), VPC_CONFIG,
                f"modules/{module} declares a Lambda with no dynamic vpc_config, so an "
                "environment that attaches the others leaves this one outside the VPC.",
            )

    def test_every_handler_module_grants_the_eni_permissions(self):
        for module in HANDLER_MODULES:
            self.assertIn(
                VPC_ACCESS_POLICY, module_text(module),
                f"modules/{module} attaches functions to a VPC without "
                f"{VPC_ACCESS_POLICY}. Lambda creates the ENI with the function's own "
                "execution role, so the function stalls in Pending and fails with an error "
                "that names the subnet rather than the missing permission.",
            )

    def test_the_endpoint_set_matches_what_the_handlers_call(self):
        text = module_text("networking")
        default = re.search(r'variable "interface_services".*?default\s*=\s*\[(.*?)\]',
                            text, re.S)
        self.assertIsNotNone(default, "interface_services lost its default")
        services = set(re.findall(r'"([^"]+)"', default.group(1)))
        self.assertEqual(
            services, EXPECTED_INTERFACE_SERVICES,
            "The interface endpoint list no longer matches the services the handlers call. "
            "With no NAT gateway there is no fallback path, so a service missing from this "
            "list fails as a timeout at the function's own limit, not as an error.",
        )

    def test_dynamodb_is_a_gateway_endpoint(self):
        self.assertIn(
            'vpc_endpoint_type = "Gateway"', module_text("networking"),
            "DynamoDB moved off the gateway endpoint. Gateway endpoints are free and "
            "interface endpoints are about $7 per month per AZ; this is the state store, "
            "so the difference is not rounding.",
        )


if __name__ == "__main__":
    unittest.main()
