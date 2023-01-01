variable "service_accounts" {
  type = list(object(
    {
      service_account_name = optional(string)
      project              = optional(string)
      create               = optional(bool, true)
      generate_key         = optional(bool, false)
      iam_roles            = optional(list(string))
      iam_binding          = optional(object({ iam_binding_role = string, iam_binding_members = list(string) }))
      key_name             = optional(string)
      service_account_id   = optional(string)
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
      ))
      node_config = optional(object({
        spot         = optional(bool, true)
        machine_type = optional(string)
        disk_size_gb = optional(number, 50)
        disk_type    = optional(string, "pd-standard") # pd-standard', 'pd-balanced' or 'pd-ssd'
        oauth_scopes = optional(list(string), [
          "https://www.googleapis.com/auth/cloud-platform",
          "https://www.googleapis.com/auth/devstorage.read_only",
        ])
        service_account   = optional(string)
        accelerator_count = optional(number)
        accelerator_type  = optional(string)
        workload_metadata_config = object({
          mode = optional(string, "GKE_METADATA")
          }
        )
      }))
  }))
  default = null
}

variable "gcs-buckets" {
  type = list(object(
    {


      bucket_name                 = optional(string)
      location                    = optional(string)
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
    }
  ))
  default = null
}

variable "cloud-function" {
  type = list(object(
    {
      name        = string
      region      = optional(string)
      code_path   = optional(string)
      description = optional(string)
      build_config = optional(object({
        runtime        = optional(string)
        entry_point    = optional(string)
        build_env_vars = optional(map(any))
        source = optional(object({
          storage_source = object({
            bucket = optional(string)
            object = optional(string)
          })
          }
        ))
        }
      ))

      service_config = optional(object({
        max_instance_count             = optional(number)
        min_instance_count             = optional(number)
        available_memory               = optional(string)
        timeout_seconds                = optional(number)
        ingress_settings               = optional(string)
        all_traffic_on_latest_revision = optional(bool)
        service_account_email          = optional(string)
        environment_variables          = optional(map(any))



        }
      ))
      event_trigger = optional(object({
        trigger_region        = optional(string)
        event_type            = optional(string)
        retry_policy          = optional(string)
        service_account_email = optional(string)
        event_filters = optional(object({
          attribute = optional(string)
          value     = optional(string)
        }))
      }))
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
