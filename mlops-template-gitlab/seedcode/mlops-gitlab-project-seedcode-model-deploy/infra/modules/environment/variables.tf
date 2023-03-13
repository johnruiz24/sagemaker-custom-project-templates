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

variable "tags" {
  description = "Common resource tags"
  type        = map(string)
}

variable "initial_instance_count" {
  description = "Initial instance count for both models"
  type = number
  default = 1
}

variable "variant_weight_v1" {
  description = "Relative model weight for model v1"
  type = number
  default = 100
}

variable "autoscaling_config" {
  description = "Describes the autoscaling"
  type = object({
    max_instance_count = number
    min_instance_count = number
    target_scale_in_cooldown = number
    target_scale_out_cooldown = number
    target_cpu_utilization = number
  })
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

variable "branch" {
  description = "branch used currently"
  type        = string
}