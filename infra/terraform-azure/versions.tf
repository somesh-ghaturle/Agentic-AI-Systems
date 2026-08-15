# This file is not a root. `terraform validate` never reaches it — CI validates `envs/dev`,
# `envs/prod`, and `envs/tenant`, each of which carries its own `versions.tf`. What does read
# this file is Dependabot, which is pointed at `/infra/terraform-azure` in
# `.github/dependabot.yml`, and a human opening the tree to find out what it targets.
#
# It therefore has to carry the same pins the roots do. It previously declared floors
# (`>= 3.0` / `>= 2.0`) while every root declared `~> 5.0` / `~> 3.0`, and a floor means the
# Dependabot entry for this directory opens nothing, since a floor never excludes a newer
# release.
#
# Unlike the AWS and GCP trees, the Azure modules declare no `required_providers` of their own
# and inherit from whichever root calls them. That makes this file the only tree-level
# statement of which majors the Azure modules are written against.
terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
