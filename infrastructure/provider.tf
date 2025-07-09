terraform {
    required_providers {
        azurerm = {
            source  = "hashicorp/azurerm"
            version = "~> 4.35.0"
        }
    }

    backend "azurerm" {
        resource_group_name  = "final-project-state-rg"
        storage_account_name = "terraformfinalprojstate"
        container_name       = "tfstate"
        key                  = "terraform.tfstate"
    }
}

provider "azurerm" {
  features {}
}
