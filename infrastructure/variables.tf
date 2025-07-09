variable "azure_subscription_id" {
  description = "The Azure subscription ID to use for the resources."
  type        = string
}

variable "azure_tenant_id" {
  description = "The Azure tenant ID to use for the resources."
  type        = string
}

variable "azure_resource_group_name" {
  description = "The name of the Azure resource group."
  type        = string
  default     = "csca-5028-final-project-rg"
}

variable "azure_location" {
  description = "The Azure region where resources will be deployed."
  type        = string
  default     = "westus3"
}
