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
