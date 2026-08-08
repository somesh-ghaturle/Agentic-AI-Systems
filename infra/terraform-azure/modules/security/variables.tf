variable "resource_group_name" {
  type = string
}

variable "location" {
  type = string
  default = "eastus"
}

variable "tenant_id" {
  type = string
}

variable "name_prefix" {
  type = string
  default = "agentic"
}

variable "service_principal_object_id" {
  type        = string
  description = "Object id of a service principal to grant Key Vault access to. Leave empty to skip."
  default     = ""
}

variable "create_model_key_secret" {
  type        = bool
  description = "When true, create a Key Vault secret for the model API key using `model_key_secret_value`."
  default     = false
}

variable "model_key_secret_name" {
  type        = string
  description = "Name for the Key Vault secret that will hold the model API key"
  default     = "model-api-key"
}

variable "model_key_secret_value" {
  type        = string
  description = "Sensitive value for the model API key. Only used when `create_model_key_secret` is true."
  default     = ""
}
