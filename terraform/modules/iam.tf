locals {

  iam_roles = flatten([for idx, value in var.service_accounts :
    [for role_idx in range(length(value.iam_roles)) : {
      "role"                 = try(value.iam_roles[role_idx], null)
      "project"              = value.project == null ? var.project : value.project
      "service_account_name" = try(value.service_account_name, null)
      "service_account_id"   = try(value.service_account_id, null)
    }]
    if try(value.iam_roles, null) != null
  ])


}

resource "google_project_iam_custom_role" "custom-roles" {
  for_each    = { for idx, sa in var.custom_roles : idx => sa if var.custom_roles != {} }
  role_id     = each.value.role_id
  project     = try(each.value.project, var.project)
  title       = each.value.title
  permissions = each.value.permissions
}

resource "google_service_account" "service_account" {
  for_each   = { for idx, sa in var.service_accounts : idx => sa if sa.create == true }
  account_id = each.value.service_account_name
  project    = try(each.value.project, var.project)
}

resource "google_project_iam_member" "grant_roles" {
  for_each = { for idx, sa in local.iam_roles : idx => sa if local.iam_roles != null }
  project  = try(each.value.project, var.project)
  role     = each.value.role
  member   = "serviceAccount:${each.value.service_account_name}@${each.value.project}.iam.gserviceaccount.com"
  depends_on = [
    google_service_account.service_account
  ]
}

resource "google_service_account_iam_binding" "iam_binding" {
  for_each           = { for idx, sa in var.service_accounts : idx => sa if sa.iam_binding != null }
  service_account_id = each.value.service_account_id
  role               = each.value.iam_binding.iam_binding_role
  members            = each.value.iam_binding.iam_binding_members
  depends_on = [
    google_service_account.service_account, google_container_cluster.primary
  ]
}


resource "google_service_account_key" "key" {
  for_each           = { for idx, sa in var.service_accounts : idx => sa if sa.generate_key == true }
  service_account_id = each.value.service_account_id
  public_key_type    = "TYPE_X509_PEM_FILE"
  depends_on = [
    google_service_account.service_account
  ]
}

resource "local_file" "key_out" {
  for_each = { for idx, sa in var.service_accounts : idx => sa if sa.generate_key == true }
  content  = base64decode(google_service_account_key.key[each.key].private_key)
  filename = "${path.module}/${each.value.key_name}"
  depends_on = [
    google_service_account_key.key
  ]
}
