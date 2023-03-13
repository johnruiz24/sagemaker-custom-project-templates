module "feature_env"{
    source                    = "../modules/environment"
    aws_account_number        = var.aws_account_number
    service_name              = "${var.project_alias}-${var.branch}"
    branch                    = var.branch

    tags = {
      application    = "${var.project_alias}"
      service        = "${var.project_alias}-${var.branch}"
      account        = "mll-dev"
      businessunit   = "machinelearninglab"
      subunit        = "machinelearninglab"
      classification = "internal"
      contact        = "a44e37f5.TUIGroup.onmicrosoft.com@emea.teams.ms"
      version        = "1.0.0"
      env            = "${var.branch}"
    }
}
