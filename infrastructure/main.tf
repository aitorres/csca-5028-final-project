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

// Container app for hosting the postgresql database
resource "azurerm_container_app" "postgres_db" {
  name = "postgres-db"
  container_app_environment_id = azurerm_container_app_environment.production_env.id
  resource_group_name          = azurerm_resource_group.resource_group.name
  revision_mode                = "Single"

  identity {
    type = "SystemAssigned"
  }

  template {
    container {
      name = "postgres"
      image = "mcr.microsoft.com/k8se/services/postgres:17"
      cpu    = "0.25"
      memory = "0.5Gi"

      min_replicas = 1
      max_replicas = 1

      liveness_probe {
        initial_delay           = 30
        interval_seconds        = 10
        failure_count_threshold = 3
        transport               = "TCP"
        port                    = 5432
      }

      env {
        name  = "POSTGRES_USER"
        value = var.postgres_user
      }
      env {
        name  = "POSTGRES_PASSWORD"
        value = var.postgres_password
      }
      env {
        name  = "POSTGRES_DB"
        value = var.postgres_db_name
      }
    }
  }

  ingress {
    external_enabled = false
    target_port      = 5432
    transport        = "auto"

    traffic_weight {
      label           = "postgres-db"
      percentage      = 100
      latest_revision = true
    }
  }
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
    server               = azurerm_container_registry.container_registry.login_server
    username             = azurerm_container_registry.container_registry.admin_username
    password_secret_name = "acrpassword"
  }

  secret {
    name  = "acrpassword"
    value = azurerm_container_registry.container_registry.admin_password
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

      env {
        name = "POSTGRESQL_URL"
        value = "postgresql://${var.postgres_user}:${var.postgres_password}@${azurerm_container_app.postgres_db.name}:5432/${var.postgres_db_name}"
      }

      liveness_probe {
        initial_delay           = 30
        interval_seconds        = 10
        failure_count_threshold = 3
        transport               = "HTTP"
        path                    = "/health"
        port                    = 8080
      }
    }
  }

  ingress {
    external_enabled = true
    target_port      = 8080
    transport        = "auto"

    traffic_weight {
      label           = "web"
      percentage      = 100
      latest_revision = true
    }
  }
}
