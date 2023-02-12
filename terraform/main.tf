
locals {
  # sensitive_env = try({ for tuple in regexall("(.*?)=\"(.*)\"", file("${path.module}/../.env")) : tuple[0] => sensitive(tuple[1]) }, null)
  envs = { for tuple in regexall("(.*?)=\"(.*)\"", file("${var.env_path}")) : tuple[0] => tuple[1] }
  gcp  = yamldecode(templatefile("${path.module}/configuration/gcp.yaml", local.envs))
  aws  = yamldecode(templatefile("${path.module}/configuration/aws.yaml", local.envs))
}

module "project" {
  source           = "./modules/"
  project          = local.envs["PROJECT"]
  region           = local.envs["GCP_REGION"]
  location         = local.envs["GCP_ZONE"]
  custom_roles     = local.gcp["IAM"]["custom_roles"]
  service_accounts = local.gcp["IAM"]["service-accounts"]
  bigquery         = local.gcp["BIGQUERY"]["datasets"]
  gke-clusters     = local.gcp["GKE"]["clusters"]
  gke-node-pools   = local.gcp["GKE"]["node_pools"]
  gcs-buckets      = local.gcp["GCS"]["buckets"]
  gcs-files        = local.gcp["GCS"]["files"]
  s3-secrets       = local.aws["SECRETSMANAGER"]
  s3-buckets       = local.aws["S3"]
  lambda           = local.aws["LAMBDA"]
}


