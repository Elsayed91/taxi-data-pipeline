# locals {
#   bigquery = flatten([for idx, value in var.bigquery :
#     [for table in try(value.tables, null) : {
#       "dataset_id"         = try(value.dataset_id, null)
#       "table_id"           = try(table.table_id, null)
#       "time_partitioning"  = try(table.time_partitioning, null)
#       "partitioning_type"  = try(table.time_partitioning.type, null)
#       "partitioning_field" = try(table.time_partitioning.field, null)
#       "expiration_ms"      = try(table.time_partitioning.expiration_ms, null)
#       "clustering_fields"  = try(table.clustering_fields, null)
#       "schema"             = try(table.schema, null)
#       "view"               = try(table.view, null)
#     }]
#     if try(value.tables, null) != null
#   ])

# }


# resource "google_bigquery_dataset" "datasets" {
#   for_each   = { for idx, val in var.bigquery : idx => val if val.dataset_id != null }
#   dataset_id = each.value.dataset_id
#   location   = each.value.region == null ? var.region : each.value.region

# }

# resource "google_bigquery_table" "tables" {
#   for_each   = { for idx, val in local.bigquery : idx => val if val.table_id != null }
#   dataset_id = each.value.dataset_id
#   table_id   = each.value.table_id
#   clustering = each.value.clustering_fields

#   dynamic "time_partitioning" {
#     for_each = each.value.time_partitioning == null ? [] : [each.value.time_partitioning]
#     content {
#       type          = each.value.partitioning_type
#       field         = each.value.partitioning_field
#       expiration_ms = each.value.expiration_ms
#     }
#   }

#   dynamic "view" {
#     for_each = each.value.view == null ? [] : [each.value.view]
#     content {
#       query          = each.value.view.view_query
#       use_legacy_sql = false
#     }
#   }

#   schema = try(file("${path.module}/${each.value.schema}"), null)
#   depends_on = [
#     google_bigquery_dataset.datasets
#   ]
# }
