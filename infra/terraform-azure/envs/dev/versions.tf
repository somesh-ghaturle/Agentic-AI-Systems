terraform {
  required_version = ">= 1.6"

  required_providers {
    # Pinned to a major. The previous unconstrained `source`-only blocks meant two people
    # running `terraform init` a month apart could resolve different majors and produce
    # different plans from identical code.
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
