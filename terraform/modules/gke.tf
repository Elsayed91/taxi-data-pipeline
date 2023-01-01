resource "google_container_cluster" "primary" {
  for_each                 = { for cluster in var.gke-clusters : cluster.name => cluster if cluster.name != null }
  project                  = each.value.project == null ? var.project : each.value.project
  name                     = each.value.name
  location                 = each.value.location == null ? var.location : each.value.location
  remove_default_node_pool = each.value.remove_default_node_pool
  initial_node_count       = each.value.initial_node_count

  dynamic "addons_config" {
    for_each = each.value.addons_config == null ? [] : [each.value.addons_config]
    content {
      horizontal_pod_autoscaling {
        disabled = each.value.addons_config.horizontal_pod_autoscaling.disabled
      }
    }

  }

  dynamic "workload_identity_config" {
    for_each = each.value.workload_identity_config == null ? [] : [each.value.workload_identity_config]
    content { workload_pool = each.value.workload_identity_config.workload_pool }
  }
}

resource "time_sleep" "wait_30_seconds" {
  depends_on      = [google_container_cluster.primary]
  create_duration = "30s"
}

resource "google_container_node_pool" "nps" {
  for_each   = { for np in var.gke-node-pools : np.name => np if np.name != null }
  name       = each.value.name
  cluster    = each.value.cluster
  node_count = each.value.node_count

  dynamic "autoscaling" {
    for_each = each.value.autoscaling == null ? [] : [each.value.autoscaling]
    content {
      min_node_count  = each.value.autoscaling.min_node_count
      max_node_count  = each.value.autoscaling.max_node_count
      location_policy = each.value.autoscaling.location_policy
    }

  }

  dynamic "management" {
    for_each = each.value.management == null ? [] : [each.value.management]
    content {
      auto_repair  = each.value.management.auto_repair
      auto_upgrade = each.value.management.auto_upgrade
    }
  }

  node_config {
    spot            = each.value.node_config.spot
    machine_type    = each.value.node_config.machine_type
    disk_size_gb    = each.value.node_config.disk_size_gb
    oauth_scopes    = each.value.node_config.oauth_scopes
    service_account = each.value.node_config.service_account
    disk_type       = each.value.node_config.disk_type
    workload_metadata_config {
      mode = each.value.node_config.workload_metadata_config.mode
    }

  }
  depends_on = [
    time_sleep.wait_30_seconds, google_service_account.service_account
  ]
}


