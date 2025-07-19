#!/bin/bash
# Script to deploy shared infrastructure components
# like PostgreSQL and RabbitMQ during provisioning
# of an Azure Virtual Machine.

set -e
set -o pipefail

# Update packages
sudo apt-get update -y
sudo apt-get upgrade -y

# Install PostgreSQL
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Configure PostgreSQL to accept remote connections
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" /etc/postgresql/*/main/postgresql.conf
echo "host all all 0.0.0.0/0 md5" | sudo tee -a /etc/postgresql/*/main/pg_hba.conf
sudo systemctl restart postgresql

# Install RabbitMQ
sudo apt-get install -y rabbitmq-server
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server

# Configure RabbitMQ to accept remote connections
sudo sed -i 's/#\s*listeners.tcp.default\s*=\s*5672/listeners.tcp.default = 5672/' /etc/rabbitmq/rabbitmq.conf || echo "listeners.tcp.default = 5672" | sudo tee -a /etc/rabbitmq/rabbitmq.conf
echo "loopback_users = none" | sudo tee -a /etc/rabbitmq/rabbitmq.conf

# Enable RabbitMQ management plugin
sudo rabbitmq-plugins enable rabbitmq_management
sudo systemctl restart rabbitmq-server
