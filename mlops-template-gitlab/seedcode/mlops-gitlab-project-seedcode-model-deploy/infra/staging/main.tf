module "feature_env"{
    source = "../modules/environment"
    aws_account_number = var.aws_account_number
    model_bucket_name = var.model_bucket_name
    branch = var.branch
    service_name = "mll-mlops-template-${var.branch}-${var.short_ref}"
    short_ref = var.short_ref

    autoscaling_config = {
        max_instance_count = 3
        min_instance_count = 1
        target_scale_in_cooldown = 200
        target_scale_out_cooldown = 200
        target_cpu_utilization = 80
        #target_invocations = 1000
    }
    
    tags = {
      application    = "mll-mlops-template"
      service        = "mll-mlops-template-${var.branch}"
      account        = "mll-dev"
      businessunit   = "machinelearninglab"
      subunit        = "machinelearninglab"
      classification = "internal"
      contact        = "a44e37f5.TUIGroup.onmicrosoft.com@emea.teams.ms"
      version        = "1.0.0"
      env            = "${var.branch}"
    }
}
