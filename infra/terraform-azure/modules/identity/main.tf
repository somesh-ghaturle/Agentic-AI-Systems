# Identity module: creates a service principal and assigns a role to it (example)
resource "azuread_application" "app" {
  display_name = "${var.name_prefix}-app"
}

resource "azuread_service_principal" "sp" {
  client_id = azuread_application.app.client_id
}

resource "azuread_service_principal_password" "sp_pwd" {
  service_principal_id = azuread_service_principal.sp.object_id
  end_date_relative     = "8760h" # 1 year
}
