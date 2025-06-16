terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.16.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Retrieve tfvars from secret manager
data "google_secret_manager_secret_version" "tfvars" {
  secret  = "cornhole-app-secrets"
  version = "latest"

}

# Decode tfvars to JSON
locals {
  tfvars = jsondecode(data.google_secret_manager_secret_version.tfvars.secret_data)
}


# Create Cloud SQL instance 
resource "google_sql_database_instance" "mysql-instance" {
  name                = "mysql-instance"
  region              = var.region
  database_version    = "MYSQL_8_0"
  deletion_protection = true

  settings {
    tier = "db-f1-micro"
    backup_configuration {
      enabled    = true
      start_time = "3:00"
    }
    ip_configuration {
      ipv4_enabled = true
  
    }
  }
}

# Create Cloud SQL database
resource "google_sql_database" "mysql-db" {
  name     = "mysql-db"
  instance = google_sql_database_instance.mysql-instance.name
}

# Create Cloud SQL user
resource "google_sql_user" "mysql-user" {
  name     = "mysql-user"
  instance = google_sql_database_instance.mysql-instance.name
  host     = "%"
  password = local.tfvars.db_password
}

resource "google_app_engine_standard_app_version" "app-version" {
  project    = var.project_id
  runtime    = "python311" 
  service    = "default"
  version_id = "v1"

  deployment {
    zip {
      source_url  = "https://storage.googleapis.com/cornhole-app-yaml/source_code.zip"
      files_count = 1
    }
  }

  entrypoint {
    shell = ""
  }

  automatic_scaling {
    min_idle_instances = 1
    max_idle_instances = 2
  }
}


# Create Service Account for Cloud SQL
resource "google_service_account" "cloud_sql_sa" {
  account_id = "cloud-sql-sa"
}

# Assign IAM roles to Cloud SQL SA
resource "google_project_iam_member" "cloud_sql_sa_role" {
  project = var.project_id
  role    = "roles/cloudsql.client"
  member  = "serviceAccount:${google_service_account.cloud_sql_sa.email}"
}

resource "google_project_iam_member" "cloud_sql_admin" {
  project = var.project_id
  role    = "roles/cloudsql.admin"
  member  = "serviceAccount:${google_service_account.cloud_sql_sa.email}"
}

#test