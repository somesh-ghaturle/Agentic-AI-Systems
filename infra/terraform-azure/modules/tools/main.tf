resource "azurerm_storage_account" "tools_sa" {
  name                     = replace("${var.name_prefix}toolssa", "-", "")
  resource_group_name      = var.resource_group_name
  location                 = var.location
  account_tier             = "Standard"
  account_replication_type = "LRS"

  tags = var.tags
}

resource "azurerm_service_plan" "tools_plan" {
  name                = "${var.name_prefix}-tools-plan"
  resource_group_name = var.resource_group_name
  location            = var.location
  os_type             = "Linux"
  sku_name            = "Y1" # Consumption plan (Serverless)

  tags = var.tags
}

resource "azurerm_linux_function_app" "tools" {
  name                = "${var.name_prefix}-tools-fa"
  resource_group_name = var.resource_group_name
  location            = var.location

  storage_account_name       = azurerm_storage_account.tools_sa.name
  storage_account_access_key = azurerm_storage_account.tools_sa.primary_access_key
  service_plan_id            = azurerm_service_plan.tools_plan.id

  site_config {
    application_stack {
      python_version = "3.10" # default python runtime for tools
    }
  }

  app_settings = merge(var.common_environment, {
    "FUNCTIONS_WORKER_RUNTIME" = "python"
  })

  tags = var.tags
}
