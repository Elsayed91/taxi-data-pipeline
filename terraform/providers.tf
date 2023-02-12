# provider "google" {
#   project = local.envs["PROJECT"]
#   region  = local.envs["GCP_REGION"]
#   zone    = local.envs["GCP_ZONE"]
# }

# provider "aws" {
#   access_key = sensitive(local.envs["AWS_ACCESS_KEY_ID"])
#   secret_key = sensitive(local.envs["AWS_SECRET_ACCESS_KEY"])
#   region     = local.envs["AWS_REGION"]
# }
