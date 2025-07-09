// Resource group to host all Azure resources for the project
resource "azurerm_resource_group" "resource_group" {
  name     = var.azure_resource_group_name
  location = var.azure_location
}

// Container registry for storing Docker images
resource "azurerm_container_registry" "container_registry" {
  name                = "csca5028finalprojectacr"
  location            = azurerm_resource_group.resource_group.location
  resource_group_name = azurerm_resource_group.resource_group.name
  sku                 = "Basic"
  admin_enabled       = true

  tags = {
    environment = "production"
  }
}

// Container app environment for hosting applications
resource "azurerm_log_analytics_workspace" "analytics_workspace" {
  name                = "FinalProject-AnalyticsWorkspace"
  location            = azurerm_resource_group.resource_group.location
  resource_group_name = azurerm_resource_group.resource_group.name
  sku                 = "PerGB2018"
  retention_in_days   = 30
}

resource "azurerm_container_app_environment" "production_env" {
  name                       = "ProductionEnvironment"
  location                   = azurerm_resource_group.resource_group.location
  resource_group_name        = azurerm_resource_group.resource_group.name
  log_analytics_workspace_id = azurerm_log_analytics_workspace.analytics_workspace.id
}

// Container app for hosting the web application
resource "azurerm_container_app" "web_app" {
  name                         = "web"
  container_app_environment_id = azurerm_container_app_environment.production_env.id
  resource_group_name          = azurerm_resource_group.resource_group.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  registry {
    server   = azurerm_container_registry.container_registry.login_server
    username = azurerm_container_registry.container_registry.admin_username
    password = azurerm_container_registry.container_registry.admin_password
  }

  template {
    container {
      name   = "web"
      image  = "${azurerm_container_registry.container_registry.login_server}/web:${var.web_image_tag}"
      cpu    = "0.25"
      memory = "0.5Gi"

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }
  }
}
