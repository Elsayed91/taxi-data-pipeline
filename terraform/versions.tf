terraform {
  backend "gcs" {
    bucket = "4e08a42ce7-bucket-tfstate"
    prefix = "terraform/state"
  }
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = ">= 2.2.3"
    }
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.45.0"
    }
    google = {
      source  = "hashicorp/google"
      version = "~> 4.45.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4.3"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2.1"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.3.0"
    }
  }
  required_version = ">= 1.0"
}
