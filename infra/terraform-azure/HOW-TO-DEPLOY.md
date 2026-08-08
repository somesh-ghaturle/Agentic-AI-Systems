# How to deploy (Azure)

A walkthrough from an empty Azure subscription to a working dev environment, then what changes for prod.

---

## Before you start

**Required:**
- Azure CLI installed and authenticated:
  ```bash
  az login
  az account set --subscription <SUBSCRIPTION_ID>
  ```
- Terraform ≥ 1.3.0
- Permissions to create Resource Groups, Storage Accounts, Key Vaults, Service Principals, Log Analytics Workspaces, Service Bus Namespaces, Search Services, and Logic Apps in the target subscription.

**Decide before the first apply:**
- `name_prefix` (defaults to `agentic-dev` / `agentic-prod`) — changing this later will recreate most resources.

---

## 1 · Remote state

For team environments, use a remote backend. In Azure, this uses a Storage Container:

```bash
# Create Resource Group for state
az group create --name agentic-tfstate-rg --location eastus

# Create Storage Account
az storage account create --name agentictfstatesa --resource-group agentic-tfstate-rg --location eastus --sku Standard_LRS

# Create Blob Container
az storage container create --name tfstate --account-name agentictfstatesa
```

Then, configure the backend in `envs/dev/main.tf` and `envs/prod/main.tf` by updating the `backend` block:
```hcl
terraform {
  backend "azurerm" {
    resource_group_name  = "agentic-tfstate-rg"
    storage_account_name = "agentictfstatesa"
    container_name       = "tfstate"
    key                  = "dev.terraform.tfstate"
  }
}
```

---

## 2 · Configure

Copy the example variables file:

```bash
cd envs/dev
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars` with your project variables, tenant ID, and custom settings.

---

## 3 · Apply

Initialize and validate the environment:

```bash
terraform init
terraform validate
terraform plan
terraform apply
```

---

## 4 · Component Mapping details

- **State** (`modules/state`): Stores workflow state in an Azure Storage Table (`executionstate`).
- **Archive** (`modules/archive`): Stores trace logs in an Azure Blob Container (`trace-archive`) with tiering and deletion policies configured via Lifecycle Management.
- **Knowledge** (`modules/knowledge`): Configures Azure AI Search (`azurerm_search_service`) for semantic search vector databases.
- **Tools** (`modules/tools`): Packages functions into a serverless Linux Function App (`azurerm_linux_function_app`).
- **Approval** (`modules/approval`): Handles gates via Service Bus Topics/Subscriptions.
- **Orchestration** (`modules/orchestration`): Deploys an Azure Logic App workflow to coordinate actions.

---

## Troubleshooting

- **Storage Account Name Limits**: Azure Storage Account names must be globally unique, lowercase, alphanumeric, and between 3 and 24 characters. If validation fails on storage account creation, modify `name_prefix` to be shorter.
- **Service Principal Credentials**: When using the identity module, the client secret is marked sensitive. Retrieve it from outputs using `terraform output -raw client_secret`.
