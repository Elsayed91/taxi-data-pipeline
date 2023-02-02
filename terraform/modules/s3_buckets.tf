# creates an AWS S3 bucket, and sets the Access Control List (ACL) for the bucket.

# The `aws_s3_bucket` resource is defined for each element in the `var.s3-buckets`
# variable, which must be a list of objects representing the S3 buckets to create. The
# `bucket` argument is set to each object's `name` field.

# The `aws_s3_bucket_acl` resource is also defined for each element in `var.s3-buckets`.
# The `bucket` argument is set to the `id` field of the corresponding `aws_s3_bucket`
# resource for that element, and the `acl` argument is set to the `acl` field of the
# object.

resource "aws_s3_bucket" "bucket" {
  for_each = { for idx, bucket in var.s3-buckets : idx => bucket if var.s3-buckets != null }
  bucket   = each.value.name

}

resource "aws_s3_bucket_acl" "bucketacl" {
  for_each = { for idx, bucket in var.s3-buckets : idx => bucket if var.s3-buckets != null }
  bucket   = aws_s3_bucket.bucket[each.key].id
  acl      = each.value.acl
}
