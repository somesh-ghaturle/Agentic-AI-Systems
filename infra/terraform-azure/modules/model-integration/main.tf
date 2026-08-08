# Model integration module placeholder
# This module does not create an Azure OpenAI account (requires tenant enrollment).
# Instead it documents variables and outputs for wiring Azure OpenAI or Azure ML.

locals {
  note = "Configure Azure OpenAI resources externally and pass endpoints/keys into consuming services."
}

output "azure_openai_endpoint" {
  value = var.azure_openai_endpoint
}

output "azure_openai_key_secret_name" {
  value = var.azure_openai_key_secret_name
}

# Example: when a Key Vault id is provided, consumers can reference the secret stored there.
# The security module creates the Key Vault and optional secret; pass that secret name here
# and consumers (applications) should read it from Key Vault rather than keeping it in plain text.

output "usage_example" {
  value = "If you want Terraform to create the model API key in KeyVault, set the security module variables: create_model_key_secret=true and model_key_secret_value (sensitive). Then set azure_openai_key_secret_name to match. Applications should retrieve the secret from KeyVault at runtime."
}
