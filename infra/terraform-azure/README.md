Azure Terraform scaffold for Agentic-AI-Systems

This folder provides a parallel Terraform layout to `infra/terraform-aws`.

Structure:
- `modules/` - reusable modules (networking, identity, security, observability, model-integration)
- `envs/` - environment examples (`dev`, `prod`)

Quick start (local):

1. Authenticate with Azure CLI:

```bash
az login
az account set --subscription <SUBSCRIPTION_ID>
```

2. Initialize Terraform in an environment folder, e.g.:

```bash
cd infra/terraform-azure/envs/dev
terraform init
terraform validate
```

Notes:
- This scaffold provides minimal module implementations; adapt to your organization's standards.
- The `model-integration` module documents how to wire Azure OpenAI / Azure ML resources.

KeyVault and Azure OpenAI guidance:

- The `security` module creates a Key Vault (`azurerm_key_vault`) and can optionally create a secret to hold a model API key. Set `create_model_key_secret=true` and provide `model_key_secret_value` securely in a protected tfvars file or via automation.
- The `identity` module can create a service principal; pass its `service_principal_id` into `security.service_principal_object_id` to grant the SP access to Key Vault.
- For Azure OpenAI, the recommended pattern is to store the API key in Key Vault and pass the Key Vault secret name to applications (via environment variables or managed identity-based retrieval). Terraform cannot create an Azure OpenAI resource without tenant enrollment in many cases; the scaffold assumes the resource is created externally and just wires endpoints/secret names.
