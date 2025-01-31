terraform {
  backend "gcs" {
    bucket = "terraform-cornhole-state-bucket"
    prefix = "terraform/state"
  }
}