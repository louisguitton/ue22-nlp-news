# Ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_user
resource "aws_iam_user" "ue22-label-studio" {
  name = "ue22-label-studio"
}

# Ref: https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/iam_access_key
resource "aws_iam_access_key" "ue22-label-studio" {
  user = aws_iam_user.ue22-label-studio.name
}

data "aws_iam_policy_document" "ue22" {
  statement {
    actions = [
      "s3:ListBucket",
    ]

    resources = [
      data.aws_s3_bucket.articles.arn
    ]

    condition {
      test     = "StringLike"
      variable = "s3:prefix"

      values = [
        "newsapi/*",
        "ue22/*",
      ]
    }
  }

  statement {
    actions = [
      "s3:GetObject",
      "s3:PutObject"
    ]

    resources = [
      "${data.aws_s3_bucket.articles.arn}/*"
    ]
  }


}

resource "aws_iam_user_policy" "ue22" {
  name   = "ue22"
  user   = aws_iam_user.ue22-label-studio.name
  policy = data.aws_iam_policy_document.ue22.json
}

output "AWS_ACCESS_KEY_ID" {
  value = aws_iam_access_key.ue22-label-studio.id
}
output "AWS_SECRET_ACCESS_KEY" {
  value = aws_iam_access_key.ue22-label-studio.secret
}
