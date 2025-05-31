# =============================================================================
# GitHub Secrets Management with Terraform
# =============================================================================
# This manages GitHub repository secrets as Infrastructure as Code
# Usage: terraform apply -var-file="secrets.tfvars"

terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

# Configure the GitHub Provider
provider "github" {
  token = var.github_token
  owner = var.github_owner
}

# Variables for secrets
variable "github_token" {
  description = "GitHub personal access token"
  type        = string
  sensitive   = true
}

variable "github_owner" {
  description = "GitHub repository owner"
  type        = string
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
}

# Application Configuration
variable "dd_service" {
  description = "Datadog service name"
  type        = string
  default     = "fastapi-app"
}

variable "dd_env" {
  description = "Datadog environment"
  type        = string
  default     = "production"
}

variable "dd_version" {
  description = "Application version"
  type        = string
  default     = "1.0"
}

# Database Configuration
variable "pghost" {
  description = "PostgreSQL host"
  type        = string
  sensitive   = true
}

variable "pgport" {
  description = "PostgreSQL port"
  type        = string
  default     = "5432"
}

variable "pgdatabase" {
  description = "PostgreSQL database name"
  type        = string
  sensitive   = true
}

variable "pguser" {
  description = "PostgreSQL username"
  type        = string
  sensitive   = true
}

variable "pgpassword" {
  description = "PostgreSQL password"
  type        = string
  sensitive   = true
}

# External API Keys
variable "openai_api_key" {
  description = "OpenAI API key"
  type        = string
  sensitive   = true
}

variable "datadog_api_key" {
  description = "Datadog API key"
  type        = string
  sensitive   = true
}

variable "datadog_app_key" {
  description = "Datadog application key"
  type        = string
  sensitive   = true
}

variable "sendgrid_api_key" {
  description = "SendGrid API key"
  type        = string
  sensitive   = true
}

variable "notion_api_key" {
  description = "Notion API key"
  type        = string
  sensitive   = true
}

variable "notion_database_id" {
  description = "Notion database ID"
  type        = string
  sensitive   = true
}

# AWS Configuration
variable "amazon_key_id" {
  description = "AWS access key ID"
  type        = string
  sensitive   = true
}

variable "amazon_key_secret" {
  description = "AWS secret access key"
  type        = string
  sensitive   = true
}

variable "amazon_s3_bucket" {
  description = "AWS S3 bucket name"
  type        = string
  sensitive   = true
}

# MongoDB Configuration
variable "mongo_conn" {
  description = "MongoDB connection string"
  type        = string
  sensitive   = true
}

variable "mongo_user" {
  description = "MongoDB username"
  type        = string
  sensitive   = true
}

variable "mongo_pw" {
  description = "MongoDB password"
  type        = string
  sensitive   = true
}

# Application Specific
variable "bug_report_email" {
  description = "Bug report email"
  type        = string
  default     = "event-8l2d0xg2@dtdg.co"
}

# GitHub Secrets Resources
resource "github_actions_secret" "dd_service" {
  repository      = var.github_repo
  secret_name     = "DD_SERVICE"
  plaintext_value = var.dd_service
}

resource "github_actions_secret" "dd_env" {
  repository      = var.github_repo
  secret_name     = "DD_ENV"
  plaintext_value = var.dd_env
}

resource "github_actions_secret" "dd_version" {
  repository      = var.github_repo
  secret_name     = "DD_VERSION"
  plaintext_value = var.dd_version
}

resource "github_actions_secret" "pghost" {
  repository      = var.github_repo
  secret_name     = "PGHOST"
  plaintext_value = var.pghost
}

resource "github_actions_secret" "pgport" {
  repository      = var.github_repo
  secret_name     = "PGPORT"
  plaintext_value = var.pgport
}

resource "github_actions_secret" "pgdatabase" {
  repository      = var.github_repo
  secret_name     = "PGDATABASE"
  plaintext_value = var.pgdatabase
}

resource "github_actions_secret" "pguser" {
  repository      = var.github_repo
  secret_name     = "PGUSER"
  plaintext_value = var.pguser
}

resource "github_actions_secret" "pgpassword" {
  repository      = var.github_repo
  secret_name     = "PGPASSWORD"
  plaintext_value = var.pgpassword
}

resource "github_actions_secret" "openai_api_key" {
  repository      = var.github_repo
  secret_name     = "OPENAI_API_KEY"
  plaintext_value = var.openai_api_key
}

resource "github_actions_secret" "datadog_api_key" {
  repository      = var.github_repo
  secret_name     = "DATADOG_API_KEY"
  plaintext_value = var.datadog_api_key
}

resource "github_actions_secret" "datadog_app_key" {
  repository      = var.github_repo
  secret_name     = "DATADOG_APP_KEY"
  plaintext_value = var.datadog_app_key
}

resource "github_actions_secret" "sendgrid_api_key" {
  repository      = var.github_repo
  secret_name     = "SENDGRID_API_KEY"
  plaintext_value = var.sendgrid_api_key
}

resource "github_actions_secret" "notion_api_key" {
  repository      = var.github_repo
  secret_name     = "NOTION_API_KEY"
  plaintext_value = var.notion_api_key
}

resource "github_actions_secret" "notion_database_id" {
  repository      = var.github_repo
  secret_name     = "NOTION_DATABASE_ID"
  plaintext_value = var.notion_database_id
}

resource "github_actions_secret" "amazon_key_id" {
  repository      = var.github_repo
  secret_name     = "AMAZON_KEY_ID"
  plaintext_value = var.amazon_key_id
}

resource "github_actions_secret" "amazon_key_secret" {
  repository      = var.github_repo
  secret_name     = "AMAZON_KEY_SECRET"
  plaintext_value = var.amazon_key_secret
}

resource "github_actions_secret" "amazon_s3_bucket" {
  repository      = var.github_repo
  secret_name     = "AMAZON_S3_BUCKET"
  plaintext_value = var.amazon_s3_bucket
}

resource "github_actions_secret" "mongo_conn" {
  repository      = var.github_repo
  secret_name     = "MONGO_CONN"
  plaintext_value = var.mongo_conn
}

resource "github_actions_secret" "mongo_user" {
  repository      = var.github_repo
  secret_name     = "MONGO_USER"
  plaintext_value = var.mongo_user
}

resource "github_actions_secret" "mongo_pw" {
  repository      = var.github_repo
  secret_name     = "MONGO_PW"
  plaintext_value = var.mongo_pw
}

resource "github_actions_secret" "bug_report_email" {
  repository      = var.github_repo
  secret_name     = "BUG_REPORT_EMAIL"
  plaintext_value = var.bug_report_email
}

# Output summary
output "secrets_created" {
  description = "Number of secrets created"
  value = length([
    github_actions_secret.dd_service,
    github_actions_secret.dd_env,
    github_actions_secret.dd_version,
    github_actions_secret.pghost,
    github_actions_secret.pgport,
    github_actions_secret.pgdatabase,
    github_actions_secret.pguser,
    github_actions_secret.pgpassword,
    github_actions_secret.openai_api_key,
    github_actions_secret.datadog_api_key,
    github_actions_secret.datadog_app_key,
    github_actions_secret.sendgrid_api_key,
    github_actions_secret.notion_api_key,
    github_actions_secret.notion_database_id,
    github_actions_secret.amazon_key_id,
    github_actions_secret.amazon_key_secret,
    github_actions_secret.amazon_s3_bucket,
    github_actions_secret.mongo_conn,
    github_actions_secret.mongo_user,
    github_actions_secret.mongo_pw,
    github_actions_secret.bug_report_email
  ])
} 