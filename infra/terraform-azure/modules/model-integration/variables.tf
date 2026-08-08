variable "azure_openai_endpoint" {
  type = string
  description = "Optional Azure OpenAI endpoint to use (e.g. https://my-openai.openai.azure.com/)"
  default = ""
}

variable "azure_openai_key_secret_name" {
  type = string
  description = "Name of secret in KeyVault where API key is stored"
  default = ""
}

variable "model_deployment_name" {
  type        = string
  description = "Name of the model deployment (for Azure OpenAI) if using deployment-based endpoints"
  default     = ""
}
