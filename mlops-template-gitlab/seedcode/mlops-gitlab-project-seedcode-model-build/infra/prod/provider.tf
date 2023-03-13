provider "aws" {
  region = var.aws_region

  assume_role {
    # aws_deployment_role is only set if it runs in the pipeline, if
    # this var is null, then no role will be assumed. That way it is
    # possible to run Terraform locally with aws-vault.
    role_arn     = var.aws_deployment_role != null ? "arn:aws:iam::${var.aws_account_number}:role/${var.aws_deployment_role}" : ""
    session_name = "deployment@${var.aws_account_number}"
  }
}
