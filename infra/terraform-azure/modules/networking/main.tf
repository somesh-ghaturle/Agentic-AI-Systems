terraform {
  required_version = ">= 1.6"
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 5.0"
    }
  }
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location

  tags = var.tags
}

resource "azurerm_virtual_network" "vnet" {
  name                = "${var.name_prefix}-vnet"
  resource_group_name = azurerm_resource_group.rg.name
  location            = azurerm_resource_group.rg.location
  address_space       = [var.address_space]

  tags = var.tags
}

resource "azurerm_subnet" "subnet" {
  name                 = "${var.name_prefix}-subnet"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.subnet_prefix]
}

# ---------------------------------------------------------------------------
# The integration subnet
#
# VNet integration for a Function App is not a property of the app alone: the subnet has to
# be *delegated* to Microsoft.Web/serverFarms, and a delegated subnet holds nothing else.
# That is why this is a second subnet rather than a flag on the first — the private
# endpoint above lives in the other one, and a subnet cannot be both.
#
# This is the half that makes the private endpoint worth having. Without it the app has no
# route into the VNet, so closing AI Search's public access removes the only path the
# handlers had. With it, the private endpoint is the path.
#
# Y1 CANNOT USE THIS. The Consumption plan has no VNet integration at any price, which is
# why dev does not wire it and why the staging root passes null when its SKU is Y1. The
# error Azure returns for the attempt names the subnet, not the plan.
# ---------------------------------------------------------------------------

resource "azurerm_subnet" "integration" {
  name                 = "${var.name_prefix}-integration"
  resource_group_name  = azurerm_resource_group.rg.name
  virtual_network_name = azurerm_virtual_network.vnet.name
  address_prefixes     = [var.integration_subnet_prefix]

  delegation {
    name = "serverfarms"

    service_delegation {
      name    = "Microsoft.Web/serverFarms"
      actions = ["Microsoft.Network/virtualNetworks/subnets/action"]
    }
  }
}
