"""The three `shared/contracts.py` copies are identical, and now that is a checked claim.

Each tree vendors its own copy so it stays portable — build.sh copies `shared/*.py` into
every package, and a reader can take one tree and go. The copies are byte-identical today,
which nothing verified: only the AWS suite declares a `TestContracts` class, so two of the
three copies were covered by a test that could not see them. If Azure's copy drifted, AWS's
tests would keep passing and Azure would ship the difference.

This is the cheap half of that problem. It does not merge the copies — it makes their
sameness the thing under test, so `TestContracts` covers all three by construction or this
fails and says which one moved.
"""

import hashlib
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
TREES = ("terraform-aws", "terraform-azure", "terraform-gcp")
CONTRACTS = "src/shared/contracts.py"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


class TestContractsCopiesAgree(unittest.TestCase):
    def test_all_three_trees_carry_the_file(self):
        missing = [t for t in TREES if not (ROOT / "infra" / t / CONTRACTS).is_file()]
        self.assertEqual([], missing, f"tree(s) missing {CONTRACTS}: {missing}")

    def test_the_copies_are_byte_identical(self):
        digests = {t: digest(ROOT / "infra" / t / CONTRACTS) for t in TREES}
        self.assertEqual(
            1,
            len(set(digests.values())),
            "shared/contracts.py has diverged across trees:\n  "
            + "\n  ".join(f"{t}  {d[:12]}" for t, d in sorted(digests.items()))
            + "\n\nOnly infra/terraform-aws/src/tests/test_handlers.py declares TestContracts, "
            "so whichever copy moved is now untested. Either port the change to all three "
            "or give the diverging tree its own contract tests.",
        )


if __name__ == "__main__":
    unittest.main()
