resource "google_storage_bucket" "buckets" {
  for_each                    = { for idx, val in var.gcs-buckets : idx => val if val.bucket_name != null }
  name                        = each.value.bucket_name
  location                    = each.value.location == null ? var.region : each.value.location
  project                     = each.value.project == null ? var.project : each.value.project
  uniform_bucket_level_access = each.value.uniform_bucket_level_access
  force_destroy               = each.value.force_destroy
  storage_class               = each.value.storage_class
  dynamic "versioning" {
    for_each = each.value.versioning == null ? [] : [each.value.versioning]
    content {
      enabled = each.value.versioning.enabled
    }

  }
}

resource "null_resource" "gsutil-hash-sync-files" {
  for_each = { for idx, val in var.gcs-files : idx => val if var.gcs-files != {} }
  triggers = {
    hashed_content = each.value.hash_strategy == "file" ? filesha256("${path.module}/${each.value.content_path}") : jsonencode({ for fn in fileset("${path.module}/${each.value.content_path}", "**") :
    fn => filesha256("${path.module}/${each.value.content_path}/${fn}") })
  }

  provisioner "local-exec" {
    command = each.value.gsutil_command
  }
  depends_on = [
    google_storage_bucket.buckets
  ]
}
