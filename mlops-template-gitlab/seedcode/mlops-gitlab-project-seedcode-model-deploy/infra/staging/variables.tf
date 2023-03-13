variable "aws_region" {
  description = "The region for the application evnironment - Default is Frankfurt as our main region"
  type        = string
  default     = "eu-central-1"
}

variable "aws_account_number" {
  description = "The account number used for the environment"
  type        = string
}

variable "aws_deployment_role" {
  description = "The IAM role that is used for Terraform to deploy the infrastructure"
  type        = string
}

variable "branch" {
  description = "branch used currently"
  type        = string
}

variable "model_bucket_name" {
  description = "name of s3 bucket containing container definition"
  type = string
}

variable "model_config_file" {
  description = "name of bucket file containing sagemker container definition"
  type = string
  default = "versions/container-version-latest.json"
}

variable "short_ref" {
  description = "Version of the service, will be short hash for dev, sit and pre-prod and tag name for prod"
  type        = string
}