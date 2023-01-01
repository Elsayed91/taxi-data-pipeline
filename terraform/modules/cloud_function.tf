# data "google_storage_project_service_account" "gcs_account" {
# }


# resource "google_project_iam_member" "gcs-pubsub-publishing" {
#   project = var.project
#   role    = "roles/pubsub.publisher"
#   member  = "serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"
# }


# resource "null_resource" "pack-fn" {
#   for_each = { for idx, val in var.cloud-function : idx => val if var.cloud-function != null }
#   triggers = {
#     hashed_content = jsonencode({ for fn in fileset("${path.module}/${each.value.code_path}", "**") :
#     fn => filesha256("${path.module}/${each.value.code_path}/${fn}") })
#   }

#   provisioner "local-exec" {
#     interpreter = ["/bin/bash", "-c"]
#     command     = "chmod +x ${path.module}/files/package_fn_code.sh && ${path.module}/files/package_fn_code.sh cloud_function ${each.value.build_config.source.storage_source.bucket}"
#   }

# }

# resource "time_sleep" "wait_60_seconds" {
#   depends_on      = [google_project_iam_member.grant_roles]
#   create_duration = "150s"
# }

# resource "google_cloudfunctions2_function" "ge-cfn" {
#   for_each    = { for idx, val in var.cloud-function : idx => val if var.cloud-function != null }
#   name        = each.value.name
#   location    = each.value.region == null ? var.region : each.value.region
#   description = each.value.description

#   build_config {
#     runtime               = each.value.build_config.runtime
#     entry_point           = each.value.build_config.entry_point # Set the entry point in the code
#     environment_variables = each.value.build_config.build_env_vars
#     source {
#       storage_source {
#         bucket = each.value.build_config.source.storage_source.bucket
#         object = each.value.build_config.source.storage_source.object
#       }
#     }
#   }

#   service_config {
#     max_instance_count             = each.value.service_config.max_instance_count
#     min_instance_count             = each.value.service_config.min_instance_count
#     available_memory               = each.value.service_config.available_memory
#     timeout_seconds                = each.value.service_config.timeout_seconds
#     environment_variables          = each.value.service_config.environment_variables
#     ingress_settings               = each.value.service_config.ingress_settings
#     all_traffic_on_latest_revision = each.value.service_config.all_traffic_on_latest_revision
#     service_account_email          = each.value.service_config.service_account_email
#   }

#   event_trigger {
#     trigger_region        = each.value.event_trigger.trigger_region == null ? var.region : each.value.event_trigger.trigger_region
#     event_type            = each.value.event_trigger.event_type
#     retry_policy          = each.value.event_trigger.retry_policy
#     service_account_email = each.value.event_trigger.service_account_email
#     event_filters {
#       attribute = each.value.event_trigger.event_filters.attribute
#       value     = each.value.event_trigger.event_filters.value
#     }
#   }

#   depends_on = [
#     time_sleep.wait_60_seconds, null_resource.pack-fn
#   ]
# }
# # [END functions_v2_basic_gcs]
