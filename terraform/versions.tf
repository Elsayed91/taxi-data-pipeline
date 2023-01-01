terraform {

  backend "local" {
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
      source = "hashicorp/random"
    }
  }

  required_version = ">= 1.0"
}



