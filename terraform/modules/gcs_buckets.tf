# creates two resources:

# 1.  A Google Cloud Storage bucket using the `google_storage_bucket` resource type. This
#     resource creates a GCS bucket and configures its properties, such as its name,
#     location, storage class, and versioning.

# 2.  A null resource using the `null_resource` resource type. This resource provisions
#     files or directories to a GCS bucket using the `gsutil` command-line tool. It
#     contains a `local-exec` provisioner that runs the `gsutil` command to upload the
#     files or directories to the GCS bucket. The hash of the files is used to determine
#     if there are changes, and the resource is re-run only if the hash changes.


# The `var.gcs-buckets` and `var.gcs-files` variables are used to configure the Google
# Cloud Storage bucket and the files/directories that are uploaded to the bucket,
# respectively.

resource "google_storage_bucket" "buckets" {
  for_each                    = { for idx, val in var.gcs-buckets : idx => val if val.bucket_name != null }
  name                        = each.value.bucket_name
  location                    = each.value.region == null ? var.region : each.value.region
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
