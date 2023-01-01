# resource "aws_s3_bucket" "bucket" {
#   for_each = { for idx, bucket in var.s3-buckets : idx => bucket if var.s3-buckets != null }
#   bucket   = each.value.name

# }

# resource "aws_s3_bucket_acl" "bucketacl" {
#   for_each = { for idx, bucket in var.s3-buckets : idx => bucket if var.s3-buckets != null }
#   bucket   = aws_s3_bucket.bucket[each.key].id
#   acl      = "public-read"
# }
