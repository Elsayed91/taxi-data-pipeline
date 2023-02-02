# creates BigQuery datasets and tables on Google Cloud Platform.

# The input to this module is defined in the var.bigquery variable, which is an array of
# maps that specifies the properties of each BigQuery dataset and table to be created.

# The locals block is used to preprocess the var.bigquery variable and flatten it into a
# list of maps, where each map represents a single table. This allows for easier iteration
# in the following resources.

# The google_bigquery_dataset resource creates a BigQuery dataset for each map in the
# preprocessed var.bigquery list. The for_each argument is used to loop through each map
# and create a dataset with the dataset_id specified in each map. The location of the
# dataset is specified by the region field, with a fallback to the value of var.region if
# not specified.

# The google_bigquery_table resource creates a BigQuery table for each map in the
# preprocessed var.bigquery list. Similar to the google_bigquery_dataset resource, the
# for_each argument is used to loop through each map and create a table with the specified
# dataset_id and table_id. The dynamic blocks are used to specify time partitioning, table
# view, and schema for the table. The schema field references a local file that specifies
# the schema for the table.

# The google_bigquery_table resource depends on the google_bigquery_dataset resource, so
# the datasets are created before the tables.

locals {
  bigquery = flatten([for idx, value in var.bigquery :
    [for table in try(value.tables, null) : {
      "dataset_id"         = try(value.dataset_id, null)
      "table_id"           = try(table.table_id, null)
      "time_partitioning"  = try(table.time_partitioning, null)
      "partitioning_type"  = try(table.time_partitioning.type, null)
      "partitioning_field" = try(table.time_partitioning.field, null)
      "expiration_ms"      = try(table.time_partitioning.expiration_ms, null)
      "clustering_fields"  = try(table.clustering_fields, null)
      "schema"             = try(table.schema, null)
      "view"               = try(table.view, null)
    }]
    if try(value.tables, null) != null
  ])

}


resource "google_bigquery_dataset" "datasets" {
  for_each   = { for idx, val in var.bigquery : idx => val if val.dataset_id != null }
  dataset_id = each.value.dataset_id
  location   = each.value.region == null ? var.region : each.value.region

}

resource "google_bigquery_table" "tables" {
  for_each            = { for idx, val in local.bigquery : idx => val if val.table_id != null }
  dataset_id          = each.value.dataset_id
  table_id            = each.value.table_id
  clustering          = each.value.clustering_fields
  deletion_protection = false
  dynamic "time_partitioning" {
    for_each = each.value.time_partitioning == null ? [] : [each.value.time_partitioning]
    content {
      type          = each.value.partitioning_type
      field         = each.value.partitioning_field
      expiration_ms = each.value.expiration_ms
    }
  }

  dynamic "view" {
    for_each = each.value.view == null ? [] : [each.value.view]
    content {
      query          = each.value.view.view_query
      use_legacy_sql = false
    }
  }

  schema = try(file("${path.module}/${each.value.schema}"), null)
  depends_on = [
    google_bigquery_dataset.datasets
  ]
}
