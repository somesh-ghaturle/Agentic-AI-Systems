# Identity — service users that hold no secret
#
# This is the module that decides whether this tree keeps the property the other three
# have: that nothing in `infra/` provisions a long-lived credential. Snowflake makes that
# harder than AWS, Azure or GCP do, because there is no ambient identity to inherit. A
# Lambda has an execution role, a Function App has a managed identity, a Cloud Run service
# has a service account — all supplied by the platform the code runs on. A Snowflake
# session has whatever the client authenticated with, and historically that meant an RSA
# private key sitting somewhere.
#
# Workload identity federation removes that. The service user carries no password, no
# key pair, and no token; it carries a *statement about which external identity may become
# it*. The handler authenticates as its AWS role, Azure managed identity or GCP service
# account, presents that to Snowflake, and Snowflake matches it against the block below.
#
# The consequence is worth stating plainly, because it is the reason this design was
# chosen over key-pair auth: there is no secret to leak, so there is no secret to rotate.
# docs/SECRETS-ROTATION.md stays true with a fourth tree in the repository.
#
# The `authenticator = "SNOWFLAKE_JWT"` alternative is real, supported, and documented in
# HOW-TO-DEPLOY.md for accounts that cannot use WIF yet. It costs a genuine rotatable
# secret. This module does not create one, and it should not be extended to.

terraform {
  required_version = ">= 1.6"
  required_providers {
    snowflake = {
      source  = "snowflakedb/snowflake"
      version = "~> 2.20"
    }
  }
}

resource "snowflake_service_user" "this" {
  for_each = var.service_users

  name         = "${var.name_prefix}_${upper(each.key)}"
  comment      = each.value.comment
  display_name = "${var.name_prefix}_${upper(each.key)}"

  # The role the session lands in. Setting it is not a security control — a user may
  # always USE ROLE any role granted to it — but it means a handler that forgets to set a
  # role runs as the intended one rather than as PUBLIC, where every query fails in a way
  # that reads like a network problem.
  default_role      = each.value.role
  default_warehouse = var.warehouse_name
  default_namespace = "${var.database_name}.${each.value.default_schema}"

  # No secondary roles. The default, ALL, activates every role granted to the user at once
  # — which would make the separation between ORCHESTRATOR and EXECUTOR meaningless for
  # any user that somehow held both. Setting NONE means the session holds exactly the role
  # it asked for.
  default_secondary_roles_option = "NONE"

  # The whole point of this module. Exactly one of these blocks is populated per user,
  # determined by which cloud the handler runs on.
  dynamic "default_workload_identity" {
    for_each = [each.value.workload_identity]

    content {
      dynamic "aws" {
        for_each = default_workload_identity.value.aws_role_arn == null ? [] : [1]
        content {
          arn = default_workload_identity.value.aws_role_arn
        }
      }

      dynamic "azure" {
        for_each = default_workload_identity.value.azure == null ? [] : [1]
        content {
          issuer  = default_workload_identity.value.azure.issuer
          subject = default_workload_identity.value.azure.subject
        }
      }

      dynamic "gcp" {
        for_each = default_workload_identity.value.gcp_subject == null ? [] : [1]
        content {
          subject = default_workload_identity.value.gcp_subject
        }
      }

      dynamic "oidc" {
        for_each = default_workload_identity.value.oidc == null ? [] : [1]
        content {
          issuer             = default_workload_identity.value.oidc.issuer
          subject            = default_workload_identity.value.oidc.subject
          oidc_audience_list = default_workload_identity.value.oidc.audience_list
        }
      }
    }
  }

  lifecycle {
    precondition {
      condition = anytrue([
        each.value.workload_identity.aws_role_arn != null,
        each.value.workload_identity.azure != null,
        each.value.workload_identity.gcp_subject != null,
        each.value.workload_identity.oidc != null,
      ])
      error_message = "Service user ${each.key} has no workload identity configured. A service user with no federated identity and no key is a user nothing can authenticate as — which fails at runtime as an opaque 390144, rather than here."
    }
  }
}

# ---------------------------------------------------------------------------
# One role per user, and no more
#
# `snowflake_grant_account_role` with `user_name` grants a role TO a user. The same
# resource with `parent_role_name` grants a role to another *role*, creating inheritance —
# which is the single change that would collapse the write boundary. This module only ever
# uses the user form. modules/security explains why; tests/test_write_boundary.py enforces
# it.
# ---------------------------------------------------------------------------

resource "snowflake_grant_account_role" "user_role" {
  for_each = var.service_users

  role_name = each.value.role
  user_name = snowflake_service_user.this[each.key].name
}

# ---------------------------------------------------------------------------
# Network policy
#
# Attached to these users rather than to the account. An account-level policy that locks a
# human admin out mid-incident is a policy someone disables permanently, and a disabled
# policy protects nothing.
# ---------------------------------------------------------------------------

resource "snowflake_network_policy_attachment" "service_users" {
  count = var.network_policy_name == null ? 0 : 1

  network_policy_name = var.network_policy_name
  set_for_account     = false
  users               = [for k, u in snowflake_service_user.this : u.name]
}
