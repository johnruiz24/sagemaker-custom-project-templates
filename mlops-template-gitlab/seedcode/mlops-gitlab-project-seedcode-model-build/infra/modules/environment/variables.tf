variable "aws_region" {
  description = "The region for the application evnironment - Default is Frankfurt as our main region"
  type        = string
  default     = "eu-central-1"
}

variable "aws_account_number" {
  description = "The account number used for the environment"
  type        = string
}

variable "service_name" {
  description = "Name of your service, will be used as a prefix for every resource name - with commit specific hash"
  type        = string
}

variable "branch" {
  description = "branch used currently"
  type        = string
}

variable "version_prefix" {
  description = "Name of version prefix for model registry container structure"
  type        = string
  default     = "versions"
}

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
}
