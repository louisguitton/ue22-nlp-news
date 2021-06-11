# Ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/s3_bucket
data "aws_s3_bucket" "articles" {
  bucket = "articles-louisguitton"
}
