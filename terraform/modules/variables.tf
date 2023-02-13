# declares variables for creating and configuring various GCP and AWS resources.

# -   `service_accounts`: defines the properties of one or more service accounts such as
#     name, project, create flag, etc.

# -   `custom_roles`: lists custom roles with role ID, title, and permissions.

# -   `bigquery`: lists BigQuery datasets and their properties such as dataset ID, region,
#     tables, and their properties such as table ID, time partitioning, clustering fields,
#     schema, etc.

# -   `gke-clusters`: lists properties for one or more Google Kubernetes Engine (GKE)
#     clusters, such as name, project, location, add-ons, node count, etc.

# -   `gke-node-pools`: lists properties for node pools in GKE clusters, such as name,
#     node count, autoscaling, management, node configuration, etc.

# -   `gcs-buckets`: lists properties for Google Cloud Storage (GCS) buckets, such as
#     name, location, project, storage class, versioning, etc.

# -   `gcs-files`: lists properties for files in GCS, such as content path, hash strategy,
#     gsutil command, etc.

# -   `s3-buckets`: lists properties for Amazon S3 buckets, such as name, access control
#     list (ACL), versioning, etc.

# -   `s3-objects`: lists properties for objects in Amazon S3, such as content path, hash
#     strategy, aws command, etc.

variable "service_accounts" {
  type = list(object(
    {
      service_account_name = optional(string)
      project              = optional(string)
      create               = optional(bool, true)
      generate_key         = optional(bool, false)
      iam_roles            = optional(list(string))
      iam_binding = optional(object({ iam_binding_role = string,
      iam_binding_members = list(string) }))
      key_name = optional(string)
  }))

}

variable "custom_roles" {
  type = list(object({
    role_id = string,
    title   = string,
  permissions = list(string) }))

  default = null
}

variable "bigquery" {
  type = list(object(
    {
      dataset_id = string
      region     = optional(string)
      tables = optional(list(object(
        {
          table_id = string
          time_partitioning = optional(object({
            type          = optional(string)
            field         = optional(string)
            expiration_ms = optional(number)
            }
          ))
          clustering_fields = optional(list(string))
          schema            = optional(string)
          view              = optional(object({ view_query = string }), null)
        }
        ))
    ) }
  ))
  default = null
}


variable "gke-clusters" {
  type = list(object(
    {
      name     = optional(string)
      project  = optional(string)
      location = optional(string)
      workload_identity_config = optional(object({
        workload_pool = optional(string)
        }
      ))
      addons_config = optional(object({
        horizontal_pod_autoscaling = optional(object({
          disabled = optional(bool, true)
        }))
        }
      ))
      initial_node_count       = optional(number, 1)
      remove_default_node_pool = optional(bool, true)

    }
  ))
  default = null
}



variable "gke-node-pools" {
  type = list(object(
    {
      name       = optional(string)
      cluster    = optional(string)
      node_count = optional(number)
      autoscaling = optional(object({
        min_node_count  = optional(number, 0)
        max_node_count  = optional(number)
        location_policy = optional(string, "ANY")
        }
      ))
      management = optional(object({
        auto_repair  = optional(bool, true)
        auto_upgrade = optional(bool, true)
        }
      ), {})
      node_config = optional(object({

        spot         = optional(bool, true)
        machine_type = optional(string)
        disk_size_gb = optional(number, 50)
        disk_type    = optional(string, "pd-standard") # pd-standard', 'pd-balanced' or 'pd-ssd'
        oauth_scopes = optional(list(string), [
          "https://www.googleapis.com/auth/cloud-platform",
          "https://www.googleapis.com/auth/devstorage.read_only",
        ])
        service_account          = optional(string)
        accelerator_count        = optional(number)
        accelerator_type         = optional(string)
        workload_metadata_config = optional(string, "GKE_METADATA")
      }))
  }))
  default = null
}

variable "gcs-buckets" {
  type = list(object(
    {


      bucket_name                 = optional(string)
      region                      = optional(string)
      project                     = optional(string)
      uniform_bucket_level_access = optional(bool, true)
      force_destroy               = optional(bool, true)
      storage_class               = optional(string, "STANDARD")
      versioning                  = optional(object({ enabled = optional(bool, false) }))
    }
  ))
  default = null
}

variable "gcs-files" {
  type = list(object(
    {
      content_path   = optional(string)
      hash_strategy  = optional(string)
      gsutil_command = optional(string)
    }
  ))
  default = null
}

variable "s3-buckets" {
  type = list(object(
    {
      name = string
      acl  = optional(string, "public-read")
    }
  ))
  default = null
}


variable "lambda" {
  type = list(object(
    {
      name              = string
      dependencies_path = optional(string)
      vars              = optional(map(any))
      trigger_bucket    = optional(string)
      code_path         = optional(string)
      memory_size       = optional(number, 128)
    }
  ))
  default = null
}



variable "s3-secrets" {
  type = list(object(
    {
      name          = string
      type          = string
      secret_string = string
      key_id        = string
    }
  ))
  default = null
}


variable "project" {
  type = string
}

variable "region" {
  type = string
}

variable "location" {
  type = string
}
