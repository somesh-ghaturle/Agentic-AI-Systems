variable "name_prefix" {
  description = "Prefix for every resource name in this module."
  type        = string
}

variable "vpc_id" {
  description = "An existing VPC. This module does not create one — see the header."
  type        = string
}

variable "subnet_ids" {
  description = "Private subnets for the handler ENIs and the interface endpoints. Two or more, in different availability zones, or the handlers share the fate of one AZ."
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) > 0
    error_message = "subnet_ids must not be empty."
  }
}

variable "interface_services" {
  description = "Services reached over interface endpoints. The default is what infra/terraform-aws/src/ actually calls: Bedrock for inference, Logs for traces, Lambda for tool invocation, Step Functions for the orchestrator's own callbacks. Add to it before adding a handler call, not after — a missing entry fails as a timeout."
  type        = list(string)
  default     = ["bedrock-runtime", "logs", "lambda", "states"]

  validation {
    condition     = length(var.interface_services) > 0
    error_message = "interface_services must not be empty. A VPC-attached handler with no endpoints can reach nothing, and with no NAT gateway there is no fallback path."
  }
}

variable "tags" {
  description = "Tags applied to every resource."
  type        = map(string)
  default     = {}
}
