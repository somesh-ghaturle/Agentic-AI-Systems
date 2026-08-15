terraform {
  required_version = ">= 1.6"

  required_providers {
    # Pinned to a major, matching what the modules and the tree-level versions.tf declare.
    # Without a ceiling, two people running `terraform init` a month apart produce different
    # plans from identical code.
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
