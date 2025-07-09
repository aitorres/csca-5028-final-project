// Resource group to host all Azure resources for the project
resource "azurerm_resource_group" "resource_group" {
    name = var.azure_resource_group_name
    location = var.azure_location
}

// Container registry for storing Docker images
resource "azurerm_container_registry" "container_registry" {
    name                = "project-container-registry"
    location            = azurerm_resource_group.resource_group.location
    resource_group_name = azurerm_resource_group.resource_group.name
    sku                 = "Basic"
    admin_enabled       = true

    tags = {
        environment = "production"
    }
}
