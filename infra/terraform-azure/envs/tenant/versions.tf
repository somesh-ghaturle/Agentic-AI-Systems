terraform {
  required_version = ">= 1.6"

  required_providers {
    # Same pins as dev and prod. This root is applied on a different cadence, which is
    # exactly how it would drift onto a different major without anyone noticing.
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
    azuread = {
      source  = "hashicorp/azuread"
      version = "~> 3.0"
    }
  }
}
