provider "azurerm" {
  features {}

  subscription_id = var.azure_subscription_id
  tenant_id       = var.azure_tenant_id

  use_oidc = var.use_oidc
}
