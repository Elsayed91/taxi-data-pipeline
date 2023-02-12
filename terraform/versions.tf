# terraform {
#   backend "gcs" {
#     bucket = "4e08a42ce7-bucket-tfstate"
#     prefix = "terraform/state"
#   }
#   required_providers {
#     local = {
#       source  = "hashicorp/local"
#       version = ">= 2.2.3"
#     }
#     aws = {
#       source  = "hashicorp/aws"
#       version = "~> 4.45.0"
#     }
#     google = {
#       source  = "hashicorp/google"
#       version = "~> 4.45.0"
#     }
#     random = {
#       source = "hashicorp/random"
#     }
#   }
#   required_version = ">= 1.0"
# }



