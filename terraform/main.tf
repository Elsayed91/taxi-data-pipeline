locals {

  sensitive_env = { for tuple in regexall("(.*?)=\"(.*)\"", file("${path.module}/../secrets/secret.env")) : tuple[0] => sensitive(tuple[1]) }
  envs          = { for tuple in regexall("(.*?)=\"(.*)\"", file("${path.module}/../.env")) : tuple[0] => tuple[1] }
  config        = yamldecode(templatefile("${path.module}/configuration/config.yaml", local.envs))

}

module "project" {

  source           = "./modules/"
  project          = local.config["common"]["project"]
  region           = local.config["common"]["region"]
  location         = local.config["common"]["location"]
  custom_roles     = local.config["GCP"]["custom_roles"]
  service_accounts = local.config["GCP"]["service-accounts"]
  # bigquery         = local.config["GCP"]["datasets"]
  gke-clusters   = local.config["GCP"]["clusters"]
  gke-node-pools = local.config["GCP"]["node_pools"]
  gcs-buckets    = local.config["GCP"]["buckets"]
  gcs-files      = local.config["GCP"]["files"]
  s3-secrets     = local.config["AWS"]["secrets"]
  s3-buckets     = local.config["AWS"]["buckets"]
  lambda         = local.config["AWS"]["lambdas"]
  # cloud-function   = local.config["GCP"]["cloud-functions"]
}

