#Model config file location
data "aws_s3_object" "mlops_model_container_config" {
  bucket = var.model_bucket_name
  key    = var.model_config_file
}

resource "aws_sagemaker_model" "model" {
  name  = "${var.service_name}-model"
  execution_role_arn = aws_iam_role.sagemaker_role.arn
  tags = var.tags

# Define endpoint config
dynamic "container" {
    iterator = container
    for_each = jsondecode(data.aws_s3_object.mlops_model_container_config.body)
    content {
        image = lookup(container.value, "Image", null)
        model_data_url  = lookup(container.value, "ModelDataUrl", null)
        environment  = lookup(container.value, "Environment", null)
      }
    }
}

resource "aws_sagemaker_endpoint_configuration" "epc" {
  name = "${var.service_name}-endpoint-config"
  tags = var.tags

  production_variants {
    variant_name = aws_sagemaker_model.model.name
    model_name  = aws_sagemaker_model.model.name
    initial_instance_count = var.initial_instance_count
    instance_type = "ml.m5.xlarge"
    initial_variant_weight = var.variant_weight_v1
  }

  # from: https://discuss.hashicorp.com/t/sagemaker-endpoint-not-updating-with-configuration-change/1727
  # By default Terraform destroys resources before creating the new one. However, in this case we want to force Terraform to create a
  # new resource first. If we do not enforce the order of: Create new endpoint config -> update sagemaker endpoint -> Destroy old endpoint config
  # Sagemaker will error when it tries to update from the old (destroyed) config to the new one.  This has no impact on runtime or uptime,
  # Sagemaker endpoints can function even if you destroy a config and do not give it a new one.
  lifecycle {
    create_before_destroy = true    
  }
}

resource "aws_sagemaker_endpoint" "ep" {
  name = "mlops-template-${var.branch}-endpoint"
  endpoint_config_name = aws_sagemaker_endpoint_configuration.epc.name
  tags = var.tags
  depends_on = [aws_sagemaker_endpoint_configuration.epc]
}

resource "aws_appautoscaling_target" "sagemaker_target_v1" {
  max_capacity = var.autoscaling_config.max_instance_count
  min_capacity = var.autoscaling_config.min_instance_count
  resource_id = "endpoint/${aws_sagemaker_endpoint.ep.name}/variant/${aws_sagemaker_model.model.name}" 
  role_arn  = aws_iam_role.sagemaker_role.arn
  scalable_dimension = "sagemaker:variant:DesiredInstanceCount"
  service_namespace  = "sagemaker"
  depends_on = [aws_sagemaker_endpoint.ep, aws_iam_role.sagemaker_role]
}

resource "aws_appautoscaling_policy" "sagemaker_policy_v1" {
  name  = "${var.service_name}-target-tracking"
  policy_type = "TargetTrackingScaling"
  resource_id = aws_appautoscaling_target.sagemaker_target_v1.resource_id
  scalable_dimension = aws_appautoscaling_target.sagemaker_target_v1.scalable_dimension
  service_namespace  = aws_appautoscaling_target.sagemaker_target_v1.service_namespace

  target_tracking_scaling_policy_configuration {
    customized_metric_specification {
      metric_name = "CPUUtilisation"
      namespace = "/aws/sagemaker/Endpoints"
      statistic = "Average"
      unit = "Percent"
      dimensions {
        name  = "EndpointName"
        value = aws_sagemaker_endpoint.ep.name
      }
      dimensions {
        name  = "VariantName"
        value = "AllTraffic"
      }
    }
    target_value       = var.autoscaling_config.target_cpu_utilization
    scale_in_cooldown  = var.autoscaling_config.target_scale_in_cooldown
    scale_out_cooldown = var.autoscaling_config.target_scale_out_cooldown
  }
  depends_on = [aws_sagemaker_endpoint.ep, aws_appautoscaling_target.sagemaker_target_v1]
}

