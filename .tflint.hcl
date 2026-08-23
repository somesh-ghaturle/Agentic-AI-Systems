# tflint — the Terraform half of the lint parity `ruff` gives Python.
#
# `terraform validate` already runs in CI, and it answers a narrower question than it
# looks like it does: is this configuration internally consistent and type-correct. It
# says nothing about a variable nobody reads, a module that pins no provider version, or
# a `terraform` block with no `required_version` — all of which apply cleanly, plan
# cleanly, and are how two people a month apart end up with different provider majors
# from identical code.
#
# The `recommended` preset is named explicitly rather than left to default. tflint's
# default preset has changed between minor versions, and a preset that moves is a rule
# set that turns a commit red without anyone editing a rule.
plugin "terraform" {
  enabled = true
  preset  = "recommended"
}
