# This file is not a root. `terraform validate` never reaches it — CI validates
# `envs/dev` and `envs/prod`, each of which carries its own `versions.tf`. What does read this
# file is Dependabot, which is pointed at `/infra/terraform-gcp` in `.github/dependabot.yml`,
# and a human opening the tree to find out what it targets.
#
# It therefore has to carry the same pins the roots do. It previously declared `>= 5.0` while
# every root and module declared `~> 6.0`, which produced two false audit findings (a "provider
# discrepancy" that was really a dead file, and a Task 21 premise that no longer held) before
# anyone noticed the file was orphaned. A floor here also means the Dependabot entry for this
# directory opens nothing, since a floor never excludes a newer release.
#
# `google-beta` and `random` are declared here and not in the roots on purpose: no root
# currently reaches a module that uses either, and declaring an unused provider in a root makes
# `terraform init` download it forever. They are named here so a module author adding one knows
# which major the tree is on.
terraform {
  required_version = ">= 1.6"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 6.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
