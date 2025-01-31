variable "project_id" {
  type        = string
  description = "GCP project id"
}

variable "region" {
  type        = string
  description = "GCP region resources"
}

variable "db_password" {
  type        = string
  description = "db password"
}

variable "GOOGLE_APPLICATION_CREDENTIALS" {
  type        = string
  description = "Path to the Google credentials JSON file"
}