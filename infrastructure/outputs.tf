output "web_app_url" {
  description = "The URL of the web application."
  value       = azurerm_container_app.web_app.latest_revision_fqdn
}
