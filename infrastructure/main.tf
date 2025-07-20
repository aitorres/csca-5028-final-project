// Resource group to host all Azure resources for the project
resource "azurerm_resource_group" "resource_group" {
  name     = var.azure_resource_group_name
  location = var.azure_location
}

// Virtual network for the virtual machine that will host
// shared resources (PostgreSQL database and RabbitMQ)
resource "azurerm_virtual_network" "shared_vnet" {
  name                = "shared-vnet"
  address_space       = ["10.0.0.0/16"]
  location            = azurerm_resource_group.resource_group.location
  resource_group_name = azurerm_resource_group.resource_group.name
}

resource "azurerm_subnet" "shared_subnet" {
  name                 = "shared-subnet"
  resource_group_name  = azurerm_resource_group.resource_group.name
  virtual_network_name = azurerm_virtual_network.shared_vnet.name
  address_prefixes     = ["10.0.2.0/24"]
}

resource "azurerm_public_ip" "shared_public_ip" {
  name                = "shared-public-ip"
  location            = azurerm_resource_group.resource_group.location
  resource_group_name = azurerm_resource_group.resource_group.name
  allocation_method   = "Static"
  sku                 = "Standard"
}

resource "azurerm_network_interface" "external_shared_nic" {
  name                = "external-shared-nic"
  location            = azurerm_resource_group.resource_group.location
  resource_group_name = azurerm_resource_group.resource_group.name

  ip_configuration {
    name                          = "internal"
    subnet_id                     = azurerm_subnet.shared_subnet.id
    private_ip_address_allocation = "Dynamic"
    public_ip_address_id          = azurerm_public_ip.shared_public_ip.id
  }
}

resource "azurerm_network_security_group" "shared_nsg" {
  name                = "shared-nsg"
  location            = azurerm_resource_group.resource_group.location
  resource_group_name = azurerm_resource_group.resource_group.name

  security_rule {
    name                       = "AllowSSH"
    priority                   = 1000
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["22"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTP"
    priority                   = 1001
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["80"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowHTTPS"
    priority                   = 1002
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["443"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowPostgres"
    priority                   = 1003
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["5432"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }

  security_rule {
    name                       = "AllowRabbitMQ"
    priority                   = 1004
    direction                  = "Inbound"
    access                     = "Allow"
    protocol                   = "Tcp"
    source_port_range          = "*"
    destination_port_ranges    = ["5672", "15672"]
    source_address_prefix      = "*"
    destination_address_prefix = "*"
  }
}

resource "azurerm_network_interface_security_group_association" "main" {
  network_interface_id      = azurerm_network_interface.external_shared_nic.id
  network_security_group_id = azurerm_network_security_group.shared_nsg.id
}


// Virtual machine to host shared resources
// NOTE: after first deployment, one manual step is required:
// 1. SSH into the VM
// 2. Connect to the database and create the user, database, password
// 3. Run the migrations
// 4. Configure RabbitMQ if needed
resource "azurerm_linux_virtual_machine" "shared_vm" {
  name                = "shared-vm"
  resource_group_name = azurerm_resource_group.resource_group.name
  location            = azurerm_resource_group.resource_group.location
  size                = "Standard_B2ats_v2"

  admin_username                  = "azureuser"
  admin_password                  = var.shared_vm_admin_password
  disable_password_authentication = false

  network_interface_ids = [
    azurerm_network_interface.external_shared_nic.id
  ]

  os_disk {
    caching              = "ReadWrite"
    storage_account_type = "Standard_LRS"
  }

  source_image_reference {
    publisher = "Canonical"
    offer     = "0001-com-ubuntu-server-jammy"
    sku       = "22_04-lts"
    version   = "latest"
  }

  custom_data = filebase64("${path.module}/deployShared.sh")

  tags = {
    environment = "production"
  }
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

// Diagnostic settings for postgres container app
resource "azurerm_monitor_diagnostic_setting" "production_diagnostics" {
  name                       = "production-diagnostics"
  target_resource_id         = azurerm_container_app_environment.production_env.id
  log_analytics_workspace_id = azurerm_log_analytics_workspace.analytics_workspace.id

  enabled_log {
    category = "ContainerAppSystemLogs"
  }

  enabled_log {
    category = "ContainerAppConsoleLogs"
  }

  enabled_metric {
    category = "AllMetrics"
  }
}

// Container app for hosting the web application
resource "azurerm_container_app" "web_app" {
  name                         = "web"
  container_app_environment_id = azurerm_container_app_environment.production_env.id
  resource_group_name          = azurerm_resource_group.resource_group.name
  revision_mode                = "Single"

  depends_on = [
    azurerm_container_registry.container_registry,
    azurerm_linux_virtual_machine.shared_vm,
  ]

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
    min_replicas = 1
    max_replicas = 1

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
        name  = "SENTRY_DSN"
        value = var.sentry_dsn
      }
      env {
        name  = "POSTGRESQL_URL"
        value = "postgresql://${var.postgres_user}:${var.postgres_password}@${azurerm_linux_virtual_machine.shared_vm.public_ip_address}:5432/${var.postgres_db_name}"
      }
      env {
        name  = "RABBITMQ_HOST"
        value = azurerm_linux_virtual_machine.shared_vm.public_ip_address
      }
      env {
        name  = "RABBITMQ_PORT"
        value = "5672"
      }
      env {
        name  = "RABBITMQ_USER"
        value = var.rabbitmq_user
      }
      env {
        name  = "RABBITMQ_PASSWORD"
        value = var.rabbitmq_password
      }
      env {
        name  = "RABBITMQ_QUEUE_NAME"
        value = var.rabbitmq_queue_name
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

    container {
      name   = "analyzer"
      image  = "${azurerm_container_registry.container_registry.login_server}/analyzer:${var.web_image_tag}"
      cpu    = "0.25"
      memory = "0.5Gi"

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "SENTRY_DSN"
        value = var.sentry_dsn
      }
      env {
        name  = "POSTGRESQL_URL"
        value = "postgresql://${var.postgres_user}:${var.postgres_password}@${azurerm_linux_virtual_machine.shared_vm.public_ip_address}:5432/${var.postgres_db_name}"
      }
      env {
        name  = "RABBITMQ_HOST"
        value = azurerm_linux_virtual_machine.shared_vm.public_ip_address
      }
      env {
        name  = "RABBITMQ_PORT"
        value = "5672"
      }
      env {
        name  = "RABBITMQ_USER"
        value = var.rabbitmq_user
      }
      env {
        name  = "RABBITMQ_PASSWORD"
        value = var.rabbitmq_password
      }
      env {
        name  = "RABBITMQ_QUEUE_NAME"
        value = var.rabbitmq_queue_name
      }
    }

    container {
      name   = "collector"
      image  = "${azurerm_container_registry.container_registry.login_server}/collector:${var.web_image_tag}"
      cpu    = "0.25"
      memory = "0.5Gi"

      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
      env {
        name  = "SENTRY_DSN"
        value = var.sentry_dsn
      }
      env {
        name  = "RABBITMQ_HOST"
        value = azurerm_linux_virtual_machine.shared_vm.public_ip_address
      }
      env {
        name  = "RABBITMQ_PORT"
        value = "5672"
      }
      env {
        name  = "RABBITMQ_USER"
        value = var.rabbitmq_user
      }
      env {
        name  = "RABBITMQ_PASSWORD"
        value = var.rabbitmq_password
      }
      env {
        name  = "RABBITMQ_QUEUE_NAME"
        value = var.rabbitmq_queue_name
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
