variable "project_alias" {
  description = "Designated project abreviated name to identify aws resources"
  type        = string
  default     = "mlops-model-pipeline-template"
}

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
