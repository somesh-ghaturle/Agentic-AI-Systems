terraform {
  required_version = ">= 1.6"

  required_providers {
    # Pinned to a major, matching what the modules declare. The tree-level versions.tf
    # uses `>= 5.0` because it documents the floor; a root that actually resolves
    # providers needs a ceiling too, or two people running `terraform init` a month apart
    # produce different plans from identical code.
    #
    # Only `google` is declared. `google-beta` and `random` appear in the tree-level
    # versions.tf for modules that may need them; nothing this root reaches uses either,
    # and declaring an unused provider means `init` downloads it forever.
    google = {
      source  = "hashicorp/google"
      version = "~> 7.44"
    }
  }
}
