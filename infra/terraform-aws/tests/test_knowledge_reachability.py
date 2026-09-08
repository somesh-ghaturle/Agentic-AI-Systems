# Static check on the one thing the knowledge module's network policy does not do.
#
# Staging and prod set `allow_public_access = false`, which admits traffic to the knowledge
# collection only through its VPC endpoint, and both grant collection data access to the
# retrieve tool's role. Nothing in this tree puts that tool inside the VPC: no Lambda here
# declares a `vpc_config`, deliberately, and `.checkov.yaml` skips CKV_AWS_117 with the
# reasoning. So the retrieve tool has no route to the endpoint it is authorized against, and
# the strict setting is declared rather than exercised.
#
# That posture is a recorded choice for a reference deployment, not a bug to fix here. What
# this file guards is the pair staying honest in both directions:
#
#   1. Add a `vpc_config` and four places that state its absence become wrong — this file,
#      `.checkov.yaml`, `infra/CHOOSING-A-TREE.md` section 4, and the note in
#      `modules/knowledge/main.tf`.
#   2. Drop that note and `allow_public_access = false` goes back to reading as though
#      retrieval works in staging and prod, which is how the gap went unstated the first time.
#
# Source-reading only, like its neighbour, so it needs no AWS credentials:
#
#     python3 -m unittest discover -s infra/terraform-aws/tests

import os
import re
import unittest

from test_write_boundary import TREE, read, tf_files

# The lead of the comment block above `aws_opensearchserverless_security_policy.network`.
CAVEAT = "REACHABILITY STOPS AT THIS ENDPOINT"

VPC_CONFIG = re.compile(r"^\s*vpc_config\s*\{", re.M)
STRICT = re.compile(r"allow_public_access\s*=\s*false")

KNOWLEDGE = os.path.join(TREE, "modules", "knowledge", "main.tf")


class TestVpcOnlyCollectionIsDeclaredNotExercised(unittest.TestCase):
    def test_no_handler_in_this_tree_is_vpc_attached(self):
        attached = [
            os.path.relpath(path, TREE)
            for path in tf_files("modules")
            if VPC_CONFIG.search(read(path))
        ]
        self.assertEqual(
            attached,
            [],
            "A vpc_config appeared in {}. That is the right direction, but it also needs "
            "egress for Bedrock, DynamoDB, S3 and Logs, and it falsifies the stated absence "
            "in .checkov.yaml (CKV_AWS_117), infra/CHOOSING-A-TREE.md section 4, "
            "infra/terraform-aws/README.md and modules/knowledge/main.tf. Update those, then "
            "this test.".format(attached),
        )

    def test_roots_that_lock_the_collection_keep_the_caveat(self):
        strict = sorted(
            os.path.relpath(os.path.dirname(path), TREE)
            for path in tf_files("envs")
            if STRICT.search(read(path))
        )
        self.assertEqual(strict, ["envs/prod", "envs/staging"])

        with open(KNOWLEDGE, encoding="utf-8") as handle:
            source = handle.read()
        self.assertIn(
            CAVEAT,
            source,
            "{} lock the knowledge collection to its VPC endpoint while no handler can reach "
            "it. modules/knowledge/main.tf has to say so, or the strict setting reads as "
            "though retrieval works there.".format(", ".join(strict)),
        )


if __name__ == "__main__":
    unittest.main()
