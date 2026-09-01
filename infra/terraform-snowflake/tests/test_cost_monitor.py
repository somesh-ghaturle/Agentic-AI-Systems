"""Static regression checks for the Snowflake warehouse cost monitor."""

import pathlib
import unittest

TREE = pathlib.Path(__file__).resolve().parents[1]


class CostMonitor(unittest.TestCase):
    def test_resource_monitor_is_optional_and_attached_to_warehouse(self):
        monitor = (TREE / "modules" / "state" / "cost-monitor.tf").read_text(
            encoding="utf-8"
        )
        state = (TREE / "modules" / "state" / "main.tf").read_text(encoding="utf-8")

        self.assertIn(
            "count = var.cost_monitor_credit_quota == null ? 0 : 1",
            monitor,
        )
        self.assertIn("credit_quota = var.cost_monitor_credit_quota", monitor)
        self.assertIn(
            'resource_monitor = var.cost_monitor_credit_quota == null ? null : '
            "snowflake_resource_monitor.warehouse_cost[0].name",
            state,
        )

    def test_dev_and_staging_enforce_limits(self):
        for environment, quota in (("dev", "10"), ("staging", "25")):
            text = (TREE / "envs" / environment / "main.tf").read_text(
                encoding="utf-8"
            )
            self.assertRegex(
                text,
                rf"cost_monitor_credit_quota\s*=\s*{quota}\b",
            )
            self.assertRegex(
                text,
                r"cost_monitor_suspend_trigger\s*=\s*100\b",
            )
            self.assertRegex(
                text,
                r"cost_monitor_suspend_immediate_trigger\s*=\s*110\b",
            )

    def test_prod_is_configurable_but_does_not_suspend_by_default(self):
        text = (TREE / "envs" / "prod" / "main.tf").read_text(encoding="utf-8")
        variables = (TREE / "envs" / "prod" / "variables.tf").read_text(
            encoding="utf-8"
        )

        self.assertIn(
            "cost_monitor_credit_quota = var.cost_monitor_credit_quota",
            text,
        )
        self.assertRegex(
            variables,
            r'variable "cost_monitor_credit_quota"\s*\{[\s\S]*?default\s*=\s*null',
        )
        self.assertNotIn("cost_monitor_suspend_trigger", text)
        self.assertNotIn("cost_monitor_suspend_immediate_trigger", text)


if __name__ == "__main__":
    unittest.main()
